"""
GRAIL — plate temperature fields for the domain-equivalence figure.

Re-runs the three alternating domains that matter and stores the field itself, so the
symmetry-plane distortion can be seen rather than only tabulated. Same cell size as the
domain study (dx 5 mm, dy 2 mm), so these are the same solutions, not a coarser preview.

Writes 06_domain_equiv/domain_fields.npz
"""
import sys, os, json
import numpy as np

sys.path.insert(0, "/home/claude/grail_cfd/tools")
from grail_cht import Materials
from grail_ext import make_geom, make_op, GrailDomain, lateral_bridge_profile

OUT = "/home/claude/grail_cfd/06_domain_equiv"
DX_MM, DY_MM = 5.0, 2.0
CASES = [("full-12-adiabatic", 12, "adiabatic"),
         ("2ch-periodic", 2, "periodic"),
         ("2ch-adiabatic", 2, "adiabatic")]

store, meta = {}, {}
for name, n_ch, lat in CASES:
    g = make_geom(n_ch)
    nx = int(round(g.L * 1000 / DX_MM))
    ny = int(round(g.W * 1000 / DY_MM))
    s = GrailDomain(g, Materials(), make_op(n_ch, f_interdig=1), nx=nx, ny=ny, lateral=lat)
    r = s.solve(max_outer=2000, tol=1e-8)
    store[name + "_Tp"] = s.Tp.astype(np.float32)
    store[name + "_xc"] = (s.xc * 1000).astype(np.float32)
    store[name + "_yc"] = (s.yc * 1000).astype(np.float32)
    store[name + "_chy"] = (s.ch_y * 1000).astype(np.float32)
    store[name + "_chdir"] = np.asarray(s.ch_dir, np.int8)
    meta[name] = {"eta": r["eta"], "Tp_std": r["Tp_std"], "Tp_mean": r["Tp_mean"],
                  "bridge_W_per_midline": float(np.mean(lateral_bridge_profile(s))),
                  "nx": nx, "ny": ny, "n_ch": n_ch, "lateral": lat}
    print("  %-20s eta %.6f  std %.4f  bridge %.3f W" %
          (name, r["eta"], r["Tp_std"], meta[name]["bridge_W_per_midline"]), flush=True)

np.savez_compressed(os.path.join(OUT, "domain_fields.npz"), **store)
json.dump(meta, open(os.path.join(OUT, "domain_fields.json"), "w"), indent=1)
print("wrote domain_fields.npz")
