"""
Rev 4 post-processing. Nothing here changes a solved row.

1. Builds the Richardson dataset: for every case present at BOTH plate grids (110, 220), each
   continuous output q gets q_rich = 2 q(220) - q(110)  (observed axial order p = 1.01, ratio 2;
   benchmark_record.md). Raw 110 and 220 values stay in their own files.
2. Paired arrangement comparison (ALT_nnn vs PAR_nnn share one Latin-Hypercube sample) for
   Rev 3, Rev 4-110, Rev 4-220, Rev 4-Richardson; with and without pairs where either row needed
   more than 900 outer iterations (Rev 3's cap).
"""
import csv, json, sys
import numpy as np

D = "/home/claude/grail_cfd/10_dataset/"
R3 = D + "GRAIL_CFD_dataset_rev3.csv"
R110 = D + "GRAIL_CFD_dataset_rev4_nx110.csv"
R220 = D + "GRAIL_CFD_dataset_rev4_nx220.csv"
RR = D + "GRAIL_CFD_dataset_rev4_richardson.csv"
OUT = D + "rev3_vs_rev4.json"

RICH = ["T_out_K", "dT_fluid_K", "Qu_W", "eta", "T_plate_mean_K", "T_plate_max_K", "T_plate_min_K",
        "plate_spread_K", "plate_std_K", "P90_K", "P95_K", "P99_K", "Q_rad_W", "Q_conv_W",
        "Q_rear_W", "U_L_W_m2K", "T_glass_mean_K", "lateral_bridge_W"]
METRICS = [("eta", "rel"), ("plate_std_K", "rel"), ("plate_spread_K", "rel"),
           ("T_plate_mean_K", "abs"), ("P90_K", "abs"), ("T_plate_max_K", "abs")]


def load(p):
    return {r["case_id"]: r for r in csv.DictReader(open(p))}


def richardson(a, b):
    rows = []
    for cid in sorted(set(a) & set(b)):
        r = dict(b[cid])
        for k in RICH:
            r[k] = repr(2 * float(b[cid][k]) - float(a[cid][k]))
        r["plate_nx"] = "richardson_2x220_minus_110"
        r["outer_iters"] = str(max(int(float(a[cid]["outer_iters"])), int(float(b[cid]["outer_iters"]))))
        rows.append(r)
    with open(RR, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
    return {r["case_id"]: r for r in rows}


def paired(rows, cap=None):
    out = {m: [] for m, _ in METRICS}; n = 0; skipped = 0
    for cid, r in rows.items():
        if not cid.startswith("ALT_"):
            continue
        p = rows.get("PAR_" + cid[4:])
        if p is None:
            continue
        if cap and (float(r["outer_iters"]) > cap or float(p["outer_iters"]) > cap):
            skipped += 1; continue
        n += 1
        for m, kind in METRICS:
            a, c = float(r[m]), float(p[m])
            out[m].append(100 * (a / c - 1) if kind == "rel" else a - c)
    res = {"n_pairs": n, "skipped_over_cap": skipped}
    for m, kind in METRICS:
        v = np.array(out[m])
        res[m] = {"unit": "%" if kind == "rel" else "K", "mean": float(v.mean()), "median": float(np.median(v)),
                  "p5": float(np.percentile(v, 5)), "p95": float(np.percentile(v, 95)),
                  "frac_alt_lower": float((v < 0).mean())}
    return res


if __name__ == "__main__":
    sets = {"rev3_nx110_nu2.9238": load(R3)}
    a, b = load(R110), load(R220)
    sets["rev4_nx110_nu4.48"] = a
    sets["rev4_nx220_nu4.48"] = b
    sets["rev4_richardson"] = richardson(a, b)
    res = {k: {"all": paired(v), "le900": paired(v, 900)} for k, v in sets.items()}
    json.dump(res, open(OUT, "w"), indent=1)
    for k, v in res.items():
        for s in ("all", "le900"):
            x = v[s]
            print("%-22s %-5s n=%3d  d_eta %+6.2f%%  d_std %+6.2f%%  d_spread %+6.2f%%  d_mean %+5.2f K  d_P90 %+5.2f K  alt-lower-std %.0f%%"
                  % (k, s, x["n_pairs"], x["eta"]["mean"], x["plate_std_K"]["mean"], x["plate_spread_K"]["mean"],
                     x["T_plate_mean_K"]["mean"], x["P90_K"]["mean"], 100 * x["plate_std_K"]["frac_alt_lower"]))
