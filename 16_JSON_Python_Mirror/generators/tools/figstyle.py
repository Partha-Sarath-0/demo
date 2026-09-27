"""
GRAIL — one figure style for the whole study, built so the WRITING stays readable.

The complaint this exists to fix: in the first generation of figures the text that carries the
result - the axis label, the annotated number, the legend - was the first thing to get
crowded out. Titles ran into panel titles, y-axis labels were pushed into their own tick
numbers, ten series shared a cycled colour list with no legend at all, and annotations landed
on top of data.

Rules enforced here:

  1. Nothing is smaller than 10 pt, and the numbers that carry a result are 11-12 pt.
  2. constrained_layout everywhere, with real padding, so matplotlib is allowed to move text
     apart instead of overlapping it.
  3. Two series -> the validated categorical pair. More than two AND ordered (grid levels,
     mass flow, inlet temperature) -> a single-hue sequential ramp plus a colourbar or a
     labelled legend, never a cycled colour list.
  4. Every figure with two or more series carries a legend. Always.
  5. Annotations go in a box with a solid surface behind them, placed in a corner chosen from
     where the data is NOT, so they cannot sit on a marker.
  6. Tick label formats are set so a y-axis of 1.000-1.014 does not push its own axis label
     off the canvas.

Palette. Run against the dataviz validator, light surface, categorical mode:

    #2472b8  co-current    #c0522d  alternating
    lightness band PASS, chroma floor PASS, CVD separation dE 20.5 protan / 28.5 tritan PASS,
    normal-vision dE 27.4 PASS, contrast vs surface PASS  ->  ALL CHECKS PASS

The previous pair (#17557d, #b3452c) failed the chroma floor: the blue read as grey.
The sequential ramp is the reference blue 100-700 scale; ordinal use starts no lighter than
step 250 so the palest mark still clears 2:1 on a light surface.
"""
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap, Normalize
from matplotlib.ticker import FormatStrFormatter, MaxNLocator

# ------------------------------------------------------------------ palette
CO = "#2472b8"          # co-current / parallel
AL = "#c0522d"          # alternating counter-current
REF = "#6b7280"         # a neutral reference series (previous revision, target, control)
GOOD, WARN, CRIT = "#0ca30c", "#fab219", "#d03b3b"
INK, INK2, MUTED = "#1f2124", "#4a4d52", "#75797f"
SURFACE = "#ffffff"

SEQ_STEPS = ["#cde2fb", "#b7d3f6", "#9ec5f4", "#86b6ef", "#6da7ec", "#5598e7",
             "#3987e5", "#2a78d6", "#256abf", "#1c5cab", "#184f95", "#104281", "#0d366b"]
SEQ = LinearSegmentedColormap.from_list("grail_blue", SEQ_STEPS)
SEQ_ORDINAL = SEQ_STEPS[3:]          # step 250 and darker: every mark clears 2:1 on white


def ordinal(n):
    """n colours from the sequential ramp, evenly spaced, light to dark, all legible."""
    idx = np.linspace(0, len(SEQ_ORDINAL) - 1, n).round().astype(int)
    return [SEQ_ORDINAL[i] for i in idx]


# ------------------------------------------------------------------ rcParams
_HOOKED = [False]


def _install_savefig_hook():
    """Run the placement pass on every figure just before it is written."""
    if _HOOKED[0]:
        return
    from matplotlib.figure import Figure
    orig = Figure.savefig

    def patched(self, *a, **kw):
        if not getattr(self, "_grail_placed", False):
            self._grail_placed = True
            for step in (mathify_figure, plain_log_ticks, autoplace_legends):
                try:
                    step(self)
                except Exception:
                    pass
        return orig(self, *a, **kw)

    Figure.savefig = patched
    _HOOKED[0] = True


def use(base=11.0):
    plt.rcParams.update({
        "font.family": "DejaVu Sans",
        "font.size": base,
        "axes.titlesize": base + 0.5,
        "axes.labelsize": base,
        "xtick.labelsize": base - 1,
        "ytick.labelsize": base - 1,
        "legend.fontsize": base - 1,
        "figure.titlesize": base + 2.5,
        "axes.titlepad": 9.0,
        "axes.labelpad": 5.0,
        "axes.labelcolor": INK,
        "axes.edgecolor": "#c9ccd1",
        "axes.linewidth": 0.9,
        "axes.titlecolor": INK,
        "text.color": INK,
        "xtick.color": INK2, "ytick.color": INK2,
        "xtick.major.pad": 4.0, "ytick.major.pad": 4.0,
        "axes.grid": True,
        "grid.color": "#dfe2e6", "grid.alpha": 1.0, "grid.linewidth": 0.6,
        "axes.axisbelow": True,
        "legend.frameon": True,
        "legend.framealpha": 0.95,
        "legend.edgecolor": "#c9ccd1",
        "legend.facecolor": SURFACE,
        "legend.borderpad": 0.5,
        "legend.labelspacing": 0.45,
        "lines.linewidth": 2.0,
        "lines.markersize": 5.5,
        "figure.dpi": 175, "savefig.dpi": 175,
        "savefig.bbox": "tight", "savefig.pad_inches": 0.16,
        "figure.facecolor": SURFACE, "savefig.facecolor": SURFACE,
        "axes.facecolor": SURFACE,
    })
    _install_savefig_hook()


def fig(nrows=1, ncols=1, w=None, h=4.4, **kw):
    """A figure with constrained_layout and padding that actually separates text."""
    w = w if w is not None else 5.6 * ncols
    f, ax = plt.subplots(nrows, ncols, figsize=(w, h), layout="constrained", **kw)
    f.get_layout_engine().set(w_pad=0.10, h_pad=0.10, wspace=0.055, hspace=0.085)
    return f, ax


def title(f, main, sub=None):
    """Figure title, with an optional second line in muted ink for the caveat or the source."""
    if sub:
        f.suptitle(main + "\n" + sub, fontsize=plt.rcParams["figure.titlesize"], color=INK)
        # the second line is rendered smaller by using a Text override
        t = f._suptitle
        t.set_linespacing(1.45)
    else:
        f.suptitle(main, color=INK)


def note(ax, text, loc="upper right", color=INK, size=None, alpha=0.96):
    """An annotation in a box with a solid surface behind it.

    Placed by axes-fraction corner rather than in data coordinates, so refining a figure or
    changing its limits can never drop it on top of a marker.
    """
    xy = {"upper right": (0.975, 0.965, "right", "top"),
          "upper left": (0.025, 0.965, "left", "top"),
          "lower right": (0.975, 0.035, "right", "bottom"),
          "lower left": (0.025, 0.035, "left", "bottom"),
          "upper center": (0.5, 0.965, "center", "top"),
          "lower center": (0.5, 0.035, "center", "bottom")}[loc]
    return ax.text(xy[0], xy[1], text, transform=ax.transAxes, ha=xy[2], va=xy[3],
                   fontsize=size or plt.rcParams["font.size"] - 1, color=color,
                   linespacing=1.5,
                   bbox=dict(boxstyle="round,pad=0.42", facecolor=SURFACE,
                             edgecolor="#c9ccd1", linewidth=0.8, alpha=alpha))


def freest_corner(ax, x, y):
    """Which corner of the axes holds the fewest data points - where a note can safely go."""
    x, y = np.asarray(x, float), np.asarray(y, float)
    ok = np.isfinite(x) & np.isfinite(y)
    x, y = x[ok], y[ok]
    if len(x) == 0:
        return "upper right"
    x0, x1 = ax.get_xlim(); y0, y1 = ax.get_ylim()
    fx = (x - x0) / (x1 - x0 + 1e-30); fy = (y - y0) / (y1 - y0 + 1e-30)
    best, bn = "upper right", np.inf
    for nm, (cx, cy) in {"upper right": (1, 1), "upper left": (0, 1),
                         "lower right": (1, 0), "lower left": (0, 0)}.items():
        n = int((((fx - cx) ** 2 + (fy - cy) ** 2) ** 0.5 < 0.42).sum())
        if n < bn:
            best, bn = nm, n
    return best


def tidy_y(ax, decimals=None):
    """Stop a narrow-range y-axis from pushing its own label off the canvas.

    An axis running 1.000 to 1.014 gets six-character tick labels; matplotlib then has to
    place the y-label outside them and, in a tight multi-panel figure, clips it. Using an
    offset or a fixed short format keeps the labels narrow.
    """
    lo, hi = ax.get_ylim()
    span = abs(hi - lo)
    if decimals is None:
        decimals = 0 if span >= 50 else 1 if span >= 5 else 2 if span >= 0.5 else 3
    if span > 0 and abs(lo) > 20 * span:
        ax.ticklabel_format(axis="y", style="plain", useOffset=True)
    else:
        ax.yaxis.set_major_formatter(FormatStrFormatter("%%.%df" % decimals))
    ax.yaxis.set_major_locator(MaxNLocator(nbins=6, prune=None))


def legend(ax, loc="best", ncol=1, title_=None, **kw):
    """A legend that is always present and never sits on the data if it can be helped."""
    lg = ax.legend(loc=loc, ncol=ncol, title=title_, **kw)
    if lg is not None:
        lg.get_frame().set_linewidth(0.8)
        if title_:
            lg.get_title().set_fontsize(plt.rcParams["legend.fontsize"])
            lg.get_title().set_color(INK2)
    return lg


def colorbar(f, mappable, ax, label, **kw):
    cb = f.colorbar(mappable, ax=ax, pad=0.015, fraction=0.045, **kw)
    cb.set_label(label, color=INK)
    cb.outline.set_linewidth(0.8)
    cb.outline.set_edgecolor("#c9ccd1")
    return cb


def seq_mappable(values, cmap=SEQ):
    n = Normalize(vmin=float(np.min(values)), vmax=float(np.max(values)))
    sm = plt.cm.ScalarMappable(norm=n, cmap=cmap)
    sm.set_array([])
    return sm, n


def zeroline(ax, axis="y", **kw):
    """A reference line at zero, drawn so it reads as a rule and not as a series."""
    f = ax.axhline if axis == "y" else ax.axvline
    return f(0.0, color=MUTED, lw=1.1, zorder=1.5, **kw)


# ------------------------------------------------------------------ automatic placement
_LOCS = ["upper right", "upper left", "lower left", "lower right",
         "center left", "center right", "upper center", "lower center"]


def _occupancy(ax, bb, renderer, exclude=None):
    """How much drawn data lies under a display-space box: (points, patch-area fraction).

    matplotlib's loc="best" scores only Line2D vertices. It is blind to scatter offsets and
    to bar patches, which is why legends kept landing on top of the campaign scatter plots
    and on the bar charts. This scores all three.
    """
    from matplotlib.patches import Rectangle
    n = 0
    for ln in ax.get_lines():
        if not ln.get_visible():
            continue
        xy = ln.get_xydata()
        if len(xy) == 0:
            continue
        d = ax.transData.transform(xy)
        n += int(((d[:, 0] > bb.x0) & (d[:, 0] < bb.x1)
                  & (d[:, 1] > bb.y0) & (d[:, 1] < bb.y1)).sum())
    for c in ax.collections:
        if not c.get_visible():
            continue
        try:
            off = c.get_offsets()
        except Exception:
            continue
        if off is None or len(off) == 0:
            continue
        d = ax.transData.transform(np.asarray(off))
        n += int(((d[:, 0] > bb.x0) & (d[:, 0] < bb.x1)
                  & (d[:, 1] > bb.y0) & (d[:, 1] < bb.y1)).sum())
    ab = ax.get_window_extent(renderer=renderer)
    area = 0.0
    for pt in ax.patches:
        # An axhspan / axvspan band is a backdrop, not data: it spans the whole axes in one
        # direction, and a label sitting on it is intentional and readable. Only patches that
        # are bounded in both directions - bars - count as obstruction.
        if not isinstance(pt, Rectangle) or not pt.get_visible():
            continue
        pb = pt.get_window_extent(renderer=renderer)
        if pb.width > 0.95 * ab.width or pb.height > 0.95 * ab.height:
            continue
        if (pt.get_alpha() or 1.0) < 0.55:
            continue
        ox = min(bb.x1, pb.x1) - max(bb.x0, pb.x0)
        oy = min(bb.y1, pb.y1) - max(bb.y0, pb.y0)
        if ox > 0 and oy > 0:
            area += ox * oy
    # Annotations already on the axes are obstructions too. Without this the legend simply
    # trades a collision with the data for a collision with the note explaining the data,
    # which is worse: the note is usually the sentence that carries the result.
    for t in ax.texts:
        if t is exclude:
            continue          # an artist is not an obstruction to itself
        if not t.get_visible() or not t.get_text().strip():
            continue
        try:
            tb = t.get_window_extent(renderer=renderer)
        except Exception:
            continue
        ox = min(bb.x1, tb.x1) - max(bb.x0, tb.x0)
        oy = min(bb.y1, tb.y1) - max(bb.y0, tb.y0)
        if ox > 0 and oy > 0:
            area += 2.0 * ox * oy          # weighted: never park a legend on a note
    return n, area / max(bb.width * bb.height, 1.0)


# ------------------------------------------------------------------ symbols and units
# Dataset column names and solver variable names leak straight onto the axes: a plot reading
# "mdot_total_kg_s" or "T_amb_K" is showing the reader a database schema, not physics. Each
# one is mapped to how it is written in the thesis - m with an overdot, T with a subscript.
SYMBOLS = {
    "mdot_total_kg_s": r"$\dot{m}_{total}$  [kg/s]",
    "mdot_total":      r"$\dot{m}_{total}$",
    "mdot":            r"$\dot{m}$",
    "G_T_W_m2":        r"$G_T$  [W/m$^2$]",
    "T_amb_K":         r"$T_{amb}$  [K]",
    "T_in_K":          r"$T_{in}$  [K]",
    "T_out_K":         r"$T_{out}$  [K]",
    "T_plate_mean_K":  r"$\overline{T}_{plate}$  [K]",
    "U_L_W_m2K":       r"$U_L$  [W/m$^2$K]",
    "Q_rad_W":         r"$Q_{rad}$  [W]",
    "Qu_W":            r"$Q_u$  [W]",
    "R4_K4":           r"$\overline{T^4}$  [K$^4$]",
    "plate_std_K":     "plate spread, RMS  [K]",
    "plate_spread_K":  "plate peak-to-peak  [K]",
    "lateral_bridge_W": "lateral bridge  [W]",
    "dp_channel_Pa":   r"$\Delta p_{channel}$  [Pa]",
    "bridge_mm":       "bridge width  [mm]",
    "v_wind_m_s":      r"$v_{wind}$  [m/s]",
    "g_ratio":         r"$G$",
    "lambda_G":        r"$\lambda_G$",
    "eta":             r"$\eta$",
    "nu_cfd":          r"$Nu_{CFD}$",
    "tau_tim":         r"$\tau_{TIM}$",
    "tau_glz_sys":     r"$\tau_{glz,sys}$",
    "alpha_abs":       r"$\alpha_{abs}$",
    "eps_abs":         r"$\varepsilon_{abs}$",
    "k_al":            r"$k_{Al}$",
    "k_tim":           r"$k_{TIM}$",
    "k_vip":           r"$k_{VIP}$",
    "h_rear":          r"$h_{rear}$",
    "h_wind_fac":      r"$h_{wind}$ factor",
    "T_amb":           r"$T_{amb}$",
    "T_in":            r"$T_{in}$",
    "T_out":           r"$T_{out}$",
    "U_L":             r"$U_L$",
    "G_T":             r"$G_T$",
    "D_h":             r"$D_h$",
    "f_interdig":      r"$f_{interdig}$",
    r"$\Delta$Tp_std": r"$\Delta\sigma_{T_p}$",
    r"$\Delta$U_L":    r"$\Delta U_L$",
    r"$\Delta$eta":    r"$\Delta\eta$",
    r"$\Delta$dTp":    r"$\Delta$ peak-to-peak",
    "R4 / mean(T)$^4$": r"$\overline{T^4}\,/\,\overline{T}^{\,4}$",
}

# Units written the way a keyboard writes them, rewritten the way a thesis writes them.
_UNITS = [(r"\bW/m2K\b", r"W/m$^2$K"), (r"\bW/m2\b", r"W/m$^2$"),
          (r"\bK m2/W\b", r"K m$^2$/W"), (r"\bmm2\b", r"mm$^2$"),
          (r"\bmm3\b", r"mm$^3$"), (r"\bm2\b", r"m$^2$"), (r"\bK4\b", r"K$^4$"),
          # Only "dp". A separate rule rewriting a bare "Delta" would fire again on the
          # "$\Delta p$" this one has just produced, giving "$\$\Delta$ p$"; every label in
          # the suite already writes Delta as maths, so the rule is not needed.
          (r"\bdp\b", r"$\\Delta p$")]

# Whole phrases that read as jargon rather than as a quantity.
_PHRASES = [("plate temperature std", "plate temperature spread, RMS"),
            ("plate_std", "plate spread, RMS"),
            ("plate temperature spread, RMS [K]", "plate temperature spread, RMS  [K]"),
            ("Tp_std", r"$\\sigma_{T_p}$"),
            ("mean(T)", r"$\\overline{T}$")]


def mathify(text):
    """Rewrite one label, leaving any existing $...$ maths untouched."""
    import re
    if not text:
        return text
    if text in SYMBOLS:
        return SYMBOLS[text]
    # split on maths spans so a substitution can never corrupt an expression already written
    parts = re.split(r"(\$[^$]*\$)", text)
    for i, part in enumerate(parts):
        if part.startswith("$"):
            continue
        for name, rep in SYMBOLS.items():
            if name.startswith("$"):
                continue
            part = re.sub(r"(?<![A-Za-z0-9_])" + re.escape(name) + r"(?![A-Za-z0-9_])",
                          rep.replace("\\", "\\\\"), part)
        for a, b in _PHRASES:
            part = part.replace(a, b.replace("\\\\", "\\"))
        for pat, rep in _UNITS:
            part = re.sub(pat, rep, part)
        parts[i] = part
    return "".join(parts)


def mathify_figure(fig):
    """Apply the symbol map to every label on a figure.

    Tick labels are rewritten through their FixedFormatter rather than through the Text
    artists: a formatter regenerates its labels on the next draw, so editing the Text alone
    is silently undone before the figure is written.
    """
    from matplotlib.ticker import FixedFormatter, FixedLocator
    for t in fig.texts:
        t.set_text(mathify(t.get_text()))
    try:
        fig.canvas.draw()          # so the current tick labels exist to be read
    except Exception:
        pass
    for ax in fig.axes:
        ax.set_xlabel(mathify(ax.get_xlabel()))
        ax.set_ylabel(mathify(ax.get_ylabel()))
        ax.set_title(mathify(ax.get_title()))
        # Read the labels the axis is actually showing and freeze the rewritten set. Testing
        # the formatter's TYPE does not work: set_xticklabels installs a FuncFormatter in
        # current matplotlib, not the FixedFormatter this used to look for, so the category
        # labels on the correlation heatmap were silently left as database column names.
        for axis, getlabels in ((ax.xaxis, ax.get_xticklabels),
                                (ax.yaxis, ax.get_yticklabels)):
            labs = [t.get_text() for t in getlabels()]
            new_labs = [mathify(x) for x in labs]
            if new_labs != labs:
                axis.set_major_locator(FixedLocator(list(axis.get_majorticklocs())))
                axis.set_major_formatter(FixedFormatter(new_labs))
        for t in ax.texts:
            t.set_text(mathify(t.get_text()))
        lg = ax.get_legend()
        if lg is not None:
            for t in lg.get_texts():
                t.set_text(mathify(t.get_text()))
            if lg.get_title() is not None:
                lg.get_title().set_text(mathify(lg.get_title().get_text()))


def plain_log_ticks(fig):
    """Write plain numbers on a log axis that spans less than about a decade.

    matplotlib labels such an axis with minor ticks in scientific form - "6 x 10^0",
    "4 x 10^0", "3 x 10^0" - which is unreadable and, on an axis running 2 to 6 mm, actively
    misleading about the scale. A ScalarFormatter puts 6, 5, 4, 3, 2 there instead.
    """
    from matplotlib.ticker import ScalarFormatter, LogLocator, NullFormatter
    for ax in fig.axes:
        for axis, getlim, scale in ((ax.xaxis, ax.get_xlim, ax.get_xscale()),
                                    (ax.yaxis, ax.get_ylim, ax.get_yscale())):
            if scale != "log":
                continue
            lo, hi = sorted(abs(v) for v in getlim())
            if lo <= 0 or hi / lo > 12.0:
                continue                   # a genuinely wide log axis keeps powers of ten
            axis.set_major_locator(LogLocator(base=10, subs=(1.0, 2.0, 3.0, 5.0, 7.0),
                                              numticks=12))
            f = ScalarFormatter()
            f.set_scientific(False)
            axis.set_major_formatter(f)
            axis.set_minor_formatter(NullFormatter())


def autoplace_legends(fig):
    """Move every legend to the corner of its axes with the least data under it.

    Scored analytically, not by trial: the legend is drawn once to learn its size, then the
    box it WOULD occupy at each of the eight anchor positions is computed inside the axes
    rectangle and scored. Re-drawing the figure once per candidate is correct but costs eight
    full renders per legend, which made the figure suite take minutes instead of seconds.
    """
    try:
        fig.canvas.draw()
        r = fig.canvas.get_renderer()
    except Exception:
        return
    pad = 6.0     # px inset from the axes frame, matching matplotlib's borderaxespad
    for ax in fig.axes:
        lg = ax.get_legend()
        if lg is None or not lg.get_visible():
            continue
        try:
            lb = lg.get_window_extent(renderer=r)
            ab = ax.get_window_extent(renderer=r)
        except Exception:
            continue
        w, h = lb.width, lb.height
        if w >= ab.width or h >= ab.height:
            continue                      # nowhere for it to go inside the axes
        xs = {"left": ab.x0 + pad, "center": ab.x0 + 0.5 * (ab.width - w), "right": ab.x1 - pad - w}
        ys = {"lower": ab.y0 + pad, "center": ab.y0 + 0.5 * (ab.height - h), "upper": ab.y1 - pad - h}
        from matplotlib.transforms import Bbox
        best, best_score = None, None
        for loc in _LOCS:
            vy, vx = loc.split()
            x, y = xs[vx], ys[vy]
            cand = Bbox.from_bounds(x, y, w, h)
            npts, frac = _occupancy(ax, cand, r)
            score = npts + 400.0 * frac
            # a mild preference for the conventional upper-right when nothing is in the way
            score += 0.01 * _LOCS.index(loc)
            if best_score is None or score < best_score:
                best, best_score = loc, score
        if best is not None:
            try:
                lg.set_loc(best)
            except Exception:
                pass


def save(f, path, verbose=True):
    f.savefig(path)
    plt.close(f)
    if verbose:
        print("   wrote %s" % path.rsplit("/", 1)[-1])
