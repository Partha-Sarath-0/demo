"""
GRAIL CFD production campaign, Rev 2 — recomputed at the grid-converged Nusselt number.

Rev 1 (`10_dataset/GRAIL_CFD_dataset_corrected.csv`) was run with nu_cfd = 3.4282, the value
measured on the medium 3-D grid. The three-level grid study (observed order p = 1.283, GCI
11.6 %) extrapolates to **2.9238**, so Rev 1 carries a +17.25 % bias on the single input that
the sensitivity analysis found controls 91 % of the uniformity difference.

Same seed, same Latin Hypercube, same bounds, same gates, same grid. Only nu_cfd changes, so
every row in Rev 2 pairs one-to-one with its Rev 1 counterpart and the difference is
attributable to nothing else.

Rev 1 is NOT deleted. It stays on disk as the record of what was reported before the
correction, and the comparison between the two is written to 10_dataset/rev1_vs_rev2.json.

Writes 10_dataset/GRAIL_CFD_dataset_rev2.csv and 11_failures/failures_rev2.csv
"""
import sys, os, csv, json, time
import numpy as np
from multiprocessing import Pool
from scipy.stats import qmc

sys.path.insert(0, "/home/claude/grail_cfd/tools")
import campaign as C

NU_NEW = 2.9238
NU_OLD = 3.4282
OUT = "/home/claude/grail_cfd/10_dataset/GRAIL_CFD_dataset_rev2.csv"
FAIL = "/home/claude/grail_cfd/11_failures/failures_rev2.csv"
REV1 = "/home/claude/grail_cfd/10_dataset/GRAIL_CFD_dataset_corrected.csv"


def build_jobs():
    """Exactly the Rev 1 sample: same sampler, same seed, same draw order."""
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
    C.NU_CFD = NU_NEW                     # set inside the worker process
    try:
        row = C.run_case(cid, p, topo)
    except Exception as e:
        return {"__fail__": [cid, topo, "exception:%s" % str(e)[:90], json.dumps(p)]}
    if not row["converged"]:
        return {"__fail__": [cid, topo, "not_converged", json.dumps(p)]}
    if abs(row["energy_error_pct"]) > 0.5:
        return {"__fail__": [cid, topo, "energy_error_%.4f" % row["energy_error_pct"],
                             json.dumps(p)]}
    if not (250.0 < row["T_plate_mean_K"] < 500.0):
        return {"__fail__": [cid, topo, "T_out_of_range_%.1f" % row["T_plate_mean_K"],
                             json.dumps(p)]}
    row["nu_cfd"] = NU_NEW
    row["dataset_rev"] = 2
    return row


def main(nw=2):
    jobs, rejects = build_jobs()
    print("%d cases to run, %d rejected by the pre-run geometry gate" % (len(jobs), len(rejects)),
          flush=True)
    t0 = time.time()
    rows, fails = [], list(rejects)
    with Pool(nw) as pool:
        for n, r in enumerate(pool.imap_unordered(one, jobs, chunksize=1), 1):
            if "__fail__" in r:
                fails.append(r["__fail__"])
            else:
                rows.append(r)
            if n % 25 == 0 or n == len(jobs):
                print("  %3d / %d   accepted %d   rejected %d   (%.0f s)"
                      % (n, len(jobs), len(rows), len(fails), time.time() - t0), flush=True)
    rows.sort(key=lambda r: r["case_id"])

    with open(OUT, "w", newline="") as fo:
        w = csv.DictWriter(fo, fieldnames=list(rows[0].keys()))
        w.writeheader(); w.writerows(rows)
    with open(FAIL, "w", newline="") as ff:
        fw = csv.writer(ff); fw.writerow(["case_id", "topology", "reason", "params"])
        fw.writerows(fails)
    print("\nwrote %s : %d rows, %d rejected  (%.0f s)"
          % (OUT, len(rows), len(fails), time.time() - t0))

    # ---------------------------------------------------------------- Rev 1 vs Rev 2
    old = {r["case_id"]: r for r in csv.DictReader(open(REV1))}
    new = {r["case_id"]: r for r in rows}
    common = sorted(set(old) & set(new))
    g = lambda d, k, ids: np.array([float(d[i][k]) for i in ids])

    def split(ids, arr_key):
        co = [i for i in ids if i.startswith("PAR")]
        al = [i for i in ids if i.startswith("ALT")]
        return co, al

    co, al = split(common, None)
    cmp = {"n_common": len(common), "n_co": len(co), "n_alt": len(al),
           "nu_old": NU_OLD, "nu_new": NU_NEW, "quantities": {}}
    for k in ("eta", "plate_std_K", "U_L_W_m2K", "T_out_K", "plate_spread_K",
              "lateral_bridge_W", "T_plate_mean_K"):
        o_co, n_co = g(old, k, co), g(new, k, co)
        o_al, n_al = g(old, k, al), g(new, k, al)
        d_old = 100 * (o_al.mean() - o_co.mean()) / o_co.mean()
        d_new = 100 * (n_al.mean() - n_co.mean()) / n_co.mean()
        cmp["quantities"][k] = {
            "co_rev1": float(o_co.mean()), "co_rev2": float(n_co.mean()),
            "alt_rev1": float(o_al.mean()), "alt_rev2": float(n_al.mean()),
            "campaign_difference_rev1_pct": float(d_old),
            "campaign_difference_rev2_pct": float(d_new),
            "shift_pct_points": float(d_new - d_old)}

    # where does the uniformity benefit now begin?
    md = g(new, "mdot_total_kg_s", al)
    # pair by flow: bin both arrangements and find the sign change of the binned difference
    mdo = g(new, "mdot_total_kg_s", co)
    bins = np.linspace(min(md.min(), mdo.min()), max(md.max(), mdo.max()), 9)
    sa = g(new, "plate_std_K", al); sc = g(new, "plate_std_K", co)
    prof = []
    for b in range(len(bins) - 1):
        ma = (md >= bins[b]) & (md < bins[b + 1])
        mc = (mdo >= bins[b]) & (mdo < bins[b + 1])
        if ma.sum() >= 3 and mc.sum() >= 3:
            prof.append({"mdot_mid": float(0.5 * (bins[b] + bins[b + 1])),
                         "d_plate_std_pct": float(100 * (sa[ma].mean() - sc[mc].mean())
                                                  / sc[mc].mean()),
                         "n_alt": int(ma.sum()), "n_co": int(mc.sum())})
    cmp["mdot_profile_rev2"] = prof
    thr = None
    for i in range(len(prof) - 1):
        if np.sign(prof[i]["d_plate_std_pct"]) != np.sign(prof[i + 1]["d_plate_std_pct"]):
            a_, b_ = prof[i], prof[i + 1]
            t = a_["d_plate_std_pct"] / (a_["d_plate_std_pct"] - b_["d_plate_std_pct"])
            thr = a_["mdot_mid"] + t * (b_["mdot_mid"] - a_["mdot_mid"])
            break
    cmp["benefit_threshold_mdot_kg_s"] = thr
    json.dump(cmp, open("/home/claude/grail_cfd/10_dataset/rev1_vs_rev2.json", "w"), indent=1)

    print("\n=== campaign-average difference, alternating vs co-current ===")
    print("  %-18s %12s %12s %10s" % ("quantity", "Rev 1", "Rev 2", "shift"))
    for k, v in cmp["quantities"].items():
        print("  %-18s %+11.3f %% %+11.3f %% %+9.3f pp"
              % (k, v["campaign_difference_rev1_pct"], v["campaign_difference_rev2_pct"],
                 v["shift_pct_points"]))
    print("\n  uniformity benefit now begins above %s"
          % ("%.5f kg/s (%.2f g/s)" % (thr, thr * 1000) if thr else "not bracketed"))


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 2)
