"""Figures for Stages 3, 5, 6, 7 (read results only; nothing is recomputed here)."""
import json, sys, numpy as np, pandas as pd
sys.path.insert(0, "/home/claude/grail_cfd/tools")
import figstyle as S
import matplotlib.pyplot as plt

S.use()
R = "/home/claude/grail_cfd/"
FD = R + "24_figures_stage3to7/"
import os; os.makedirs(FD, exist_ok=True)
rep = json.load(open(R + "21_surrogate/stage3_report.json"))

# ---- F15 parity plots (test set) ----
labels = {"eta": ("Thermal efficiency", "-"), "plate_std_K": ("Plate temperature std", "K"),
          "log_dp_Pa": ("Channel pressure drop", "Pa"), "T_plate_mean_K": ("Mean plate temperature", "K")}
f, axs = S.fig(1, 4, w=16, h=4.3)
for ax, (k, (lab, u)) in zip(axs, labels.items()):
    t = pd.read_csv(R + "21_surrogate/test_parity_%s.csv" % k)
    y, p = (np.exp(t.true), np.exp(t.pred)) if k == "log_dp_Pa" else (t.true, t.pred)
    lo, hi = min(y.min(), p.min()), max(y.max(), p.max())
    ax.plot([lo, hi], [lo, hi], color=S.REF, lw=1)
    ax.scatter(y, p, s=22, color=S.CO, edgecolor="white", lw=0.4)
    m = rep["targets"][k]["ann_ensemble_test"]
    ax.set(xlabel="GRAIL-CHT (%s)" % u, ylabel="ANN (%s)" % u, title=lab)
    if k == "log_dp_Pa":
        ax.set_xscale("log"); ax.set_yscale("log")
    S.note(ax, "test R² %.4f\nMAPE %.2f %%" % (m["R2"], rep["targets"][k]["ann_ensemble_test_MAPE_pct"]), loc="lower right")
S.title(f, "F15  ANN surrogate on the 60-case hold-out test set", "10-member ensemble, tuned by 5-fold CV on the 240 training cases")
S.save(f, FD + "F15_ann_parity.png")

# ---- F16 SHAP importance ----
X_COLS = ["G_T", "T_in", "T_amb", "v_wind", "mdot", "bridge", "g_ratio", "lambda_G", "arrangement"]
f, axs = S.fig(1, 3, w=16, h=4.6)
for ax, k in zip(axs, ["eta", "plate_std_K", "log_dp_Pa"]):
    sv = np.load(R + "21_surrogate/shap_%s.npy" % k)
    imp = np.abs(sv).mean(0); o = np.argsort(imp)
    ax.barh(np.array(X_COLS)[o], imp[o], color=S.CO)
    ax.set(xlabel="mean |SHAP| (%s)" % {"eta": "efficiency", "plate_std_K": "K", "log_dp_Pa": "ln Pa"}[k],
           title=labels[k][0])
S.title(f, "F16  What drives each output (SHAP, test set)", "design inputs: bridge, g_ratio, lambda_G; arrangement 1 = alternating")
S.save(f, FD + "F16_shap_importance.png")

# ---- F17 Pareto front ----
A = pd.read_csv(R + "23_optimisation/pareto_fronts.csv")
sel = pd.read_csv(R + "23_optimisation/selected_points_surrogate.csv")
f, axs = S.fig(1, 2, w=13, h=4.8)
for arr, col in [("parallel", S.CO), ("alternating", S.AL)]:
    g = A[A.arrangement == arr]
    axs[0].scatter(g.plate_std_K, g.eta, s=12, color=col, label=arr, alpha=0.8)
    axs[1].scatter(g.mdot_total_kg_s * 1000, g.eta, s=12, color=col, label=arr, alpha=0.8)
    b = sel[(sel.arrangement == arr) & (sel.pick == "as_built")]
    axs[0].scatter(b.plate_std_K, b.eta, marker="*", s=220, color=col, edgecolor="black", zorder=5)
axs[0].set(xlabel="plate temperature std (K)", ylabel="thermal efficiency (-)", title="Pareto fronts (surrogate)")
axs[1].set(xlabel="total mass flow (g/s)", ylabel="thermal efficiency (-)", title="Efficiency along the front vs flow")
S.legend(axs[0]); S.legend(axs[1])
S.note(axs[0], "★ as-built design", loc="lower right")
S.title(f, "F17  NSGA-II fronts at G 800 W/m², T_in 40 °C, T_amb 30 °C", "third objective, pumping power, is below 0.1 mW for every point")
S.save(f, FD + "F17_pareto.png")

# ---- F18 efficiency curves ----
v = pd.read_csv(R + "22_system/virtual_test_matrix_with_x.csv")
C = json.load(open(R + "22_system/efficiency_correlations.json"))
f, ax = S.fig(1, 1, w=7.5, h=4.8)
xx = np.linspace(0, 0.08, 50)
for arr, col in [("parallel", S.CO), ("alternating", S.AL)]:
    c = C[arr]; g = v[v.arrangement == arr]
    ax.plot(xx, c["eta0"] - c["a1_W_m2K"] * xx - c["a2_W_m2K2"] * 800 * xx ** 2, color=col, label="%s fit (G 800)" % arr)
    ax.scatter(g.x, g.eta, color=col, s=26, edgecolor="white", zorder=4)
ax.set(xlabel="reduced temperature (Tm − Ta)/G (K m²/W)", ylabel="thermal efficiency (-)")
S.legend(ax)
S.title(f, "F18  Collector efficiency curves from the GRAIL-CHT virtual test", "points: solver (Richardson); lines: eta0 − a1 x − a2 G x²")
S.save(f, FD + "F18_efficiency_curves.png")

# ---- F19 monthly yield + solar fraction ----
mth = pd.read_csv(R + "20_annual/monthly_collector_yield.csv", index_col=0)
res = json.load(open(R + "20_annual/stage7_results.json"))
f, axs = S.fig(1, 3, w=18, h=4.6)
m = np.arange(1, 13); wdt = 0.38
axs[0].bar(m - wdt / 2, mth["parallel_Tin313"], wdt, color=S.CO, label="parallel")
axs[0].bar(m + wdt / 2, mth["alternating_Tin313"], wdt, color=S.AL, label="alternating")
axs[0].set(xlabel="month", ylabel="useful heat (kWh/m²)", title="Collector yield, inlet 40 °C", xticks=m)
S.legend(axs[0])
sw = pd.read_csv(R + "20_annual/sizing_sweep.csv")
for arr, col in [("parallel", S.CO), ("alternating", S.AL)]:
    g = sw[sw.arrangement == arr]
    axs[1].plot(g.n_modules, g.solar_fraction * 100, marker="o", color=col, label=arr)
    axs[2].plot(g.n_modules, g.LCOH_Rs_kWh, marker="s", color=col, label=arr)
axs[2].axhline(4.70 / 0.95, color=S.REF, lw=1.2, ls=":", label="electric geyser (4.70 ÷ 0.95)")
axs[1].set(xlabel="GRAIL modules (0.528 m² each)", ylabel="solar fraction (%)", title="Solar fraction, 100 L/day at 45 °C", xticks=[1, 2, 3, 4])
axs[2].set(xlabel="GRAIL modules (0.528 m² each)", ylabel="cost of heat (Rs/kWh)", title="Levelised cost of solar heat", xticks=[1, 2, 3, 4])
S.legend(axs[1], loc="lower right"); S.legend(axs[2], loc="upper center")
S.title(f, "F19  Berhampur annual simulation (PVGIS TMY 2005-2023)", "tilt 19.3°, due south")
S.save(f, FD + "F19_annual_monthly.png")
print("figures written to", FD)
