"""
GRAIL CFD — mesh figures on the CORRECTED CAD geometry.

Every section here is evaluated on the actual NURBS surface from the STEP file and meshed
with the structured O-grid that the CFD uses, so the pictures are of the real mesh, not an
illustration. Replaces the superseded mesh figures, which showed the channel GROWING from
5.200 to 8.300 mm (CR-01) with a 1.0 mm root fillet (CR-05).
"""
import sys, os, importlib.util
import numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection

FIG = '/home/claude/grail_cfd/12_figures'
os.makedirs(FIG, exist_ok=True)
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10,
                     "figure.dpi": 170, "savefig.dpi": 170, "savefig.bbox": "tight"})
AL = "#c8795c"; ALE = "#8c3f22"; WA = "#9dc3e6"; WAE = "#1f4e79"

spec = importlib.util.spec_from_file_location("OG", "/home/claude/grail_cfd/03_mesh/ogrid.py")
OG = importlib.util.module_from_spec(spec); sys.modules["OG"] = OG; spec.loader.exec_module(OG)

NU, NR, NX = 64, 10, 40
print("building the O-grid from the CAD surface ...")
W, occV = OG.wall_points(-60.0, NU, NX)
print("  wall points %s   OCC volume %.3f mm3" % (str(W.shape), occV))


def section_cells(ring, nr=NR, nc=None, fcore=0.45, grad=1.18):
    """Return the quad cells of one meshed section: O-ring + TFI core."""
    nu = len(ring); nc = nc or nu // 4
    C = ring.mean(axis=0)
    B = C + fcore * (ring - C)
    s = np.array([(grad ** k - 1) / (grad - 1) for k in range(nr + 1)], float)
    r = s / s[-1]
    layers = [B + r[m] * (ring - B) for m in range(nr + 1)]
    quads = []
    for m in range(nr):
        for i in range(nu):
            i2 = (i + 1) % nu
            quads.append([layers[m][i], layers[m][i2], layers[m + 1][i2], layers[m + 1][i]])
    G = OG.tfi_core(B, nc)
    for i in range(nc):
        for j in range(nc):
            quads.append([G[i, j], G[i + 1, j], G[i + 1, j + 1], G[i, j + 1]])
    return np.array(quads), len(quads)


def draw(ax, quads, fc, ec, lw=0.35, alpha=1.0):
    from matplotlib.patches import Polygon
    from matplotlib.collections import PatchCollection
    ps = [Polygon(q[:, 1:3], closed=True) for q in quads]
    pc = PatchCollection(ps, facecolor=fc, edgecolor=ec, linewidths=lw, alpha=alpha)
    ax.add_collection(pc)


def sheet_quads(ring, y0, y1, nz=6, nyy=26, t_lo=-1.0, t_up=1.0):
    """Flat bond-land cells either side of the channel, z from -1 to +1 mm."""
    ys = np.linspace(y0, y1, nyy + 1)
    zs = np.linspace(t_lo, t_up, nz + 1)
    q = []
    for i in range(nyy):
        for j in range(nz):
            q.append(np.array([[0, ys[i], zs[j]], [0, ys[i + 1], zs[j]],
                               [0, ys[i + 1], zs[j + 1]], [0, ys[i], zs[j + 1]]]))
    return np.array(q)


def dome_shell(ring, t=1.0, n=6):
    """Metal shell outside the channel wall, offset along the local outward normal."""
    nu = len(ring); C = ring.mean(axis=0)
    nrm = []
    for i in range(nu):
        tg = ring[(i + 1) % nu] - ring[(i - 1) % nu]
        tg = tg / (np.linalg.norm(tg) + 1e-12)
        v = ring[i] - C; v[0] = 0.0
        v = v - np.dot(v, tg) * tg
        nrm.append(v / (np.linalg.norm(v) + 1e-12))
    nrm = np.array(nrm)
    layers = [ring + (t * k / n) * nrm for k in range(n + 1)]
    q = []
    for m in range(n):
        for i in range(nu):
            if ring[i, 2] < 0.05 and ring[(i + 1) % nu, 2] < 0.05:
                continue                                   # skip the flat bonded floor
            i2 = (i + 1) % nu
            q.append([layers[m][i], layers[m][i2], layers[m + 1][i2], layers[m + 1][i]])
    return np.array(q)


def section_figure(k, label, fname):
    ring = W[k].copy()
    ring[:, 1] -= -60.0                       # centre on the channel
    quads, ncell = section_cells(ring)
    A = 0.0
    for q in quads:
        y = q[:, 1]; z = q[:, 2]
        A += 0.5 * abs(np.dot(y, np.roll(z, -1)) - np.dot(z, np.roll(y, -1)))
    per = np.linalg.norm(np.diff(np.vstack([ring, ring[:1]]), axis=0), axis=1).sum()
    Dh = 4 * A / per
    fig, ax = plt.subplots(figsize=(11.0, 3.9))
    draw(ax, sheet_quads(ring, -20, ring[:, 1].min()), AL, ALE, 0.4)
    draw(ax, sheet_quads(ring, ring[:, 1].max(), 20), AL, ALE, 0.4)
    draw(ax, dome_shell(ring), AL, ALE, 0.4)
    draw(ax, quads, WA, WAE, 0.35)
    ax.set_xlim(-20, 20); ax.set_ylim(-1.4, 8.6); ax.set_aspect("equal")
    ax.set_xlabel("y  [mm]"); ax.set_ylabel("z  [mm]")
    ax.set_title("Channel cross-section — %s\n"
                 "$D_h$ = %.3f mm     A = %.3f mm$^2$     wetted perimeter P = %.3f mm"
                 % (label, Dh, A, per), fontsize=11.5)
    ax.text(0.015, 0.93, "%d fluid cells per section  (O-grid: %d ring + %d core)\n"
                         "aluminium AA1050 shell — water core" % (ncell, NU * NR, (NU // 4) ** 2),
            transform=ax.transAxes, fontsize=8.5, color="0.3", va="top")
    fig.savefig(os.path.join(FIG, fname)); plt.close(fig)
    print("  %s  Dh %.3f  A %.3f  P %.3f  cells %d" % (fname, Dh, A, per, ncell))
    return Dh, A, per


print("\nsection figures")
d0 = section_figure(0, "INLET,  $\\xi$ = 0", "M1_section_inlet.png")
d1 = section_figure(NX, "OUTLET,  $\\xi$ = 1", "M2_section_outlet.png")
print("\n  grading ratio from the meshed sections: %.6f" % (d1[0] / d0[0]))

# ---------------------------------------------------------------- root fillet detail
ring = W[0].copy(); ring[:, 1] -= -60.0
quads, _ = section_cells(ring)
fig, ax = plt.subplots(figsize=(6.6, 5.4))
draw(ax, sheet_quads(ring, ring[:, 1].max(), 20), AL, ALE, 0.6)
draw(ax, dome_shell(ring), AL, ALE, 0.6)
draw(ax, quads, WA, WAE, 0.55)
ax.set_xlim(2.0, 7.5); ax.set_ylim(-1.3, 3.0); ax.set_aspect("equal")
ax.set_xlabel("y  [mm]"); ax.set_ylabel("z  [mm]")
ax.set_title("Root-fillet detail — tangent blend, $\\xi$ = 0\n"
             "root fillet r = 0.5 mm  (decision D4; the superseded model used 1.0 mm)",
             fontsize=11)
ax.text(0.03, 0.05, "$R = \\dfrac{(h_s-r)^2 + ((w_s-2r)/2)^2 - (r+t)^2}{2\\,[(h_s-r)-(r+t)]}$",
        transform=ax.transAxes, fontsize=10, color="0.25")
fig.savefig(os.path.join(FIG, "M3_root_fillet.png")); plt.close(fig)
print("  M3_root_fillet.png")

# ---------------------------------------------------------------- swept mesh, 3-D
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
fig = plt.figure(figsize=(12.5, 6.2))
ax = fig.add_subplot(111, projection="3d")
stations = range(0, NX + 1, 2)
polys_w, polys_a = [], []
for k in stations:
    ring = W[k].copy()
    q, _ = section_cells(ring, nr=6)
    polys_w += [p[:, [0, 1, 2]] for p in q[::7]]
    polys_a += [p[:, [0, 1, 2]] for p in dome_shell(ring, n=3)[::5]]
pcw = Poly3DCollection(polys_w, facecolor=WA, edgecolor=WAE, linewidths=0.18, alpha=0.95)
pca = Poly3DCollection(polys_a, facecolor=AL, edgecolor=ALE, linewidths=0.18, alpha=0.75)
ax.add_collection3d(pca); ax.add_collection3d(pcw)
ax.set_xlim(-550, 550); ax.set_ylim(-75, -45); ax.set_zlim(-2, 8)
ax.set_box_aspect((5.2, 0.9, 0.8))
ax.set_xlabel("x [mm]"); ax.set_ylabel("y [mm]"); ax.set_zlabel("z [mm]")
ax.view_init(elev=22, azim=-60)
ax.set_title("Structured hexahedral mesh swept along one channel — the section SHRINKS\n"
             "$D_h$ 5.199 mm at $\\xi$ = 0  to  2.807 mm at $\\xi$ = 1", fontsize=12)
fig.savefig(os.path.join(FIG, "M4_swept_mesh.png")); plt.close(fig)
print("  M4_swept_mesh.png")

# ---------------------------------------------------------------- multi-channel strip
fig, ax = plt.subplots(figsize=(13.0, 3.4))
for ch, yc in enumerate([-100.0, -60.0, -20.0, 20.0]):
    Wk, _ = OG.wall_points(yc, NU, 4)
    ring = Wk[0].copy(); ring[:, 1] -= 0.0
    q, _ = section_cells(ring, nr=8)
    draw(ax, q, WA, WAE, 0.3)
    draw(ax, dome_shell(ring), AL, ALE, 0.3)
    draw(ax, sheet_quads(ring, ring[:, 1].max(), ring[:, 1].max() + 31.286 / 1.0 * 0 + 15.6), AL, ALE, 0.3)
    draw(ax, sheet_quads(ring, ring[:, 1].min() - 15.6, ring[:, 1].min()), AL, ALE, 0.3)
ax.set_xlim(-125, 45); ax.set_ylim(-1.4, 7.5); ax.set_aspect("equal")
ax.set_xlabel("y  [mm]"); ax.set_ylabel("z  [mm]")
ax.set_title("Four adjacent channels at the inlet — 40 mm pitch, 31.286 mm conductive bridge\n"
             "the bridge is the lateral conduction path the mechanism depends on", fontsize=11.5)
fig.savefig(os.path.join(FIG, "M5_multichannel.png")); plt.close(fig)
print("  M5_multichannel.png")
print("\ndone")
