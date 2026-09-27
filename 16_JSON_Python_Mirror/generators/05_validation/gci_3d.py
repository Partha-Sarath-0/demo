"""
GRAIL — grid convergence index on the 3-D channel solution.

Combines the three levels extracted by extract_3d.py. Refinement ratio is taken from the
actual cell counts, r = (N_fine / N_coarse)^(1/3).

Writes 05_validation/gci_3d.json
"""
import os, json
import numpy as np
import sys

sys.path.insert(0, "/home/claude/grail_cfd/05_validation")
from gci_plate import gci

V = "/home/claude/grail_cfd/05_validation"
CASES = [("L1", os.path.join(V, "gci3d/L1")),
         ("L2", "/home/claude/grail_cfd/04_baseline/ch05_flow"),
         ("L3", os.path.join(V, "gci3d/L3"))]
QOI = ("dP_Pa", "dT_K", "peak_bulk_mid", "Nu_developed", "Nu_mid", "volume_mm3")

q = {}
for lab, c in CASES:
    p = os.path.join(c, "qoi.json")
    if not os.path.exists(p):
        raise SystemExit("missing %s — run extract_3d.py on %s first" % (p, c))
    q[lab] = json.load(open(p))

n = [q[l]["ncell"] for l, _ in CASES]
h = [n[-1] ** (1 / 3) / x ** (1 / 3) for x in n]        # relative cell size, fine = 1
r21 = (n[2] / n[1]) ** (1 / 3)
r32 = (n[1] / n[0]) ** (1 / 3)
print("cells %s   r21 %.4f   r32 %.4f" % (n, r21, r32))

out = {"levels": [{"label": l, "ncell": q[l]["ncell"], "h_rel": hh}
                  for (l, _), hh in zip(CASES, h)],
       "r21": r21, "r32": r32, "raw": q, "gci": {}}

print("\n  %-14s %10s %10s %10s   %6s  %12s  %8s"
      % ("quantity", "L1", "L2", "L3(fine)", "p", "extrapolated", "GCI %"))
for k in QOI:
    v3, v2, v1 = q["L1"][k], q["L2"][k], q["L3"][k]     # coarse, medium, fine
    g = gci(v1, v2, v3, r21, r32)
    out["gci"][k] = {"L1": v3, "L2": v2, "L3": v1, **g,
                     "u_num_rel_pct": g["gci_pct"] / 1.25 if g["gci_pct"] else 0.0}
    print("  %-14s %10.5g %10.5g %10.5g   %6s  %12.6g  %8.4f"
          % (k, v3, v2, v1, ("%.3f" % g["p"]) if g["p"] else "-",
             g["f_extrap"], g["gci_pct"]))

nu = out["gci"]["Nu_developed"]
out["nu_cfd_discretisation_uncertainty"] = {
    "value_fine_grid": nu["L3"], "gci_pct": nu["gci_pct"],
    "u_num_rel_pct": nu["u_num_rel_pct"],
    "assumed_in_monte_carlo_pct": 5.0,
    "assumption_conservative": bool(nu["u_num_rel_pct"] < 5.0),
    "note": "this bounds only the DISCRETISATION part of nu_cfd. The larger term is the "
            "modelling assumption that one constant Nusselt number represents a graded, "
            "developing channel; a grid study cannot bound that."}

json.dump(out, open(os.path.join(V, "gci_3d.json"), "w"), indent=1)
print("\nNu_mean on the fine grid %.4f, discretisation u = %.2f %% "
      "(the Monte Carlo assumed %.1f %%: %s)"
      % (nu["L3"], nu["u_num_rel_pct"], 5.0,
         "conservative" if nu["u_num_rel_pct"] < 5.0 else "NOT conservative — restate"))
print("wrote gci_3d.json")
