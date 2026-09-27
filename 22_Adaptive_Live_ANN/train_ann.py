"""
Stage 1 - Train a base ANN (runs on Kaggle, Google Colab or locally).

Usage on Kaggle / Colab: paste this into a notebook cell (or `!python train_ann.py`),
then edit CSV_PATH and TARGET below. With CSV_PATH = None a synthetic demo dataset is used.

Outputs (folder `ann_artifacts/`), used later by the live dashboard:
  model.keras         - trained network
  preprocessor.joblib - scaler / encoder fitted on the training data
  metadata.json       - features, task type, baseline metrics, per-feature
                        reference stats (for drift detection)
  reference_data.csv  - sample of training data (for drift tests / replay)
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
from sklearn.metrics import accuracy_score, f1_score, r2_score, mean_absolute_error, mean_squared_error

# ---------------- CONFIG ----------------
CSV_PATH = None        # e.g. "/kaggle/input/my-dataset/data.csv" or "/content/data.csv"
TARGET = "target"      # name of the output column
TASK = "auto"          # "auto", "regression" or "classification"
EPOCHS = 100
BATCH_SIZE = 32
OUT_DIR = "ann_artifacts"
SEED = 42
# ----------------------------------------

np.random.seed(SEED)
tf.random.set_seed(SEED)


def make_demo_data(n=5000):
    """Synthetic regression data: y depends non-linearly on x1..x4."""
    rng = np.random.default_rng(SEED)
    df = pd.DataFrame({
        "x1": rng.normal(0, 1, n),
        "x2": rng.uniform(-2, 2, n),
        "x3": rng.normal(5, 2, n),
        "x4": rng.choice(["A", "B", "C"], n),
    })
    df["target"] = (3 * df.x1 + np.sin(2 * df.x2) * 4 + 0.5 * df.x3 ** 1.5
                    + df.x4.map({"A": 0, "B": 2, "C": -2}) + rng.normal(0, 0.5, n))
    return df


df = pd.read_csv(CSV_PATH) if CSV_PATH else make_demo_data()
df = df.dropna(subset=[TARGET])
print(f"Data: {df.shape[0]} rows, {df.shape[1]} columns")

X, y_raw = df.drop(columns=[TARGET]), df[TARGET]
if TASK == "auto":
    TASK = "classification" if (y_raw.dtype == object or y_raw.nunique() <= 10) else "regression"
print("Task:", TASK)

num_cols = X.select_dtypes(include="number").columns.tolist()
cat_cols = [c for c in X.columns if c not in num_cols]
X[num_cols] = X[num_cols].fillna(X[num_cols].median())
X[cat_cols] = X[cat_cols].fillna("missing").astype(str)

pre = ColumnTransformer([
    ("num", StandardScaler(), num_cols),
    ("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False), cat_cols),
])

label_enc = None
if TASK == "classification":
    label_enc = LabelEncoder()
    y = label_enc.fit_transform(y_raw.astype(str))
    n_classes = len(label_enc.classes_)
else:
    y = y_raw.astype(float).values

X_tr, X_te, y_tr, y_te = train_test_split(
    X, y, test_size=0.2, random_state=SEED,
    stratify=y if TASK == "classification" else None)
X_tr_p = pre.fit_transform(X_tr).astype("float32")
X_te_p = pre.transform(X_te).astype("float32")

# ---------------- MODEL ----------------
def build_model(n_in):
    inp = keras.Input(shape=(n_in,))
    h = keras.layers.Dense(64, activation="relu")(inp)
    h = keras.layers.Dropout(0.1)(h)
    h = keras.layers.Dense(32, activation="relu")(h)
    h = keras.layers.Dense(16, activation="relu")(h)
    if TASK == "regression":
        out, loss, metrics = keras.layers.Dense(1)(h), "mse", ["mae"]
    elif n_classes == 2:
        out, loss, metrics = keras.layers.Dense(1, activation="sigmoid")(h), "binary_crossentropy", ["accuracy"]
    else:
        out, loss, metrics = keras.layers.Dense(n_classes, activation="softmax")(h), "sparse_categorical_crossentropy", ["accuracy"]
    m = keras.Model(inp, out)
    m.compile(optimizer=keras.optimizers.Adam(1e-3), loss=loss, metrics=metrics)
    return m

model = build_model(X_tr_p.shape[1])
model.summary()
history = model.fit(
    X_tr_p, y_tr, validation_split=0.15, epochs=EPOCHS, batch_size=BATCH_SIZE, verbose=2,
    callbacks=[keras.callbacks.EarlyStopping(patience=10, restore_best_weights=True),
               keras.callbacks.ReduceLROnPlateau(patience=5, factor=0.5)])

# ---------------- EVALUATE ----------------
pred = model.predict(X_te_p, verbose=0)
if TASK == "regression":
    p = pred.ravel()
    metrics = {"r2": float(r2_score(y_te, p)), "mae": float(mean_absolute_error(y_te, p)),
               "rmse": float(np.sqrt(mean_squared_error(y_te, p)))}
else:
    p = (pred.ravel() > 0.5).astype(int) if n_classes == 2 else pred.argmax(1)
    metrics = {"accuracy": float(accuracy_score(y_te, p)),
               "f1_macro": float(f1_score(y_te, p, average="macro"))}
print("Test metrics:", metrics)

# ---------------- SAVE ----------------
os.makedirs(OUT_DIR, exist_ok=True)
model.save(f"{OUT_DIR}/model.keras")
joblib.dump({"preprocessor": pre, "label_encoder": label_enc}, f"{OUT_DIR}/preprocessor.joblib")

ref_stats = {c: {"mean": float(X_tr[c].mean()), "std": float(X_tr[c].std()),
                 "min": float(X_tr[c].min()), "max": float(X_tr[c].max())} for c in num_cols}
ref_stats.update({c: {"freq": X_tr[c].value_counts(normalize=True).round(4).to_dict()} for c in cat_cols})
meta = {"target": TARGET, "task": TASK, "numeric_features": num_cols, "categorical_features": cat_cols,
        "classes": label_enc.classes_.tolist() if label_enc else None,
        "baseline_metrics": metrics, "reference_stats": ref_stats,
        "n_train": int(len(X_tr)), "model_version": 1}
json.dump(meta, open(f"{OUT_DIR}/metadata.json", "w"), indent=2)
df.sample(min(2000, len(df)), random_state=SEED).to_csv(f"{OUT_DIR}/reference_data.csv", index=False)

try:  # optional loss plot
    import matplotlib.pyplot as plt
    plt.plot(history.history["loss"], label="train"); plt.plot(history.history["val_loss"], label="val")
    plt.xlabel("epoch"); plt.ylabel("loss"); plt.legend(); plt.title("Training loss")
    plt.savefig(f"{OUT_DIR}/loss_curve.png", dpi=120); plt.show()
except Exception:
    pass

print(f"\nSaved to ./{OUT_DIR}/ -> download this folder; the dashboard will load it.")
# Kaggle: files appear under Output (/kaggle/working/ann_artifacts).
# Colab : !zip -r ann_artifacts.zip ann_artifacts  then  from google.colab import files; files.download("ann_artifacts.zip")
