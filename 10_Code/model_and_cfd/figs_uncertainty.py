import sys
"""
GRAIL — uncertainty and sensitivity figures U1 - U4.

U1  grid convergence of the claim quantities, with Richardson extrapolation and GCI bands
U2  input-uncertainty distributions, paired against unpaired
U3  sensitivity ranking: which inputs the result actually depends on
U4  the campaign-grid correction measured across operating points
"""
import os, json
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
sys.path.insert(0, '/home/claude/grail_cfd/tools')
import figstyle as FS
FS.use()

V = "/home/claude/grail_cfd/05_validation"
FIG = "/home/claude/grail_cfd/12_figures"
CO, AL, NEU = FS.CO, FS.AL, "#3d7a5a"


def load(name):
    p = os.path.join(V, name)
    return json.load(open(p)) if os.path.exists(p) else None


# ------------------------------------------------------------------ U1 grid convergence
G = load("gci_plate.json")
if G:
    lv = G["levels"]
    h = np.array([l["h_mm"] for l in lv])            # coarse -> fine
    keys = ["%dx%d" % (l["nx"], l["ny"]) for l in lv]
    fig, ax = plt.subplots(1, 3, figsize=(14.07, 5.17), layout="constrained")

    for a, q, lab in ((ax[0], "Tp_std", "plate temperature spread"),
                      (ax[1], "eta", "efficiency"),
                      (ax[2], "U_L", "loss coefficient $U_L$")):
        d = np.array([100.0 * (G["raw"]["alt"][k][q] - G["raw"]["co"][k][q])
                      / G["raw"]["co"][k][q] for k in keys])
        a.plot(h, d, "o-", color=AL, lw=1.7, ms=6, label="computed")
        for trip, c, ls in (("L4L3L2", "#444444", "--"), ("L3L2L1", "#999999", ":")):
            g = G["gci_difference"][trip]["d_%s_pct" % q]
            if g.get("f_extrap") is not None and np.isfinite(g["f_extrap"]):
                a.axhline(g["f_extrap"], color=c, ls=ls, lw=1.1,
                          label="Richardson, %s (p = %.2f)"
                                % (trip, g["p"]) if g["p"] else trip)
        g = G["gci_difference"]["L4L3L2"]["d_%s_pct" % q]
        f1 = d[-1]
        band = abs(f1) * g["gci_pct"] / 100.0
        a.fill_between([h.min() * 0.85, h.max() * 1.1], f1 - band, f1 + band,
                       color=AL, alpha=0.13, lw=0,
                       label="GCI on the finest grid, %.1f %%" % g["gci_pct"])
        a.set_xscale("log")
        a.set_xlabel("representative cell size  h  [mm]")
        a.set_ylabel("alternating $-$ co-current  [%]")
        a.set_title(lab, fontsize=11.6)
        a.invert_xaxis()
        a.legend(frameon=True, framealpha=0.94, fontsize=9.0, loc="lower right")
    ax[0].annotate("the campaign grid\nsits here", xy=(h[0], d[0] if False else
                   100.0 * (G["raw"]["alt"][keys[0]]["Tp_std"] - G["raw"]["co"][keys[0]]["Tp_std"])
                   / G["raw"]["co"][keys[0]]["Tp_std"]),
                   xytext=(0.36, 0.88), textcoords="axes fraction", fontsize=9.6, color="0.3",
                   arrowprops=dict(arrowstyle="->", color="0.45", lw=0.9))
    fig.suptitle("Fig U1 — Grid convergence of the alternating-minus-co-current difference. "
                 "Refinement reduces the uniformity benefit; efficiency and $U_L$ barely move.",
                 fontsize=12.1)
    fig.savefig(FIG + "/U1_grid_convergence.png"); plt.close(fig)
    print("wrote U1")

# ------------------------------------------------------------------ U2 input uncertainty
M = load("mc_summary.json")
if M:
    import csv as _csv
    rows = list(_csv.DictReader(open(os.path.join(V, "mc_samples.csv"))))
    col = lambda k: np.array([float(r[k]) for r in rows])
    fig, ax = plt.subplots(1, 3, figsize=(14.07, 5.03), layout="constrained")

    ax[0].hist(col("co_eta"), bins=34, color=CO, alpha=0.75, label="co-current")
    ax[0].hist(col("alt_eta"), bins=34, color=AL, alpha=0.75, label="alternating")
    ax[0].set_xlabel("efficiency"); ax[0].set_ylabel("samples")
    ax[0].set_title("Efficiency under input uncertainty", fontsize=11.6)
    ax[0].legend(frameon=True, framealpha=0.94, fontsize=9.6)

    d = col("d_Tp_std_pct")
    ax[1].hist(d, bins=34, color=NEU, alpha=0.85)
    lo, hi = np.percentile(d, [2.5, 97.5])
    for v, s in ((d.mean(), "-"), (lo, "--"), (hi, "--")):
        ax[1].axvline(v, color="0.15", ls=s, lw=1.1)
    ax[1].set_xlabel("alternating $-$ co-current plate spread  [%]")
    ax[1].set_ylabel("samples")
    ax[1].set_title("The uniformity difference\nmean %.2f %%, 95 %% CI [%.2f, %.2f]"
                    % (d.mean(), lo, hi), fontsize=11.6)

    qs = ["Tp_std", "eta", "U_L", "dTp"]
    paired = [M["difference"]["d_%s_pct" % q]["sd"] for q in qs]
    unp = [M["difference"]["d_%s_pct" % q]["unpaired_sd_would_be_pct"] for q in qs]
    x = np.arange(len(qs))
    ax[2].bar(x - 0.19, paired, 0.38, color=NEU, label="paired (correct)")
    ax[2].bar(x + 0.19, unp, 0.38, color="#bbbbbb", label="unpaired (overstated)")
    ax[2].set_xticks(x); ax[2].set_xticklabels(["$\\Delta$" + q for q in qs], fontsize=10.1)
    ax[2].set_ylabel("standard deviation  [%]")
    ax[2].set_title("Pairing the draws is what makes\nthe difference measurable", fontsize=11.6)
    ax[2].legend(frameon=True, framealpha=0.94, fontsize=9.6)
    fig.suptitle("Fig U2 — Propagated property and boundary-condition uncertainty, "
                 "%d paired Monte Carlo samples on the campaign grid"
                 % M["n_accepted"], fontsize=12.1)
    fig.savefig(FIG + "/U2_input_uncertainty.png"); plt.close(fig)
    print("wrote U2")

    # -------------------------------------------------------------- U3 sensitivity
    fig, ax = plt.subplots(1, 2, figsize=(13.44, 5.71), layout="constrained")
    for a, q, ttl in ((ax[0], "co_eta", "efficiency (co-current)"),
                      (ax[1], "d_Tp_std_pct", "the uniformity difference")):
        s = M["sensitivity"][q]
        names = s["ranked"][:9][::-1]
        vals = [s["src"][n] for n in names]
        cols = [AL if v < 0 else CO for v in vals]
        a.barh(np.arange(len(names)), vals, color=cols)
        a.set_yticks(np.arange(len(names))); a.set_yticklabels(names, fontsize=10.1)
        a.axvline(0, color="0.3", lw=0.8)
        a.set_xlabel("standardised regression coefficient")
        a.set_title("%s\nlinear model $R^2$ = %.3f" % (ttl, s["R2_of_linear_model"]))
        # The share labels used to be placed in DATA coordinates a fixed 0.02 from the bar
        # tip. On a negative bar that put the label straight on top of the y tick label
        # ("eps_abs1 %"), and on the longest bar it ran off the right edge. Offsetting in
        # POINTS from the tip, and giving the axis 18 % headroom, keeps every label clear.
        a.margins(x=0.18)
        for i, n in enumerate(names):
            a.annotate("%.0f %%" % s["variance_share_pct"][n], xy=(vals[i], i),
                       xytext=(7 if vals[i] >= 0 else -7, 0), textcoords="offset points",
                       va="center", ha="left" if vals[i] >= 0 else "right",
                       fontsize=9.5, color=FS.INK2)
    fig.suptitle("Fig U3 \u2014 Which inputs the results actually depend on\n"
                 "Bars are signed. The label at each bar tip is that input's share of "
                 "the variance.")
    fig.savefig(FIG + "/U3_sensitivity.png"); plt.close(fig)
    print("wrote U3")

# ------------------------------------------------------------------ U4 campaign correction
C = load("grid_correction.json")
if C:
    fig, ax = plt.subplots(1, 3, figsize=(14.4, 5.2), layout="constrained")
    keys = ["%dx%d" % tuple(l) for l in C["levels"]]
    md = np.array([q["mdot_total"] for q in C["points"]]) * 1000.0
    # Ten operating points is ten lines. They used to be drawn in matplotlib's cycled colour
    # list with no legend at all, which made them unidentifiable. They are ORDERED by mass
    # flow, so they get a single-hue sequential ramp and a colourbar instead.
    sm, norm = FS.seq_mappable(md)
    for q, mm in sorted(zip(C["points"], md), key=lambda t: t[1]):
        h = [q["levels"][k]["h_mm"] for k in keys]
        d = [q["levels"][k]["d_Tp_std_pct"] for k in keys]
        ax[0].plot(h, d, "o-", lw=1.7, ms=5, color=FS.SEQ(norm(mm)))
    ax[0].invert_xaxis()
    ax[0].set_xlabel("representative cell size  h  [mm]   (finer to the right)")
    ax[0].set_ylabel("$\\Delta$ plate spread  [%]")
    ax[0].set_title("Every operating point shrinks with refinement")
    FS.zeroline(ax[0])
    FS.colorbar(fig, sm, ax[0], "total mass flow  [g/s]")

    d1 = np.array([q["levels"][keys[0]]["d_Tp_std_pct"] for q in C["points"]])
    d3 = np.array([q["levels"][keys[2]]["d_Tp_std_pct"] for q in C["points"]])
    shift = d3 - d1
    ax[1].scatter(md, shift, s=58, color=AL, lw=0, zorder=3)
    ax[1].axhline(shift.mean(), color=FS.INK, lw=1.4, zorder=2)
    FS.zeroline(ax[1])
    ax[1].set_xlabel("total mass flow  [g/s]")
    ax[1].set_ylabel("shift  [percentage points]")
    ax[1].set_title("The correction is additive, not a scale factor")
    FS.note(ax[1], "mean shift\n%+.2f $\\pm$ %.2f pp" % (shift.mean(), shift.std(ddof=1)),
            FS.freest_corner(ax[1], md, shift))

    ax[2].scatter(md, d1, s=54, color=FS.REF, lw=0, label="campaign grid, 110 x 120", zorder=3)
    ax[2].scatter(md, d3, s=54, color=AL, lw=0, label="refined, 220 x 240", zorder=3)
    FS.zeroline(ax[2])
    ax[2].set_xlabel("total mass flow  [g/s]")
    ax[2].set_ylabel("$\\Delta$ plate spread  [%]")
    ax[2].set_title("Refinement shifts every point the same way")
    FS.legend(ax[2], loc="lower left")
    # CR-15: the 1.81 g/s threshold this panel used to mark is WITHDRAWN. It was read off
    # these same ten points, computed at the Rev 1 Nusselt number; in the recomputed campaign
    # no mass-flow bin changes sign. The panel says so rather than quietly dropping the line.
    FS.note(ax[2], "computed at Nu = 3.4282 (Rev 1).\nThe 1.81 g/s threshold once read\n"
                   "off this panel is WITHDRAWN, CR-15.",
            "upper right", color=FS.INK2, size=9.5)
    fig.suptitle("Fig U4 \u2014 Measured correction from the campaign grid to 220 x 240, "
                 "over %d campaign operating points" % C["n_points"])
    fig.savefig(FIG + "/U4_campaign_correction.png"); plt.close(fig)
    print("wrote U4")

print("done")
