"""Roadmap V7 - alternating vs parallel at MATCHED MEAN PLATE TEMPERATURE.
For each target mean plate temperature, the inlet temperature of each arrangement is found by a
secant search so that GRAIL-CHT's plate mean temperature equals the target (|error| < 0.05 K).
Everything else is identical for both arrangements: as-built geometry (bridge 31.286 mm,
G 0.539935, lambda 1.0), design flow 2.75 g/s, G = 800 W/m2, T_amb = 303.15 K, wind 3 m/s.
Each evaluation is the Rev 4.2 Richardson point (cht_point.run at nx 110 and 220, 2 f220 - f110),
extended with the radiative metric R4 (= mean T^4) and T_R4 = R4^0.25. Nothing in
campaign*.py, grail_cht.py or cht_point.py is modified."""
import sys, json, time
from multiprocessing import Pool
sys.path.insert(0, "/home/claude/grail_cfd/tools")
import cht_point as P

OUT = "/home/claude/grail_cfd/29_v7/"
BASE = dict(G_T=800.0, T_amb=303.15, v_wind=3.0, mdot_total=0.00275,
            bridge_mm=31.285944, g_ratio=0.539935, lam_G=1.0)
KEYS = P.RICH + ["R4_K4", "T_R4_K", "Q_rad_W", "U_L_W_m2K"]
TARGETS = (320.0, 330.0, 340.0)


def evaluate(Tin, topo):
    p = dict(BASE, T_in=Tin)
    a, b = P.run(p, topo, 110), P.run(p, topo, 220)
    ok = bool(a["converged"] and b["converged"] and abs(a["energy_error_pct"]) < 0.5
              and abs(b["energy_error_pct"]) < 0.5)
    r = {k: 2 * b[k] - a[k] for k in KEYS}
    r.update(converged=ok, T_in_K=Tin, e110=a["energy_error_pct"], e220=b["energy_error_pct"])
    return r


def job(args):
    target, topo = args
    log = []
    x0, x1 = target - 12.0, target - 6.0                 # T_in guesses (plate runs above inlet)
    r0 = evaluate(x0, topo); log.append(r0)
    r1 = evaluate(x1, topo); log.append(r1)
    for _ in range(8):
        f0, f1 = r0["T_plate_mean_K"] - target, r1["T_plate_mean_K"] - target
        if abs(f1) < 0.05:
            break
        x2 = x1 - f1 * (x1 - x0) / (f1 - f0)
        x0, r0, x1 = x1, r1, x2
        r1 = evaluate(x1, topo); log.append(r1)
    res = dict(arrangement="alternating" if topo else "parallel", target_K=target,
               match_error_K=r1["T_plate_mean_K"] - target, evaluations=len(log), **r1)
    json.dump(dict(result=res, log=log), open(OUT + "v7_%s_%d.json" % (res["arrangement"], target), "w"),
              indent=1, default=float)
    print(json.dumps({k: res[k] for k in ("arrangement", "target_K", "T_in_K", "eta", "T_R4_K",
                                           "plate_std_K", "match_error_K", "converged")}, default=float), flush=True)
    return res


if __name__ == "__main__":
    t = time.time()
    with Pool(2) as pool:
        rows = pool.map(job, [(T, topo) for T in TARGETS for topo in (1, 0)])
    import csv
    with open(OUT + "v7_matched_mean_T.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader(); w.writerows(rows)
    print("done %.0f s" % (time.time() - t))
