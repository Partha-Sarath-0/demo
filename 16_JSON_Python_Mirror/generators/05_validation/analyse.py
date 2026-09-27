"""
GRAIL — combine the grid, input-uncertainty and correction studies into one statement of
total uncertainty on each reported quantity, and restate the campaign numbers on a converged
grid.

Total standard uncertainty is combined in quadrature from three independent contributions:
  u_num    discretisation, taken as GCI/1.25 (removing Roache's 1.25 safety factor converts a
           95 %-coverage band back to a standard uncertainty, per ASME V&V 20 practice)
  u_in     property and boundary-condition uncertainty, from the paired Monte Carlo
  u_iter   iterative convergence, from the solver's own residual floor
Round-off is not carried: the solver runs in float64 and the energy balance closes to 1e-7 %.

Writes 05_validation/uncertainty_summary.json
"""
import os, json, csv
import numpy as np

V = "/home/claude/grail_cfd/05_validation"
DATA = os.environ.get('GRAIL_DATASET', '/home/claude/grail_cfd/10_dataset/GRAIL_CFD_dataset_corrected.csv')


def load(n):
    p = os.path.join(V, n)
    return json.load(open(p)) if os.path.exists(p) else None


G, M, C = load("gci_plate.json"), load("mc_summary.json"), load("grid_correction.json")
out = {"method": "ASME V&V 20-2009 / Roache GCI, combined in quadrature with a paired "
                 "Monte Carlo over input uncertainty"}

# ------------------------------------------------------------------ 1. numerical
num = {}
if G:
    fine = "%dx%d" % (G["levels"][-1]["nx"], G["levels"][-1]["ny"])
    for q in ("Tp_std", "eta", "U_L", "dTp", "R4"):
        k = "d_%s_pct" % q
        a = G["gci_difference"]["L4L3L2"][k]
        b = G["gci_difference"]["L3L2L1"][k]
        vals = a["values_fine_to_coarse"]
        # the two triplets disagree on the observed order when a quantity is not yet in the
        # asymptotic range; take the larger GCI and say so rather than picking the flattering one
        gci = max(a["gci_pct"], b["gci_pct"])
        num[k] = {
            "finest_grid_value_pct": vals[0],
            "campaign_grid_value_pct": b["values_fine_to_coarse"][-1],
            "observed_order_fine_triplet": a["p"], "observed_order_coarse_triplet": b["p"],
            "richardson_fine_triplet": a["f_extrap"], "richardson_coarse_triplet": b["f_extrap"],
            "gci_pct_of_value": gci,
            "u_num_pct_points": abs(vals[0]) * gci / 100.0 / 1.25,
            "asymptotic": bool(a["p"] and b["p"] and abs(a["p"] - b["p"]) < 0.5)}
    for tag in ("co", "alt"):
        for q in ("eta", "Tp_std", "Tp_mean", "U_L"):
            g = G["gci"]["L4L3L2"][tag][q]
            num["%s_%s" % (tag, q)] = {
                "finest_grid_value": G["raw"][tag][fine][q],
                "gci_pct": g["gci_pct"], "observed_order": g["p"],
                "u_num_rel_pct": g["gci_pct"] / 1.25}
out["numerical"] = num

# ------------------------------------------------------------------ 2. input
inp = {}
if M:
    for k, s in M["difference"].items():
        inp[k] = {"mean_pct": s["mean"], "u_in_pct_points": s["sd"],
                  "ci95": [s["p2_5"], s["p97_5"]],
                  "unpaired_would_be": s["unpaired_sd_would_be_pct"],
                  "pairing_gain": s["unpaired_sd_would_be_pct"] / s["sd"] if s["sd"] else None}
    for k, s in M["qoi"].items():
        inp[k] = {"mean": s["mean"], "u_in_rel_pct": s["rel_sd_pct"], "ci95": [s["p2_5"], s["p97_5"]]}
out["input"] = inp

# ------------------------------------------------------------------ 3. iterative
out["iterative"] = {
    "conjugate_solver": {"tolerance": 1e-8, "energy_balance_error_pct_max": 5.6e-7,
                         "note": "outer-loop residual driven to 1e-8; the energy balance, an "
                                 "independent check, closes to under 1e-6 %. Iterative "
                                 "uncertainty is at least three orders below the other two "
                                 "terms and is not carried."},
    "openfoam_baseline": {"Ux": 5.3461e-11, "p": 1.5287e-08, "continuity": 2.4805e-10,
                          "iterations": 518}}

# ------------------------------------------------------------------ 4. combined
comb = {}
for q in ("Tp_std", "eta", "U_L", "dTp"):
    k = "d_%s_pct" % q
    if k in num and k in inp:
        un, ui = num[k]["u_num_pct_points"], inp[k]["u_in_pct_points"]
        val = num[k]["finest_grid_value_pct"]
        u = float(np.hypot(un, ui))
        comb[k] = {"value_on_finest_grid_pct": val,
                   "u_numerical_pct_points": un, "u_input_pct_points": ui,
                   "u_combined_pct_points": u, "expanded_k2_pct_points": 2 * u,
                   "statement": "%+.2f %% +/- %.2f (k = 2)" % (val, 2 * u),
                   "excludes_zero_at_k2": bool(abs(val) > 2 * u),
                   "dominant_term": "numerical" if un > ui else "input"}
out["combined"] = comb

# ------------------------------------------------------------------ 5. campaign restatement
if C:
    pts = C["points"]
    k1 = "%dx%d" % tuple(C["levels"][0])
    k3 = "%dx%d" % tuple(C["levels"][2])
    d1 = np.array([p["levels"][k1]["d_Tp_std_pct"] for p in pts])
    d3 = np.array([p["levels"][k3]["d_Tp_std_pct"] for p in pts])
    md = np.array([p["mdot_total"] for p in pts])
    shift = d3 - d1
    A = np.column_stack([np.ones(len(d1)), d1])
    beta, *_ = np.linalg.lstsq(A, d3, rcond=None)
    pred = A @ beta
    r2 = 1 - ((d3 - pred) ** 2).sum() / ((d3 - d3.mean()) ** 2).sum()

    rows = list(csv.DictReader(open(DATA)))
    co = np.array([float(r["plate_std_K"]) for r in rows if r["arrangement"] == "parallel"])
    al = np.array([float(r["plate_std_K"]) for r in rows if r["arrangement"] == "alternating"])
    camp = 100.0 * (al.mean() - co.mean()) / co.mean()

    # sign change: where does the benefit actually begin?
    order = np.argsort(md)
    cross = None
    for i in range(len(order) - 1):
        a, b = order[i], order[i + 1]
        if np.sign(d3[a]) != np.sign(d3[b]):
            t = d3[a] / (d3[a] - d3[b])
            cross = float(md[a] + t * (md[b] - md[a]))
            break

    out["campaign_restatement"] = {
        "n_points": len(pts),
        "additive_shift_pct_points": {"mean": float(shift.mean()), "sd": float(shift.std(ddof=1)),
                                      "min": float(shift.min()), "max": float(shift.max())},
        "linear_map_d3_from_d1": {"intercept": float(beta[0]), "slope": float(beta[1]),
                                  "R2": float(r2)},
        "campaign_grid_average_pct": float(camp),
        "restated_on_220x240_pct": float(beta[0] + beta[1] * camp),
        "restated_simple_shift_pct": float(camp + shift.mean()),
        "benefit_threshold_mdot_kg_s": cross,
        "note": "the correction is additive, roughly +2 percentage points, not a scale factor; "
                "it must not be applied as a ratio because d_Tp_std changes sign across the "
                "mass-flow range"}

json.dump(out, open(os.path.join(V, "uncertainty_summary.json"), "w"), indent=1)

print("=== COMBINED UNCERTAINTY, finest grid, k = 2 ===")
for k, c in comb.items():
    print("  %-14s %s   [num %.3f | input %.3f pp]   %s"
          % (k, c["statement"], c["u_numerical_pct_points"], c["u_input_pct_points"],
             "distinguishable from zero" if c["excludes_zero_at_k2"] else "NOT distinguishable from zero"))
if C:
    r = out["campaign_restatement"]
    print("\n=== CAMPAIGN RESTATEMENT ===")
    print("  additive shift 110x120 -> 220x240 : %+.3f +/- %.3f pp  (range %+.2f .. %+.2f)"
          % (r["additive_shift_pct_points"]["mean"], r["additive_shift_pct_points"]["sd"],
             r["additive_shift_pct_points"]["min"], r["additive_shift_pct_points"]["max"]))
    print("  campaign average as published      : %+.2f %%" % r["campaign_grid_average_pct"])
    print("  restated on 220x240                : %+.2f %% (linear map, R2 %.4f)"
          % (r["restated_on_220x240_pct"], r["linear_map_d3_from_d1"]["R2"]))
    print("  uniformity benefit begins above    : %s"
          % ("%.5f kg/s" % r["benefit_threshold_mdot_kg_s"] if r["benefit_threshold_mdot_kg_s"]
             else "not bracketed by these points"))
print("\nwrote uncertainty_summary.json")
