"""Stage 5 - NSGA-II multi-objective design optimisation on the Stage 3 ANN surrogate.

Decision variables (inside the campaign bounds only - no extrapolation):
  mdot_total 1.0-4.5 g/s, bridge 20-37 mm, g_ratio 0.35-1.0, lambda_G 0.5-2.0.
Arrangement is discrete: NSGA-II is run separately for alternating and parallel and the fronts
are merged (exact for a single binary variable).
Reference operating point (ENGINEERING_ASSUMPTION, Berhampur-representative clear-sky noon):
  G_T 800 W/m2, T_in 313.15 K (40 C), T_amb 303.15 K (30 C), wind 3.0 m/s.
Objectives: maximise eta; minimise plate_std_K; minimise pumping power W = dp * mdot / rho.
Surrogate = mean of the 10-member tuned ANN ensemble; the ensemble spread is carried with each
Pareto point. Selected points are re-evaluated with GRAIL-CHT in stage5_verify.py.
"""
import pickle, json, numpy as np, pandas as pd
from pymoo.core.problem import Problem
from pymoo.algorithms.moo.nsga2 import NSGA2
from pymoo.optimize import minimize

S = pickle.load(open("/home/claude/grail_cfd/21_surrogate/ann_surrogate.pkl", "rb"))
M, XC = S["models"], S["X_COLS"]
REF = dict(G_T_W_m2=800.0, T_in_K=313.15, T_amb_K=303.15, v_wind_m_s=3.0)
VAR = ["mdot_total_kg_s", "bridge_mm", "g_ratio", "lambda_G"]
LO = np.array([S["bounds"][v][0] for v in VAR]); HI = np.array([S["bounds"][v][1] for v in VAR])
OUT = "/home/claude/grail_cfd/23_optimisation"
import os; os.makedirs(OUT, exist_ok=True)


def build(Xv, topo):
    Z = np.zeros((len(Xv), len(XC)))
    for j, c in enumerate(XC):
        Z[:, j] = REF[c] if c in REF else (topo if c == "f_interdig" else Xv[:, VAR.index(c)])
    return Z


def predict(Xv, topo):
    Z = build(Xv, topo)
    out = {}
    for n in ["eta", "plate_std_K", "log_dp_Pa"]:
        P = np.array([m.predict(Z) for m in M[n]])
        out[n], out[n + "_sd"] = P.mean(0), P.std(0)
    out["dp_Pa"] = np.exp(out["log_dp_Pa"])
    out["W_pump_W"] = out["dp_Pa"] * Xv[:, 0] / 997.0
    return out


class Prob(Problem):
    def __init__(self, topo):
        super().__init__(n_var=4, n_obj=3, xl=LO, xu=HI); self.topo = topo

    def _evaluate(self, X, out, *a, **k):
        p = predict(X, self.topo)
        out["F"] = np.column_stack([-p["eta"], p["plate_std_K"], p["W_pump_W"]])


fronts = []
for topo in (1, 0):
    res = minimize(Prob(topo), NSGA2(pop_size=200), ("n_gen", 250), seed=7, verbose=False)
    X = res.X; p = predict(X, topo)
    df = pd.DataFrame(X, columns=VAR); df["arrangement"] = "alternating" if topo else "parallel"
    for k in ["eta", "eta_sd", "plate_std_K", "plate_std_K_sd", "dp_Pa", "W_pump_W"]:
        df[k] = p[k]
    fronts.append(df)
    print(topo, len(df), "eta %.4f-%.4f  std %.2f-%.2f K  W %.2e-%.2e W" % (
        df.eta.min(), df.eta.max(), df.plate_std_K.min(), df.plate_std_K.max(), df.W_pump_W.min(), df.W_pump_W.max()))
A = pd.concat(fronts, ignore_index=True)
# global non-dominated filter across the two arrangements
F = np.column_stack([-A.eta, A.plate_std_K, A.W_pump_W]).astype(float)
nd = np.ones(len(A), bool)
for i in range(len(A)):
    nd[i] = not np.any(np.all(F <= F[i], 1) & np.any(F < F[i], 1))
A["global_nondominated"] = nd
A.to_csv(f"{OUT}/pareto_fronts.csv", index=False)

# representative points: per arrangement - max eta, min plate_std, knee (closest to utopia in
# normalised objective space); plus the as-built design evaluated by the same surrogate
sel = []
for arr, g in A.groupby("arrangement"):
    Fn = np.column_stack([-g.eta, g.plate_std_K, g.W_pump_W]).astype(float)
    Fn = (Fn - Fn.min(0)) / (Fn.max(0) - Fn.min(0) + 1e-12)
    for tag, i in [("max_eta", g.eta.idxmax()), ("min_std", g.plate_std_K.idxmin()),
                   ("knee", g.index[np.argmin(np.linalg.norm(Fn, axis=1))])]:
        sel.append(dict(A.loc[i], pick=tag))
for topo in (1, 0):
    xb = np.array([[0.00275, 31.285944, 0.539935, 1.0]]); p = predict(xb, topo)
    sel.append(dict(zip(VAR, xb[0]), arrangement="alternating" if topo else "parallel", pick="as_built",
                    **{k: float(p[k][0]) for k in ["eta", "eta_sd", "plate_std_K", "plate_std_K_sd", "dp_Pa", "W_pump_W"]}))
pd.DataFrame(sel).to_csv(f"{OUT}/selected_points_surrogate.csv", index=False)
print(pd.DataFrame(sel)[["arrangement", "pick", *VAR, "eta", "plate_std_K", "W_pump_W"]].round(5).to_string())
print("global nondominated by arrangement:", A[A.global_nondominated].arrangement.value_counts().to_dict())
