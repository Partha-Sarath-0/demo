"""Render the GRAIL transient animations: co-current, alternating, and a combined view."""
import sys, os, subprocess, time
import numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
sys.path.insert(0, '/home/claude/grail_cfd/tools')
from grail_cht import Geometry, Materials, Operating
from transient import GrailTransient

OUT = '/home/claude/grail_cfd/12_figures/video'
os.makedirs(OUT, exist_ok=True)
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 11})

NX, NY = 110, 120
T_END, DT = 900.0, 2.0
SAVE_EVERY = 1                      # 451 frames -> 15 s at 30 fps, full startup to steady state

runs = {}
for f, name in ((0, 'co_current'), (1, 'counter_current')):
    t0 = time.time()
    g = Geometry(); m = Materials(); op = Operating(f_interdig=f)
    s = GrailTransient(g, m, op, nx=NX, ny=NY)
    fr, tt = s.run(t_end=T_END, dt=DT, save_every=SAVE_EVERY)
    runs[name] = (s, fr, tt)
    print("%-16s %d frames, final Tp mean %.3f K  (%.1f s)"
          % (name, len(fr), fr[-1].mean(), time.time() - t0), flush=True)

allT = np.concatenate([np.array(fr).ravel() for _, fr, _ in runs.values()])
VMIN, VMAX = allT.min() - 273.15, allT.max() - 273.15
print("common colour scale: %.2f - %.2f degC" % (VMIN, VMAX))


def render(name, s, frames, times, title, w=1600, h=900, fps=30):
    d = os.path.join(OUT, name); os.makedirs(d, exist_ok=True)
    for f in os.listdir(d):
        os.remove(os.path.join(d, f))
    fig = plt.figure(figsize=(w / 100, h / 100), dpi=100)
    gs = fig.add_gridspec(2, 1, height_ratios=[3.0, 1.0], hspace=0.42,
                          left=0.07, right=0.90, top=0.86, bottom=0.10)
    axf = fig.add_subplot(gs[0]); axl = fig.add_subplot(gs[1])
    im = axf.pcolormesh(s.xc * 1000, s.yc * 1000, (frames[0] - 273.15).T,
                        cmap="inferno", vmin=VMIN, vmax=VMAX, shading="auto")
    cax = fig.add_axes([0.915, 0.42, 0.016, 0.44])
    cb = fig.colorbar(im, cax=cax); cb.set_label("absorber temperature  [$^\\circ$C]", fontsize=11)
    for j, yc in enumerate(s.ch_y):
        axf.annotate("", xy=((260 if s.ch_dir[j] > 0 else -260), yc * 1000),
                     xytext=((-260 if s.ch_dir[j] > 0 else 260), yc * 1000),
                     arrowprops=dict(arrowstyle="->", color="white", lw=1.1, alpha=0.9))
    axf.set_xlabel("x  [mm]"); axf.set_ylabel("y  [mm]"); axf.set_aspect(1.0)
    tstamp = axf.text(0.012, 0.94, "", transform=axf.transAxes, color="white",
                      fontsize=13, fontweight="bold")
    mean_hist, max_hist, std_hist = [], [], []
    l1, = axl.plot([], [], color="#b3452c", lw=1.8, label="mean")
    l2, = axl.plot([], [], color="#17557d", lw=1.4, label="max")
    l3, = axl.plot([], [], color="#3d7a5a", lw=1.4, ls="--", label="std $\\times$ 5")
    axl.set_xlim(0, times[-1]); axl.set_ylim(VMIN - 1, VMAX + 2)
    axl.set_xlabel("time  [s]"); axl.set_ylabel("plate T  [$^\\circ$C]")
    axl.grid(alpha=0.25); axl.legend(frameon=False, fontsize=9, ncol=3, loc="lower right")
    fig.suptitle(title, fontsize=14, y=0.955)
    for k, (F, t) in enumerate(zip(frames, times)):
        im.set_array((F - 273.15).T.ravel())
        tstamp.set_text("t = %6.1f s" % t)
        Tc = F - 273.15
        mean_hist.append(Tc.mean()); max_hist.append(Tc.max())
        std_hist.append(VMIN + Tc.std() * 5)
        l1.set_data(times[:k + 1], mean_hist)
        l2.set_data(times[:k + 1], max_hist)
        l3.set_data(times[:k + 1], std_hist)
        fig.savefig(os.path.join(d, "f%04d.png" % k), dpi=100)
    plt.close(fig)
    mp4 = os.path.join(OUT, "GRAIL_CFD_%s.mp4" % name)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(fps),
                    "-i", os.path.join(d, "f%04d.png"), "-c:v", "libx264",
                    "-pix_fmt", "yuv420p", "-crf", "20", mp4], check=True)
    print("  wrote", mp4, os.path.getsize(mp4) // 1024, "KB", flush=True)
    return mp4


for name, ttl in (('co_current', "GRAIL absorber startup — CO-CURRENT (all 12 channels same direction)"),
                  ('counter_current', "GRAIL absorber startup — ALTERNATING COUNTER-CURRENT")):
    s, fr, tt = runs[name]
    render(name, s, fr, tt, ttl)
print("done")
