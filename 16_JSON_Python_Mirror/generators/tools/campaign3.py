"""
GRAIL CFD production campaign, Rev 3 — recomputed with temperature-dependent thermal
conductivity of water.

The audit of Rev 2 (`14_provenance/dataset_audit_record.md`) found a property-model
inconsistency: viscosity was carried as mu(T) through the Vogel relation and varies by a
factor of 2.84 across the campaign, while thermal conductivity was held fixed at
0.610 W/m.K — the value at 26.6 C. Because the heat-transfer closure is

    h(x) = Nu * k / Dh(x)

an error in k is mathematically identical to the same percentage error in Nu, and Nu is the
single input the sensitivity analysis found controls 91 % of the uniformity difference.

Measured on the Rev 2 rows, the fixed 0.610 understates k by up to +10.44 % (mean +5.02 %),
with 166 of 300 cases beyond 5 %. Scaling by the calibrated Rev 1 -> Rev 2 slope of
0.6175 pp per 1 % of Nu, the estimate was that Delta plate spread would move from
-21.09 % to about -18.0 %. This campaign replaces that estimate with a measurement.

Same seed, same Latin Hypercube, same bounds, same pre-run geometry gate, same grid, same
Nusselt closure (2.9238). ONLY k becomes k(T), evaluated at the local fluid temperature and
refreshed inside the existing outer iteration. Every Rev 3 row therefore pairs one-to-one
with its Rev 2 counterpart and the difference is attributable to nothing else.

Rev 2 is NOT deleted, exactly as Rev 1 was not deleted when Rev 2 superseded it.

Writes 10_dataset/GRAIL_CFD_dataset_rev3.csv, 11_failures/failures_rev3.csv and
10_dataset/rev2_vs_rev3.json
"""
import sys, os, csv, json, time
import numpy as np
from multiprocessing import Pool
from scipy.stats import qmc

sys.path.insert(0, "/home/claude/grail_cfd/tools")
import campaign as C
import grail_cht as G

NU = 2.9238
OUT = "/home/claude/grail_cfd/10_dataset/GRAIL_CFD_dataset_rev3.csv"
FAIL = "/home/claude/grail_cfd/11_failures/failures_rev3.csv"
REV2 = "/home/claude/grail_cfd/10_dataset/GRAIL_CFD_dataset_rev2.csv"
CMP = "/home/claude/grail_cfd/10_dataset/rev2_vs_rev3.json"


# ---------------------------------------------------------------- k(T) patch
_orig_run_case = C.run_case


def run_case_kT(cid, p, topo):
    """C.run_case with k_of_T switched on.

    run_case builds its own GrailCHT, so the flag is injected by wrapping the constructor
    for the duration of the call rather than by duplicating run_case, which would risk the
    two campaigns drifting apart in some other detail.
    """
    orig = G.GrailCHT.__init__

    def patched(self, geo, mat, op, nx=220, ny=240, nu_cfd=3.428, k_of_T=False):
        orig(self, geo, mat, op, nx=nx, ny=ny, nu_cfd=nu_cfd, k_of_T=True)

    G.GrailCHT.__init__ = patched
    try:
        return _orig_run_case(cid, p, topo)
    finally:
        G.GrailCHT.__init__ = orig


def build_jobs():
    """Exactly the Rev 1 / Rev 2 sample: same sampler, same seed, same draw order."""
    sampler = qmc.LatinHypercube(d=len(C.KEYS), seed=C.SEED)
    jobs, rejects = [], []
    for topo in (0, 1):
        sample = sampler.random(n=C.N_PER_TOPOLOGY)
        for i in range(C.N_PER_TOPOLOGY):
            p = {k: C.BOUNDS[k][0] + sample[i, j] * (C.BOUNDS[k][1] - C.BOUNDS[k][0])
                 for j, k in enumerate(C.KEYS)}
            cid = "%s_%03d" % ("ALT" if topo else "PAR", i)
            w_ch = C.Geometry.PITCH * 1000.0 - p["bridge_mm"]
            if w_ch < 3.0:
                rejects.append([cid, topo,
                                "invalid_geometry:w_ch=%.2f_mm_below_3mm_rollbond_minimum" % w_ch,
                                json.dumps(p)])
                continue
            jobs.append((cid, p, topo))
    return jobs, rejects


def one(job):
    cid, p, topo = job
    C.NU_CFD = NU                          # set inside the worker process
    try:
        row = run_case_kT(cid, p, topo)
    except Exception as e:
        return {"__fail__": [cid, topo, "exception:%s" % str(e)[:90], json.dumps(p)]}
    # Identical acceptance gates to Rev 2. Nothing is loosened to admit more rows.
    if not row["converged"]:
        return {"__fail__": [cid, topo, "not_converged", json.dumps(p)]}
    if abs(row["energy_error_pct"]) > 0.5:
        return {"__fail__": [cid, topo, "energy_error_%.4f" % row["energy_error_pct"],
                             json.dumps(p)]}
    if not (250.0 < row["T_plate_mean_K"] < 500.0):
        return {"__fail__": [cid, topo, "T_out_of_range_%.1f" % row["T_plate_mean_K"],
                             json.dumps(p)]}
    row["nu_cfd"] = NU
    row["dataset_rev"] = 3
    row["k_model"] = "k(T)_cubic_273_373K"
    return row


def main(nw=2):
    jobs, rejects = build_jobs()
    print("Rev 3 — k(T). %d cases, %d rejected by the pre-run geometry gate"
          % (len(jobs), len(rejects)), flush=True)
    t0 = time.time()
    rows, fails = [], list(rejects)
    with Pool(nw) as pool:
        for n, r in enumerate(pool.imap_unordered(one, jobs, chunksize=1), 1):
            if "__fail__" in r:
                fails.append(r["__fail__"])
            else:
                rows.append(r)
            if n % 10 == 0 or n == len(jobs):
                el = time.time() - t0
                print("  %3d / %d   accepted %d   rejected %d   (%.0f s, eta %.0f s)"
                      % (n, len(jobs), len(rows), len(fails), el, el / n * (len(jobs) - n)),
                      flush=True)
    rows.sort(key=lambda r: r["case_id"])

    with open(OUT, "w", newline="") as fo:
        w = csv.DictWriter(fo, fieldnames=list(rows[0].keys()))
        w.writeheader(); w.writerows(rows)
    with open(FAIL, "w", newline="") as ff:
        fw = csv.writer(ff); fw.writerow(["case_id", "topology", "reason", "params"])
        fw.writerows(fails)
    print("\nwrote %s : %d rows, %d rejected  (%.0f s)"
          % (OUT, len(rows), len(fails), time.time() - t0), flush=True)

    # ---------------------------------------------------------------- Rev 2 vs Rev 3
    old = {r["case_id"]: r for r in csv.DictReader(open(REV2))}
    new = {r["case_id"]: r for r in rows}
    common = sorted(set(old) & set(new))
    g = lambda d, k, ids: np.array([float(d[i][k]) for i in ids])
    co = [i for i in common if i.startswith("PAR")]
    al = [i for i in common if i.startswith("ALT")]

    cmp = {"n_common": len(common), "n_co": len(co), "n_alt": len(al),
           "nu": NU, "change": "k fixed 0.610 -> k(T) cubic, 273-373 K",
           "quantities": {}, "paired": {}}

    for k in ("eta", "plate_std_K", "U_L_W_m2K", "T_out_K", "plate_spread_K",
              "lateral_bridge_W", "T_plate_mean_K"):
        o_co, n_co = g(old, k, co), g(new, k, co)
        o_al, n_al = g(old, k, al), g(new, k, al)
        d_old = 100 * (o_al.mean() - o_co.mean()) / o_co.mean()
        d_new = 100 * (n_al.mean() - n_co.mean()) / n_co.mean()
        cmp["quantities"][k] = {
            "co_rev2": float(o_co.mean()), "co_rev3": float(n_co.mean()),
            "alt_rev2": float(o_al.mean()), "alt_rev3": float(n_al.mean()),
            "campaign_difference_rev2_pct": float(d_old),
            "campaign_difference_rev3_pct": float(d_new),
            "shift_pct_points": float(d_new - d_old)}
        # paired, case by case — the clean measurement of what k(T) did
        cmp["paired"][k] = {
            "co_current_mean_change": float((n_co - o_co).mean()),
            "alternating_mean_change": float((n_al - o_al).mean())}

    # U_L on the conditioned subset, per the audit
    for tag, ids in (("co", co), ("alt", al)):
        dT = g(new, "T_plate_mean_K", ids) - g(new, "T_amb_K", ids)
        ul = g(new, "U_L_W_m2K", ids)
        m = np.abs(dT) >= 5.0
        cmp.setdefault("U_L_conditioned_5K", {})[tag] = {
            "n": int(m.sum()), "mean": float(ul[m].mean()), "sd": float(ul[m].std(ddof=1))}
    c5 = cmp["U_L_conditioned_5K"]
    se = np.sqrt(c5["co"]["sd"] ** 2 / c5["co"]["n"] + c5["alt"]["sd"] ** 2 / c5["alt"]["n"])
    c5["difference_pct"] = float(100 * (c5["alt"]["mean"] - c5["co"]["mean"]) / c5["co"]["mean"])
    c5["expanded_k2_pp"] = float(200 * se / c5["co"]["mean"])

    json.dump(cmp, open(CMP, "w"), indent=2)
    print("wrote %s" % CMP)
    q = cmp["quantities"]
    print("\n%-20s %14s %14s %12s" % ("quantity", "Rev 2 diff", "Rev 3 diff", "shift"))
    for k, v in q.items():
        print("  %-18s %+13.3f %% %+13.3f %% %+11.3f pp"
              % (k, v["campaign_difference_rev2_pct"], v["campaign_difference_rev3_pct"],
                 v["shift_pct_points"]))
    print("\nU_L, |Tp - Tamb| >= 5 K :  %+.2f %% +/- %.2f pp (k = 2), n = %d + %d"
          % (c5["difference_pct"], c5["expanded_k2_pp"], c5["co"]["n"], c5["alt"]["n"]))


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 2)
