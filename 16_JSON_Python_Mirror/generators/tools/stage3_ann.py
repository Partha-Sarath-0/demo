"""Stage 3 - ANN surrogate of GRAIL-CHT, trained on the frozen Rev 4.2 dataset (read-only).

Design
- Inputs (9, all sampled model inputs): G_T, T_in, T_amb, v_wind, mdot_total, bridge, g_ratio,
  lambda_G, f_interdig. No derived column is used as an input (no leakage).
- Targets (4): eta, plate_std_K, log(dp_channel_Pa), T_plate_mean_K.
- Split: 20 % hold-out test set (stratified by arrangement, seed 42), never seen during tuning.
- Tuning: 5-fold CV grid search on the 80 % training set, per target.
- Model: scikit-learn MLPRegressor (feed-forward ANN), inputs and target standardised.
- Baselines on the SAME split: linear regression and Gaussian-process regression, so the
  ANN is judged against something, not in isolation.
- Uncertainty: 10-member ensemble (different seeds) of the tuned ANN; the spread is reported.
- Explainability: SHAP (KernelExplainer) on the tuned ANN, test set, k-means background.
The dataset file is opened read-only and its md5 is recorded; nothing is written back to it.
"""
import json, hashlib, time, pickle, os
import numpy as np, pandas as pd
from sklearn.model_selection import train_test_split, GridSearchCV, KFold
from sklearn.neural_network import MLPRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline
from sklearn.compose import TransformedTargetRegressor
from sklearn.linear_model import LinearRegression
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import RBF, WhiteKernel, ConstantKernel as C
from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error
import warnings; warnings.filterwarnings("ignore")

DATA = "/home/claude/grail_cfd/19_rev41/GRAIL_CFD_dataset_FINAL_rev4.2.csv"
OUT = "/home/claude/grail_cfd/21_surrogate"
os.makedirs(OUT, exist_ok=True)
X_COLS = ["G_T_W_m2", "T_in_K", "T_amb_K", "v_wind_m_s", "mdot_total_kg_s",
          "bridge_mm", "g_ratio", "lambda_G", "f_interdig"]
TARGETS = {"eta": ("eta", None), "plate_std_K": ("plate_std_K", None),
           "log_dp_Pa": ("dp_channel_Pa", "log"), "T_plate_mean_K": ("T_plate_mean_K", None)}

md5 = hashlib.md5(open(DATA, "rb").read()).hexdigest()
d = pd.read_csv(DATA)
assert len(d) == 300 and d.converged.all()
X = d[X_COLS].values
idx = np.arange(len(d))
tr, te = train_test_split(idx, test_size=0.2, random_state=42, stratify=d.f_interdig)


def target(name):
    col, tf = TARGETS[name]
    y = d[col].values.astype(float)
    return np.log(y) if tf == "log" else y


def ann(h=(32, 32), a=1e-3, seed=0):
    net = MLPRegressor(hidden_layer_sizes=h, alpha=a, activation="tanh", solver="lbfgs",
                       max_iter=5000, random_state=seed)
    return TransformedTargetRegressor(make_pipeline(StandardScaler(), net),
                                      transformer=StandardScaler())


def metrics(y, p):
    return dict(R2=r2_score(y, p), RMSE=float(np.sqrt(mean_squared_error(y, p))),
                MAE=mean_absolute_error(y, p), max_abs=float(np.max(np.abs(y - p))))


grid = {"regressor__mlpregressor__hidden_layer_sizes": [(16,), (32,), (16, 16), (32, 32), (64, 32), (32, 32, 16)],
        "regressor__mlpregressor__alpha": [1e-4, 1e-3, 1e-2, 1e-1, 1.0]}
report, models = {"dataset": DATA, "dataset_md5": md5, "n_train": len(tr), "n_test": len(te),
                  "inputs": X_COLS, "targets": {}}, {}
t0 = time.time()
for name in TARGETS:
    y = target(name)
    gs = GridSearchCV(ann(), grid, cv=KFold(5, shuffle=True, random_state=1), scoring="r2", n_jobs=2)
    gs.fit(X[tr], y[tr])
    bp = gs.best_params_
    h, a = bp["regressor__mlpregressor__hidden_layer_sizes"], bp["regressor__mlpregressor__alpha"]
    ens = [ann(h, a, seed=s).fit(X[tr], y[tr]) for s in range(10)]
    P = np.array([m.predict(X[te]) for m in ens])
    p_mean, p_std = P.mean(0), P.std(0)
    lin = make_pipeline(StandardScaler(), LinearRegression()).fit(X[tr], y[tr])
    gp = TransformedTargetRegressor(make_pipeline(StandardScaler(), GaussianProcessRegressor(
        C(1.0) * RBF(np.ones(len(X_COLS))) + WhiteKernel(1e-3), normalize_y=False,
        n_restarts_optimizer=3, random_state=0)), transformer=StandardScaler()).fit(X[tr], y[tr])
    yt = y[te]
    rec = dict(best_architecture=list(h), best_alpha=a, cv_R2_mean=gs.best_score_,
               ann_ensemble_test=metrics(yt, p_mean),
               ann_single_test_R2_range=[float(min(r2_score(yt, p) for p in P)), float(max(r2_score(yt, p) for p in P))],
               ensemble_mean_pred_std=float(p_std.mean()),
               linear_test=metrics(yt, lin.predict(X[te])), gpr_test=metrics(yt, gp.predict(X[te])),
               train_R2=r2_score(y[tr], np.mean([m.predict(X[tr]) for m in ens], 0)))
    if TARGETS[name][1] == "log":
        rec["ann_ensemble_test_in_Pa"] = metrics(np.exp(yt), np.exp(p_mean))
        rec["ann_ensemble_test_MAPE_pct"] = float(np.mean(np.abs(np.exp(p_mean) - np.exp(yt)) / np.exp(yt)) * 100)
    else:
        rec["ann_ensemble_test_MAPE_pct"] = float(np.mean(np.abs(p_mean - yt) / np.abs(yt)) * 100)
    report["targets"][name] = rec
    models[name] = ens
    pd.DataFrame({"case_id": d.case_id.values[te], "true": yt, "pred": p_mean, "pred_std": p_std}
                 ).to_csv(f"{OUT}/test_parity_{name}.csv", index=False)
    print(name, json.dumps({k: rec[k] for k in ["best_architecture", "best_alpha", "cv_R2_mean"]}),
          "test R2 ANN %.4f  GPR %.4f  lin %.4f" % (rec["ann_ensemble_test"]["R2"], rec["gpr_test"]["R2"],
                                                   rec["linear_test"]["R2"]), "%.0fs" % (time.time() - t0), flush=True)

pickle.dump({"models": models, "X_COLS": X_COLS, "TARGETS": TARGETS, "train_idx": tr, "test_idx": te,
             "bounds": {c: [float(d[c].min()), float(d[c].max())] for c in X_COLS}},
            open(f"{OUT}/ann_surrogate.pkl", "wb"))

# ---- SHAP on the ensemble mean (test set) ----
import shap
bg = shap.kmeans(X[tr], 20)
shap_out = {}
for name in ["eta", "plate_std_K", "log_dp_Pa"]:
    f = lambda Z, n=name: np.mean([m.predict(Z) for m in models[n]], 0)
    ex = shap.KernelExplainer(f, bg)
    sv = ex.shap_values(X[te], nsamples=400, silent=True)
    np.save(f"{OUT}/shap_{name}.npy", sv)
    imp = np.abs(sv).mean(0)
    shap_out[name] = dict(sorted(zip(X_COLS, map(float, imp)), key=lambda t: -t[1]))
    print("SHAP", name, {k: round(v, 5) for k, v in shap_out[name].items()}, flush=True)
report["shap_mean_abs_test"] = shap_out
np.save(f"{OUT}/X_test.npy", X[te])
json.dump(report, open(f"{OUT}/stage3_report.json", "w"), indent=1, default=float)
print("done %.0fs" % (time.time() - t0))
