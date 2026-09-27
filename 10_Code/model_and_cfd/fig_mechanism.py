import sys, numpy as np, json
sys.path.insert(0, '/home/claude/grail_cfd/tools')
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patheffects as pe
sys.path.insert(0, '/home/claude/grail_cfd/tools')
import figstyle as FS
FS.use()
from grail_cht import Geometry, Materials, Operating, GrailCHT

FIG = "/home/claude/grail_cfd/12_figures"
NX, NY = 110, 120

runs = {}
for f, name, Tin in ((0, "parallel", 300.0), (1, "alternating", 300.0),
                     (1, "alternating_matched", 285.689)):
    g = Geometry(); m = Materials(); op = Operating(f_interdig=f, T_in=Tin)
    s = GrailCHT(g, m, op, nx=NX, ny=NY)
    r = s.solve(max_outer=900, tol=1e-6)
    runs[name] = (s, r)
    print("%-22s Tp_mean %.3f  std %.4f  R4 %.6e  Q_u %.3f" %
          (name, r['Tp_mean'], r['Tp_std'], r['R4'], r['Q_u']), flush=True)

sp, rp = runs["parallel"]; sa, ra = runs["alternating"]
sm, rm = runs["alternating_matched"]

# ---------------- F8: side-by-side plate fields, identical scale
vmin = min(sp.Tp.min(), sa.Tp.min()) - 273.15
vmax = max(sp.Tp.max(), sa.Tp.max()) - 273.15
fig, axs = plt.subplots(2, 1, figsize=(9.4, 8.2), layout="constrained")
fig.get_layout_engine().set(w_pad=0.10, h_pad=0.14, hspace=0.10)
for ax, (s, r), ttl in zip(axs, (runs["parallel"], runs["alternating"]),
                           ("Parallel flow  ($f_{interdig}$ = 0)",
                            "Alternating counter-current  ($f_{interdig}$ = 1)")):
    im = ax.pcolormesh(s.xc * 1000, s.yc * 1000, (s.Tp - 273.15).T,
                       cmap="inferno", vmin=vmin, vmax=vmax, shading="auto")
    for j, yc in enumerate(s.ch_y):
        ax.annotate("", xy=((300 if s.ch_dir[j] > 0 else -300), yc * 1000),
                    xytext=((-300 if s.ch_dir[j] > 0 else 300), yc * 1000),
                    # White arrows vanish against the pale end of the colour ramp, which is
                    # exactly where the alternating field is most interesting. A dark arrow
                    # with a white outline reads on both ends of the ramp.
                    arrowprops=dict(arrowstyle="-|>", color="#101010", lw=1.5,
                                    alpha=0.95, mutation_scale=13,
                                    path_effects=[pe.withStroke(linewidth=3.2,
                                                                foreground="white")]))
    ax.set_ylabel("y  (mm)"); ax.set_title(ttl, fontsize=11.1)
    ax.set_aspect(1.0)
axs[1].set_xlabel("x  (mm)")
cb = fig.colorbar(im, ax=axs, fraction=0.022, pad=0.012)
cb.set_label("absorber temperature  ($^\\circ$C)")
fig.suptitle("GRAIL mechanism study — matched mass flow, irradiance, geometry and ambient",
             fontsize=12.1)
fig.savefig(FIG + "/F8_mechanism_fields.png"); plt.close(fig)

# ---------------- F9: temperature distribution incl. the upper tail
fig, ax = plt.subplots(1, 2, figsize=(9.27, 4.15), layout="constrained")
bins = np.linspace(vmin, vmax, 90)
ax[0].hist((sp.Tp.ravel() - 273.15), bins=bins, histtype="step", lw=1.5,
           color=FS.CO, label="parallel", density=True)
ax[0].hist((sa.Tp.ravel() - 273.15), bins=bins, histtype="step", lw=1.5,
           color=FS.AL, label="alternating", density=True)
ax[0].set_xlabel("absorber temperature ($^\\circ$C)"); ax[0].set_ylabel("density")
ax[0].set_title("Matched mass flow", fontsize=11.1); ax[0].legend(frameon=True, framealpha=0.94, fontsize=9.6)

b2 = np.linspace(min(sp.Tp.min(), sm.Tp.min()) - 273.15,
                 max(sp.Tp.max(), sm.Tp.max()) - 273.15, 90)
ax[1].hist((sp.Tp.ravel() - 273.15), bins=b2, histtype="step", lw=1.5,
           color=FS.CO, label="parallel", density=True)
ax[1].hist((sm.Tp.ravel() - 273.15), bins=b2, histtype="step", lw=1.5,
           color="#3d7a5a", label="alternating, matched mean", density=True)
ax[1].set_xlabel("absorber temperature ($^\\circ$C)")
ax[1].set_title("Matched MEAN plate temperature", fontsize=11.1)
ax[1].legend(frameon=True, framealpha=0.94, fontsize=9.6)
fig.suptitle("Absorber temperature distribution — the flattening, and what it is worth",
             fontsize=12.1)
fig.savefig(FIG + "/F9_temperature_distribution.png"); plt.close(fig)

# ---------------- bridge conduction
def lateral(s):
    kt = s.m.k_al * s.t_y
    d = np.zeros_like(s.Tp); d[:, :-1] = (s.Tp[:, 1:] - s.Tp[:, :-1]) / s.dy
    kf = np.zeros_like(s.Tp); kf[:, :-1] = 2 * kt[:, :-1] * kt[:, 1:] / (kt[:, :-1] + kt[:, 1:])
    q = kf * d
    mids = 0.5 * (s.ch_y[:-1] + s.ch_y[1:])
    return [np.abs(q[:, int(np.argmin(np.abs(s.yc - ym)))]).sum() * s.dx for ym in mids], mids

qp, mids = lateral(sp); qa, _ = lateral(sa)
fig, ax = plt.subplots(figsize=(6.59, 4.02), layout="constrained")
w = 8
ax.bar(mids * 1000 - w / 2, qp, width=w, color=FS.CO, label="parallel")
ax.bar(mids * 1000 + w / 2, qa, width=w, color=FS.AL, label="alternating")
ax.set_xlabel("bridge midline position  y (mm)")
ax.set_ylabel("lateral conduction  (W)")
ax.set_title("Heat crossing each bridge — the mechanism, measured directly", fontsize=11.1)
ax.legend(frameon=True, framealpha=0.94, fontsize=9.6)
ax.set_ylim(0, max(max(qa), max(qp)) * 1.28)
ax.text(0.02, 0.955, "total across the plate\nparallel %.3f W     alternating %.1f W" % (sum(qp), sum(qa)),
        va="top",
        bbox=dict(boxstyle="round,pad=0.42", facecolor="white", edgecolor="#c9ccd1", lw=0.8),
        transform=ax.transAxes, fontsize=10.1)
fig.savefig(FIG + "/F10_bridge_conduction.png"); plt.close(fig)
print("\nfigures written")
