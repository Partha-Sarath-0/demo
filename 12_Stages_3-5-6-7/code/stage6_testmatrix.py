"""Stage 6a - steady-state 'virtual test' of the as-built GRAIL collector with GRAIL-CHT (same
settings and Richardson treatment as Rev 4.2), in the style of an ISO 9806 steady-state test.
Geometry fixed at the as-built CAD values (bridge 31.286 mm, G 0.539935, lambda 1.0).
Flow fixed at the design flow 2.75 g/s (campaign mid-range; ENGINEERING_ASSUMPTION for the annual
system). All points lie inside the campaign input bounds except none - checked below."""
import sys, csv, json, itertools, time
from multiprocessing import Pool
sys.path.insert(0, "/home/claude/grail_cfd/tools")
import cht_point as P

OUT = "/home/claude/grail_cfd/22_system/virtual_test_matrix.csv"
GEO = dict(bridge_mm=31.285944, g_ratio=0.539935, lam_G=1.0, mdot_total=0.00275)
pts = []
for topo in (1, 0):
    for G, Tin in itertools.product((500.0, 900.0), (293.15, 308.15, 323.15, 332.15)):
        pts.append((topo, dict(G_T=G, T_in=Tin, T_amb=303.15, v_wind=3.0)))
    pts.append((topo, dict(G_T=900.0, T_in=323.15, T_amb=303.15, v_wind=0.5)))
    pts.append((topo, dict(G_T=900.0, T_in=323.15, T_amb=303.15, v_wind=4.9)))
    pts.append((topo, dict(G_T=700.0, T_in=332.15, T_amb=288.15, v_wind=3.0)))
B = {"G_T": (400, 1000), "T_in": (288, 333), "T_amb": (283, 313), "v_wind": (0, 5)}
for _, p in pts:
    for k, (lo, hi) in B.items():
        assert lo <= p[k] <= hi, (k, p[k])


def job(a):
    topo, p = a
    q = dict(p, **GEO)
    r = P.point(q, topo)
    return dict(arrangement="alternating" if topo else "parallel", **q, **r)


if __name__ == "__main__":
    import os; os.makedirs("/home/claude/grail_cfd/22_system", exist_ok=True)
    t = time.time(); rows = []
    with Pool(2) as pool:
        for i, r in enumerate(pool.imap_unordered(job, pts), 1):
            rows.append(r); print(i, len(pts), r["arrangement"], r["G_T"], r["T_in"], r["v_wind"],
                                  "eta %.4f conv %s %.0fs" % (r["eta"], r["converged"], time.time() - t), flush=True)
    with open(OUT, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    print("done")
