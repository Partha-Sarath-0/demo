"""
GRAIL — input uncertainty propagation, paired Monte Carlo.

Every draw is run through BOTH arrangements with identical inputs. That pairing is the point:
the uniformity claim is a difference, and a difference between two runs that share the same
property draw, the same grid and the same solver has most of its systematic error cancelled.
Reporting the difference's own spread is therefore correct, and reporting it as the quadrature
sum of the two separate spreads would badly overstate it. Both are computed here so the
difference is visible.

Input uncertainties: every entry below is an ENGINEERING_ASSUMPTION unless the basis column
names a roadmap source. The roadmap's own material table (14_provenance/material_database.md)
gives handbook values for the material class with no tolerances, and its verification item V6
requires confirmation against supplier datasheets before final runs. Until that is done, these
standard uncertainties are assumed, they are stated here rather than buried, and the sensitivity
ranking shows exactly which of them the result actually depends on.

Usage:  python3 mc_uncertainty.py [n_pairs] [n_workers]
Writes 05_validation/mc_samples.csv and mc_summary.json
"""
import sys, os, csv, json, time
import numpy as np
from multiprocessing import Pool

sys.path.insert(0, "/home/claude/grail_cfd/tools")
from grail_cht import Geometry, Materials, Operating, GrailCHT
from campaign import lateral_bridge

OUT = "/home/claude/grail_cfd/05_validation"
NX, NY = 110, 120                 # the campaign grid, so this band applies to the campaign
SEED = 20260916
TOL = 1e-6

# name -> (nominal, standard uncertainty, kind, basis)
INPUTS = {
    "k_al":        (229.0,   0.02, "rel",  "AA1050 handbook value; temper/purity spread"),
    "nu_cfd":      (3.428,   0.05, "rel",  "extracted from this study's own 3-D CFD"),
    "alpha_abs":   (0.95,    0.010, "abs", "TiNOX datasheet tolerance"),
    "eps_abs":     (0.04,    0.010, "abs", "TiNOX datasheet tolerance"),
    "tau_glz_sys": (0.833,   0.010, "abs", "two-pane system, roadmap correction C11"),
    "tau_tim":     (0.82,    0.020, "abs", "homogenised PC honeycomb"),
    "k_tim":       (0.075,   0.05, "rel",  "handbook, perpendicular direction"),
    "k_vip":       (0.006,   0.13, "rel",  "fumed-silica VIP, 20 % service derate over 25 y"),
    "h_wind_fac":  (1.0,     0.15, "rel",  "scatter of the linear wind-convection correlation"),
    "h_rear":      (3.0,     0.5,  "abs",  "still-air external coefficient"),
    "mdot_total":  (0.0025,  0.02, "rel",  "pump and flowmeter class"),
    "G_T":         (800.0,   0.02, "rel",  "class-A pyranometer"),
    "T_amb":       (298.15,  0.5,  "abs",  "ambient measurement"),
}
QOI = ("eta", "T_out", "dT", "Tp_mean", "Tp_std", "dTp", "U_L", "R4", "Q_rad",
       "lateral_bridge_W")


def draw(n, rng):
    S = {}
    for k, (nom, u, kind, _) in INPUTS.items():
        z = rng.standard_normal(n)
        S[k] = nom * (1.0 + u * z) if kind == "rel" else nom + u * z
    S["eps_abs"] = np.clip(S["eps_abs"], 0.005, 0.95)
    S["alpha_abs"] = np.clip(S["alpha_abs"], 0.5, 0.999)
    S["tau_glz_sys"] = np.clip(S["tau_glz_sys"], 0.3, 0.999)
    S["tau_tim"] = np.clip(S["tau_tim"], 0.3, 0.999)
    S["h_rear"] = np.clip(S["h_rear"], 0.3, None)
    S["k_vip"] = np.clip(S["k_vip"], 1e-4, None)
    return S


def one(args):
    i, p = args
    out = {"sample": i}
    for f, tag in ((0, "co"), (1, "alt")):
        class M(Materials):
            k_al = p["k_al"]; alpha_abs = p["alpha_abs"]; eps_abs = p["eps_abs"]
            tau_glz_sys = p["tau_glz_sys"]; tau_tim = p["tau_tim"]
            k_tim = p["k_tim"]; k_vip = p["k_vip"]; h_rear = p["h_rear"]

        class O(Operating):
            @property
            def h_wind(self):
                return (5.7 + 3.8 * self.v_wind) * p["h_wind_fac"]

        op = O(G_T=p["G_T"], T_amb=p["T_amb"], mdot_total=p["mdot_total"], f_interdig=f)
        s = GrailCHT(Geometry(), M(), op, nx=NX, ny=NY, nu_cfd=p["nu_cfd"])
        r = s.solve(max_outer=1200, tol=TOL)
        if not r["converged"] or abs(r["energy_error_pct"]) > 0.5:
            return {"sample": i, "reject": "not_converged" if not r["converged"]
                    else "energy_error_%.4f" % r["energy_error_pct"], **p}
        r["lateral_bridge_W"] = lateral_bridge(s)
        for q in QOI:
            out["%s_%s" % (tag, q)] = float(r[q])
    for q in ("eta", "Tp_std", "U_L", "dTp", "R4"):
        a, c = out["alt_%s" % q], out["co_%s" % q]
        out["d_%s_pct" % q] = 100.0 * (a - c) / c
    out.update({k: float(v) for k, v in p.items()})
    return out


def main(npair, nw):
    rng = np.random.default_rng(SEED)
    S = draw(npair, rng)
    jobs = [(i, {k: float(S[k][i]) for k in INPUTS}) for i in range(npair)]
    t0 = time.time()
    rows, rejects = [], []
    with Pool(nw) as pool:
        for n, r in enumerate(pool.imap_unordered(one, jobs, chunksize=1), 1):
            (rejects if "reject" in r else rows).append(r)
            if n % 10 == 0 or n == npair:
                print("  %4d / %d   accepted %d   rejected %d   (%.0f s)"
                      % (n, npair, len(rows), len(rejects), time.time() - t0), flush=True)
    rows.sort(key=lambda r: r["sample"])

    cols = sorted(rows[0].keys())
    with open(os.path.join(OUT, "mc_samples.csv"), "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=cols); w.writeheader(); w.writerows(rows)

    def stat(key):
        v = np.array([r[key] for r in rows], float)
        return dict(mean=float(v.mean()), sd=float(v.std(ddof=1)),
                    rel_sd_pct=float(100 * v.std(ddof=1) / abs(v.mean())) if v.mean() else None,
                    p2_5=float(np.percentile(v, 2.5)), p97_5=float(np.percentile(v, 97.5)),
                    n=len(v))

    summary = {"n_pairs": npair, "n_accepted": len(rows), "n_rejected": len(rejects),
               "grid": [NX, NY], "seed": SEED, "tol": TOL,
               "inputs": {k: {"nominal": v[0], "u": v[1], "kind": v[2], "basis": v[3],
                              "class": "ENGINEERING_ASSUMPTION"} for k, v in INPUTS.items()},
               "qoi": {}, "difference": {}, "sensitivity": {}}
    for tag in ("co", "alt"):
        for q in QOI:
            summary["qoi"]["%s_%s" % (tag, q)] = stat("%s_%s" % (tag, q))
    for q in ("eta", "Tp_std", "U_L", "dTp", "R4"):
        summary["difference"]["d_%s_pct" % q] = stat("d_%s_pct" % q)
        # what the band would look like if the pairing were ignored
        a = np.array([r["alt_%s" % q] for r in rows]); c = np.array([r["co_%s" % q] for r in rows])
        naive = 100 * np.sqrt((a.std(ddof=1) / a.mean()) ** 2 + (c.std(ddof=1) / c.mean()) ** 2)
        summary["difference"]["d_%s_pct" % q]["unpaired_sd_would_be_pct"] = float(naive)

    # standardised regression coefficients: which inputs drive each output
    X = np.column_stack([[r[k] for r in rows] for k in INPUTS])
    Xs = (X - X.mean(0)) / X.std(0, ddof=1)
    A = np.column_stack([np.ones(len(Xs)), Xs])
    for q in ["co_eta", "alt_eta", "d_Tp_std_pct", "d_eta_pct", "alt_Tp_std", "co_Tp_std"]:
        y = np.array([r[q] for r in rows], float)
        ys = (y - y.mean()) / y.std(ddof=1)
        beta, *_ = np.linalg.lstsq(A, ys, rcond=None)
        pred = A @ beta
        r2 = 1.0 - ((ys - pred) ** 2).sum() / ((ys - ys.mean()) ** 2).sum()
        src = {k: float(b) for k, b in zip(INPUTS, beta[1:])}
        summary["sensitivity"][q] = {
            "R2_of_linear_model": float(r2),
            "src": src,
            "variance_share_pct": {k: float(100 * b * b / sum(v * v for v in src.values()))
                                   for k, b in src.items()},
            "ranked": sorted(src, key=lambda k: -abs(src[k]))}
    summary["rejected"] = rejects
    json.dump(summary, open(os.path.join(OUT, "mc_summary.json"), "w"), indent=1)

    print("\naccepted %d of %d   (%.0f s)" % (len(rows), npair, time.time() - t0))
    for q in ("eta", "Tp_std"):
        for tag in ("co", "alt"):
            s_ = summary["qoi"]["%s_%s" % (tag, q)]
            print("  %-4s %-8s %.6g  +/- %.4g  (%.3f %%)" % (tag, q, s_["mean"], s_["sd"],
                                                             s_["rel_sd_pct"]))
    print("\n  the claim quantities:")
    for q in ("Tp_std", "eta", "U_L", "dTp"):
        s_ = summary["difference"]["d_%s_pct" % q]
        print("    d_%-8s %+8.4f %%  sd %.4f  95%% CI [%+.4f, %+.4f]   (unpaired would read %.3f)"
              % (q, s_["mean"], s_["sd"], s_["p2_5"], s_["p97_5"],
                 s_["unpaired_sd_would_be_pct"]))
    print("\n  drivers of d_Tp_std_pct (R2 %.4f):" % summary["sensitivity"]["d_Tp_std_pct"]["R2_of_linear_model"])
    for k in summary["sensitivity"]["d_Tp_std_pct"]["ranked"][:6]:
        print("    %-12s SRC %+.4f   variance share %5.1f %%"
              % (k, summary["sensitivity"]["d_Tp_std_pct"]["src"][k],
                 summary["sensitivity"]["d_Tp_std_pct"]["variance_share_pct"][k]))


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 200,
         int(sys.argv[2]) if len(sys.argv) > 2 else 2)
