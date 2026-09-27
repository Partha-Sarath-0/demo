"""
GRAIL — Rev 1 vs Rev 2 of the production campaign, at the two Nusselt numbers.

Rev 1 ran at nu_cfd = 3.4282, the value measured on the medium 3-D grid. The three-level
grid study (observed order p = 1.283, GCI 11.6 %) extrapolates to 2.9238, so Rev 1 carried a
+17.25 % bias on the single input the sensitivity analysis found controls 91 % of the
uniformity difference. Rev 2 is the same 291 cases - same seed, same Latin Hypercube, same
bounds, same gates, same grid - with only that number changed.

Two comparisons are made and they answer different questions.

  PAIRED, case by case. Every Rev 2 row has a Rev 1 twin with identical inputs, so the
  difference between them is caused by nu_cfd and by nothing else. This is the clean
  measurement of what the correction did.

  CAMPAIGN AVERAGE, arrangement against arrangement. The co-current and alternating halves
  of the campaign are two INDEPENDENT Latin Hypercube samples of the same parameter space,
  not a matched pair (campaign.build_jobs draws sampler.random twice). Their difference is
  therefore a difference of sample means and carries sampling error, which is reported.

The lateral bridge is reported in WATTS and never as a percentage. Under co-current flow the
lateral bridge is exactly zero by symmetry (CR-12), so a ratio against it is a division by a
number that is only non-zero through cell-alignment sampling noise; campaign2.py printed
+2.2e14 % for it, which is that division and not a result.

Writes 05_validation/rev2_analysis.json and 12_figures/R1_rev1_vs_rev2.png
"""
import os, sys, csv, json
import numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
sys.path.insert(0, "/home/claude/grail_cfd/tools")
import figstyle as FS
FS.use()

D = "/home/claude/grail_cfd/10_dataset"
OUT = "/home/claude/grail_cfd/05_validation/rev2_analysis.json"
FIG = "/home/claude/grail_cfd/12_figures"
NU_OLD, NU_NEW = 3.4282, 2.9238
CO, AL = FS.CO, FS.AL

QTY = [("eta", "efficiency", "-"),
       ("plate_std_K", "plate spread, RMS", "K"),
       ("plate_spread_K", "plate peak-to-peak", "K"),
       ("U_L_W_m2K", "loss coefficient", "W/m2K"),
       ("T_out_K", "outlet temperature", "K"),
       ("T_plate_mean_K", "mean plate temperature", "K")]


def load(p):
    return {r["case_id"]: r for r in csv.DictReader(open(p))}


old = load(D + "/GRAIL_CFD_dataset_corrected.csv")
new = load(D + "/GRAIL_CFD_dataset_rev2.csv")
common = sorted(set(old) & set(new))
co_ids = [i for i in common if i.startswith("PAR")]
al_ids = [i for i in common if i.startswith("ALT")]
g = lambda d, k, ids: np.array([float(d[i][k]) for i in ids])

res = {"nu_rev1": NU_OLD, "nu_rev2": NU_NEW,
       "nu_shift_pct": 100 * (NU_NEW - NU_OLD) / NU_OLD,
       "n_common": len(common), "n_co": len(co_ids), "n_alt": len(al_ids),
       "rev1_rows_only": sorted(set(old) - set(new)),
       "rev2_rows_only": sorted(set(new) - set(old))}

# ---------------------------------------------------------------- 1. paired, case by case
paired = {}
for k, label, unit in QTY:
    rec = {}
    for tag, ids in (("co", co_ids), ("alt", al_ids)):
        o, n = g(old, k, ids), g(new, k, ids)
        d = n - o
        rec[tag] = {"rev1_mean": float(o.mean()), "rev2_mean": float(n.mean()),
                    "paired_shift_mean": float(d.mean()),
                    "paired_shift_sd": float(d.std(ddof=1)),
                    "paired_shift_pct_mean": float((100 * d / o).mean()),
                    "n": len(ids)}
    paired[k] = {"label": label, "unit": unit, **rec}
res["paired_rev1_to_rev2"] = paired

# lateral bridge, in watts only
bl = {}
for tag, ids in (("co", co_ids), ("alt", al_ids)):
    o, n = g(old, "lateral_bridge_W", ids), g(new, "lateral_bridge_W", ids)
    bl[tag] = {"rev1_mean_W": float(o.mean()), "rev2_mean_W": float(n.mean()),
               "rev1_max_abs_W": float(np.abs(o).max()),
               "rev2_max_abs_W": float(np.abs(n).max()),
               "paired_shift_mean_W": float((n - o).mean())}
bl["note"] = ("absolute watts only. Under co-current flow the lateral bridge is exactly zero "
              "by symmetry (CR-12); the small non-zero readings are a cell-alignment "
              "sampling artefact and a ratio against them is meaningless.")
res["lateral_bridge_W"] = bl

# ---------------------------------------------------------------- 2. arrangement difference
arr = {}
for k, label, unit in QTY:
    row = {"label": label, "unit": unit}
    for rev, d in (("rev1", old), ("rev2", new)):
        c, a = g(d, k, co_ids), g(d, k, al_ids)
        # two independent samples: Welch standard error on the difference of means
        se = math_se = np.sqrt(c.var(ddof=1) / len(c) + a.var(ddof=1) / len(a))
        row[rev] = {"co_mean": float(c.mean()), "alt_mean": float(a.mean()),
                    "difference": float(a.mean() - c.mean()),
                    "difference_pct": float(100 * (a.mean() - c.mean()) / c.mean()),
                    "se_of_difference": float(se),
                    "se_of_difference_pct": float(100 * se / c.mean()),
                    "distinguishable_at_k2": bool(abs(a.mean() - c.mean()) > 2 * se)}
    row["shift_pct_points"] = row["rev2"]["difference_pct"] - row["rev1"]["difference_pct"]
    arr[k] = row
res["arrangement_difference"] = arr

# ---------------------------------------------------------------- 3. flow-rate dependence
# Binned, and flagged for what it is: the two arrangements are independent samples, so each
# bin compares different parameter draws and the bin-to-bin scatter is sampling noise, not
# structure. Rev 1 read a sign change near 1.81 g/s from this same construction.
prof = {"note": ("binned over independent samples; bin-to-bin scatter is sampling noise. "
                 "The only robust statement is the sign of the difference in every bin."),
        "bins": []}
mo_c, mo_a = g(new, "mdot_total_kg_s", co_ids), g(new, "mdot_total_kg_s", al_ids)
edges = np.linspace(min(mo_c.min(), mo_a.min()), max(mo_c.max(), mo_a.max()), 9)
for rev, d in (("rev1", old), ("rev2", new)):
    sc, sa = g(d, "plate_std_K", co_ids), g(d, "plate_std_K", al_ids)
    mc, ma = g(d, "mdot_total_kg_s", co_ids), g(d, "mdot_total_kg_s", al_ids)
    rows = []
    for b in range(len(edges) - 1):
        ia = (ma >= edges[b]) & (ma < edges[b + 1])
        ic = (mc >= edges[b]) & (mc < edges[b + 1])
        if ia.sum() >= 3 and ic.sum() >= 3:
            se = np.sqrt(sc[ic].var(ddof=1) / ic.sum() + sa[ia].var(ddof=1) / ia.sum())
            rows.append({"mdot_mid_g_s": float(500 * (edges[b] + edges[b + 1])),
                         "d_plate_std_pct": float(100 * (sa[ia].mean() - sc[ic].mean())
                                                  / sc[ic].mean()),
                         "se_pct": float(100 * se / sc[ic].mean()),
                         "n_alt": int(ia.sum()), "n_co": int(ic.sum())})
    prof[rev] = rows
    signs = {np.sign(r["d_plate_std_pct"]) for r in rows}
    prof[rev + "_all_bins_favour_alternating"] = bool(signs == {-1.0})
res["flow_profile"] = prof

# ------------------------------------------------- 4. the censoring Rev 1 did not know about
# Rev 1 lost 9 alternating cases to the not_converged gate and none co-current, so its
# campaign average compared 150 co-current rows against 141 alternating ones. Rev 2 loses
# none: the lower Nusselt number leaves the coupled solve better conditioned. The 9 rows are
# not a random 9 - they are the lowest-flow, worst-uniformity alternating cases in the
# sample, so Rev 1's average was taken over a sample with its own hardest cases removed.
# That is a censoring bias, and it flatters alternating.
recovered = sorted(set(new) - set(old))
al_all = [i for i in new if i.startswith("ALT")]
co_all = [i for i in new if i.startswith("PAR")]
cen = {"rev1_lost_rows": sorted(set(old) - set(new)) or None,
       "rev1_missing_from_rev2": sorted(set(old) - set(new)),
       "rows_recovered_in_rev2": recovered,
       "n_recovered": len(recovered),
       "all_recovered_are_alternating": all(i.startswith("ALT") for i in recovered)}
if recovered:
    md_all = g(new, "mdot_total_kg_s", al_all)
    md_rec = g(new, "mdot_total_kg_s", recovered)
    sd_all = g(new, "plate_std_K", al_all)
    sd_rec = g(new, "plate_std_K", recovered)
    cen["recovered_mdot_mean_g_s"] = float(1000 * md_rec.mean())
    cen["alternating_mdot_mean_g_s"] = float(1000 * md_all.mean())
    cen["recovered_mdot_max_g_s"] = float(1000 * md_rec.max())
    cen["campaign_mdot_min_g_s"] = float(1000 * min(md_all.min(),
                                                    g(new, "mdot_total_kg_s", co_all).min()))
    cen["recovered_plate_std_mean_K"] = float(sd_rec.mean())
    cen["alternating_plate_std_mean_K"] = float(sd_all.mean())
    ca, aa = g(new, "plate_std_K", co_all), sd_all
    se = np.sqrt(ca.var(ddof=1) / len(ca) + aa.var(ddof=1) / len(aa))
    cen["uncensored_rev2"] = {
        "n_co": len(co_all), "n_alt": len(al_all),
        "d_plate_std_pct": float(100 * (aa.mean() - ca.mean()) / ca.mean()),
        "se_pct": float(100 * se / ca.mean())}
    cen["censored_291_rev2_d_plate_std_pct"] = arr["plate_std_K"]["rev2"]["difference_pct"]
    cen["censored_291_rev1_d_plate_std_pct"] = arr["plate_std_K"]["rev1"]["difference_pct"]
    cen["reading"] = (
        "two corrections of opposite sign, of similar size. Fixing the Nusselt number alone, "
        "on the 291 rows both revisions share, strengthens the uniformity benefit from "
        "%.2f %% to %.2f %%. Putting the 9 censored low-flow rows back weakens it to %.2f %%. "
        "The headline number is the uncensored one, because it is the only average taken over "
        "the sample that was actually drawn."
        % (cen["censored_291_rev1_d_plate_std_pct"],
           cen["censored_291_rev2_d_plate_std_pct"],
           cen["uncensored_rev2"]["d_plate_std_pct"]))
res["censoring"] = cen

json.dump(res, open(OUT, "w"), indent=1)

# ---------------------------------------------------------------- figure
fig, ax = plt.subplots(1, 3, figsize=(13.6, 5.3), layout="constrained")
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9.5})

k = "plate_std_K"
a0 = ax[0]
o_a, n_a = g(old, k, al_ids), g(new, k, al_ids)
o_c, n_c = g(old, k, co_ids), g(new, k, co_ids)
a0.plot(o_c, n_c, ".", ms=4, color=CO, label="co-current, %d cases" % len(co_ids))
a0.plot(o_a, n_a, ".", ms=4, color=AL, label="alternating, %d cases" % len(al_ids))
lim = [0, max(o_a.max(), o_c.max()) * 1.05]
a0.plot(lim, lim, "-", lw=0.8, color="0.4")
a0.set_xlim(lim); a0.set_ylim(lim)
a0.set_xlabel("plate spread, Rev 1 at Nu = %.4f   [K]" % NU_OLD)
a0.set_ylabel("plate spread, Rev 2 at Nu = %.4f   [K]" % NU_NEW)
a0.set_title("paired: same case, only Nu changed")
FS.legend(a0, loc="upper left")


a1 = ax[1]
labels = [arr[q]["label"] for q, _, _ in QTY]
r1 = [arr[q]["rev1"]["difference_pct"] for q, _, _ in QTY]
r2 = [arr[q]["rev2"]["difference_pct"] for q, _, _ in QTY]
e1 = [2 * arr[q]["rev1"]["se_of_difference_pct"] for q, _, _ in QTY]
e2 = [2 * arr[q]["rev2"]["se_of_difference_pct"] for q, _, _ in QTY]
yy = np.arange(len(labels))
a1.barh(yy - 0.19, r1, 0.36, xerr=e1, color="0.62", ecolor="0.35",
        error_kw=dict(lw=0.8, capsize=2), label="Rev 1")
a1.barh(yy + 0.19, r2, 0.36, xerr=e2, color=AL, ecolor="0.35",
        error_kw=dict(lw=0.8, capsize=2), label="Rev 2")
a1.set_yticks(yy); a1.set_yticklabels(labels)
a1.axvline(0, color="0.3", lw=0.8)
a1.set_xlabel("alternating minus co-current   [%],  bars are k = 2")
a1.set_title("campaign average, both revisions")
FS.legend(a1)
a1.grid(axis="x")

a2 = ax[2]
for rev, col, mk in (("rev1", "0.55", "s"), ("rev2", AL, "o")):
    r = prof[rev]
    x = [q["mdot_mid_g_s"] for q in r]
    y = [q["d_plate_std_pct"] for q in r]
    e = [2 * q["se_pct"] for q in r]
    a2.errorbar(x, y, yerr=e, fmt=mk + "-", ms=4, lw=1.1, color=col,
                elinewidth=0.8, capsize=2, label=rev.upper())
a2.axhline(0, color="0.3", lw=0.9)
a2.set_xlabel("total mass flow   [g/s]")
a2.set_ylabel("change in plate spread   [%]")
a2.set_title("flow dependence (independent samples)")
FS.legend(a2)


fig.suptitle("GRAIL campaign, Rev 1 (Nu = 3.4282) against Rev 2 (grid-extrapolated "
             "Nu = 2.9238) \u2014 %d paired cases" % len(common))

fig.savefig(FIG + "/R1_rev1_vs_rev2.png", dpi=165, bbox_inches="tight")
plt.close(fig)

# ---------------------------------------------------------------- console
print("nu %.4f -> %.4f  (%+.2f %%),  %d paired cases  (%d co, %d alt)"
      % (NU_OLD, NU_NEW, res["nu_shift_pct"], len(common), len(co_ids), len(al_ids)))
print("\npaired shift, Rev 1 -> Rev 2 (same case, only Nu changed)")
print("  %-26s %14s %14s" % ("quantity", "co-current", "alternating"))
for k, label, unit in QTY:
    p = paired[k]
    print("  %-26s %+9.4f %-4s %+9.4f %-4s"
          % (label, p["co"]["paired_shift_mean"], unit,
             p["alt"]["paired_shift_mean"], unit))
print("\ncampaign average, alternating minus co-current")
print("  %-26s %18s %18s %10s" % ("quantity", "Rev 1", "Rev 2", "shift"))
for k, label, unit in QTY:
    a = arr[k]
    print("  %-26s %+8.3f +/- %-5.3f %% %+8.3f +/- %-5.3f %% %+8.3f pp%s"
          % (label, a["rev1"]["difference_pct"], 2 * a["rev1"]["se_of_difference_pct"],
             a["rev2"]["difference_pct"], 2 * a["rev2"]["se_of_difference_pct"],
             a["shift_pct_points"],
             "" if a["rev2"]["distinguishable_at_k2"] else "   NOT distinguishable at k=2"))
print("\nlateral bridge, watts (never a ratio - co-current is zero by symmetry)")
for tag in ("co", "alt"):
    print("  %-12s Rev 1 %+8.4f W   Rev 2 %+8.4f W   max|.| %8.4f W"
          % (tag, bl[tag]["rev1_mean_W"], bl[tag]["rev2_mean_W"], bl[tag]["rev2_max_abs_W"]))
print("\nevery flow bin favours alternating:  Rev 1 %s   Rev 2 %s"
      % (prof["rev1_all_bins_favour_alternating"], prof["rev2_all_bins_favour_alternating"]))
if recovered:
    print("\ncensoring in Rev 1")
    print("  %d rows recovered in Rev 2, all alternating: %s"
          % (cen["n_recovered"], cen["all_recovered_are_alternating"]))
    print("  their mass flow  %.2f g/s mean, %.2f g/s at most, against %.2f g/s campaign mean"
          % (cen["recovered_mdot_mean_g_s"], cen["recovered_mdot_max_g_s"],
             cen["alternating_mdot_mean_g_s"]))
    print("  their plate spread %.2f K mean against %.2f K for alternating overall"
          % (cen["recovered_plate_std_mean_K"], cen["alternating_plate_std_mean_K"]))
    print("  d_plate_std   Rev 1 (291) %+7.2f %% -> Rev 2 (291) %+7.2f %% -> Rev 2 (all %d) "
          "%+7.2f +/- %.2f %%"
          % (cen["censored_291_rev1_d_plate_std_pct"],
             cen["censored_291_rev2_d_plate_std_pct"],
             cen["uncensored_rev2"]["n_co"] + cen["uncensored_rev2"]["n_alt"],
             cen["uncensored_rev2"]["d_plate_std_pct"],
             2 * cen["uncensored_rev2"]["se_pct"]))
print("\nwrote %s and R1_rev1_vs_rev2.png" % OUT)
