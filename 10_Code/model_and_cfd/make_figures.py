"""All figures of the current (Rev 4 / 3-D benchmark) results. Reads only saved results."""
import os, sys, json, csv
import numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
sys.path.insert(0, os.path.dirname(__file__))
import cht_post as P

R = "/home/claude/grail_cfd"; B = R + "/15_benchmark"; DS = R + "/10_dataset"; CH = R + "/06_cht"
OUT = sys.argv[1] if len(sys.argv) > 1 else R + "/16_figures"
os.makedirs(OUT, exist_ok=True)
CO, ALT, GREY, INK, MUT = "#2a78d6", "#eb6834", "#8a8984", "#0b0b0b", "#52514e"
plt.rcParams.update({"font.size": 10, "axes.edgecolor": "#b5b4ad", "axes.labelcolor": INK,
    "xtick.color": MUT, "ytick.color": MUT, "axes.grid": True, "grid.color": "#e6e5e0",
    "grid.linewidth": 0.6, "axes.spines.top": False, "axes.spines.right": False,
    "lines.linewidth": 2, "lines.markersize": 7, "legend.frameon": False, "savefig.dpi": 200,
    "figure.facecolor": "white"})
J = lambda f: json.load(open(f))
def save(fig, name):
    fig.tight_layout(); fig.savefig(os.path.join(OUT, name)); plt.close(fig); print("fig", name)

# 1 -- 3-D axial grid study
ax_ = J(B + "/cht3d_axial_study.json"); nx = [60, 120, 240]
d = lambda k, lv: 100 * (ax_[lv + "_alt"][k] / ax_[lv + "_co"][k] - 1)
fig, a = plt.subplots(1, 2, figsize=(9, 3.6))
a[0].plot(nx, [d("eta", "nx%d" % n) for n in nx], "o-", color=INK)
a[0].set(xscale="log", xticks=nx, xticklabels=nx, xlabel="axial cells NX (NU 64)", ylabel="Δη alt vs co (%)",
         title="Efficiency difference — converged")
a[1].plot(nx, [d("Tp_std", "nx%d" % n) for n in nx], "o-", color=INK)
a[1].set(xscale="log", xticks=nx, xticklabels=nx, xlabel="axial cells NX (NU 64)", ylabel="Δ plate std (%)",
         title="Uniformity difference — oscillatory")
for q in a: q.minorticks_off(); q.set_xticks(nx); q.set_xticklabels(nx)
save(fig, "F01_3D_axial_grid_study.png")

# 2 -- cross-section Nu study
nu = J(B + "/nu_developed_summary.json")
cells = [80640, 138240, 322560]; lv = ["NU48", "NU64", "NU96"]
h = [(c / cells[-1]) ** -0.5 for c in cells]
fig, a = plt.subplots(figsize=(6.4, 4))
a.plot(h, [np.mean(nu[k]) for k in lv], "o-", color=CO, label="3-D conjugate, developed region")
a.plot([0], [4.48], "D", color=INK, label="extrapolated 4.48 (GCI 2.1 %)")
a.plot([0, h[-1]], [4.48, np.mean(nu["NU96"])], ":", color=INK, lw=1)
a.axhline(4.088, color=GREY, ls="--", lw=1); a.text(1.02, 4.10, "H1 reference 4.088", color=MUT, fontsize=8)
a.axhline(2.9238, color=ALT, ls="--", lw=1); a.text(1.02, 2.94, "campaign Rev 1–3: 2.9238 (H2-type)", color=MUT, fontsize=8)
for x, k in zip(h, lv): a.annotate(k, (x, np.mean(nu[k])), textcoords="offset points", xytext=(0, 8), ha="center", fontsize=8, color=MUT)
a.set(xlabel="relative cross-section cell size h/h_NU96", ylabel="Nu", ylim=(2.7, 4.9), xlim=(-0.05, 2.3),
      title="Nusselt closure: cross-section grid study")
a.legend(loc="center right"); save(fig, "F02_Nu_cross_section_study.png")

# 3 -- Nu(x) profiles
def prof(f):
    dd = J(f); out = []
    for t in ("y_low", "y_high"):
        v = dd[t]; s = v["stations"]; x = np.array([q["x"] for q in s]); n = np.array([q["Nu"] for q in s])
        xi = (x - x.min()) / (x.max() - x.min()); xi = xi if v["flow_sign"] > 0 else 1 - xi
        o = np.argsort(xi); out.append((xi[o], n[o]))
    return out
fig, a = plt.subplots(1, 2, figsize=(10, 3.8))
for f, lab, c in (("nu_co_nu48_nr4_nx120.json", "NU 48", "#86b6ef"), ("nu_co_nx120.json", "NU 64", CO), ("nu_co_nu96_nr8_nx120.json", "NU 96", "#104281")):
    xi, n = prof(B + "/" + f)[0]; a[0].plot(xi, n, color=c, label=lab, lw=1.6)
a[0].set(ylim=(3.5, 7), xlabel="ξ along flow", ylabel="local Nu", title="Grid levels (design flow)"); a[0].legend()
for f, lab, c in (("nu_co_nx120_m1p0.json", "1.0 g/s", "#86b6ef"), ("nu_co_nx120.json", "2.49 g/s (design)", CO), ("nu_co_nx120_m4p5.json", "4.5 g/s", "#104281")):
    xi, n = prof(B + "/" + f)[0]; a[1].plot(xi, n, color=c, label=lab, lw=1.6)
a[1].set(ylim=(3.5, 7), xlabel="ξ along flow", ylabel="local Nu", title="Flow envelope (NU 64)"); a[1].legend()
save(fig, "F03_Nu_profiles.png")

# 4 -- ROM axial convergence vs 3-D
rd = J(B + "/rom_design_axial.json"); nxs = [220, 440, 880]
dstd = [100 * (rd["alt_nx%d" % n]["Tp_std"] / rd["co_nx%d" % n]["Tp_std"] - 1) for n in nxs]
fig, a = plt.subplots(figsize=(6.4, 4))
a.plot([1 / 110] + [1 / n for n in nxs], [-10.51] + dstd, "o-", color=CO, label="GRAIL-CHT (ROM), Nu 4.6")
a.plot([0], [-7.33], "D", color=CO); a.annotate("extrapolated −7.33 %", (0, -7.33), xytext=(6, -12), textcoords="offset points", fontsize=8, color=MUT)
a.axhspan(-5.37 - 0.5, -5.37 + 0.5, color=ALT, alpha=0.15, lw=0)
a.axhline(-5.37, color=ALT, lw=1.5, label="3-D conjugate NX 240 (NU 64), ±0.5 pp")
a.axvline(1 / 110, color=GREY, ls=":", lw=1); a.text(1 / 110, -10.9, " Rev 1–3 grid", fontsize=8, color=MUT)
a.set(xlabel="1 / axial plate cells", ylabel="Δ plate std alt vs co (%)", title="Model-form gap after both grids converge ≈ 2 pp")
a.legend(loc="lower left"); save(fig, "F04_ROM_vs_3D_axial.png")

# 5 -- per-arrangement ROM vs 3-D bars
c3, a3 = ax_["nx240_co"], ax_["nx240_alt"]
ex = lambda arr, k: 2 * rd[arr + "_nx880"][k] - rd[arr + "_nx440"][k]
fig, a = plt.subplots(1, 2, figsize=(9, 3.6)); w = 0.36; x = np.arange(2)
for i, (k, lab) in enumerate((("eta", "efficiency η"), ("Tp_std", "plate std (K)"))):
    a[i].bar(x - w / 2 - 0.01, [c3[k], a3[k]], w, color=GREY, label="3-D NX 240")
    a[i].bar(x + w / 2 + 0.01, [ex("co", k), ex("alt", k)], w, color=CO, label="ROM extrapolated")
    a[i].set(xticks=x, xticklabels=["co-current", "alternating"], ylabel=lab); a[i].grid(axis="x")
a[0].legend(loc="upper center", bbox_to_anchor=(1.1, 1.18), ncol=2); fig.suptitle(""); save(fig, "F05_ROM_vs_3D_bars.png")

# 6 -- Rev 4.1 arrangement comparison, UNPAIRED (two independent LHS groups of 150)
DF = __import__("pandas").read_csv(R + "/19_rev41/GRAIL_CFD_dataset_FINAL_rev4.1.csv")
GA, GP = DF[DF.f_interdig == 1], DF[DF.f_interdig == 0]
fig, a = plt.subplots(1, 2, figsize=(9.5, 4))
for i, (c, lab) in enumerate((("eta", "thermal efficiency η"), ("plate_std_K", "plate temperature std (K)"))):
    bp = a[i].boxplot([GP[c], GA[c]], widths=0.5, patch_artist=True, medianprops=dict(color=INK),
                      flierprops=dict(marker="o", ms=3, mec=GREY))
    for b_, col in zip(bp["boxes"], (CO, ALT)): b_.set(facecolor=col, alpha=0.35, edgecolor=col)
    a[i].set(xticks=[1, 2], xticklabels=["parallel (n=150)", "alternating (n=150)"], ylabel=lab); a[i].grid(axis="x")
a[0].set_title("η: mean −7.3 % (Mann–Whitney p = 2e-8)"); a[1].set_title("std: median −1.1 % (p = 0.76, n.s.)")
save(fig, "F06_arrangement_groups_rev41.png")

# 7 -- Rev 4.1 by flow-rate tercile, UNPAIRED group statistics
m = DF.mdot_total_kg_s * 1000; edges = [1.0, 2.17, 3.34, 4.5]; labs = ["1.0–2.2", "2.2–3.3", "3.3–4.5"]
de, ds = [], []
for lo, hi in zip(edges[:-1], edges[1:]):
    A_ = DF[(DF.f_interdig == 1) & (m >= lo) & (m < hi)]; P_ = DF[(DF.f_interdig == 0) & (m >= lo) & (m < hi)]
    de.append(100 * (A_.eta.mean() / P_.eta.mean() - 1)); ds.append(100 * (A_.plate_std_K.median() / P_.plate_std_K.median() - 1))
fig, a = plt.subplots(1, 2, figsize=(9.5, 3.8)); x = np.arange(3)
a[0].bar(x, de, 0.55, color=ALT); a[0].axhline(0, color=MUT, lw=0.8)
a[0].set(xticks=x, xticklabels=labs, xlabel="total flow (g/s)", ylabel="Δ mean η, alt vs par (%)", title="Efficiency: lower at every flow")
a[1].bar(x, ds, 0.55, color=[ALT if v > 0 else CO for v in ds]); a[1].axhline(0, color=MUT, lw=0.8)
a[1].set(xticks=x, xticklabels=labs, xlabel="total flow (g/s)", ylabel="Δ median plate std, alt vs par (%)", title="Uniformity: worse at low flow, better at high")
for ax_i, vals in ((a[0], de), (a[1], ds)):
    for xi, v in zip(x, vals): ax_i.annotate("%+.1f %%" % v, (xi, v), ha="center", va="bottom" if v > 0 else "top", fontsize=9, color=INK)
    ax_i.grid(axis="x")
save(fig, "F07_arrangement_by_flow_rev41.png")

# 8 -- heat recirculation (alt NX60 stations)
al = J(B + "/nu_alt_nx60.json")
fig, a = plt.subplots(1, 2, figsize=(10, 3.8))
for t, c in (("y_low", CO), ("y_high", ALT)):
    s = al[t]["stations"]; x = np.array([q["x"] for q in s]); o = np.argsort(x)
    a[0].plot(x[o] * 1000, np.array([q["Tb"] for q in s])[o], color=c, label=t.replace("y_", "channel "))
    a[1].plot(x[o] * 1000, np.array([q["qprime"] for q in s])[o], color=c, label=t.replace("y_", "channel "))
a[0].set(xlabel="x (mm)", ylabel="bulk fluid T (K)", title="Alternating: fluid peaks mid-channel"); a[0].legend()
a[1].axhline(0, color=MUT, lw=0.8); a[1].set(xlabel="x (mm)", ylabel="q′ wall→fluid (W/m)", title="Negative q′: heat returned to the plate"); a[1].legend()
save(fig, "F08_heat_recirculation_alt.png")

# 9 -- plate temperature maps (3-D NX240, bottom surface)
fig, a = plt.subplots(2, 1, figsize=(10, 5.6))
fig.subplots_adjust(hspace=0.55)
maps = []
for arr in ("co", "alt"):
    c = CH + "/bench_%s_nx240" % arr; t = J(c + "/convergence.json")["converged_at"]
    _, C = P.patch_geometry(c + "/constant/solid/polyMesh", "solid_bottom")
    T = np.atleast_1d(P.boundary_values(c + "/%s/solid/T" % t, "solid_bottom")); maps.append((C, T))
lo = min(m[1].min() for m in maps); hi = max(m[1].max() for m in maps)
for ax, (C, T), lab in zip(a, maps, ("co-current", "alternating")):
    tc = ax.tricontourf(C[:, 0] * 1000, C[:, 1] * 1000, T, levels=np.linspace(lo, hi, 25), cmap="Blues_r" if False else "inferno")
    ax.set(ylabel="y (mm)", title="%s — rear surface T, std %.2f K" % (lab, np.std(T))); ax.grid(False); ax.set_aspect("auto")
a[1].set_xlabel("x (mm)"); fig.colorbar(tc, ax=a, label="T (K)"); fig.savefig(os.path.join(OUT, "F09_plate_T_maps_3D.png")); plt.close(fig); print("fig F09")

# 10 -- envelope: ROM vs 3-D co-current
env = [("1.0", 0.39957, 10.673, 0.39974, 10.667, 10.666), ("2.49", 0.51597, 5.7907, 0.51582, 5.7452, 5.7612), ("4.5", 0.55855, 3.5376, 0.5582, 3.464, 3.5046)]
fig, a = plt.subplots(figsize=(6.4, 3.8)); x = np.arange(3); w = 0.26
a.bar(x - w - 0.02, [e[2] for e in env], w, color=GREY, label="3-D conjugate")
a.bar(x, [e[4] for e in env], w, color=CO, label="ROM, constant Nu 4.6")
a.bar(x + w + 0.02, [e[5] for e in env], w, color="#104281", label="ROM, 3-D Nu(ξ) profile")
a.set(xticks=x, xticklabels=[e[0] + " g/s" for e in env], ylabel="co-current plate std (K)", title="Nu envelope check"); a.grid(axis="x"); a.legend()
save(fig, "F10_Nu_envelope.png")

# ---- Roadmap 12.1 figures from the final dataset (Rev 4.1, unpaired groups)
# F11 loss breakdown (group means, signed net flows)
fig, a = plt.subplots(figsize=(6.4, 4)); x = np.arange(2); bot = np.zeros(2)
for c, lab, col in (("Q_rad_W", "radiative (plate→glass)", "#86b6ef"), ("Q_conv_W", "convective/conductive (plate→glass)", CO), ("Q_rear_W", "rear", "#104281")):
    v = np.array([GP[c].mean(), GA[c].mean()]); a.bar(x, v, 0.5, bottom=bot, color=col, label=lab, edgecolor="white", lw=2); bot += v
a.set(xticks=x, xticklabels=["parallel", "alternating"], ylabel="mean heat loss (W)", title="Loss breakdown, group means (Rev 4.1)"); a.grid(axis="x"); a.legend(loc="upper left")
save(fig, "F11_loss_breakdown_rev41.png")
# F12 correlation heatmap (Pearson), inputs vs outputs
ins = ["G_T_W_m2", "T_in_K", "T_amb_K", "v_wind_m_s", "mdot_total_kg_s", "bridge_mm", "g_ratio", "lambda_G", "f_interdig"]
outs = ["eta", "Qu_W", "T_plate_mean_K", "plate_std_K", "plate_spread_K", "T_R4_K", "U_L_W_m2K", "dp_channel_Pa"]
Cm = np.array([[np.corrcoef(DF[i], DF[o])[0, 1] for o in outs] for i in ins])
fig, a = plt.subplots(figsize=(8.5, 5.5)); im = a.imshow(Cm, cmap="RdBu_r", vmin=-1, vmax=1)
a.set(xticks=range(len(outs)), xticklabels=outs, yticks=range(len(ins)), yticklabels=ins, title="Pearson r, inputs vs outputs (Rev 4.1, n = 300)")
plt.setp(a.get_xticklabels(), rotation=35, ha="right"); a.grid(False)
for ii in range(len(ins)):
    for jj in range(len(outs)): a.text(jj, ii, "%.2f" % Cm[ii, jj], ha="center", va="center", fontsize=7, color="white" if abs(Cm[ii, jj]) > 0.6 else INK)
fig.colorbar(im, ax=a, shrink=0.8); save(fig, "F12_correlation_heatmap_rev41.png")
# F13/F14 grading: eta and dp vs g_ratio
fig, a = plt.subplots(1, 2, figsize=(10, 3.8))
for G_, col, lab in ((GP, CO, "parallel"), (GA, ALT, "alternating")):
    a[0].scatter(G_.g_ratio, G_.eta, s=14, color=col, label=lab, edgecolor="white", lw=0.5)
    a[1].scatter(G_.g_ratio, G_.dp_channel_Pa, s=14, color=col, label=lab, edgecolor="white", lw=0.5)
a[0].set(xlabel="G = D_h,out / D_h,in", ylabel="η", title="Grading result (all other inputs vary)"); a[0].legend()
a[1].set(xlabel="G = D_h,out / D_h,in", ylabel="Δp per channel (Pa)", yscale="log", title="Grading penalty"); a[1].legend()
save(fig, "F13_F14_grading_rev41.png")
# F9 histogram of plate std; F10 T_R4 vs bridge
fig, a = plt.subplots(1, 2, figsize=(10, 3.8)); bins = np.linspace(DF.plate_std_K.min(), DF.plate_std_K.max(), 30)
a[0].hist(GP.plate_std_K, bins, color=CO, alpha=0.6, label="parallel"); a[0].hist(GA.plate_std_K, bins, color=ALT, alpha=0.6, label="alternating")
a[0].set(xlabel="plate temperature std (K)", ylabel="cases", title="Distribution of plate non-uniformity"); a[0].legend()
for G_, col, lab in ((GP, CO, "parallel"), (GA, ALT, "alternating")):
    a[1].scatter(G_.bridge_mm, G_.T_R4_K - G_.T_plate_mean_K, s=14, color=col, label=lab, edgecolor="white", lw=0.5)
a[1].set(xlabel="bridge width (mm)", ylabel="T_R4 − T_mean (K)", title="Radiative excess temperature vs bridge"); a[1].legend()
save(fig, "F09b_F10b_distribution_bridge_rev41.png")
