"""GRAIL CFD figure suite, part 2 — campaign figures, co-current vs alternating counter-current.

All rows come from the CORRECTED converging geometry. The superseded 480-row dataset
(diverging channel, CR-01) contributes nothing.
"""
import os, sys, csv, math
import numpy as np
import sys
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
sys.path.insert(0, '/home/claude/grail_cfd/tools')
import figstyle as FS
FS.use()

CSV = os.environ.get('GRAIL_DATASET', '/home/claude/grail_cfd/10_dataset/GRAIL_CFD_dataset_corrected.csv')
FIG = os.environ.get('GRAIL_FIGDIR', '/home/claude/grail_cfd/12_figures')
CO = FS.CO      # co-current / parallel
AL = FS.AL      # alternating counter-current

rows = list(csv.DictReader(open(CSV)))
for r in rows:
    for k, v in r.items():
        if k not in ('case_id', 'geometry_version', 'solver', 'arrangement', 'converged'):
            try: r[k] = float(v)
            except ValueError: pass
co = [r for r in rows if r['arrangement'] == 'parallel']
al = [r for r in rows if r['arrangement'] == 'alternating']
print("dataset: %d rows   co-current %d   alternating %d" % (len(rows), len(co), len(al)))
G = lambda s, k: np.array([r[k] for r in s], dtype=float)


def scat(ax, xk, yk, xlabel, ylabel):
    ax.scatter(G(co, xk), G(co, yk), s=16, alpha=0.65, color=CO, label="co-current", lw=0)
    ax.scatter(G(al, xk), G(al, yk), s=16, alpha=0.65, color=AL, label="alternating", lw=0)
    ax.set_xlabel(xlabel); ax.set_ylabel(ylabel)


# ---------------------------------------------------------------- C10 efficiency
fig, ax = plt.subplots(1, 2, figsize=(11.85, 4.82), layout="constrained")
scat(ax[0], 'G_T_W_m2', 'eta', "irradiance G$_T$ [W/m2]", "efficiency")
ax[0].legend(frameon=True, framealpha=0.94, fontsize=10.1)
for s, c, lb in ((co, CO, "co-current"), (al, AL, "alternating")):
    ax[1].scatter((G(s, 'T_in_K') - G(s, 'T_amb_K')), G(s, 'eta'), s=16, alpha=0.65, color=c, lw=0, label=lb)
ax[1].set_xlabel("T$_{in}$ - T$_{amb}$ [K]"); ax[1].set_ylabel("efficiency")
ax[1].legend(frameon=True, framealpha=0.94, fontsize=10.1)
fig.suptitle("Fig C10 — Efficiency against irradiance and reduced temperature (%d CFD cases, converging geometry, Rev 2)"
             % len(rows), fontsize=12.1, y=1.04)
fig.savefig(FIG + "/C10_efficiency.png"); plt.close(fig)

# ---------------------------------------------------------------- C11 Hottel-Whillier
fig, ax = plt.subplots(figsize=(7.83, 5.63), layout="constrained")
fits = {}
for s, c, lb in ((co, CO, "co-current"), (al, AL, "alternating")):
    x = (G(s, 'T_in_K') - G(s, 'T_amb_K')) / G(s, 'G_T_W_m2')
    y = G(s, 'eta')
    ax.scatter(x, y, s=16, alpha=0.6, color=c, lw=0, label=lb)
    m, b = np.polyfit(x, y, 1)
    xs = np.linspace(x.min(), x.max(), 50)
    ax.plot(xs, m * xs + b, color=c, lw=1.8)
    fits[lb] = (b, -m)
    print("  %-12s eta_0 = %.4f   F_R U_L = %.4f W/m2K" % (lb, b, -m))
ax.set_xlabel("(T$_{in}$ - T$_{amb}$)/G$_T$  [K m2/W]"); ax.set_ylabel("efficiency")
ax.legend(frameon=True, framealpha=0.94, fontsize=10.6)
ax.set_title("Fig C11 — Hottel-Whillier curve fitted to the CFD dataset, Rev 2 at Nu = 2.9238\n"
             "co-current $\\eta_0$ = %.4f, F$_R$U$_L$ = %.3f   |   alternating $\\eta_0$ = %.4f, F$_R$U$_L$ = %.3f"
             % (fits['co-current'][0], fits['co-current'][1],
                fits['alternating'][0], fits['alternating'][1]), fontsize=11.6)
fig.savefig(FIG + "/C11_hottel_whillier.png"); plt.close(fig)

# ---------------------------------------------------------------- C12 dT and plate overheat
fig, ax = plt.subplots(1, 2, figsize=(11.85, 4.82), layout="constrained")
scat(ax[0], 'G_T_W_m2', 'dT_fluid_K', "G$_T$ [W/m2]", "fluid temperature rise [K]")
ax[0].legend(frameon=True, framealpha=0.94, fontsize=10.1)
for s, c in ((co, CO), (al, AL)):
    ax[1].scatter(G(s, 'G_T_W_m2'), G(s, 'T_plate_mean_K') - G(s, 'T_amb_K'), s=16, alpha=0.65, color=c, lw=0)
ax[1].set_xlabel("G$_T$ [W/m2]"); ax[1].set_ylabel("plate mean above ambient [K]")
fig.suptitle("Fig C12 — Temperature rise and plate overheat versus irradiance", fontsize=12.1)
fig.savefig(FIG + "/C12_temperature_rise.png"); plt.close(fig)

# ---------------------------------------------------------------- C13 wind
fig, ax = plt.subplots(1, 2, figsize=(11.85, 4.82), layout="constrained")
for s, c, lb in ((co, CO, "co-current"), (al, AL, "alternating")):
    v = G(s, 'v_wind_m_s'); e = G(s, 'eta')
    bins = np.linspace(0, 5, 6)
    idx = np.digitize(v, bins) - 1
    xm = [v[idx == i].mean() for i in range(5) if (idx == i).any()]
    ym = [e[idx == i].mean() for i in range(5) if (idx == i).any()]
    ax[0].plot(xm, ym, "o-", color=c, lw=1.8, ms=6, label=lb)
    ax[1].scatter(G(s, 'h_wind_W_m2K'), e, s=14, alpha=0.5, color=c, lw=0, label=lb)
ax[0].set_xlabel("wind speed [m/s]"); ax[0].set_ylabel("mean efficiency"); ax[0].legend(frameon=True, framealpha=0.94, fontsize=10.1)
ax[1].set_xlabel("wind coefficient h$_{wind}$ = 5.7 + 3.8v  [W/m2K]"); ax[1].set_ylabel("efficiency")
ax[1].legend(frameon=True, framealpha=0.94, fontsize=10.1)
fig.suptitle("Fig C13 — Sensitivity to wind speed", fontsize=12.1)
fig.savefig(FIG + "/C13_wind.png"); plt.close(fig)

# ---------------------------------------------------------------- C17 correlation matrix
ins = ['G_T_W_m2', 'T_in_K', 'T_amb_K', 'v_wind_m_s', 'mdot_total_kg_s', 'bridge_mm', 'g_ratio', 'lambda_G']
outs = ['T_out_K', 'Qu_W', 'eta', 'T_plate_mean_K', 'plate_spread_K', 'plate_std_K',
        'R4_K4', 'Q_rad_W', 'U_L_W_m2K', 'lateral_bridge_W', 'dp_channel_Pa']
M = np.zeros((len(outs), len(ins)))
for i, o in enumerate(outs):
    for j, k in enumerate(ins):
        M[i, j] = np.corrcoef(G(rows, k), G(rows, o))[0, 1]
fig, ax = plt.subplots(figsize=(10.30, 6.97), layout="constrained")
im = ax.imshow(M, cmap="RdBu_r", vmin=-1, vmax=1, aspect="auto")
ax.set_xticks(range(len(ins))); ax.set_xticklabels(ins, rotation=45, ha="right", fontsize=10.1)
ax.set_yticks(range(len(outs))); ax.set_yticklabels(outs, fontsize=10.1)
for i in range(len(outs)):
    for j in range(len(ins)):
        ax.text(j, i, "%.2f" % M[i, j], ha="center", va="center", fontsize=9.1,
                color="white" if abs(M[i, j]) > 0.55 else "black")
cb = fig.colorbar(im, ax=ax, fraction=0.025); cb.set_label("Pearson r")
ax.set_title("Fig C17 — Input/output correlation across the CFD dataset, Rev 2 at Nu = 2.9238 (%d cases)" % len(rows),
             fontsize=12.1)
fig.savefig(FIG + "/C17_correlation.png"); plt.close(fig)

# ---------------------------------------------------------------- C20 distributions
fig, ax = plt.subplots(1, 3, figsize=(13.39, 4.56), layout="constrained")
for k, a, lbl in (('eta', ax[0], "efficiency"),
                  ('T_plate_mean_K', ax[1], "mean plate temperature [K]"),
                  ('plate_std_K', ax[2], "plate temperature std [K]")):
    lo = min(G(co, k).min(), G(al, k).min()); hi = max(G(co, k).max(), G(al, k).max())
    b = np.linspace(lo, hi, 34)
    a.hist(G(co, k), bins=b, color=CO, alpha=0.6, label="co-current")
    a.hist(G(al, k), bins=b, color=AL, alpha=0.6, label="alternating")
    a.set_xlabel(lbl); a.set_ylabel("cases"); a.legend(frameon=True, framealpha=0.94, fontsize=10.1)
fig.suptitle("Fig C20 — Distributions over the CFD dataset, Rev 2 at Nu = 2.9238", fontsize=12.1)
fig.savefig(FIG + "/C20_distributions.png"); plt.close(fig)

# ---------------------------------------------------------------- C21 the mechanism across the campaign
fig, ax = plt.subplots(1, 3, figsize=(13.39, 4.56), layout="constrained")
ax[0].scatter(G(co, 'bridge_mm'), G(co, 'lateral_bridge_W'), s=16, alpha=0.65, color=CO, lw=0, label="co-current")
ax[0].scatter(G(al, 'bridge_mm'), G(al, 'lateral_bridge_W'), s=16, alpha=0.65, color=AL, lw=0, label="alternating")
ax[0].set_xlabel("bridge width [mm]"); ax[0].set_ylabel("lateral bridge conduction [W]")
ax[0].legend(frameon=True, framealpha=0.94, fontsize=10.1)
ax[1].scatter(G(co, 'bridge_mm'), G(co, 'plate_std_K'), s=16, alpha=0.65, color=CO, lw=0)
ax[1].scatter(G(al, 'bridge_mm'), G(al, 'plate_std_K'), s=16, alpha=0.65, color=AL, lw=0)
ax[1].set_xlabel("bridge width [mm]"); ax[1].set_ylabel("plate temperature std [K]")
ax[2].scatter(G(co, 'T_plate_mean_K'), G(co, 'R4_K4') / G(co, 'T_plate_mean_K') ** 4,
              s=16, alpha=0.65, color=CO, lw=0)
ax[2].scatter(G(al, 'T_plate_mean_K'), G(al, 'R4_K4') / G(al, 'T_plate_mean_K') ** 4,
              s=16, alpha=0.65, color=AL, lw=0)
ax[2].set_xlabel("mean plate temperature [K]"); ax[2].set_ylabel("R4 / mean(T)$^4$")
fig.suptitle("Fig C21 — The mechanism across the campaign: bridge conduction, flattening, and what it does to R4",
             fontsize=12.1)
fig.savefig(FIG + "/C21_mechanism_campaign.png"); plt.close(fig)

print("\nwrote C10, C11, C12, C13, C17, C20, C21")
print("\nquality: energy error max %.4f %%   all converged: %s"
      % (max(abs(r['energy_error_pct']) for r in rows),
         all(str(r['converged']) == 'True' for r in rows)))
