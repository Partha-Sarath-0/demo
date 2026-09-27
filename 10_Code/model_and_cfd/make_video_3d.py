"""New video: converged 3-D conjugate solutions (NX 240, NU 64, design flow), co-current vs alternating.
Background = 3-D rear-surface temperature (same colour scale). Tracers move at the bulk velocity
u(x) = mdot/(rho A(x)) along each channel in its own flow direction (massless markers of bulk speed).
Reads saved 3-D fields only; nothing is re-solved."""
import os, sys, json, numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.animation import FFMpegWriter
sys.path.insert(0, os.path.dirname(__file__))
import cht_post as P
R = "/home/claude/grail_cfd"; CH = R + "/06_cht"; OUT = R + "/12_figures/video/GRAIL_3D_conjugate_rev41.mp4"
maps = {}
for arr in ("co", "alt"):
    c = CH + "/bench_%s_nx240" % arr; t = json.load(open(c + "/convergence.json"))["converged_at"]
    _, Cc = P.patch_geometry(c + "/constant/solid/polyMesh", "solid_bottom")
    maps[arr] = (Cc, np.atleast_1d(P.boundary_values(c + "/%s/solid/T" % t, "solid_bottom")))
lo = min(m[1].min() for m in maps.values()); hi = max(m[1].max() for m in maps.values())
L = 1.1; G = 0.539935; mdot = 2.077072e-4; rho = 997.0; A_in = 27.9726e-6
def u(xi):  # section scales with (Dh/Dh_in)^2, linear grading as a visual approximation of the CAD taper
    return mdot / (rho * A_in * (1 - (1 - G) * xi) ** 2)
# channel centre lines of the 2-channel strip (y = -20, +20 mm); co: both flow -x ; alt: opposite
lanes = {"co": [(-20, -1), (20, -1)], "alt": [(-20, -1), (20, +1)]}
rng = np.random.default_rng(1); N = 14
fig, ax = plt.subplots(2, 1, figsize=(11, 6.2)); fig.subplots_adjust(hspace=0.45, right=0.86)
for a, arr, lab in zip(ax, ("co", "alt"), ("co-current (both channels −x)", "alternating counter-current")):
    Cc, T = maps[arr]
    tc = a.tricontourf(Cc[:, 0] * 1000, Cc[:, 1] * 1000, T, levels=np.linspace(lo, hi, 30), cmap="inferno")
    a.set(title="%s — 3-D conjugate rear-surface T, std %.2f K" % (lab, T.std()), ylabel="y (mm)")
ax[1].set_xlabel("x (mm)")
cax = fig.add_axes([0.88, 0.12, 0.02, 0.76]); fig.colorbar(tc, cax=cax, label="T (K)")
dots = {}
for a, arr in zip(ax, ("co", "alt")):
    pts = []
    for (y, s) in lanes[arr]:
        xi = rng.random(N)
        pts.append([xi, y, s])
    dots[arr] = (pts, [a.plot([], [], "o", ms=5, mfc="white", mec="black", mew=0.6)[0] for _ in pts])
txt = fig.text(0.02, 0.01, "", fontsize=9)
fig.text(0.02, 0.965, "GRAIL Collector — converged 3-D conjugate CFD (OpenFOAM, NX 240, design flow). Tracers: bulk velocity, not particle paths.", fontsize=9)
DT = 0.5  # s per frame
wr = FFMpegWriter(fps=20, bitrate=2400)
with wr.saving(fig, OUT, dpi=110):
    for k in range(400):
        for arr in ("co", "alt"):
            pts, lines = dots[arr]
            for (p, ln) in zip(pts, lines):
                xi, y, s = p
                xi[:] = (xi + DT * u(xi) / L) % 1.0
                x = (0.5 - xi) * L * 1000 if s < 0 else (xi - 0.5) * L * 1000
                ln.set_data(x, np.full_like(x, y))
        txt.set_text("tracer time %.0f s" % (k * DT))
        wr.grab_frame()
print("wrote", OUT)
