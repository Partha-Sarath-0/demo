"""Evaluate GRAIL-CHT at one operating/design point exactly as the Rev 4.2 campaign did:
Rev 4 settings (k(T), tol 1e-6, cap 3000, same Nu closure), plate grids nx110 and nx220 (ny as
campaign), result = Richardson 2 f(220) - f(110) for every output column, identical to Rev 4.1/4.2.
Nothing in campaign*.py or grail_cht.py is modified; this module only calls them."""
import sys, json
import numpy as np, pandas as pd
sys.path.insert(0, "/home/claude/grail_cfd/tools")
import campaign as C
import campaign4 as C4

NU = float(pd.read_csv("/home/claude/grail_cfd/19_rev41/GRAIL_CFD_dataset_FINAL_rev4.2.csv",
                       usecols=["Nu_closure_input"]).Nu_closure_input.iloc[0])
RICH = ["T_out_K", "dT_fluid_K", "Qu_W", "eta", "T_plate_mean_K", "T_plate_max_K", "T_plate_min_K",
        "plate_spread_K", "plate_std_K", "dp_channel_Pa", "T_glass_mean_K"]


def run(p, topo, nx):
    C.NU_CFD = NU; C.NX = nx; C4.NU = NU; C4.PLATE_NX = nx
    return C4.run_case_rev4("pt", p, topo)


def point(p, topo):
    """p: dict G_T, T_in, T_amb, v_wind, mdot_total, bridge_mm, g_ratio, lam_G."""
    a, b = run(p, topo, 110), run(p, topo, 220)
    ok = bool(a["converged"] and b["converged"] and abs(a["energy_error_pct"]) < 0.5
              and abs(b["energy_error_pct"]) < 0.5)
    out = {k: 2 * b[k] - a[k] for k in RICH}
    out.update(converged=ok, e110=a["energy_error_pct"], e220=b["energy_error_pct"],
               it=max(a["outer_iters"], b["outer_iters"]), eta_110=a["eta"], eta_220=b["eta"])
    return out


if __name__ == "__main__":
    import time
    t = time.time()
    p = dict(G_T=800.0, T_in=313.15, T_amb=303.15, v_wind=3.0, mdot_total=0.00275,
             bridge_mm=31.285944, g_ratio=0.539935, lam_G=1.0)
    print(json.dumps(point(p, 1), default=float), "%.0fs" % (time.time() - t))
