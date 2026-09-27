"""GRAIL transient animations — frames piped straight to ffmpeg as raw RGB (no PNG round-trip)."""
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
T_END, DT = 900.0, 2.5          # 361 frames -> 12 s at 30 fps, full startup
W, H, FPS = 1600, 900, 30

runs = {}
for f, name in ((0, 'co_current'), (1, 'counter_current')):
    t0 = time.time()
    s = GrailTransient(Geometry(), Materials(), Operating(f_interdig=f), nx=NX, ny=NY)
    fr, tt = s.run(t_end=T_END, dt=DT, save_every=1)
    runs[name] = (s, fr, tt)
    print("%-16s %d frames  final Tp mean %.2f K  std %.3f  (%.0f s)"
          % (name, len(fr), fr[-1].mean(), fr[-1].std(), time.time() - t0), flush=True)

allT = np.concatenate([np.array(fr).ravel() for _, fr, _ in runs.values()])
VMIN, VMAX = allT.min() - 273.15, allT.max() - 273.15
print("common colour scale %.2f - %.2f degC" % (VMIN, VMAX), flush=True)


def render(name, s, frames, times, title):
    fig = plt.figure(figsize=(W / 100, H / 100), dpi=100)
    gs = fig.add_gridspec(2, 1, height_ratios=[3.0, 1.0], hspace=0.40,
                          left=0.07, right=0.885, top=0.87, bottom=0.10)
    axf = fig.add_subplot(gs[0]); axl = fig.add_subplot(gs[1])
    im = axf.pcolormesh(s.xc * 1000, s.yc * 1000, (frames[0] - 273.15).T,
                        cmap="inferno", vmin=VMIN, vmax=VMAX, shading="auto")
    cax = fig.add_axes([0.90, 0.44, 0.016, 0.43])
    cb = fig.colorbar(im, cax=cax); cb.set_label("absorber temperature  [$^\\circ$C]", fontsize=11)
    for j, yc in enumerate(s.ch_y):
        axf.annotate("", xy=((250 if s.ch_dir[j] > 0 else -250), yc * 1000),
                     xytext=((-250 if s.ch_dir[j] > 0 else 250), yc * 1000),
                     arrowprops=dict(arrowstyle="->", color="white", lw=1.1, alpha=0.9))
    axf.set_xlabel("x  [mm]"); axf.set_ylabel("y  [mm]"); axf.set_aspect(1.0)
    tstamp = axf.text(0.012, 0.93, "", transform=axf.transAxes, color="white",
                      fontsize=14, fontweight="bold")
    mh, xh, sh = [], [], []
    l1, = axl.plot([], [], color="#d9663d", lw=2.0, label="mean")
    l2, = axl.plot([], [], color="#5b9bd5", lw=1.5, label="max")
    l3, = axl.plot([], [], color="#3d7a5a", lw=1.5, ls="--", label="std $\\times$ 5 (offset)")
    axl.set_xlim(0, times[-1]); axl.set_ylim(VMIN - 1.0, VMAX + 2.0)
    axl.set_xlabel("time  [s]"); axl.set_ylabel("plate T  [$^\\circ$C]")
    axl.grid(alpha=0.25); axl.legend(frameon=False, fontsize=9, ncol=3, loc="lower right")
    fig.suptitle(title, fontsize=14, y=0.955)
    fig.canvas.draw()
    w, h = fig.canvas.get_width_height()

    mp4 = os.path.join(OUT, "GRAIL_CFD_%s.mp4" % name)
    p = subprocess.Popen(
        ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgba",
         "-s", "%dx%d" % (w, h), "-framerate", str(FPS), "-i", "-",
         "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "20", mp4],
        stdin=subprocess.PIPE)
    t0 = time.time()
    for k, (F, t) in enumerate(zip(frames, times)):
        Tc = F - 273.15
        im.set_array(Tc.T.ravel())
        tstamp.set_text("t = %5.0f s" % t)
        mh.append(Tc.mean()); xh.append(Tc.max()); sh.append(VMIN + Tc.std() * 5)
        l1.set_data(times[:k + 1], mh); l2.set_data(times[:k + 1], xh); l3.set_data(times[:k + 1], sh)
        fig.canvas.draw()
        p.stdin.write(np.asarray(fig.canvas.buffer_rgba()).tobytes())
    p.stdin.close(); p.wait()
    plt.close(fig)
    print("  %s  %d KB  (%.0f s render)" % (mp4, os.path.getsize(mp4) // 1024, time.time() - t0),
          flush=True)
    return mp4


render('co_current', *runs['co_current'],
       title="GRAIL absorber startup - CO-CURRENT   (all 12 channels flow the same way)")
render('counter_current', *runs['counter_current'],
       title="GRAIL absorber startup - ALTERNATING COUNTER-CURRENT   (neighbours oppose)")
print("done")
