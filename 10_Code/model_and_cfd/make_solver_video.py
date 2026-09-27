"""
GRAIL — solver-progress video on the CORRECTED converging geometry.

Three panels, matching the layout of the superseded video but built entirely from this
study's own data:

  top-left    the 3-D velocity field in the x-z projection, at genuine intermediate SIMPLE
              iterations written by a re-run of the baseline case (04_baseline/ch05_anim).
              Nothing is interpolated or repeated to fake motion.
  top-right   the real residual history parsed out of the OpenFOAM log (09_post/residuals.py):
              Ux, Uz, p and the time-step continuity error, drawn up to the current iteration.
  bottom      the converged conjugate plate field with tracers advected at the true local bulk
              velocity u(x) = Q / A(x). Because the section CONVERGES, tracers ACCELERATE
              downstream, 7.448 -> 25.547 mm/s, a factor 1/G^2 = 3.4302.

Usage:  python3 make_solver_video.py <alt|co>
"""
import sys, os, json, time, subprocess
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.path.insert(0, "/home/claude/grail_cfd/tools")
from grail_cht import Geometry, Materials, Operating, GrailCHT

ANIM = os.environ.get("GRAIL_ANIM_CASE", "/home/claude/grail_cfd/04_baseline/ch05_anim")
OUT = "/home/claude/grail_cfd/12_figures/video"
os.makedirs(OUT, exist_ok=True)
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10})

W, H, FPS = 1408, 792, 20
NFRAME = int(os.environ.get("GRAIL_NFRAME", 320))
T_END = 100.0                      # s of tracer time, one full transit is 90.17 s
NX, NY = 220, 240
NSAMP = 14000                      # cells drawn in the velocity panel
NTRACER = 26                       # per channel

MODE = (sys.argv[1] if len(sys.argv) > 1 else "alt").lower()
F_INTERDIG = 0 if MODE.startswith("co") else 1
NAME = "co_current" if F_INTERDIG == 0 else "counter_current"
TITLE = ("GRAIL collector - conjugate CFD, CO-CURRENT absorber"
         if F_INTERDIG == 0 else
         "GRAIL collector - conjugate CFD, alternating counter-current absorber")

t0 = time.time()

# ---------------------------------------------------------------- 1. velocity snapshots
import pyvista as pv
r = pv.OpenFOAMReader(os.path.join(ANIM, "case.foam"))
r.cell_to_point_creation = False
times = [t for t in r.time_values if t > 0]
print("velocity snapshots: %d written times, %g ... %g" % (len(times), times[0], times[-1]),
      flush=True)

r.set_active_time_value(times[0])
blk = r.read()["internalMesh"]
cc = np.asarray(blk.cell_centers().points)
rng = np.random.default_rng(20260916)
sel = rng.choice(len(cc), size=min(NSAMP, len(cc)), replace=False)
PX, PZ = cc[sel, 0] * 1000.0, cc[sel, 2] * 1000.0

UMAG = np.empty((len(times), len(sel)), np.float32)
for k, t in enumerate(times):
    r.set_active_time_value(t)
    b = r.read()["internalMesh"]
    UMAG[k] = np.linalg.norm(np.asarray(b.cell_data["U"])[sel], axis=1) * 1000.0
    if k % 10 == 0:
        print("   t=%-6g  |U| max %7.3f mm/s   (%.0f s)" % (t, UMAG[k].max(), time.time() - t0),
              flush=True)
VMAX = float(np.percentile(UMAG[-1], 99.7))
print("velocity panel ready, colour scale 0 - %.2f mm/s (%.0f s)" % (VMAX, time.time() - t0),
      flush=True)

# ---------------------------------------------------------------- 2. residual history
R = json.load(open("/home/claude/grail_cfd/09_post/residuals.json"))["flow"]
RIT = np.array(R["iter"])
RES = {k: np.array(R[k], float) for k in ("Ux", "Uz", "p", "continuity")}
NIT = int(RIT[-1])
print("residuals: %d SIMPLE iterations" % NIT, flush=True)

# ---------------------------------------------------------------- 3. conjugate plate + tracers
g, m, op = Geometry(), Materials(), Operating(f_interdig=F_INTERDIG)
s = GrailCHT(g, m, op, nx=NX, ny=NY)
CACHE = os.path.join(OUT, "plate_%s_%dx%d.npz" % (NAME, NX, NY))
if os.path.exists(CACHE):
    d = np.load(CACHE, allow_pickle=True)
    s.Tp = d["Tp"]
    res = json.loads(str(d["res"]))
    print("conjugate plate loaded from cache", flush=True)
else:
    res = s.solve(max_outer=900, tol=1e-6)
    np.savez_compressed(CACHE, Tp=s.Tp,
                        res=json.dumps({k: float(v) for k, v in res.items()
                                        if isinstance(v, (int, float, np.floating, np.integer))}))
print("conjugate solve: eta %.5f  Tp mean %.2f K  std %.3f K  energy error %.2e %%  (%.0f s)"
      % (res["eta"], res["Tp_mean"], res["Tp_std"], res["energy_error_pct"], time.time() - t0),
      flush=True)
TP = s.Tp - 273.15

Q = op.mdot_ch / m.rho_w
U_IN = Q / g.area(0.0) * 1000.0
U_OUT = Q / g.area(1.0) * 1000.0


def u_of_xi(xi):
    """True local bulk speed [m/s] from mass conservation on the graded section."""
    return Q / g.area(np.clip(xi, 0.0, 1.0))


# tracers: xi in [0,1] along each channel's own flow direction
rng2 = np.random.default_rng(7)
tx = np.tile(np.linspace(0.0, 1.0, NTRACER, endpoint=False), (g.N_CH, 1))
tx += rng2.uniform(-0.004, 0.004, tx.shape)
tx = np.clip(tx, 0.0, 0.999)

DT = T_END / (NFRAME - 1)

# ---------------------------------------------------------------- 4. figure
fig = plt.figure(figsize=(W / 100, H / 100), dpi=100)
gs = fig.add_gridspec(2, 2, height_ratios=[1.0, 1.06], width_ratios=[1.0, 1.0],
                      hspace=0.42, wspace=0.30,
                      left=0.062, right=0.915, top=0.885, bottom=0.085)
axV = fig.add_subplot(gs[0, 0])
axR = fig.add_subplot(gs[0, 1])
axP = fig.add_subplot(gs[1, :])

sc = axV.scatter(PX, PZ, c=UMAG[0], s=1.6, cmap="turbo", vmin=0.0, vmax=VMAX, lw=0)
cbV = fig.colorbar(sc, ax=axV, pad=0.015, fraction=0.045)
cbV.set_label("|U|  [mm/s]", fontsize=9)
axV.set_xlabel("x  [mm]", fontsize=9); axV.set_ylabel("z  [mm]", fontsize=9)
axV.set_xlim(-560, 560); axV.set_ylim(-0.30, 5.05)
axV.tick_params(labelsize=8)
titV = axV.set_title("Velocity field at SIMPLE iteration 0 / %d" % NIT, fontsize=10)
axV.annotate("", xy=(520, 4.55), xytext=(-520, 4.55),
             arrowprops=dict(arrowstyle="->", color="0.35", lw=1.0))
axV.text(0, 4.66, "flow  —  section converges, $D_h$ 5.199 $\\rightarrow$ 2.807 mm",
         ha="center", fontsize=8, color="0.3")
axV.text(-545, 4.22, "baseline channel, y = -60 mm   105,600 hexahedra   %s cells drawn"
         % "{:,}".format(len(sel)), fontsize=7.5, color="0.35", va="bottom")

COL = {"Ux": "#b02418", "Uz": "#2f7d32", "p": "#17557d", "continuity": "#d98b1f"}
lines = {}
for k in ("Ux", "Uz", "p", "continuity"):
    lines[k], = axR.plot([], [], color=COL[k], lw=1.2, label=k)
axR.axhline(1e-6, ls="--", lw=0.9, color="#17557d", alpha=0.6)
axR.axhline(1e-7, ls="--", lw=0.9, color="#b02418", alpha=0.6)
axR.text(NIT * 0.995, 1.25e-6, "p tolerance 1e-6", fontsize=7, color="#17557d", ha="right")
axR.text(NIT * 0.995, 1.25e-7, "U tolerance 1e-7", fontsize=7, color="#b02418", ha="right")
axR.set_yscale("log"); axR.set_xlim(0, NIT); axR.set_ylim(1e-12, 3.0)
axR.set_xlabel("SIMPLE iteration", fontsize=9); axR.set_ylabel("initial residual", fontsize=9)
axR.set_title("Solver convergence  —  simpleFoam, OpenFOAM v1912", fontsize=10)
axR.grid(alpha=0.25); axR.legend(frameon=False, fontsize=8, ncol=2, loc="lower left")
axR.tick_params(labelsize=8)

pm = axP.pcolormesh(s.xc * 1000, s.yc * 1000, TP.T, cmap="inferno", shading="auto")
cbP = fig.colorbar(pm, ax=axP, pad=0.012, fraction=0.030)
cbP.set_label("plate T  [$^\\circ$C]", fontsize=9)
axP.set_xlabel("x  [mm]", fontsize=9); axP.set_ylabel("y  [mm]", fontsize=9)
axP.tick_params(labelsize=8)
axP.set_title("Converged conjugate solution  —  tracers move at the true local bulk velocity "
              "(cyan: flow $+x$   green: flow $-x$)", fontsize=10)
CY, GR = "#35d1f5", "#7ee23e"
tsc = axP.scatter([], [], s=17, lw=0.5, edgecolor="0.1", zorder=5)
clock = axP.text(0.011, 0.885, "", transform=axP.transAxes, color="white", fontsize=12,
                 fontweight="bold",
                 bbox=dict(boxstyle="round,pad=0.30", fc="black", ec="none", alpha=0.42))
axP.text(0.011, 0.055,
         "u = $\\dot m$ / ($\\rho$ A(x)):  %.2f mm/s at $\\xi$ = 0  $\\rightarrow$  %.2f mm/s at "
         "$\\xi$ = 1   (factor 1/G$^2$ = %.4f);  transit 90.2 s"
         % (U_IN, U_OUT, 1.0 / g.G_RATIO ** 2),
         transform=axP.transAxes, color="white", fontsize=8.5,
         bbox=dict(boxstyle="round,pad=0.30", fc="black", ec="none", alpha=0.42))
fig.suptitle(TITLE, fontsize=13, y=0.958)
fig.canvas.draw()
w, h = fig.canvas.get_width_height()

cols = np.array([CY if d > 0 else GR for d in s.ch_dir])
tcol = np.repeat(cols, NTRACER)

mp4 = os.path.join(OUT, os.environ.get("GRAIL_TAG", "") + "GRAIL_CFD_solver_%s.mp4" % NAME)
p = subprocess.Popen(
    ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgba",
     "-s", "%dx%d" % (w, h), "-framerate", str(FPS), "-i", "-",
     "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "20", mp4], stdin=subprocess.PIPE)

tr = time.time()
for f in range(NFRAME):
    frac = f / (NFRAME - 1)

    k = min(int(round(frac * (len(times) - 1))), len(times) - 1)
    sc.set_array(UMAG[k])
    titV.set_text("Velocity field at SIMPLE iteration %d / %d" % (times[k], NIT))

    nit = max(int(round(frac * NIT)), 1)
    msk = RIT <= nit
    for key in lines:
        y = RES[key][msk]
        good = np.isfinite(y) & (y > 0)
        lines[key].set_data(RIT[msk][good], y[good])

    # advance tracers by the local speed; re-inject at the inlet on exit
    for _ in range(4):
        tx += (u_of_xi(tx) / g.L) * (DT / 4.0)
    out = tx >= 1.0
    tx[out] -= 1.0

    xi = tx
    sgn = s.ch_dir[:, None]
    xm = np.where(sgn > 0, -g.L / 2 + xi * g.L, g.L / 2 - xi * g.L) * 1000.0
    ym = np.repeat(s.ch_y[:, None], NTRACER, axis=1) * 1000.0
    tsc.set_offsets(np.column_stack([xm.ravel(), ym.ravel()]))
    tsc.set_facecolor(tcol)
    clock.set_text("tracer time  t = %5.1f s" % (frac * T_END))

    fig.canvas.draw()
    p.stdin.write(np.asarray(fig.canvas.buffer_rgba()).tobytes())
p.stdin.close(); p.wait()
print("wrote %s  %d KB  (render %.0f s, total %.0f s)"
      % (mp4, os.path.getsize(mp4) // 1024, time.time() - tr, time.time() - t0))

json.dump({"mode": NAME, "f_interdig": F_INTERDIG, "frames": NFRAME, "fps": FPS,
           "simple_iterations": NIT, "velocity_snapshots": len(times),
           "u_in_mm_s": U_IN, "u_out_mm_s": U_OUT, "speed_ratio": 1.0 / g.G_RATIO ** 2,
           "transit_s": 90.17, "eta": res["eta"], "Tp_mean_K": res["Tp_mean"],
           "Tp_std_K": res["Tp_std"], "energy_error_pct": res["energy_error_pct"]},
          open(os.path.join(OUT, "solver_%s.json" % NAME), "w"), indent=1)
