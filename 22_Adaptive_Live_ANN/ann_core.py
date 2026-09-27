"""
Core logic of the Adaptive / Live ANN (no UI) - used by dashboard.py.

Loads the artifacts written by train_ann.py and provides:
  predict()        - multi-output prediction in real units
  drift_report()   - data drift of new inputs vs the reference data (KS test, PSI, range check)
  evaluate()       - accuracy of a model on labelled data
  decide()         - keep / incremental update / full retrain
  train_candidate()- build an updated model (incremental fine-tune with replay, or full retrain)
  deploy()         - make the candidate the live model (versioned, with history log)
  rollback()       - go back to an earlier version
"""
import json
import os
import shutil
import time

import joblib
import numpy as np
import pandas as pd
import tensorflow as tf
from tensorflow import keras
from scipy.stats import ks_2samp
from sklearn.metrics import r2_score, mean_absolute_error, accuracy_score
from sklearn.model_selection import train_test_split

# thresholds (documented so they can be quoted in the thesis)
KS_P = 0.01            # KS-test p-value below this ...
PSI_MOD = 0.10         # ... and PSI above this -> drift
PSI_HIGH = 0.25        # PSI above this alone -> drift
OUT_OF_RANGE = 0.10    # >10 % of new values outside training range -> drift
CAT_TVD = 0.20         # categorical: total variation distance above this -> drift
DEGRADED = 1.5         # a target is "degraded" if its RMSE > 1.5 x its training RMSE
FULL_FRAC = 0.30       # > 30 % of targets degraded ...
FULL_RATIO = 4.0       # ... or any target RMSE > 4 x baseline -> full retrain (else incremental)
FORGET_TOL = 0.02      # candidate may lose at most this much skill on old (reference) data

# "skill" = 1 - MSE / Var_ref(target): like R2 but always normalised by the variance of the
# whole reference data set, so it stays meaningful on small / narrow batches of new data.


class MaskedMSE(keras.losses.Loss):
    """Same loss as in train_ann.py: y_true = [values | mask]."""
    def call(self, y_true, y_pred):
        n = tf.shape(y_pred)[-1]
        y, m = y_true[:, :n], y_true[:, n:]
        return tf.reduce_sum(m * tf.square(y - y_pred), -1) / (tf.reduce_sum(m, -1) + 1e-6)


def truthy(s):
    return s.astype(str).str.strip().str.lower().isin(["true", "1", "1.0", "yes"])


def _psi(ref, new, bins=10):
    edges = np.unique(np.quantile(ref, np.linspace(0, 1, bins + 1)))
    if len(edges) < 3:                       # (almost) constant reference column
        return float(np.mean(~np.isin(new, np.unique(ref))))
    edges[0], edges[-1] = -np.inf, np.inf
    p = np.histogram(ref, edges)[0] / len(ref)
    q = np.histogram(new, edges)[0] / len(new)
    p, q = np.clip(p, 1e-4, None), np.clip(q, 1e-4, None)
    return float(np.sum((q - p) * np.log(q / p)))


class LiveANN:
    def __init__(self, art_dir):
        self.dir = art_dir
        self.load()

    # ---------------- loading ----------------
    def load(self):
        d = self.dir
        self.meta = json.load(open(os.path.join(d, "metadata.json")))
        pp = joblib.load(os.path.join(d, "preprocessor.joblib"))
        self.x_pre, self.y_scaler = pp["x_preprocessor"], pp["y_scaler"]
        self.label_encs = pp.get("label_encoders", {}) or {}
        self.model = keras.models.load_model(os.path.join(d, "model.keras"), compile=False)
        self.ref = pd.read_csv(os.path.join(d, "reference_data.csv"))
        hp = os.path.join(d, "history.json")
        if os.path.exists(hp):
            self.history = json.load(open(hp))
        else:
            self.history = [{"version": self.meta.get("model_version", 1), "time": "initial training",
                             "mode": "initial", "n_new": 0, "deployed": True,
                             "mean_r2": self.meta.get("mean_r2")}]

        m = self.meta
        self.inputs = m["inputs"]
        self.num_in, self.cat_in = m["numeric_inputs"], m["categorical_inputs"]
        self.num_tg = m.get("regression_targets") or m.get("targets")
        self.cat_tg = m.get("classification_targets", [])
        self.heads = m["heads"]
        self.log_tg = m.get("log_targets", [])
        self.conv_col = m.get("converged_col", "converged")
        self.stats = m["reference_stats"]
        self.baseline = {t: v.get("rmse") for t, v in m["baseline_metrics"].items() if isinstance(v, dict)}
        ok = truthy(self.ref[self.conv_col]) if self.conv_col in self.ref else pd.Series(True, index=self.ref.index)
        self.ref_var = {t: float(pd.to_numeric(self.ref.loc[ok, t], errors="coerce").var())
                        for t in self.num_tg if t in self.ref}

    @property
    def version(self):
        return self.meta.get("model_version", 1)

    # ---------------- prediction ----------------
    def prep_X(self, df):
        X = pd.DataFrame(index=df.index)
        for c in self.num_in:
            X[c] = pd.to_numeric(df[c], errors="coerce") if c in df else np.nan
            X[c] = X[c].fillna(self.stats[c]["mean"])
        for c in self.cat_in:
            X[c] = df[c].fillna("missing").astype(str) if c in df else "missing"
        return self.x_pre.transform(X[self.inputs]).astype("float32")

    def predict(self, df, model=None):
        model = model or self.model
        out = model.predict(self.prep_X(df), verbose=0)
        Ys = np.zeros((len(df), len(self.num_tg)), dtype="float32")
        for g, ts in self.heads.items():
            Ys[:, [self.num_tg.index(t) for t in ts]] = out[g]
        Y = pd.DataFrame(self.y_scaler.inverse_transform(Ys), columns=self.num_tg, index=df.index)
        if self.log_tg:
            Y[self.log_tg] = np.expm1(Y[self.log_tg])
        for t in self.cat_tg:
            p = np.asarray(out[f"cls_{t}"])
            Y[t] = self.label_encs[t].inverse_transform(p.argmax(1))
            Y[f"{t}_confidence"] = p.max(1)
        return Y

    def out_of_range(self, row):
        """Inputs of a single row that lie outside the training range."""
        bad = []
        for c in self.num_in:
            v = float(row[c])
            if v < self.stats[c]["min"] or v > self.stats[c]["max"]:
                bad.append(c)
        for c in self.cat_in:
            if str(row[c]) not in self.stats[c]["freq"]:
                bad.append(c)
        return bad

    # ---------------- monitoring ----------------
    def drift_report(self, new):
        rows = []
        for c in self.num_in:
            if c not in new:
                continue
            r = pd.to_numeric(self.ref[c], errors="coerce").dropna().values
            n = pd.to_numeric(new[c], errors="coerce").dropna().values
            if len(n) < 5:
                continue
            ks = ks_2samp(r, n)
            psi = _psi(r, n)
            oor = float(np.mean((n < r.min()) | (n > r.max())))
            drift = bool((ks.pvalue < KS_P and psi > PSI_MOD) or psi > PSI_HIGH or oor > OUT_OF_RANGE)
            rows.append({"feature": c, "type": "numeric", "ref_mean": r.mean(), "new_mean": n.mean(),
                         "ks_p": ks.pvalue, "psi": psi, "out_of_range": oor, "drift": drift})
        for c in self.cat_in:
            if c not in new:
                continue
            p = self.ref[c].astype(str).value_counts(normalize=True)
            q = new[c].astype(str).value_counts(normalize=True)
            tvd = 0.5 * float(p.reindex(p.index.union(q.index), fill_value=0)
                              .sub(q.reindex(p.index.union(q.index), fill_value=0)).abs().sum())
            unseen = float(q[~q.index.isin(p.index)].sum())
            rows.append({"feature": c, "type": "categorical", "tvd": tvd, "out_of_range": unseen,
                         "drift": bool(tvd > CAT_TVD or unseen > 0.05)})
        return pd.DataFrame(rows)

    def has_labels(self, df):
        return any(t in df.columns for t in self.num_tg)

    def evaluate(self, df, model=None):
        """Per-target metrics on labelled rows (converged rows only for regression)."""
        if not self.has_labels(df) or len(df) == 0:
            return None
        pred = self.predict(df, model)
        ok = truthy(df[self.conv_col]).values if self.conv_col in df else np.ones(len(df), bool)
        rows = []
        for t in self.num_tg:
            if t not in df:
                continue
            yt = pd.to_numeric(df[t], errors="coerce").values
            m = ok & ~np.isnan(yt)
            if m.sum() < 3 or np.var(yt[m]) == 0:
                continue
            yp = pred[t].values[m]
            rmse = float(np.sqrt(np.mean((yt[m] - yp) ** 2)))
            var = self.ref_var.get(t) or np.var(yt[m]) or 1.0
            base = self.baseline.get(t)
            rows.append({"target": t, "skill": 1 - rmse ** 2 / var, "r2": r2_score(yt[m], yp),
                         "rmse": rmse, "mae": mean_absolute_error(yt[m], yp), "baseline_rmse": base,
                         "rmse_ratio": rmse / base if base else np.nan})
        for t in self.cat_tg:
            if t in df:
                rows.append({"target": t, "accuracy": accuracy_score(df[t].astype(str), pred[t].astype(str))})
        return pd.DataFrame(rows).set_index("target") if rows else None

    @staticmethod
    def mean_r2(perf):
        """Mean skill over regression targets (ref-normalised R2)."""
        if perf is None or "skill" not in perf:
            return None
        return float(perf["skill"].dropna().mean())

    def decide(self, drift, perf):
        """Returns (decision, explanation). decision in keep / incremental / full_retrain / need_labels."""
        n_drift = int(drift["drift"].sum()) if len(drift) else 0
        if perf is None or "r2" not in perf:
            if n_drift:
                return "need_labels", (f"Data drift in {n_drift} input(s), but the new data has no target "
                                       "values, so the model cannot be checked or updated. Upload labelled data.")
            return "keep", "No drift and no labels - nothing to do."
        p = perf.dropna(subset=["rmse_ratio"])
        if not len(p):
            return "keep", "No comparable targets in the new data."
        deg = p[p.rmse_ratio > DEGRADED].sort_values("rmse_ratio", ascending=False)
        frac, worst = len(deg) / len(p), float(p.rmse_ratio.max())
        top = ", ".join(f"{i} (x{r.rmse_ratio:.1f})" for i, r in deg.head(4).iterrows()) or "none"
        info = (f"{len(deg)}/{len(p)} targets degraded (RMSE > {DEGRADED}x baseline): {top}. "
                f"Drifted inputs: {n_drift}.")
        if not len(deg):
            why = "Model still accurate on the new data" + (" despite the input drift" if n_drift else "")
            return "keep", f"{why} -> keep current model. {info}"
        if frac <= FULL_FRAC and worst <= FULL_RATIO:
            return "incremental", f"Some targets degraded -> incremental update (fine-tune with replay). {info}"
        return "full_retrain", f"Strong / widespread degradation (concept drift) -> full retrain. {info}"

    # ---------------- updating ----------------
    def _pack(self, df):
        X = self.prep_X(df)
        Yn = df.reindex(columns=self.num_tg).apply(pd.to_numeric, errors="coerce")
        if self.log_tg:
            Yn[self.log_tg] = np.log1p(Yn[self.log_tg].clip(lower=-0.999))
        nan = Yn.isna().values
        Ys = self.y_scaler.transform(Yn.fillna(0)).astype("float32")
        conv = truthy(df[self.conv_col]).values if self.conv_col in df else np.ones(len(df), bool)
        y, sw = {}, {}
        for g, ts in self.heads.items():
            cols = [self.num_tg.index(t) for t in ts]
            mask = (conv[:, None] & ~nan[:, cols]).astype("float32")
            y[g] = np.concatenate([Ys[:, cols], mask], axis=1)
            sw[g] = np.ones(len(df), dtype="float32")
        for t in self.cat_tg:
            le = self.label_encs[t]
            if t in df:
                v = df[t].astype(str).values
                known = np.isin(v, le.classes_)
                y[f"cls_{t}"] = le.transform(np.where(known, v, le.classes_[0]))
                sw[f"cls_{t}"] = known.astype("float32")
            else:
                y[f"cls_{t}"] = np.zeros(len(df), dtype=int)
                sw[f"cls_{t}"] = np.zeros(len(df), dtype="float32")
        return X, y, sw

    def _compile(self, m, lr):
        losses = {g: MaskedMSE() for g in self.heads}
        losses.update({f"cls_{t}": "sparse_categorical_crossentropy" for t in self.cat_tg})
        m.compile(optimizer=keras.optimizers.AdamW(lr, weight_decay=1e-4), loss=losses)

    def train_candidate(self, new_df, mode="incremental", epochs=None, on_epoch=None, seed=0):
        """Train an updated model. Nothing is changed until deploy() is called."""
        new_df = new_df.reset_index(drop=True)
        if len(new_df) >= 8:
            new_tr, new_val = train_test_split(new_df, test_size=0.25, random_state=seed)
        else:
            new_tr = new_val = new_df
        ref_tr, ref_val = train_test_split(self.ref, test_size=0.2, random_state=seed)

        if mode == "incremental":        # start from current weights, small LR, replay old data
            cand = keras.models.clone_model(self.model)
            cand.set_weights(self.model.get_weights())
            lr, epochs = 1e-4, epochs or 40
            replay = ref_tr.sample(min(len(ref_tr), max(2 * len(new_tr), 200)), random_state=seed)
            train = pd.concat([new_tr, replay], ignore_index=True)
        else:                            # fresh weights, same architecture, all data
            cand = keras.models.clone_model(self.model)
            lr, epochs = 1e-3, epochs or 200
            train = pd.concat([ref_tr, new_tr], ignore_index=True)
        self._compile(cand, lr)

        val = pd.concat([new_val, ref_val.sample(min(len(ref_val), 300), random_state=seed)], ignore_index=True)
        X, y, sw = self._pack(train)
        Xv, yv, swv = self._pack(val)
        cbs = [keras.callbacks.EarlyStopping(patience=10 if mode == "incremental" else 25,
                                             restore_best_weights=True)]
        if on_epoch:
            cbs.append(keras.callbacks.LambdaCallback(on_epoch_end=lambda e, logs: on_epoch(e, epochs, logs)))
        hist = cand.fit(X, y, sample_weight=sw, validation_data=(Xv, yv, swv), epochs=epochs,
                        batch_size=32, verbose=0, callbacks=cbs)

        res = {"mode": mode, "candidate": cand, "n_new": len(new_df),
               "loss": hist.history["loss"], "val_loss": hist.history["val_loss"],
               "old_new": self.evaluate(new_val), "cand_new": self.evaluate(new_val, cand),
               "old_ref": self.evaluate(ref_val), "cand_ref": self.evaluate(ref_val, cand),
               "cand_all": self.evaluate(val, cand),
               "new_df": new_df}
        r = {k: self.mean_r2(res[k]) for k in ["old_new", "cand_new", "old_ref", "cand_ref"]}
        res["scores"] = r
        better = r["cand_new"] is not None and r["old_new"] is not None and r["cand_new"] > r["old_new"]
        no_forget = r["cand_ref"] is None or r["old_ref"] is None or r["cand_ref"] >= r["old_ref"] - FORGET_TOL
        res["accept"] = bool(better and no_forget)
        res["reason"] = ("Candidate is better on the new data and keeps accuracy on old data."
                         if res["accept"] else
                         "Rejected: " + ("not better on new data. " if not better else "") +
                         ("forgets old data (skill on reference data dropped too much)." if not no_forget else ""))
        return res

    def _save_history(self):
        json.dump(self.history, open(os.path.join(self.dir, "history.json"), "w"), indent=2, default=str)

    def log_rejected(self, res):
        self.history.append({"version": None, "time": time.strftime("%Y-%m-%d %H:%M:%S"), "mode": res["mode"],
                             "n_new": res["n_new"], "deployed": False, **res["scores"], "reason": res["reason"]})
        self._save_history()

    def deploy(self, res):
        d, old_v = self.dir, self.version
        vdir = os.path.join(d, "versions")
        os.makedirs(os.path.join(vdir, f"v{old_v}"), exist_ok=True)
        old_path = os.path.join(vdir, f"v{old_v}", "model.keras")
        if not os.path.exists(old_path):
            shutil.copy(os.path.join(d, "model.keras"), old_path)
        new_v = max([old_v] + [h["version"] for h in self.history if h.get("version")]) + 1
        os.makedirs(os.path.join(vdir, f"v{new_v}"), exist_ok=True)
        res["candidate"].save(os.path.join(vdir, f"v{new_v}", "model.keras"))
        res["candidate"].save(os.path.join(d, "model.keras"))

        # new data becomes part of the reference (drift baseline + future replay)
        self.ref = pd.concat([self.ref, res["new_df"].reindex(columns=self.ref.columns)], ignore_index=True)
        self.ref.to_csv(os.path.join(d, "reference_data.csv"), index=False)

        # new per-target baseline = candidate accuracy on held-out old + new data
        perf = res["cand_all"]
        if perf is not None and "rmse" in perf:
            for t, r in perf.dropna(subset=["rmse"]).iterrows():
                self.meta["baseline_metrics"].setdefault(t, {}).update({"rmse": r.rmse, "r2": r.skill})
        self.meta["model_version"] = new_v
        self.meta["mean_r2"] = float(np.mean([v["r2"] for v in self.meta["baseline_metrics"].values()
                                              if isinstance(v, dict) and v.get("r2") is not None]))
        json.dump(self.meta, open(os.path.join(d, "metadata.json"), "w"), indent=2, default=str)

        self.history.append({"version": new_v, "time": time.strftime("%Y-%m-%d %H:%M:%S"), "mode": res["mode"],
                             "n_new": res["n_new"], "deployed": True, **res["scores"],
                             "mean_r2": self.meta["mean_r2"]})
        self._save_history()
        self.load()
        return new_v

    def available_versions(self):
        vdir = os.path.join(self.dir, "versions")
        if not os.path.isdir(vdir):
            return []
        return sorted(int(v[1:]) for v in os.listdir(vdir)
                      if v.startswith("v") and os.path.exists(os.path.join(vdir, v, "model.keras")))

    def rollback(self, v):
        shutil.copy(os.path.join(self.dir, "versions", f"v{v}", "model.keras"), os.path.join(self.dir, "model.keras"))
        self.meta["model_version"] = v
        json.dump(self.meta, open(os.path.join(self.dir, "metadata.json"), "w"), indent=2, default=str)
        self.history.append({"version": v, "time": time.strftime("%Y-%m-%d %H:%M:%S"), "mode": "rollback",
                             "n_new": 0, "deployed": True})
        self._save_history()
        self.load()
