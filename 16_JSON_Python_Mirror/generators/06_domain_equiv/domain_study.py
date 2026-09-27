"""
GRAIL — domain-equivalence study. Closes CR-03.

CR-03 says a plain symmetry plane is not valid under alternating flow: neighbours across a
bridge run in opposite directions, so the field is glide-symmetric rather than
mirror-symmetric, and an adiabatic plane on a bridge midline would suppress exactly the
lateral conduction the mechanism depends on. That was an argument. This measures it.

Five domains, all at the same cell size (dx = 5 mm, dy = 2 mm), all alternating, with
co-current as a control:

    full-12-adiabatic   the reference: the physical plate, real adiabatic edges
    3ch-adiabatic       a three-channel strip cut on bridge midlines, symmetry planes
    3ch-periodic        the same strip, wrapped
    2ch-adiabatic       a two-channel strip, symmetry planes
    2ch-periodic        the same strip, wrapped - the only narrow domain that can carry
                        the glide symmetry, because two channels is one full period

Comparison is against the INTERIOR of the full plate, not its edge channels, since a strip
is meant to represent an interior slice.

Writes 06_domain_equiv/domain_study.json
"""
import sys, os, json, time
import numpy as np

sys.path.insert(0, "/home/claude/grail_cfd/tools")
from grail_cht import Materials, Operating
from grail_ext import make_geom, make_op, GrailDomain, lateral_bridge_profile

OUT = "/home/claude/grail_cfd/06_domain_equiv"
os.makedirs(OUT, exist_ok=True)
DX_MM, DY_MM = 5.0, 2.0
CASES = [("full-12-adiabatic", 12, "adiabatic"),
         ("3ch-adiabatic", 3, "adiabatic"),
         ("3ch-periodic", 3, "periodic"),
         ("2ch-adiabatic", 2, "adiabatic"),
         ("2ch-periodic", 2, "periodic")]


def run(n_ch, lateral, f_interdig):
    g = make_geom(n_ch)
    nx = int(round(g.L * 1000 / DX_MM))
    ny = int(round(g.W * 1000 / DY_MM))
    s = GrailDomain(g, Materials(), make_op(n_ch, f_interdig=f_interdig),
                    nx=nx, ny=ny, lateral=lateral)
    r = s.solve(max_outer=2000, tol=1e-8)
    r["nx"], r["ny"], r["n_ch"], r["lateral"] = nx, ny, n_ch, lateral
    r["bridge_W"] = lateral_bridge_profile(s)
    r["bridge_W_total"] = float(sum(r["bridge_W"]))
    r["bridge_W_per_midline"] = (float(np.mean(r["bridge_W"])) if r["bridge_W"] else 0.0)
    return s, r


def interior(s, n_keep):
    """Plate statistics over the central n_keep channels only."""
    g = s.g
    lo = (g.N_CH - n_keep) // 2
    ys = s.ch_y[lo:lo + n_keep]
    y0, y1 = ys.min() - g.PITCH / 2, ys.max() + g.PITCH / 2
    m = (s.yc >= y0 - 1e-9) & (s.yc <= y1 + 1e-9)
    T = s.Tp[:, m]
    return {"Tp_mean": float(T.mean()), "Tp_std": float(T.std()),
            "Tp_max": float(T.max()), "Tp_min": float(T.min()),
            "n_cols": int(m.sum())}


if __name__ == "__main__":
    t0 = time.time()
    out = {"dx_mm": DX_MM, "dy_mm": DY_MM, "cases": {}}
    for f, tag in ((1, "alternating"), (0, "co_current")):
        out["cases"][tag] = {}
        ref_s = ref_r = None
        for name, n_ch, lat in CASES:
            s, r = run(n_ch, lat, f)
            if name.startswith("full"):
                ref_s, ref_r = s, r
            rec = {k: r[k] for k in ("eta", "T_out", "dT", "Tp_mean", "Tp_std", "dTp",
                                     "U_L", "energy_error_pct", "outer", "converged",
                                     "nx", "ny", "n_ch", "lateral",
                                     "bridge_W_total", "bridge_W_per_midline")}
            rec["bridge_W"] = r["bridge_W"]
            # compare like with like: the strip against the same number of interior channels
            rec["interior"] = interior(s, n_ch if n_ch < 12 else 12)
            rec["ref_interior_same_width"] = interior(ref_s, n_ch)
            out["cases"][tag][name] = rec
            print("%-12s %-18s eta %.6f  Tp_std %.4f  bridge/midline %8.3f W  "
                  "outer %4d  (%.0f s)"
                  % (tag, name, r["eta"], r["Tp_std"], r["bridge_W_per_midline"],
                     r["outer"], time.time() - t0), flush=True)

    # headline: how much does a symmetry plane cost, against the reference interior?
    summ = {}
    for tag in out["cases"]:
        ref = out["cases"][tag]["full-12-adiabatic"]
        summ[tag] = {}
        for name in out["cases"][tag]:
            if name.startswith("full"):
                continue
            c = out["cases"][tag][name]
            ri = c["ref_interior_same_width"]
            summ[tag][name] = {
                "d_eta_pct": 100 * (c["eta"] - ref["eta"]) / ref["eta"],
                "d_Tp_std_vs_ref_interior_pct":
                    100 * (c["interior"]["Tp_std"] - ri["Tp_std"]) / ri["Tp_std"],
                "d_Tp_mean_K": c["interior"]["Tp_mean"] - ri["Tp_mean"],
                "bridge_per_midline_W": c["bridge_W_per_midline"],
                "ref_bridge_per_midline_W": ref["bridge_W_per_midline"],
                "bridge_per_midline_vs_ref_pct":
                    (100 * (c["bridge_W_per_midline"] - ref["bridge_W_per_midline"])
                     / ref["bridge_W_per_midline"])
                    if ref["bridge_W_per_midline"] > 1e-6 else None}
    out["summary_vs_full_plate"] = summ
    json.dump(out, open(os.path.join(OUT, "domain_study.json"), "w"), indent=1)

    print("\n=== against the full plate's interior ===")
    for tag in summ:
        print(" %s" % tag)
        for name, v in summ[tag].items():
            print("   %-16s d_eta %+7.3f %%   d_Tp_std %+8.3f %%   d_Tp_mean %+7.3f K   "
                  "bridge %8.3f W vs %8.3f W %s"
                  % (name, v["d_eta_pct"], v["d_Tp_std_vs_ref_interior_pct"],
                     v["d_Tp_mean_K"], v["bridge_per_midline_W"],
                     v["ref_bridge_per_midline_W"],
                     ("(%+.2f %%)" % v["bridge_per_midline_vs_ref_pct"])
                     if v["bridge_per_midline_vs_ref_pct"] is not None else "(ref ~ 0)"))
    print("\ntotal %.0f s" % (time.time() - t0))
