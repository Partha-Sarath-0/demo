"""Fig G1 — 3-D grid convergence and the Nusselt correction."""
import json
import numpy as np
import sys
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
sys.path.insert(0, '/home/claude/grail_cfd/tools')
import figstyle as FS
FS.use()

V = "/home/claude/grail_cfd/05_validation/"
FIG = "/home/claude/grail_cfd/12_figures"
CO, AL, NEU = FS.CO, FS.AL, "#3d7a5a"

NU = json.load(open(V + "nu_gci.json"))
G3 = json.load(open(V + "gci_3d.json")) if __import__("os").path.exists(V + "gci_3d.json") else None
F = json.load(open(V + "final_uncertainty.json"))
C = json.load(open(V + "nu_corrected.json"))

lv = NU["levels"]
order = ["L1", "L2", "L3"]
n = np.array([lv[k]["ncell"] for k in order], float)
nu = np.array([lv[k]["Nu"] for k in order])
h = (n[-1] / n) ** (1 / 3)

fig, ax = plt.subplots(1, 3, figsize=(15.04, 5.63), layout="constrained")


tick_lab = ["%s\n%s" % (k, "{:,}".format(int(n[i]))) for i, k in enumerate(order)]
ax[0].plot(h, nu, "o-", color=AL, lw=1.9, ms=7)
ax[0].axhline(NU["Nu_extrapolated"], color="0.25", ls="--", lw=1.2)
ax[0].text(h.min(), NU["Nu_extrapolated"], "Richardson  %.4f " % NU["Nu_extrapolated"],
           fontsize=9.6, va="bottom", ha="right", color="0.25")
ax[0].axhline(NU["nu_used_by_solver"], color=CO, ls=":", lw=1.4)
ax[0].text(h.min(), NU["nu_used_by_solver"], "used by the solver  %.4f " % NU["nu_used_by_solver"],
           fontsize=9.6, va="bottom", ha="right", color=CO)
ax[0].invert_xaxis()
ax[0].set_xticks(h); ax[0].set_xticklabels(tick_lab, fontsize=9.6)
ax[0].set_xlabel("grid level / cells")
ax[0].set_ylim(2.86, 3.83)
ax[0].set_ylabel("Nu, developed region")
ax[0].set_title("Nusselt number is not grid converged\nobserved order p = %.2f, GCI %.1f %%"
                % (NU["observed_order"], NU["gci_pct"]), fontsize=11.4)

if G3:
    qs = [("dP_Pa", "pressure drop"), ("dT_K", "temperature rise"),
          ("peak_bulk_mid", "peak / bulk velocity")]
    for q, lab in qs:
        g = G3["gci"][q]
        v = np.array([g["L1"], g["L2"], g["L3"]])
        ax[1].plot(h, v / v[-1], "o-", lw=1.7, ms=6,
                   label="%s  (p %.2f, GCI %.2f %%)" % (lab, g["p"] or 0, g["gci_pct"]))
    ax[1].axhline(1.0, color="0.4", lw=0.9)
    ax[1].invert_xaxis()
    ax[1].set_xticks(h); ax[1].set_xticklabels(tick_lab, fontsize=9.6)
    ax[1].set_xlabel("grid level / cells")
    ax[1].set_ylabel("value / value on the finest grid")
    ax[1].set_title("The hydraulic quantities ARE converged", fontsize=11.4)
    ax[1].legend(frameon=True, framealpha=0.94, fontsize=9.2)

keys = ["d_Tp_std_pct", "d_eta_pct", "d_U_L_pct", "d_dTp_pct"]
labs = ["$\\Delta$ plate spread\n(RMS)", "$\\Delta$ efficiency", "$\\Delta U_L$",
        "$\\Delta$ plate spread\n(peak-to-peak)"]
y = np.arange(len(keys))
vals = [F["quantities"][k]["value_nu_corrected_pct"] for k in keys]
errs = [F["quantities"][k]["expanded_k2_pct_points"] for k in keys]
old = [F["quantities"][k]["value_as_run_pct"] for k in keys]
cols = [NEU if F["quantities"][k]["excludes_zero_at_k2"] else "#b0b0b0" for k in keys]
ax[2].errorbar(vals, y, xerr=errs, fmt="o", ms=8, capsize=5, lw=1.8,
               ecolor="0.35", markerfacecolor="none", markeredgewidth=0)
for i in range(len(keys)):
    ax[2].plot(vals[i], y[i], "o", ms=9, color=cols[i], zorder=5)
    ax[2].plot(old[i], y[i], "x", ms=7, color=AL, zorder=5)
ax[2].axvline(0.0, color=FS.AL, lw=1.4)
ax[2].set_yticks(y); ax[2].set_yticklabels(labs, fontsize=10.0)
ax[2].tick_params(axis="y", pad=2)
ax[2].set_xlabel("alternating $-$ co-current  [%]")
ax[2].set_title("Final result, k = 2\ncircle: Nu-corrected   cross: as originally run",
                fontsize=11.4)
ax[2].invert_yaxis()

fig.suptitle("Fig G1 — 3-D grid convergence closes the uncertainty assessment. Correcting the "
             "Nusselt number for its +14.7 %% grid bias nearly doubles the uniformity benefit, "
             "to %+.1f %% $\\pm$ %.1f."
             % (F["quantities"]["d_Tp_std_pct"]["value_nu_corrected_pct"],
                F["quantities"]["d_Tp_std_pct"]["expanded_k2_pct_points"]),
             fontsize=11.9, y=1.04)
fig.savefig(FIG + "/G1_3d_grid_convergence.png", bbox_inches="tight"); plt.close(fig)
print("wrote G1")
