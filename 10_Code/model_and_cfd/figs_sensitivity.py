"""GRAIL CFD — grading, bridge and fillet sensitivity, plus dataset quality control."""
import os, csv
import numpy as np
import sys
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
sys.path.insert(0, '/home/claude/grail_cfd/tools')
import figstyle as FS
FS.use()

CSV = os.environ.get('GRAIL_DATASET', '/home/claude/grail_cfd/10_dataset/GRAIL_CFD_dataset_corrected.csv')
FIG = os.environ.get('GRAIL_FIGDIR', '/home/claude/grail_cfd/12_figures')
CO, AL = FS.CO, FS.AL

rows = list(csv.DictReader(open(CSV)))
for r in rows:
    for k, v in r.items():
        if k not in ('case_id', 'geometry_version', 'solver', 'arrangement', 'converged'):
            try: r[k] = float(v)
            except ValueError: pass
co = [r for r in rows if r['arrangement'] == 'parallel']
al = [r for r in rows if r['arrangement'] == 'alternating']
G = lambda s, k: np.array([r[k] for r in s], float)
print("rows %d  (co %d / alt %d)" % (len(rows), len(co), len(al)))


def binned(x, y, nb=8):
    b = np.linspace(x.min(), x.max(), nb + 1)
    i = np.clip(np.digitize(x, b) - 1, 0, nb - 1)
    xs, ys, es = [], [], []
    for k in range(nb):
        m = i == k
        if m.sum() >= 3:
            xs.append(x[m].mean()); ys.append(y[m].mean()); es.append(y[m].std())
    return np.array(xs), np.array(ys), np.array(es)


# ---------------------------------------------------------------- C18 grading sensitivity
fig, ax = plt.subplots(1, 3, figsize=(13.60, 4.69), layout="constrained")
for s, c, lb in ((co, CO, "co-current"), (al, AL, "alternating")):
    if not s: continue
    x, y, e = binned(G(s, 'g_ratio'), G(s, 'eta'))
    ax[0].errorbar(x, y, yerr=e, fmt="o-", color=c, lw=1.6, ms=5, capsize=3, label=lb)
    x, y, e = binned(G(s, 'g_ratio'), G(s, 'dp_channel_Pa'))
    ax[1].errorbar(x, y, yerr=e, fmt="o-", color=c, lw=1.6, ms=5, capsize=3, label=lb)
    x, y, e = binned(G(s, 'lambda_G'), G(s, 'eta'))
    ax[2].errorbar(x, y, yerr=e, fmt="s-", color=c, lw=1.6, ms=5, capsize=3, label=lb)
ax[0].axvline(0.539935, ls=":", color="0.45"); ax[0].text(0.548, ax[0].get_ylim()[0], " as built", fontsize=9.6, color="0.4")
ax[0].set_xlabel("grading ratio  G"); ax[0].set_ylabel("efficiency")
ax[0].set_title("Efficiency vs endpoint grading", fontsize=11.6)
ax[1].axvline(0.539935, ls=":", color="0.45")
ax[1].set_xlabel("grading ratio  G"); ax[1].set_ylabel("channel dp [Pa]")
ax[1].set_title("Hydraulic penalty of grading", fontsize=11.6); ax[1].set_yscale("log")
ax[2].axvline(1.0, ls=":", color="0.45"); ax[2].set_xlabel("grading exponent  $\\lambda_G$")
ax[2].set_ylabel("efficiency"); ax[2].set_title("Effect of the distribution law", fontsize=11.6)
for a in ax: a.legend(frameon=True, framealpha=0.94, fontsize=9.6)
fig.suptitle("Fig C18 — Grading sensitivity: endpoint ratio G and exponent $\\lambda_G$ varied independently",
             fontsize=12.1)
fig.savefig(FIG + "/C18_grading.png"); plt.close(fig)

# ---------------------------------------------------------------- C19 bridge sensitivity
fig, ax = plt.subplots(1, 3, figsize=(13.60, 4.69), layout="constrained")
for s, c, lb in ((co, CO, "co-current"), (al, AL, "alternating")):
    if not s: continue
    for j, key, ylab in ((0, 'lateral_bridge_W', "lateral bridge conduction [W]"),
                         (1, 'plate_std_K', "plate temperature std [K]"),
                         (2, 'R4_K4', "R4 / mean(T)$^4$")):
        yv = G(s, key) / G(s, 'T_plate_mean_K') ** 4 if key == 'R4_K4' else G(s, key)
        x, y, e = binned(G(s, 'bridge_mm'), yv)
        ax[j].errorbar(x, y, yerr=e, fmt="o-", color=c, lw=1.6, ms=5, capsize=3, label=lb)
        ax[j].set_xlabel("bridge width [mm]"); ax[j].set_ylabel(ylab)
ax[0].axvline(31.286, ls=":", color="0.45")
ax[0].text(31.9, ax[0].get_ylim()[1] * 0.1, " as built\n 31.286 mm", fontsize=9.6, color="0.4")
for a in ax: a.legend(frameon=True, framealpha=0.94, fontsize=9.6)
ax[0].set_title("The mechanism, measured", fontsize=11.6)
ax[1].set_title("Homogenisation", fontsize=11.6)
ax[2].set_title("Radiation proxy (nonuniformity part)", fontsize=11.6)
fig.suptitle("Fig C19 — Bridge-width sensitivity across 20 - 37 mm "
             "(60 mm is unreachable at 40 mm pitch: bridge = pitch - w_ch)",
             fontsize=12.1, y=1.045)
fig.savefig(FIG + "/C19_bridge.png"); plt.close(fig)

# ---------------------------------------------------------------- C22 dataset QC
fig, ax = plt.subplots(1, 3, figsize=(13.60, 4.56), layout="constrained")
ee = np.abs(G(rows, 'energy_error_pct'))
ax[0].hist(ee, bins=30, color="#3d7a5a")
ax[0].set_xlabel("|energy balance error| [%]"); ax[0].set_ylabel("cases")
ax[0].set_title("Energy conservation, every accepted case", fontsize=11.6)
ax[0].text(0.35, 0.8, "max %.6f %%\ngate: 0.5 %%" % ee.max(), transform=ax[0].transAxes, fontsize=10.6)
ax[1].scatter(G(co, 'outer_iters'), G(co, 'eta'), s=14, alpha=0.6, color=CO, lw=0, label="co-current")
if al:
    ax[1].scatter(G(al, 'outer_iters'), G(al, 'eta'), s=14, alpha=0.6, color=AL, lw=0, label="alternating")
ax[1].set_xlabel("outer iterations to converge"); ax[1].set_ylabel("efficiency")
ax[1].set_title("Convergence effort", fontsize=11.6); ax[1].legend(frameon=True, framealpha=0.94, fontsize=9.6)
ax[2].scatter(G(rows, 'Re_in'), G(rows, 'Re_out'), s=14, alpha=0.6, color="#c47b20", lw=0)
lim = [0, max(G(rows, 'Re_out')) * 1.05]
ax[2].plot(lim, lim, "k--", lw=1.0)
ax[2].set_xlim(lim); ax[2].set_ylim(lim)
ax[2].set_xlabel("Re at inlet"); ax[2].set_ylabel("Re at outlet")
ax[2].set_title("Re RISES downstream in every case\n(the converging-channel signature)", fontsize=11.6)
fig.suptitle("Fig C22 — Dataset quality control", fontsize=12.1)
fig.savefig(FIG + "/C22_quality.png"); plt.close(fig)

print("wrote C18, C19, C22")
