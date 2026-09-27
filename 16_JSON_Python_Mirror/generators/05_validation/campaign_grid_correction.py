"""
GRAIL — how much does the campaign grid inflate the uniformity result?

The design-point grid study showed that the alternating-minus-co-current plate-temperature
spread SHRINKS with refinement: -13.80 % on the campaign grid (110 x 120), -11.52 % on the
finest grid tested (311 x 339). The whole 291-case campaign was run on the campaign grid, so
every uniformity number in the dataset carries that inflation.

This re-runs a spread of campaign operating points at three grid levels and measures the
correction directly, rather than assuming the design-point factor transfers. Points are drawn
from the accepted dataset itself, stratified by mass flow, because mass flow is what the
campaign showed drives the effect.

Writes 05_validation/grid_correction.json
"""
import sys, os, csv, json, time
import numpy as np

sys.path.insert(0, "/home/claude/grail_cfd/tools")
from grail_cht import Geometry, Materials, Operating, GrailCHT

OUT = "/home/claude/grail_cfd/05_validation"
CSV = "/home/claude/grail_cfd/10_dataset/GRAIL_CFD_dataset_corrected.csv"
LEVELS = [(110, 120), (156, 170), (220, 240)]
NPOINT = 10
SEED = 20260916


def pick():
    """Stratify the accepted co-current cases by mass flow and take one per stratum."""
    rows = [r for r in csv.DictReader(open(CSV)) if r["arrangement"] == "parallel"]
    for r in rows:
        for src, dst in (("mdot_total_kg_s", "mdot_total"), ("G_T_W_m2", "G_T"),
                         ("T_in_K", "T_in"), ("T_amb_K", "T_amb"),
                         ("v_wind_m_s", "v_wind"), ("bridge_mm", "bridge_mm"),
                         ("g_ratio", "g_ratio"), ("lambda_G", "lambda_G")):
            r[dst] = float(r[src])
    rows.sort(key=lambda r: r["mdot_total"])
    rng = np.random.default_rng(SEED)
    out, n = [], len(rows)
    for s in range(NPOINT):
        lo, hi = s * n // NPOINT, (s + 1) * n // NPOINT
        out.append(rows[lo + int(rng.integers(0, max(hi - lo, 1)))])
    return out


def run(p, nx, ny, f):
    geo = Geometry(g_ratio=p["g_ratio"], lam_g=p["lambda_G"], bridge=p["bridge_mm"] / 1000.0)
    op = Operating(G_T=p["G_T"], T_in=p["T_in"], T_amb=p["T_amb"], v_wind=p["v_wind"],
                   mdot_total=p["mdot_total"], f_interdig=f)
    s = GrailCHT(geo, Materials(), op, nx=nx, ny=ny)
    return s.solve(max_outer=1500, tol=1e-7)


if __name__ == "__main__":
    pts = pick()
    t0 = time.time()
    res = []
    for i, p in enumerate(pts):
        rec = {"case_id": p["case_id"], "mdot_total": p["mdot_total"], "G_T": p["G_T"],
               "v_wind": p["v_wind"], "bridge_mm": p["bridge_mm"], "levels": {}}
        for nx, ny in LEVELS:
            rc = run(p, nx, ny, 0)
            ra = run(p, nx, ny, 1)
            d_std = 100.0 * (ra["Tp_std"] - rc["Tp_std"]) / rc["Tp_std"]
            d_eta = 100.0 * (ra["eta"] - rc["eta"]) / rc["eta"]
            rec["levels"]["%dx%d" % (nx, ny)] = {
                "h_mm": 1000.0 * np.sqrt((Geometry.L * Geometry.W) / (nx * ny)),
                "co_Tp_std": rc["Tp_std"], "alt_Tp_std": ra["Tp_std"],
                "d_Tp_std_pct": d_std, "d_eta_pct": d_eta,
                "co_eta": rc["eta"], "alt_eta": ra["eta"],
                "converged": bool(rc["converged"] and ra["converged"]),
                "max_energy_error_pct": max(abs(rc["energy_error_pct"]),
                                            abs(ra["energy_error_pct"]))}
        k1, k3 = "%dx%d" % LEVELS[0], "%dx%d" % LEVELS[2]
        rec["ratio_L3_over_L1"] = (rec["levels"][k3]["d_Tp_std_pct"]
                                   / rec["levels"][k1]["d_Tp_std_pct"])
        res.append(rec)
        print("  %-8s mdot %.5f  d_std %7.3f -> %7.3f -> %7.3f %%   ratio %.4f   (%.0f s)"
              % (p["case_id"], p["mdot_total"],
                 rec["levels"]["%dx%d" % LEVELS[0]]["d_Tp_std_pct"],
                 rec["levels"]["%dx%d" % LEVELS[1]]["d_Tp_std_pct"],
                 rec["levels"]["%dx%d" % LEVELS[2]]["d_Tp_std_pct"],
                 rec["ratio_L3_over_L1"], time.time() - t0), flush=True)

    rat = np.array([r["ratio_L3_over_L1"] for r in res])
    summary = {"n_points": len(res), "levels": LEVELS, "seed": SEED,
               "correction_factor_L1_to_L3": {
                   "mean": float(rat.mean()), "sd": float(rat.std(ddof=1)),
                   "min": float(rat.min()), "max": float(rat.max()),
                   "meaning": "multiply a campaign-grid d_Tp_std_pct by this to reach the "
                              "220x240 value; < 1 means the campaign grid overstates the effect"},
               "points": res}
    json.dump(summary, open(os.path.join(OUT, "grid_correction.json"), "w"), indent=1)
    print("\ncorrection factor campaign grid -> 220x240 : %.4f +/- %.4f  (range %.4f - %.4f)"
          % (rat.mean(), rat.std(ddof=1), rat.min(), rat.max()))
    print("total %.0f s" % (time.time() - t0))
