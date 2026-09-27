"""
GRAIL — discretisation uncertainty on the conjugate plate grid.

Four grid levels at a constant refinement ratio r = sqrt(2) in cell count per direction, both
arrangements on every level. The quantity that matters is not any single-arrangement number but
the ALTERNATING - CO-CURRENT difference, because that difference is what the uniformity claim
rests on. It is reported with its own GCI, computed on the difference itself rather than
inferred from the two separate bands (which would be pessimistic: the two runs share the grid,
so most of the discretisation error is common and cancels).

Method: Roache's grid convergence index as set out in ASME V&V 20-2009.
    p    = ln(|e32/e21|) / ln(r)                observed order, solved with the sign term
    f_ex = f1 + (f1 - f2) / (r^p - 1)           Richardson extrapolation
    GCI  = Fs * |(f1 - f2) / f1| / (r^p - 1)    Fs = 1.25 for three or more levels

Writes 05_validation/gci_plate.json
"""
import sys, os, json, time
import numpy as np

sys.path.insert(0, "/home/claude/grail_cfd/tools")
from grail_cht import Geometry, Materials, Operating, GrailCHT
from campaign import lateral_bridge

OUT = "/home/claude/grail_cfd/05_validation"
os.makedirs(OUT, exist_ok=True)

# constant refinement ratio in total cell count: each level doubles nx*ny
LEVELS = [(110, 120), (156, 170), (220, 240), (311, 339)]
QOI = ("eta", "T_out", "Tp_mean", "Tp_std", "dTp", "U_L", "R4", "Q_rad")


def run(nx, ny, f):
    g, m, op = Geometry(), Materials(), Operating(f_interdig=f)
    s = GrailCHT(g, m, op, nx=nx, ny=ny)
    r = s.solve(max_outer=1500, tol=1e-8)
    r["lateral_bridge_W"] = lateral_bridge(s)
    r["h_mm"] = 1000.0 * np.sqrt((g.L * g.W) / (nx * ny))
    r["ncell"] = nx * ny
    return r


def gci(f1, f2, f3, r21, r32, Fs=1.25):
    """f1 = finest. Returns observed order, extrapolated value, GCI on the fine grid."""
    e21, e32 = f2 - f1, f3 - f2
    if abs(e21) < 1e-14 or abs(e32) < 1e-14:
        return dict(p=None, f_extrap=float(f1), gci_pct=0.0, ratio=None,
                    note="differences at round-off; grid-converged to machine precision")
    s = np.sign(e32 / e21)
    p = 2.0
    for _ in range(200):                       # fixed-point solve, ASME V&V 20 eq. 1-5
        q = np.log((r21 ** p - s) / (r32 ** p - s))
        p_new = abs(np.log(abs(e32 / e21)) + q) / np.log(r21)
        if abs(p_new - p) < 1e-12:
            p = p_new
            break
        p = 0.5 * (p + p_new)
    denom = r21 ** p - 1.0
    f_ex = f1 + (f1 - f2) / denom if abs(denom) > 1e-12 else float("nan")
    g_pct = Fs * abs((f1 - f2) / f1) / denom * 100.0 if abs(f1) > 1e-14 else float("nan")
    return dict(p=float(p), f_extrap=float(f_ex), gci_pct=float(g_pct),
                ratio=float(e32 / e21), oscillatory=bool(s < 0))


if __name__ == "__main__":
    t0 = time.time()
    R = {"co": {}, "alt": {}}
    for nx, ny in LEVELS:
        for key, f in (("co", 0), ("alt", 1)):
            r = run(nx, ny, f)
            R[key]["%dx%d" % (nx, ny)] = r
            print("%-4s %4dx%-4d  h %.4f mm  eta %.6f  Tp_std %.5f  bridge %8.3f W  "
                  "outer %4d  err %+.2e %%  (%.0f s)"
                  % (key, nx, ny, r["h_mm"], r["eta"], r["Tp_std"], r["lateral_bridge_W"],
                     r["outer"], r["energy_error_pct"], time.time() - t0), flush=True)

    keys = ["%dx%d" % lv for lv in LEVELS]          # coarse -> fine
    fine = keys[::-1]                                # fine -> coarse for the GCI triplets
    out = {"levels": [{"nx": lv[0], "ny": lv[1], "ncell": lv[0] * lv[1],
                       "h_mm": R["co"][k]["h_mm"]} for lv, k in zip(LEVELS, keys)],
           "raw": R, "gci": {}, "gci_difference": {}}

    for trip_name, trip in (("L4L3L2", fine[0:3]), ("L3L2L1", fine[1:4])):
        h = [R["co"][k]["h_mm"] for k in trip]
        r21, r32 = h[1] / h[0], h[2] / h[1]
        out["gci"][trip_name] = {"r21": r21, "r32": r32}
        for key in ("co", "alt"):
            out["gci"][trip_name][key] = {}
            for q in QOI + ("lateral_bridge_W",):
                v = [R[key][k][q] for k in trip]
                out["gci"][trip_name][key][q] = gci(v[0], v[1], v[2], r21, r32)
        # the claim quantity: relative difference between arrangements, per grid
        out["gci_difference"][trip_name] = {"r21": r21, "r32": r32}
        for q in ("Tp_std", "eta", "U_L", "dTp", "R4"):
            d = [100.0 * (R["alt"][k][q] - R["co"][k][q]) / R["co"][k][q] for k in trip]
            out["gci_difference"][trip_name]["d_%s_pct" % q] = {
                "values_fine_to_coarse": d, **gci(d[0], d[1], d[2], r21, r32)}

    json.dump(out, open(os.path.join(OUT, "gci_plate.json"), "w"), indent=1)

    print("\n--- GCI on the finest grid (triplet L4/L3/L2) ---")
    t = out["gci"]["L4L3L2"]
    for key in ("co", "alt"):
        for q in QOI:
            g_ = t[key][q]
            print("  %-4s %-10s p %-6s  extrap %-14s  GCI %.4f %%"
                  % (key, q, ("%.3f" % g_["p"]) if g_["p"] else "-",
                     "%.6g" % g_["f_extrap"], g_["gci_pct"]))
    print("\n--- GCI on the ALTERNATING - CO-CURRENT difference ---")
    d = out["gci_difference"]["L4L3L2"]
    for q in ("Tp_std", "eta", "U_L", "dTp", "R4"):
        g_ = d["d_%s_pct" % q]
        print("  d_%-8s fine value %+8.4f %%   p %-6s   GCI %.4f %% of the difference"
              % (q, g_["values_fine_to_coarse"][0],
                 ("%.3f" % g_["p"]) if g_["p"] else "-", g_["gci_pct"]))
    print("\ntotal %.0f s" % (time.time() - t0))
