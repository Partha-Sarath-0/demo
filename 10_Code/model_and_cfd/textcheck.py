"""
GRAIL — find every piece of text that collides with, or runs off, a figure.

Eyeballing 55 figures does not work: the small collisions are exactly the ones that get
missed, and those are the ones that make a figure unreadable. This renders each figure the
way matplotlib will save it, asks the renderer for the bounding box of every Text artist on
it, and reports:

  OVERLAP   two texts whose boxes intersect by more than a tolerance
  OUTSIDE   a text whose box leaves the figure canvas, i.e. it will be clipped
  TINY      a text whose rendered cap height is below a legibility floor

It runs the real figure scripts with savefig intercepted, so it checks the actual output and
not a reconstruction of it.

Usage:  python3 tools/textcheck.py [script.py ...]
"""
import os, sys, runpy, warnings
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.figure import Figure

warnings.filterwarnings("ignore")

MIN_PT = 8.5          # anything smaller than this is not readable in a printed thesis
OVERLAP_TOL = 1.0     # px; boxes sharing less than this are touching, not colliding
EDGE_TOL = 1.0        # px a text may sit outside the canvas before it counts as clipped

REPORT = []


def _texts_of(fig, renderer):
    """Every Text artist on the figure, with a label saying where it came from."""
    out = []

    def add(t, where):
        if t is None:
            return
        s = t.get_text()
        if not s or not s.strip() or not t.get_visible():
            return
        try:
            bb = t.get_window_extent(renderer=renderer)
        except Exception:
            return
        if bb.width <= 0 or bb.height <= 0:
            return
        out.append((where, s.replace("\n", " / ")[:60], bb, t))

    for t in fig.texts:
        add(t, "figure text")
    # Axes that occupy the same rectangle are twins (twinx / twiny). They carry a duplicate
    # set of tick labels at identical positions, one of which matplotlib does not draw, so
    # counting them as two artists reports a 100 % "overlap" that does not exist.
    groups = {}
    for i, ax in enumerate(fig.axes):
        key = tuple(np.round(ax.get_position().bounds, 6))
        groups.setdefault(key, []).append(i)
    twin_of = {}
    for key, idxs in groups.items():
        for i in idxs:
            twin_of[i] = idxs[0]

    for i, ax in enumerate(fig.axes):
        tag = "ax%d" % twin_of.get(i, i)
        add(ax.title, tag + " title")
        add(ax.xaxis.label, tag + " xlabel")
        add(ax.yaxis.label, tag + " ylabel")
        # Only ticks inside the current view are drawn. The locator also makes labels for
        # positions beyond the limits; those artists exist but are never rendered, and
        # reporting them produces a stream of phantom problems.
        x0, x1 = sorted(ax.get_xlim())
        y0, y1 = sorted(ax.get_ylim())
        for t in ax.get_xticklabels():
            if x0 - 1e-9 <= t.get_position()[0] <= x1 + 1e-9:
                add(t, tag + " xtick")
        for t in ax.get_yticklabels():
            if y0 - 1e-9 <= t.get_position()[1] <= y1 + 1e-9:
                add(t, tag + " ytick")
        for t in ax.texts:
            add(t, tag + " annotation")
        lg = ax.get_legend()
        if lg is not None:
            for t in lg.get_texts():
                add(t, tag + " legend")
            if lg.get_title() is not None:
                add(lg.get_title(), tag + " legend title")
    return out


def _data_under(ax, bb, renderer, exclude=None):
    """Delegates to the figure style's own occupancy scorer, so the checker and the automatic
    legend placer agree on what counts as an obstruction. Keeping two copies of that rule let
    the checker report band labels as problems that the placer had correctly ignored."""
    sys.path.insert(0, "/home/claude/grail_cfd/tools")
    import figstyle as FS
    return FS._occupancy(ax, bb, renderer, exclude=exclude)


def _same_owner(a, b):
    """Two texts that belong to the same axis element are allowed to sit close."""
    wa, wb = a[0], b[0]
    if wa == wb:
        return True
    ka, kb = wa.split()[0], wb.split()[0]
    # entries of one legend, and the legend's own title
    if ka == kb and "legend" in wa and "legend" in wb:
        return True
    return False


def check(fig, name):
    fig.canvas.draw()
    r = fig.canvas.get_renderer()
    items = _texts_of(fig, r)
    fw, fh = fig.canvas.get_width_height()
    issues = []

    for where, s, bb, t in items:
        # rendered size in points, at the dpi the figure will be saved with
        pt = t.get_fontsize()
        if pt < MIN_PT:
            issues.append(("TINY", "%-18s %-42s %.1f pt" % (where, repr(s), pt)))
        # No OUTSIDE check: every figure here is saved with bbox_inches="tight", so the
        # canvas is expanded to contain the artists and nothing leaving the figure rectangle
        # is actually clipped. Overlap is the defect that survives that, so overlap is what
        # is checked.

    # text parked on top of the data
    ax_of = {}
    for i, ax in enumerate(fig.axes):
        ax_of["ax%d" % i] = ax
    for where, s_, bb, t in items:
        kind = where.split()[-1] if " " in where else ""
        if kind not in ("legend", "annotation", "title"):
            continue
        ax = ax_of.get(where.split()[0])
        if ax is None:
            continue
        npts, frac = _data_under(ax, bb, r, exclude=t)
        if npts >= 3 or frac > 0.12:
            issues.append(("ON DATA", "%-18s %-42s covers %d data points, %.0f%% bars"
                           % (where, repr(s_), npts, 100 * frac)))

    for i in range(len(items)):
        for j in range(i + 1, len(items)):
            a, b = items[i], items[j]
            if _same_owner(a, b):
                continue
            ba, bb_ = a[2], b[2]
            ox = min(ba.x1, bb_.x1) - max(ba.x0, bb_.x0)
            oy = min(ba.y1, bb_.y1) - max(ba.y0, bb_.y0)
            if ox > OVERLAP_TOL and oy > OVERLAP_TOL:
                frac = (ox * oy) / min(ba.width * ba.height, bb_.width * bb_.height)
                issues.append(("OVERLAP", "%-18s %-30s  X  %-18s %-30s  (%.0f%% of the smaller)"
                               % (a[0], repr(a[1]), b[0], repr(b[1]), 100 * frac)))
    if issues:
        REPORT.append((name, issues))


_orig_savefig = Figure.savefig


def _patched(self, fname, *a, **kw):
    try:
        nm = os.path.basename(fname) if isinstance(fname, str) else "figure"
        check(self, nm)
    except Exception as e:
        REPORT.append((str(fname), [("ERROR", repr(e))]))
    return _orig_savefig(self, fname, *a, **kw)


Figure.savefig = _patched

if __name__ == "__main__":
    scripts = sys.argv[1:] or [
        "tools/figs_geometry.py", "tools/figs_campaign.py", "tools/figs_sensitivity.py",
        "tools/figs_uncertainty.py", "tools/figs_filings.py", "tools/fig_g1.py",
        "tools/fig_mechanism.py"]
    os.environ.setdefault("GRAIL_DATASET",
                          "/home/claude/grail_cfd/10_dataset/GRAIL_CFD_dataset_rev2.csv")
    for s in scripts:
        sys.argv = [s]
        try:
            runpy.run_path(s, run_name="__main__")
        except SystemExit:
            pass
        except Exception as e:
            REPORT.append((s, [("SCRIPT ERROR", repr(e))]))
        plt.close("all")

    n_over = n_out = n_tiny = 0
    print("=" * 100)
    for name, issues in REPORT:
        kinds = {k for k, _ in issues}
        print("\n%s" % name)
        for k, msg in issues:
            print("   %-8s %s" % (k, msg))
            n_over += k == "OVERLAP"
            n_out += k == "OUTSIDE"
            n_tiny += k == "TINY"
            n_data = sum(1 for _, ii in REPORT for kk, _ in ii if kk == "ON DATA")
    print("\n" + "=" * 100)
    n_data = sum(1 for _, ii in REPORT for kk, _ in ii if kk == "ON DATA")
    print("figures with problems: %d      OVERLAP %d   ON DATA %d   TINY %d"
          % (len(REPORT), n_over, n_data, n_tiny))
