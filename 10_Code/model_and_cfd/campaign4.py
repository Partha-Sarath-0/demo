"""
GRAIL production campaign, Rev 4 — the Nusselt closure corrected to the CONJUGATE value.

WHY
The Level-3 benchmark (15_benchmark/benchmark_record.md) established that the campaign's closure,
Nu = 2.9238, was extracted from a fluid-only 3-D case with a heat flux uniform around the channel
perimeter (the H2 condition). The real absorber's aluminium wall is nearly isothermal around the
perimeter (the H1 condition), and the 3-D conjugate solution gives Nu close to the H1 value. With
the conjugate Nu, GRAIL-CHT reproduces the 3-D conjugate solution to 0.1 pp on the arrangement
difference; with 2.9238 it overstates the uniformity benefit about threefold.

WHAT CHANGES, AND ONLY THIS
Rev 3 -> Rev 4: nu_cfd 2.9238 -> the grid-converged conjugate Nu (passed on the command line and
recorded in every row). Everything else is Rev 3: same seed, same Latin Hypercube, same bounds,
same pre-run geometry gate, plate grid 110 x 120 by default (a finer axial grid may be passed as
argv[3]; the ROM is first-order axially, p = 1.01, see benchmark_record.md; recorded per row), k(T) on, and IDENTICAL acceptance gates
(converged at tol 1e-6, |energy error| < 0.5 %, 250 < T_plate_mean < 500 K).

The one numerical-budget change, stated rather than hidden: the outer-iteration CAP rises from
900 to 3000. A higher Nu stiffens the coupled solve; Rev 3 already lost its two hardest low-flow
rows at the 900 cap. Raising a cap is not loosening a tolerance: a row is still accepted only if
it meets tol 1e-6. Every row carries `outer_iters`, and rows that needed more than 900 are
reported separately so the result can be quoted with and without them.

Rev 1, 2 and 3 are NOT deleted and remain bit-reproducible (campaign.py is not edited).
"""
import sys, os, csv, json, time
import numpy as np
from multiprocessing import Pool

sys.path.insert(0, "/home/claude/grail_cfd/tools")
import campaign as C
import campaign3 as C3
import grail_cht as G

MAX_OUTER = 3000
OUT = "/home/claude/grail_cfd/10_dataset/GRAIL_CFD_dataset_rev4.csv"
FAIL = "/home/claude/grail_cfd/11_failures/failures_rev4.csv"
REV3 = "/home/claude/grail_cfd/10_dataset/GRAIL_CFD_dataset_rev3.csv"
CMP = "/home/claude/grail_cfd/10_dataset/rev3_vs_rev4.json"
NU = None                                  # set from argv in main
PLATE_NX = C.NX                            # axial plate cells; default = Rev 1-3 value (110)


def run_case_rev4(cid, p, topo):
    """C.run_case with k(T) on (as Rev 3) and the iteration cap raised; nothing else touched."""
    orig_init, orig_solve = G.GrailCHT.__init__, G.GrailCHT.solve

    def init(self, geo, mat, op, nx=220, ny=240, nu_cfd=3.428, k_of_T=False):
        orig_init(self, geo, mat, op, nx=nx, ny=ny, nu_cfd=nu_cfd, k_of_T=True)

    def solve(self, tol=1e-6, max_outer=200, verbose=False):
        assert tol == 1e-6, "tolerance must not change"
        return orig_solve(self, tol=tol, max_outer=MAX_OUTER, verbose=verbose)

    G.GrailCHT.__init__, G.GrailCHT.solve = init, solve
    try:
        return C.run_case(cid, p, topo)
    finally:
        G.GrailCHT.__init__, G.GrailCHT.solve = orig_init, orig_solve


def one(job):
    cid, p, topo = job
    C.NU_CFD = NU
    C.NX = PLATE_NX
    try:
        row = run_case_rev4(cid, p, topo)
    except Exception as e:
        return {"__fail__": [cid, topo, "exception:%s" % str(e)[:90], json.dumps(p)]}
    if not row["converged"]:
        return {"__fail__": [cid, topo, "not_converged", json.dumps(p)]}
    if abs(row["energy_error_pct"]) > 0.5:
        return {"__fail__": [cid, topo, "energy_error_%.4f" % row["energy_error_pct"], json.dumps(p)]}
    if not (250.0 < row["T_plate_mean_K"] < 500.0):
        return {"__fail__": [cid, topo, "T_out_of_range_%.1f" % row["T_plate_mean_K"], json.dumps(p)]}
    row["nu_cfd"] = NU
    row["nu_basis"] = "conjugate_3D_benchmark_H1_type"
    row["dataset_rev"] = 4
    row["k_model"] = "k(T)_cubic_273_373K"
    row["outer_cap"] = MAX_OUTER
    row["plate_nx"] = PLATE_NX
    row["plate_ny"] = C.NY
    return row


def main(nw=2):
    jobs, rejects = C3.build_jobs()
    print("Rev 4 — Nu %.4f, k(T), cap %d, plate %dx%d. %d cases" % (NU, MAX_OUTER, PLATE_NX, C.NY, len(jobs)), flush=True)
    t0 = time.time(); rows, fails = [], list(rejects)
    with Pool(nw) as pool:
        for n, r in enumerate(pool.imap_unordered(one, jobs, chunksize=1), 1):
            (fails.append(r["__fail__"]) if "__fail__" in r else rows.append(r))
            if n % 10 == 0 or n == len(jobs):
                el = time.time() - t0
                print("  %3d / %d   accepted %d   rejected %d   (%.0f s, eta %.0f s)"
                      % (n, len(jobs), len(rows), len(fails), el, el / n * (len(jobs) - n)), flush=True)
    rows.sort(key=lambda r: r["case_id"])
    with open(OUT, "w", newline="") as fo:
        w = csv.DictWriter(fo, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
    with open(FAIL, "w", newline="") as ff:
        fw = csv.writer(ff); fw.writerow(["case_id", "topology", "reason", "params"]); fw.writerows(fails)
    print("wrote %s : %d rows, %d rejected (%.0f s)" % (OUT, len(rows), len(fails), time.time() - t0))


if __name__ == "__main__":
    NU = float(sys.argv[1])
    if len(sys.argv) > 3:
        PLATE_NX = int(sys.argv[3])
        OUT = OUT.replace(".csv", "_nx%d.csv" % PLATE_NX); FAIL = FAIL.replace(".csv", "_nx%d.csv" % PLATE_NX)
    main(int(sys.argv[2]) if len(sys.argv) > 2 else 2)
