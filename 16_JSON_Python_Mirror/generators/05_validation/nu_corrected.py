"""
GRAIL — what changes if the Nusselt number is corrected to its grid-converged value?

The 3-D grid study puts the observed order at p = 1.283 and extrapolates Nu (developed region,
original extraction method) to 2.9238. The conjugate solver has been run throughout with
3.4282, the value measured on the medium grid, which is +14.71 % high.

That is a bias, not an uncertainty, and it sits on the input the sensitivity analysis found
controls 91 % of the uniformity difference. Rather than extrapolate the linear model 2.9 standard
deviations outside its sampled range, this measures it.
"""
import sys, json
import numpy as np
sys.path.insert(0, "/home/claude/grail_cfd/tools")
from grail_cht import Geometry, Materials, Operating, GrailCHT

NX, NY = 220, 240
out = {"nu_values": {}, "note": "same grid, same properties, only nu_cfd changes"}
for tag, nu in (("as_run_3.4282", 3.4282), ("grid_converged_2.9238", 2.9238)):
    rec = {}
    for name, f in (("co", 0), ("alt", 1)):
        s = GrailCHT(Geometry(), Materials(), Operating(f_interdig=f), nx=NX, ny=NY, nu_cfd=nu)
        r = s.solve(max_outer=2500, tol=1e-8)
        rec[name] = {k: r[k] for k in ("eta", "Tp_mean", "Tp_std", "U_L", "T_out", "dTp")}
    for q in ("eta", "Tp_std", "U_L", "dTp"):
        rec["d_%s_pct" % q] = 100 * (rec["alt"][q] - rec["co"][q]) / rec["co"][q]
    out["nu_values"][tag] = rec
    print("nu = %.4f :  co eta %.6f  alt eta %.6f   d_eta %+.3f %%   d_Tp_std %+.3f %%"
          % (nu, rec["co"]["eta"], rec["alt"]["eta"], rec["d_eta_pct"], rec["d_Tp_std_pct"]),
          flush=True)

a = out["nu_values"]["as_run_3.4282"]; b = out["nu_values"]["grid_converged_2.9238"]
out["shift"] = {("d_%s_pct" % q): b["d_%s_pct" % q] - a["d_%s_pct" % q]
                for q in ("eta", "Tp_std", "U_L", "dTp")}
out["shift"]["co_eta_abs"] = b["co"]["eta"] - a["co"]["eta"]
out["shift"]["alt_eta_abs"] = b["alt"]["eta"] - a["alt"]["eta"]
json.dump(out, open("/home/claude/grail_cfd/05_validation/nu_corrected.json", "w"), indent=1)
print("\nshift from correcting nu_cfd:")
for k, v in out["shift"].items():
    print("   %-16s %+.4f" % (k, v))
