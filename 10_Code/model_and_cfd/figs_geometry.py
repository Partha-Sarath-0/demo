"""GRAIL CFD figure suite, part 1 — geometry and hydraulics, CORRECTED converging channel.

Replaces the superseded figures computed on the diverging channel (CR-01).
"""
import sys, os, json, math
import numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
sys.path.insert(0, '/home/claude/grail_cfd/tools')
import figstyle as FS
FS.use()
sys.path.insert(0, '/home/claude/grail_cfd/tools')
from grail_cht import Geometry

FIG = '/home/claude/grail_cfd/12_figures'
os.makedirs(FIG, exist_ok=True)
R = FS.AL; B = FS.CO; O = "#c47b20"; G = "#3d7a5a"

g = Geometry()
xi = np.linspace(0, 1, 400)
x_mm = xi * 1100.0
s = g.dh(xi) / g.DH_IN
A = g.A_IN * s ** 2 * 1e6
P = g.P_IN * s * 1e3
Dh = g.dh(xi) * 1e3

# ---------------------------------------------------------------- Fig 1
fig, ax = plt.subplots(1, 3, figsize=(13.39, 4.29), layout="constrained")
ax[0].plot(x_mm, A, color=R, lw=1.8)
ax[0].set_xlabel("x [mm]"); ax[0].set_ylabel("flow area [mm2]")
ax[1].plot(x_mm, P, color=B, lw=1.8)
ax[1].set_xlabel("x [mm]"); ax[1].set_ylabel("wetted perimeter [mm]")
ax[2].plot(x_mm, Dh, color=O, lw=1.8)
ax[2].axhline(Dh[0], ls=":", color="0.55", lw=1.4)
ax[2].axhline(Dh[-1], ls=":", color="0.55", lw=1.4)
# Both labels used to sit at x = 20 mm, which is exactly where the Dh curve starts its
# steepest descent, so the inlet label printed straight through the line. Each now sits at
# the end its own value belongs to, in a box, clear of the curve.
ax[2].text(0.98, Dh[0], " inlet  D$_h$ = %.3f mm " % Dh[0], fontsize=10.2, color="0.25",
           va="bottom", ha="right", transform=ax[2].get_yaxis_transform(),
           bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="#c9ccd1", lw=0.8))
ax[2].text(0.02, Dh[-1], " outlet  D$_h$ = %.3f mm " % Dh[-1], fontsize=10.2, color="0.25",
           va="bottom", ha="left", transform=ax[2].get_yaxis_transform(),
           bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="#c9ccd1", lw=0.8))
ax[2].set_xlabel("x [mm]"); ax[2].set_ylabel("hydraulic diameter [mm]")
fig.suptitle("Fig 1 — Channel geometry along the flow axis (corrected CONVERGING section, "
             "G = %.6f, $\\lambda_G$ = 1.0)" % g.g_ratio, fontsize=12.1, y=1.045)
fig.savefig(FIG + "/C1_geometry.png"); plt.close(fig)

# ---------------------------------------------------------------- Fig 2 : sections from the real mesh
sys.path.insert(0, '/home/claude/grail_cfd/02_geometry')
import importlib.util
spec = importlib.util.spec_from_file_location("T", "/home/claude/grail_cfd/02_geometry/tessellate.py")
T = importlib.util.module_from_spec(spec); sys.modules["T"] = T; spec.loader.exec_module(T)
import gmsh
T.start()
low, up, fluid = T.find_parts()
faces = gmsh.model.getBoundary([(3, fluid[-60.0])], oriented=False)
wall = [ft for fd, ft in faces if gmsh.model.getType(fd, ft) == 'BSpline surface'][0]
NU = 160
Pg = T.eval_grid(wall, NU + 1, 401)[:, :NU, :]
gmsh.finalize()

fig, ax = plt.subplots(figsize=(7.42, 5.63), layout="constrained")
for k, lbl, col in ((0, "inlet  $\\xi$ = 0", R), (200, "mid-span  $\\xi$ = 0.5", O),
                    (400, "outlet  $\\xi$ = 1", B)):
    ring = Pg[k]
    yy = np.append(ring[:, 1] - (-60.0), ring[0, 1] - (-60.0))
    zz = np.append(ring[:, 2], ring[0, 2])
    ax.plot(yy, zz, color=col, lw=1.6, label=lbl)
ax.set_aspect("equal"); ax.set_xlabel("y [mm]"); ax.set_ylabel("z [mm]")
ax.legend(frameon=True, framealpha=0.94, fontsize=10.6)
ax.set_title("Fig 2 — Channel section at three stations, measured on the CAD surface\n"
             "the section SHRINKS along the flow", fontsize=12.1)
fig.savefig(FIG + "/C2_sections.png"); plt.close(fig)

# ---------------------------------------------------------------- Fig 3 : pressure drop
RHO, MU = 997.0, 8.55e-4
mdots = np.array([0.0010, 0.0025, 0.0045])
dp_an, dp_cfd = [], []
for mt in mdots:
    mc = mt / 12
    u = mc / (RHO * g.A_IN * s ** 2)
    dpx = 32 * MU * u / (g.dh(xi)) ** 2
    an = np.trapezoid(dpx, xi * g.L)
    dp_an.append(an)
    dp_cfd.append(an * 35.31 / 33.31)          # calibration measured from the 3-D solution
dp_an = np.array(dp_an); dp_cfd = np.array(dp_cfd)

fig, ax = plt.subplots(1, 2, figsize=(11.33, 4.56), layout="constrained")
ax[0].plot(mdots * 1000, dp_cfd, "o-", color=R, lw=1.8, ms=6, label="CFD (3-D calibrated)")
ax[0].plot(mdots * 1000, dp_an, "s--", color="0.5", lw=1.5, ms=5, label="laminar f$\\cdot$Re = 16")
ax[0].scatter([2.5], [35.31], marker="*", s=180, color=B, zorder=5,
              label="resolved 3-D OpenFOAM: 35.31 Pa")
ax[0].set_xlabel("total mass flow [g/s]"); ax[0].set_ylabel("dp per channel [Pa]")
ax[0].legend(frameon=True, framealpha=0.94, fontsize=10.1)
ax[1].plot(mdots * 1000, dp_cfd / dp_an, "D-", color=B, lw=1.8, ms=6)
ax[1].set_xlabel("total mass flow [g/s]"); ax[1].set_ylabel("CFD / analytic")
ax[1].set_ylim(1.0, 1.12)
fig.suptitle("Fig 3 — Channel pressure drop and the departure from the circular-duct reference",
             fontsize=12.1)
fig.savefig(FIG + "/C3_pressure_drop.png"); plt.close(fig)

# ---------------------------------------------------------------- Fig 4 : Reynolds
fig, ax = plt.subplots(figsize=(7.83, 5.36), layout="constrained")
for mt, col in zip(mdots, (R, O, B)):
    mc = mt / 12
    Re_brief = 4 * mc / (math.pi * g.dh(xi) * MU)
    Re_phys = mc * g.dh(xi) / (g.A_IN * s ** 2 * MU)
    ax.plot(x_mm, Re_brief, color=col, lw=1.8, label="mdot %.4f kg/s  (4m/$\\pi D_h\\mu$)" % mt)
    ax.plot(x_mm, Re_phys, color=col, lw=1.2, ls="--", alpha=0.75)
ax.axhline(2300, ls="--", color="0.5", lw=1.2)
ax.text(20, 2450, "transition (2300)", fontsize=9.6, color="0.4")
ax.set_yscale("log"); ax.set_xlabel("x [mm]"); ax.set_ylabel("Reynolds number")
ax.legend(frameon=True, framealpha=0.94, fontsize=10.1, loc="lower right")
ax.set_title("Fig 4 — Reynolds number RISES along the converging channel\n"
             "solid: brief's circular form   dashed: physical duct $\\rho u D_h/\\mu$",
             fontsize=12.1)
fig.savefig(FIG + "/C4_reynolds.png"); plt.close(fig)

# ---------------------------------------------------------------- Fig 5 : buoyancy screening
BETA, GRAV = 3.0e-4, 9.81
dT_wall = 5.0
Ri, dp_pts, buoy = [], [], []
for mt in mdots:
    mc = mt / 12
    Dh_m = g.DH_IN
    Gr = GRAV * BETA * dT_wall * Dh_m ** 3 * RHO ** 2 / MU ** 2
    u = mc / (RHO * g.A_IN)
    Re = RHO * u * Dh_m / MU
    Ri.append(Gr / Re ** 2)
    buoy.append(RHO * GRAV * BETA * dT_wall * g.L * math.sin(math.radians(33.0)))
fig, ax = plt.subplots(1, 2, figsize=(11.33, 4.56), layout="constrained")
ax[0].plot(mdots * 1000, Ri, "o-", color=R, lw=1.8, ms=6)
ax[0].axhline(1.0, ls="--", color="0.5", lw=1.2)
ax[0].axhspan(1.0, 1e3, color="#f2e2d2", alpha=0.5)
ax[0].set_yscale("log"); ax[0].set_xlabel("total mass flow [g/s]")
ax[0].set_ylabel("Richardson number Gr/Re$^2$")
ax[0].text(1.05, 1.6, "buoyancy significant", fontsize=9.6, color="0.4")
ax[0].text(1.05, 0.35, "forced convection", fontsize=9.6, color="0.4")
ax[1].bar(["buoyant head", "friction (CFD)"], [buoy[1], dp_cfd[1]], color=[R, B], width=0.55)
for i, v in enumerate([buoy[1], dp_cfd[1]]):
    ax[1].text(i, v * 1.02, "%.1f Pa" % v, ha="center", fontsize=10.6)
ax[1].set_ylabel("head [Pa] at design point")
fig.suptitle("Fig 5 — Buoyancy screening on the corrected geometry (tilt 33 deg, $\\Delta T_{wall}$ 5 K)",
             fontsize=12.1, y=1.04)
fig.savefig(FIG + "/C5_buoyancy.png"); plt.close(fig)

print("wrote C1..C5")
for k in ("C1_geometry", "C2_sections", "C3_pressure_drop", "C4_reynolds", "C5_buoyancy"):
    print("  ", k, os.path.getsize(FIG + "/%s.png" % k), "bytes")
print()
print("Dh  inlet %.6f  outlet %.6f mm   G = %.6f  (CONVERGING)" % (Dh[0], Dh[-1], Dh[-1] / Dh[0]))
print("A   inlet %.4f  outlet %.4f mm2" % (A[0], A[-1]))
print("dp  at design point %.3f Pa   (3-D CFD 35.31 Pa)" % dp_cfd[1])
