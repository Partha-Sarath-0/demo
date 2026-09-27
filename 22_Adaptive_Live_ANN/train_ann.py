"""
Stage 1 - Train a base multi-output ANN (runs on Kaggle, Google Colab or locally).

Solar-collector dataset: design/operating conditions (INPUTS) -> thermal/hydraulic results (TARGETS).
One network predicts all TARGETS at once. Each target is standardised separately, so
large values (Qu_W, dp_channel_Pa) and small ones (eta) are learnt equally well.

Usage on Kaggle / Colab: paste into a notebook cell, set CSV_PATH, run.
With CSV_PATH = None a synthetic demo dataset (same column names) is used.

Outputs (folder `ann_artifacts/`), used later by the live dashboard:
  model.keras, preprocessor.joblib, metadata.json, reference_data.csv, loss_curve.png
"""
import json, os
import numpy as np
import pandas as pd
import joblib
import tensorflow as tf
from tensorflow import keras
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error

# ---------------- CONFIG ----------------
CSV_PATH = None        # e.g. "/kaggle/input/collector/data.csv" or "/content/data.csv"

# What you set / know BEFORE running the simulation
INPUTS = [
    "arrangement", "f_interdig",                                   # layout
    "G_T_W_m2", "T_in_K", "T_amb_K", "v_wind_m_s", "mdot_total_kg_s",  # operating conditions
    "bridge_mm", "g_ratio", "lambda_G",                            # geometry
    "Dh_in_mm", "Dh_out_mm", "A_in_mm2", "A_out_mm2",
]

# What the simulation computes (the ANN predicts all of these together)
TARGETS = [
    "T_out_K", "dT_fluid_K", "Qu_W", "eta",
    "dp_channel_Pa", "W_pump_W",
    "T_plate_mean_K", "T_plate_max_K", "plate_spread_K",
    "U_L_W_m2K",
]

ONLY_CONVERGED = True  # drop rows where converged is False
EPOCHS = 300
BATCH_SIZE = 32
OUT_DIR = "ann_artifacts"
SEED = 42
# ----------------------------------------

np.random.seed(SEED)
tf.random.set_seed(SEED)


def make_demo_data(n=3000):
    """Rough synthetic stand-in with the same column names, only for testing the pipeline."""
    r = np.random.default_rng(SEED)
    d = pd.DataFrame({
        "arrangement": r.choice(["parallel", "interdigitated"], n), "f_interdig": r.uniform(0, 1, n),
        "G_T_W_m2": r.uniform(200, 1100, n), "T_in_K": r.uniform(290, 350, n),
        "T_amb_K": r.uniform(270, 310, n), "v_wind_m_s": r.uniform(0, 8, n),
        "mdot_total_kg_s": r.uniform(0.005, 0.05, n), "bridge_mm": r.uniform(1, 5, n),
        "g_ratio": r.uniform(0.2, 0.8, n), "lambda_G": r.uniform(0.5, 2, n),
        "Dh_in_mm": r.uniform(2, 8, n), "Dh_out_mm": r.uniform(2, 8, n),
        "A_in_mm2": r.uniform(5, 50, n), "A_out_mm2": r.uniform(5, 50, n),
        "converged": True,
    })
    UL = 3 + 0.6 * d.v_wind_m_s
    Qu = 2.0 * (0.8 * d.G_T_W_m2 - UL * (d.T_in_K - d.T_amb_K)) * (0.9 + 0.05 * (d.arrangement == "interdigitated"))
    dT = Qu / (d.mdot_total_kg_s * 4180)
    d["U_L_W_m2K"], d["Qu_W"], d["dT_fluid_K"] = UL, Qu, dT
    d["T_out_K"] = d.T_in_K + dT
    d["eta"] = Qu / (2.0 * d.G_T_W_m2)
    d["dp_channel_Pa"] = 1e5 * d.mdot_total_kg_s ** 1.8 / (d.Dh_in_mm / 5) ** 4.8
    d["W_pump_W"] = d.dp_channel_Pa * d.mdot_total_kg_s / 1000
    d["T_plate_mean_K"] = d.T_in_K + dT / 2 + 0.01 * d.G_T_W_m2
    d["plate_spread_K"] = 0.005 * d.G_T_W_m2 * d.bridge_mm
    d["T_plate_max_K"] = d.T_plate_mean_K + d.plate_spread_K / 2
    return d


df = pd.read_csv(CSV_PATH) if CSV_PATH else make_demo_data()
print(f"Loaded {len(df)} rows")

if ONLY_CONVERGED and "converged" in df.columns:
    df = df[df["converged"].astype(str).str.lower().isin(["true", "1", "yes"])]
    print(f"Converged rows: {len(df)}")

missing = [c for c in INPUTS + TARGETS if c not in df.columns]
if missing:
    raise ValueError(f"Columns not in CSV: {missing}")

df = df.dropna(subset=TARGETS)
X = df[INPUTS].copy()
Y = df[TARGETS].astype(float)

# drop inputs that never change (they carry no information)
const = [c for c in INPUTS if X[c].nunique() <= 1]
if const:
    print("Dropping constant inputs:", const)
    X = X.drop(columns=const)

num_cols = X.select_dtypes(include="number").columns.tolist()
cat_cols = [c for c in X.columns if c not in num_cols]
X[num_cols] = X[num_cols].fillna(X[num_cols].median())
X[cat_cols] = X[cat_cols].fillna("missing").astype(str)
print("Numeric inputs:", num_cols, "\nCategorical inputs:", cat_cols)

x_pre = ColumnTransformer([
    ("num", StandardScaler(), num_cols),
    ("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False), cat_cols),
])
y_scaler = StandardScaler()

X_tr, X_te, Y_tr, Y_te = train_test_split(X, Y, test_size=0.2, random_state=SEED)
X_tr_p = x_pre.fit_transform(X_tr).astype("float32")
X_te_p = x_pre.transform(X_te).astype("float32")
Y_tr_s = y_scaler.fit_transform(Y_tr).astype("float32")

# ---------------- MODEL ----------------
def build_model(n_in, n_out):
    inp = keras.Input(shape=(n_in,))
    h = keras.layers.Dense(128, activation="relu")(inp)
    h = keras.layers.Dense(128, activation="relu")(h)
    h = keras.layers.Dense(64, activation="relu")(h)
    out = keras.layers.Dense(n_out)(h)              # one linear neuron per target
    m = keras.Model(inp, out)
    m.compile(optimizer=keras.optimizers.Adam(1e-3), loss="mse", metrics=["mae"])
    return m

model = build_model(X_tr_p.shape[1], len(TARGETS))
model.summary()
history = model.fit(
    X_tr_p, Y_tr_s, validation_split=0.15, epochs=EPOCHS, batch_size=BATCH_SIZE, verbose=2,
    callbacks=[keras.callbacks.EarlyStopping(patience=25, restore_best_weights=True),
               keras.callbacks.ReduceLROnPlateau(patience=10, factor=0.5)])

# ---------------- EVALUATE (per target, in real units) ----------------
Y_pred = y_scaler.inverse_transform(model.predict(X_te_p, verbose=0))
metrics = {}
for i, t in enumerate(TARGETS):
    yt, yp = Y_te[t].values, Y_pred[:, i]
    metrics[t] = {"r2": float(r2_score(yt, yp)), "mae": float(mean_absolute_error(yt, yp)),
                  "rmse": float(np.sqrt(mean_squared_error(yt, yp)))}
report = pd.DataFrame(metrics).T
print("\nTest metrics per target:\n", report.round(4))
print("Mean R2:", round(report.r2.mean(), 4))

# ---------------- SAVE ----------------
os.makedirs(OUT_DIR, exist_ok=True)
model.save(f"{OUT_DIR}/model.keras")
joblib.dump({"x_preprocessor": x_pre, "y_scaler": y_scaler}, f"{OUT_DIR}/preprocessor.joblib")

ref_stats = {c: {"mean": float(X_tr[c].mean()), "std": float(X_tr[c].std()),
                 "min": float(X_tr[c].min()), "max": float(X_tr[c].max())} for c in num_cols}
ref_stats.update({c: {"freq": X_tr[c].value_counts(normalize=True).round(4).to_dict()} for c in cat_cols})
meta = {"inputs": num_cols + cat_cols, "numeric_inputs": num_cols, "categorical_inputs": cat_cols,
        "targets": TARGETS, "baseline_metrics": metrics, "mean_r2": float(report.r2.mean()),
        "reference_stats": ref_stats, "n_train": int(len(X_tr)), "model_version": 1}
json.dump(meta, open(f"{OUT_DIR}/metadata.json", "w"), indent=2)
df[num_cols + cat_cols + TARGETS].to_csv(f"{OUT_DIR}/reference_data.csv", index=False)

try:
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(1, 2, figsize=(12, 4))
    ax[0].plot(history.history["loss"], label="train"); ax[0].plot(history.history["val_loss"], label="val")
    ax[0].set_yscale("log"); ax[0].set_xlabel("epoch"); ax[0].set_title("Loss (scaled MSE)"); ax[0].legend()
    report.r2.plot.barh(ax=ax[1]); ax[1].set_xlim(min(0, report.r2.min()), 1); ax[1].set_title("Test R² per target")
    plt.tight_layout(); plt.savefig(f"{OUT_DIR}/loss_curve.png", dpi=120); plt.show()
except Exception:
    pass

print(f"\nSaved to ./{OUT_DIR}/ -> download this folder; the dashboard will load it.")
# Kaggle: files appear under Output (/kaggle/working/ann_artifacts).
# Colab : !zip -r ann_artifacts.zip ann_artifacts
#         from google.colab import files; files.download("ann_artifacts.zip")
