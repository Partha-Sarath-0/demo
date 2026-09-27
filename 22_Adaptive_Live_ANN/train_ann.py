"""
Stage 1 - Advanced multi-task ANN using ALL dataset columns
(runs on Kaggle, Google Colab or locally).

How every column is used
------------------------
  ID          case_id                      -> row identifier only (kept in outputs, never learnt)
  INPUTS      design + operating conditions + solver/model configuration
  TARGETS     every other column -> predicted by the network
                - numeric targets  : regression, grouped into physics heads
                - categorical/bool : classification heads (e.g. `converged`)

Architecture (multi-task learning)
----------------------------------
  inputs -> shared trunk of residual blocks (Dense + BatchNorm + SiLU + Dropout + skip)
         -> one regression head per physics group (fluid, hydraulics, plate, energy, ...)
         -> one classification head per categorical target
  * each numeric target is standardised; strongly skewed positive targets get log1p first
  * rows that did not converge still train the `converged` head but are masked out
    of the regression heads (their physics values are unreliable)
  * inputs/targets that are constant in the dataset are dropped automatically (reported)

Outputs (folder `ann_artifacts/`), used later by the live dashboard:
  model.keras, preprocessor.joblib, metadata.json, reference_data.csv, test_metrics.csv, training.png
"""
import json, os
import numpy as np
import pandas as pd
import joblib
import tensorflow as tf
from tensorflow import keras
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, OneHotEncoder, LabelEncoder
from sklearn.compose import ColumnTransformer
from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error, accuracy_score, f1_score

# ================= CONFIG =================
CSV_PATH = None        # e.g. "/kaggle/input/collector/data.csv" or "/content/data.csv"

ID_COLS = ["case_id"]

INPUTS = [
    # layout / geometry
    "geometry_version", "arrangement", "f_interdig", "bridge_mm", "g_ratio", "lambda_G",
    "Dh_in_mm", "Dh_out_mm", "A_in_mm2", "A_out_mm2",
    # operating conditions
    "G_T_W_m2", "T_in_K", "T_amb_K", "v_wind_m_s", "mdot_total_kg_s",
    # solver / model configuration
    "solver", "Nu_closure_input", "Nu_closure_basis", "dataset_rev", "k_model",
    "outer_cap", "plate_nx", "plate_ny",
]
# TARGETS = every remaining column (computed automatically below)

CONVERGED_COL = "converged"   # regression loss is masked where this is False

# physics groups -> one output head each (matched by column name; unmatched go to "other")
GROUPS = {
    "flow":       ["mdot_channel", "Re_in", "Re_out", "mu_Pa_s", "dp_channel", "W_pump"],
    "boundary":   ["q_abs", "T_sky", "h_wind"],
    "fluid":      ["T_out", "dT_fluid", "Qu_W", "eta"],
    "plate":      ["T_plate", "plate_spread", "plate_std", "P90", "P95", "P99", "R4", "Tmean_pow4", "T_R4"],
    "energy":     ["Q_solar", "Q_rad", "Q_conv", "Q_rear", "U_L", "T_glass", "lateral_bridge"],
    "solver":     ["energy_error", "outer_iters", "residual"],
}

EPOCHS = 400
BATCH_SIZE = 32
WIDTH, N_BLOCKS, DROPOUT = 256, 4, 0.1
OUT_DIR = "ann_artifacts"
SEED = 42
# ==========================================

np.random.seed(SEED)
tf.random.set_seed(SEED)


def make_demo_data(n=3000):
    """Rough synthetic stand-in with the thesis column names, only for testing the pipeline."""
    r = np.random.default_rng(SEED)
    d = pd.DataFrame({
        "case_id": [f"C{i:05d}" for i in range(n)], "geometry_version": r.choice(["v5", "v7"], n),
        "solver": "fvm", "arrangement": r.choice(["parallel", "interdigitated"], n),
        "f_interdig": r.uniform(0, 1, n), "G_T_W_m2": r.uniform(200, 1100, n),
        "T_in_K": r.uniform(290, 350, n), "T_amb_K": r.uniform(270, 310, n),
        "v_wind_m_s": r.uniform(0, 8, n), "mdot_total_kg_s": r.uniform(0.005, 0.05, n),
        "bridge_mm": r.uniform(1, 5, n), "g_ratio": r.uniform(0.2, 0.8, n), "lambda_G": r.uniform(0.5, 2, n),
        "Dh_in_mm": r.uniform(2, 8, n), "Dh_out_mm": r.uniform(2, 8, n),
        "A_in_mm2": r.uniform(5, 50, n), "A_out_mm2": r.uniform(5, 50, n),
        "Nu_closure_input": r.choice([4.36, 7.54], n), "Nu_closure_basis": r.choice(["laminar", "fd"], n),
        "dataset_rev": 3, "k_model": r.choice(["const", "T-dep"], n), "outer_cap": 200,
        "plate_nx": r.choice([40, 80], n), "plate_ny": r.choice([20, 40], n),
    })
    UL = 3 + 0.6 * d.v_wind_m_s
    Qu = 2.0 * (0.8 * d.G_T_W_m2 - UL * (d.T_in_K - d.T_amb_K)) * (0.9 + 0.05 * (d.arrangement == "interdigitated"))
    dT = Qu / (d.mdot_total_kg_s * 4180)
    d["mdot_channel_kg_s"] = d.mdot_total_kg_s / 10
    d["mu_Pa_s"] = 1e-3 * np.exp(-0.02 * (d.T_in_K - 293))
    d["Re_in"] = 4 * d.mdot_channel_kg_s / (np.pi * d.Dh_in_mm / 1000 * d.mu_Pa_s)
    d["Re_out"] = d.Re_in * d.Dh_in_mm / d.Dh_out_mm
    d["dp_channel_Pa"] = 1e5 * d.mdot_total_kg_s ** 1.8 / (d.Dh_in_mm / 5) ** 4.8
    d["W_pump_W"] = d.dp_channel_Pa * d.mdot_total_kg_s / 1000
    d["q_abs_W_m2"] = 0.8 * d.G_T_W_m2
    d["T_sky_K"] = 0.0552 * d.T_amb_K ** 1.5
    d["h_wind_W_m2K"] = 2.8 + 3 * d.v_wind_m_s
    d["T_out_K"], d["dT_fluid_K"], d["Qu_W"] = d.T_in_K + dT, dT, Qu
    d["eta"] = Qu / (2.0 * d.G_T_W_m2)
    d["T_plate_mean_K"] = d.T_in_K + dT / 2 + 0.01 * d.G_T_W_m2
    d["plate_spread_K"] = 0.005 * d.G_T_W_m2 * d.bridge_mm
    d["T_plate_max_K"] = d.T_plate_mean_K + d.plate_spread_K / 2
    d["T_plate_min_K"] = d.T_plate_mean_K - d.plate_spread_K / 2
    d["plate_std_K"] = d.plate_spread_K / 4
    for p, z in [("P90_K", 1.28), ("P95_K", 1.64), ("P99_K", 2.33)]:
        d[p] = d.T_plate_mean_K + z * d.plate_std_K
    d["Tmean_pow4_K4"] = d.T_plate_mean_K ** 4
    d["R4_K4"] = d.Tmean_pow4_K4 * (1 + 6 * (d.plate_std_K / d.T_plate_mean_K) ** 2)
    d["T_R4_K"] = d.R4_K4 ** 0.25
    d["Q_solar_W"] = 2.0 * d.q_abs_W_m2
    d["Q_rad_W"] = 0.3 * (d.Q_solar_W - Qu); d["Q_conv_W"] = 0.5 * (d.Q_solar_W - Qu)
    d["Q_rear_W"] = 0.2 * (d.Q_solar_W - Qu)
    d["U_L_W_m2K"] = UL
    d["T_glass_mean_K"] = (d.T_plate_mean_K + d.T_amb_K) / 2
    d["lateral_bridge_W"] = 2 * d.bridge_mm * d.plate_spread_K
    d["energy_error_pct"] = np.abs(r.normal(0, 0.3, n))
    d["outer_iters"] = r.integers(10, 200, n)
    d["residual"] = 10 ** r.uniform(-9, -4, n)
    d["converged"] = d.residual < 1e-5
    return d


# ---------------- LOAD ----------------
df = pd.read_csv(CSV_PATH) if CSV_PATH else make_demo_data()
print(f"Loaded {len(df)} rows x {df.shape[1]} columns")

missing = [c for c in ID_COLS + INPUTS if c not in df.columns]
if missing:
    raise ValueError(f"Columns not in CSV: {missing}")

TARGETS = [c for c in df.columns if c not in ID_COLS + INPUTS]

# drop constant columns (no information to learn from / to predict)
dropped_const = [c for c in INPUTS + TARGETS if df[c].nunique(dropna=True) <= 1]
INPUTS = [c for c in INPUTS if c not in dropped_const]
TARGETS = [c for c in TARGETS if c not in dropped_const]
if dropped_const:
    print("Constant columns dropped:", dropped_const)

def is_categorical(s):
    return pd.api.types.is_bool_dtype(s) or not pd.api.types.is_numeric_dtype(s)

num_in = [c for c in INPUTS if not is_categorical(df[c])]
cat_in = [c for c in INPUTS if c not in num_in]
num_tg = [c for c in TARGETS if not is_categorical(df[c])]
cat_tg = [c for c in TARGETS if c not in num_tg]
print(f"Inputs : {len(num_in)} numeric + {len(cat_in)} categorical")
print(f"Targets: {len(num_tg)} regression + {len(cat_tg)} classification {cat_tg}")

# converged mask (1 = trust physics values)
if CONVERGED_COL in df.columns:
    conv_mask = df[CONVERGED_COL].astype(str).str.lower().isin(["true", "1", "yes"]).astype("float32").values
else:
    conv_mask = np.ones(len(df), dtype="float32")
print(f"Converged rows: {int(conv_mask.sum())} / {len(df)}")

# group numeric targets into physics heads
group_of = {}
for t in num_tg:
    group_of[t] = next((g for g, keys in GROUPS.items() if any(t.startswith(k) for k in keys)), "other")
head_targets = {}
for t in num_tg:
    head_targets.setdefault(group_of[t], []).append(t)
for g, ts in head_targets.items():
    print(f"  head '{g}': {ts}")

# ---------------- PREPROCESS ----------------
X = df[INPUTS].copy()
X[num_in] = X[num_in].fillna(X[num_in].median())
X[cat_in] = X[cat_in].fillna("missing").astype(str)

Yn = df[num_tg].astype(float).copy()
log_targets = [t for t in num_tg if (Yn[t].dropna() > 0).all() and abs(Yn[t].skew()) > 2]
Yn[log_targets] = np.log1p(Yn[log_targets])
print("log1p applied to skewed targets:", log_targets)
nan_mask = Yn.isna().values                 # missing target values are masked too
Yn = Yn.fillna(Yn.median())

label_encs = {t: LabelEncoder().fit(df[t].astype(str)) for t in cat_tg}

idx_tr, idx_te = train_test_split(np.arange(len(df)), test_size=0.2, random_state=SEED)

x_pre = ColumnTransformer([
    ("num", StandardScaler(), num_in),
    ("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False), cat_in),
])
y_scaler = StandardScaler().fit(Yn.iloc[idx_tr][conv_mask[idx_tr] == 1] if conv_mask[idx_tr].sum() > 0 else Yn.iloc[idx_tr])
X_p = np.vstack([x_pre.fit_transform(X.iloc[idx_tr]), x_pre.transform(X.iloc[idx_te])]).astype("float32")
X_tr_p, X_te_p = X_p[:len(idx_tr)], X_p[len(idx_tr):]
Ys = y_scaler.transform(Yn).astype("float32")


def pack_targets(idx):
    """Targets and per-element weights for each head."""
    ys, ws = {}, {}
    for g, ts in head_targets.items():
        cols = [num_tg.index(t) for t in ts]
        ys[g] = Ys[idx][:, cols]
        ws[g] = (conv_mask[idx][:, None] * (~nan_mask[idx][:, cols])).astype("float32")
    for t in cat_tg:
        ys[f"cls_{t}"] = label_encs[t].transform(df[t].astype(str).values[idx])
        ws[f"cls_{t}"] = np.ones(len(idx), dtype="float32")
    return ys, ws


# ---------------- MODEL ----------------
class MaskedMSE(keras.losses.Loss):
    """MSE that ignores masked elements; y_true carries [values | mask] concatenated."""
    def call(self, y_true, y_pred):
        n = tf.shape(y_pred)[-1]
        y, m = y_true[:, :n], y_true[:, n:]
        return tf.reduce_sum(m * tf.square(y - y_pred), -1) / (tf.reduce_sum(m, -1) + 1e-6)


def res_block(h, width, drop):
    s = h
    h = keras.layers.Dense(width)(h); h = keras.layers.BatchNormalization()(h); h = keras.layers.Activation("silu")(h)
    h = keras.layers.Dropout(drop)(h)
    h = keras.layers.Dense(width)(h); h = keras.layers.BatchNormalization()(h)
    return keras.layers.Activation("silu")(keras.layers.Add()([s, h]))


def build_model(n_in):
    inp = keras.Input(shape=(n_in,), name="inputs")
    h = keras.layers.Dense(WIDTH, activation="silu")(inp)
    for _ in range(N_BLOCKS):
        h = res_block(h, WIDTH, DROPOUT)
    outputs, losses = {}, {}
    for g, ts in head_targets.items():
        z = keras.layers.Dense(WIDTH // 2, activation="silu")(h)
        z = keras.layers.Dense(64, activation="silu")(z)
        outputs[g] = keras.layers.Dense(len(ts), name=g)(z)
        losses[g] = MaskedMSE()
    for t in cat_tg:
        k = len(label_encs[t].classes_)
        z = keras.layers.Dense(64, activation="silu")(h)
        outputs[f"cls_{t}"] = keras.layers.Dense(k, activation="softmax", name=f"cls_{t}")(z)
        losses[f"cls_{t}"] = "sparse_categorical_crossentropy"
    m = keras.Model(inp, outputs)
    m.compile(optimizer=keras.optimizers.AdamW(1e-3, weight_decay=1e-4), loss=losses)
    return m


def to_fit(ys, ws):
    """Regression heads get [y | mask] so the masked loss can use it; classification uses sample weights."""
    y_fit, sw = {}, {}
    for k in ys:
        if k in head_targets:
            y_fit[k] = np.concatenate([ys[k], ws[k]], axis=1)
            sw[k] = np.ones(len(ws[k]), dtype="float32")
        else:
            y_fit[k], sw[k] = ys[k], ws[k]
    return y_fit, sw


model = build_model(X_tr_p.shape[1])
model.summary()

# validation split taken from the training part
idx_fit, idx_val = train_test_split(np.arange(len(idx_tr)), test_size=0.15, random_state=SEED)
yf, wf = to_fit(*pack_targets(idx_tr[idx_fit]))
yv, wv = to_fit(*pack_targets(idx_tr[idx_val]))
history = model.fit(
    X_tr_p[idx_fit], yf, sample_weight=wf,
    validation_data=(X_tr_p[idx_val], yv, wv),
    epochs=EPOCHS, batch_size=BATCH_SIZE, verbose=2,
    callbacks=[keras.callbacks.EarlyStopping(patience=30, restore_best_weights=True),
               keras.callbacks.ReduceLROnPlateau(patience=12, factor=0.5, min_lr=1e-5)])

# ---------------- EVALUATE (per target, real units, converged test rows) ----------------
pred = model.predict(X_te_p, verbose=0)
Ys_pred = np.zeros((len(idx_te), len(num_tg)), dtype="float32")
for g, ts in head_targets.items():
    Ys_pred[:, [num_tg.index(t) for t in ts]] = pred[g]
Y_pred = pd.DataFrame(y_scaler.inverse_transform(Ys_pred), columns=num_tg)
Y_true = df[num_tg].iloc[idx_te].reset_index(drop=True).astype(float)
Y_pred[log_targets] = np.expm1(Y_pred[log_targets])

rows = []
ok = conv_mask[idx_te] == 1
for t in num_tg:
    m = ok & Y_true[t].notna().values
    yt, yp = Y_true[t].values[m], Y_pred[t].values[m]
    rows.append({"target": t, "head": group_of[t], "type": "regression",
                 "r2": r2_score(yt, yp), "mae": mean_absolute_error(yt, yp),
                 "rmse": float(np.sqrt(mean_squared_error(yt, yp)))})
for t in cat_tg:
    yt = label_encs[t].transform(df[t].astype(str).values[idx_te])
    yp = pred[f"cls_{t}"].argmax(1)
    rows.append({"target": t, "head": "classification", "type": "classification",
                 "accuracy": accuracy_score(yt, yp), "f1_macro": f1_score(yt, yp, average="macro")})
report = pd.DataFrame(rows).set_index("target")
pd.set_option("display.width", 160)
print("\nTest metrics:\n", report.round(4).to_string())
reg = report[report.type == "regression"]
print(f"\nMean R2 over {len(reg)} regression targets: {reg.r2.mean():.4f}   (median {reg.r2.median():.4f})")

# ---------------- SAVE ----------------
os.makedirs(OUT_DIR, exist_ok=True)
model.save(f"{OUT_DIR}/model.keras")
joblib.dump({"x_preprocessor": x_pre, "y_scaler": y_scaler, "label_encoders": label_encs},
            f"{OUT_DIR}/preprocessor.joblib")
report.to_csv(f"{OUT_DIR}/test_metrics.csv")

ref_stats = {c: {"mean": float(X[c].mean()), "std": float(X[c].std()),
                 "min": float(X[c].min()), "max": float(X[c].max())} for c in num_in}
ref_stats.update({c: {"freq": X[c].value_counts(normalize=True).round(4).to_dict()} for c in cat_in})
meta = {
    "id_cols": ID_COLS, "inputs": INPUTS, "numeric_inputs": num_in, "categorical_inputs": cat_in,
    "regression_targets": num_tg, "classification_targets": cat_tg, "heads": head_targets,
    "log_targets": log_targets, "dropped_constant": dropped_const, "converged_col": CONVERGED_COL,
    "baseline_metrics": json.loads(report.to_json(orient="index")),
    "mean_r2": float(reg.r2.mean()), "reference_stats": ref_stats,
    "n_train": int(len(idx_tr)), "model_version": 1,
    "architecture": {"width": WIDTH, "res_blocks": N_BLOCKS, "dropout": DROPOUT},
}
json.dump(meta, open(f"{OUT_DIR}/metadata.json", "w"), indent=2, default=str)
df.to_csv(f"{OUT_DIR}/reference_data.csv", index=False)

try:
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(1, 2, figsize=(14, max(4, 0.25 * len(reg))))
    ax[0].plot(history.history["loss"], label="train"); ax[0].plot(history.history["val_loss"], label="val")
    ax[0].set_yscale("log"); ax[0].set_xlabel("epoch"); ax[0].set_title("Total multi-task loss"); ax[0].legend()
    reg.r2.sort_values().plot.barh(ax=ax[1]); ax[1].set_xlim(min(0, reg.r2.min()), 1)
    ax[1].set_title("Test R² per target"); ax[1].axvline(0.9, ls="--", c="gray")
    plt.tight_layout(); plt.savefig(f"{OUT_DIR}/training.png", dpi=120); plt.show()
except Exception:
    pass

print(f"\nSaved to ./{OUT_DIR}/ -> download this folder; the dashboard will load it.")
# Kaggle: files appear under Output (/kaggle/working/ann_artifacts).
# Colab : !zip -r ann_artifacts.zip ann_artifacts
#         from google.colab import files; files.download("ann_artifacts.zip")
