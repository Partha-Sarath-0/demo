"""GRAIL combined simulation video — co-current and alternating side by side, identical scale."""
import sys, os, subprocess, time
import numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
sys.path.insert(0, '/home/claude/grail_cfd/tools')
from grail_cht import Geometry, Materials, Operating
from transient import GrailTransient

OUT = '/home/claude/grail_cfd/12_figures/video'
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10})
NX, NY = 110, 120
T_END, DT = 900.0, 2.5
W, H, FPS = 1408, 792, 20

R = {}
for f, nm in ((0, 'co'), (1, 'alt')):
    s = GrailTransient(Geometry(), Materials(), Operating(f_interdig=f), nx=NX, ny=NY)
    fr, tt = s.run(t_end=T_END, dt=DT, save_every=1)
    R[nm] = (s, fr, tt)
    print("%s: %d frames, final mean %.2f K std %.3f" % (nm, len(fr), fr[-1].mean(), fr[-1].std()),
          flush=True)
allT = np.concatenate([np.array(v[1]).ravel() for v in R.values()])
VMIN, VMAX = allT.min() - 273.15, allT.max() - 273.15
times = R['co'][2]

fig = plt.figure(figsize=(W / 100, H / 100), dpi=100)
gs = fig.add_gridspec(3, 1, height_ratios=[1.0, 1.0, 0.85], hspace=0.55,
                      left=0.075, right=0.875, top=0.885, bottom=0.085)
ax0 = fig.add_subplot(gs[0]); ax1 = fig.add_subplot(gs[1]); ax2 = fig.add_subplot(gs[2])
ims = []
for ax, nm, ttl in ((ax0, 'co', "CO-CURRENT   $f_{interdig}$ = 0"),
                    (ax1, 'alt', "ALTERNATING COUNTER-CURRENT   $f_{interdig}$ = 1")):
    s, fr, _ = R[nm]
    im = ax.pcolormesh(s.xc * 1000, s.yc * 1000, (fr[0] - 273.15).T,
                       cmap="inferno", vmin=VMIN, vmax=VMAX, shading="auto")
    ims.append(im)
    for j, yc in enumerate(s.ch_y):
        ax.annotate("", xy=((230 if s.ch_dir[j] > 0 else -230), yc * 1000),
                    xytext=((-230 if s.ch_dir[j] > 0 else 230), yc * 1000),
                    arrowprops=dict(arrowstyle="->", color="white", lw=0.9, alpha=0.9))
    ax.set_ylabel("y [mm]"); ax.set_title(ttl, fontsize=11); ax.set_aspect(1.1)
ax1.set_xlabel("x [mm]")
cax = fig.add_axes([0.888, 0.42, 0.014, 0.46])
cb = fig.colorbar(ims[0], cax=cax); cb.set_label("absorber temperature  [$^\\circ$C]", fontsize=10)
tstamp = ax0.text(0.012, 0.88, "", transform=ax0.transAxes, color="white",
                  fontsize=13, fontweight="bold")

hco, halt, sco, salt = [], [], [], []
lc, = ax2.plot([], [], color="#5b9bd5", lw=2.0, label="co-current, mean")
la, = ax2.plot([], [], color="#d9663d", lw=2.0, label="alternating, mean")
lcs, = ax2.plot([], [], color="#5b9bd5", lw=1.3, ls="--", label="co-current, std")
las, = ax2.plot([], [], color="#d9663d", lw=1.3, ls="--", label="alternating, std")
ax2.set_xlim(0, times[-1]); ax2.set_ylim(0, VMAX + 3)
ax2.set_xlabel("time [s]"); ax2.set_ylabel("plate T [$^\\circ$C]")
ax2.grid(alpha=0.25); ax2.legend(frameon=False, fontsize=8.5, ncol=4, loc="lower right")
fig.suptitle("GRAIL Collector — conjugate startup, corrected converging geometry "
             "(G = 0.5399, $\\lambda_G$ = 1.0)", fontsize=13, y=0.958)
fig.canvas.draw()
w, h = fig.canvas.get_width_height()
mp4 = os.path.join(OUT, "GRAIL_CFD_simulation.mp4")
p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgba",
                      "-s", "%dx%d" % (w, h), "-framerate", str(FPS), "-i", "-",
                      "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "20", mp4],
                     stdin=subprocess.PIPE)
t0 = time.time()
for k in range(len(times)):
    Tc = R['co'][1][k] - 273.15
    Ta = R['alt'][1][k] - 273.15
    ims[0].set_array(Tc.T.ravel()); ims[1].set_array(Ta.T.ravel())
    tstamp.set_text("t = %5.0f s" % times[k])
    hco.append(Tc.mean()); halt.append(Ta.mean()); sco.append(Tc.std()); salt.append(Ta.std())
    lc.set_data(times[:k + 1], hco); la.set_data(times[:k + 1], halt)
    lcs.set_data(times[:k + 1], sco); las.set_data(times[:k + 1], salt)
    fig.canvas.draw()
    p.stdin.write(np.asarray(fig.canvas.buffer_rgba()).tobytes())
p.stdin.close(); p.wait()
print("wrote %s  %d KB  (%.0f s)" % (mp4, os.path.getsize(mp4) // 1024, time.time() - t0))
