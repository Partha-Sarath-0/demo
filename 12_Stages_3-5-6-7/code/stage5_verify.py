"""Re-evaluate every selected Stage 5 point with GRAIL-CHT (Richardson, Rev 4.2 settings) at the
same reference operating point, and report surrogate-vs-solver error. No surrogate result is
quoted as a final design result without this check."""
import sys, time, pandas as pd
from multiprocessing import Pool
sys.path.insert(0, "/home/claude/grail_cfd/tools")
import cht_point as P
D = "/home/claude/grail_cfd/23_optimisation/"
REF = dict(G_T=800.0, T_in=313.15, T_amb=303.15, v_wind=3.0)


def job(r):
    p = dict(REF, mdot_total=r["mdot_total_kg_s"], bridge_mm=r["bridge_mm"], g_ratio=r["g_ratio"],
             lam_G=r["lambda_G"])
    o = P.point(p, 1 if r["arrangement"] == "alternating" else 0)
    return dict(arrangement=r["arrangement"], pick=r["pick"], eta_ann=r["eta"], eta_cht=o["eta"],
                std_ann=r["plate_std_K"], std_cht=o["plate_std_K"], dp_ann=r["dp_Pa"], dp_cht=o["dp_channel_Pa"],
                Tmax_cht=o["T_plate_max_K"], converged=o["converged"])


if __name__ == "__main__":
    s = pd.read_csv(D + "selected_points_surrogate.csv").to_dict("records")
    with Pool(2) as pool:
        rows = pool.map(job, s)
    v = pd.DataFrame(rows)
    v["eta_err_pp"] = (v.eta_ann - v.eta_cht) * 100
    v["std_err_pct"] = (v.std_ann - v.std_cht) / v.std_cht * 100
    v["dp_err_pct"] = (v.dp_ann - v.dp_cht) / v.dp_cht * 100
    v.to_csv(D + "verification_vs_GRAIL-CHT.csv", index=False)
    print(v.round(4).to_string())
