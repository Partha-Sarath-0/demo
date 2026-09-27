"""V5 component check: GRAIL-CHT loss sub-models vs measured values of Beikircher et al.,
Sol. Energy Mater. Sol. Cells 141 (2015) 398-406 (ZAE Bayern), and the efficiency line of
Kessentini et al. (CTTC/UPC, honeycomb/slat TIM collector).

Only GRAIL-CHT's own functions and Materials are used (tools/grail_cht.py). Nothing is changed or tuned.
Measured values (as printed in the paper, read from its text/Table 1):
  honeycomb front (with ETFE film), U_front = 2.2 W/m2K (30 mm), 1.95 W/m2K (40 mm)
  VSI rear, 40 mm, 70-120 C absorber: silica 0.25-0.45 W/m2K, perlite 0.50-0.84 W/m2K
  VSI prototype (EN 12975-2, AR glass): eta0 0.89, a1 3.28, a2 0.014
  VSI improvement in a1 vs 40 mm mineral wool: >= ~0.5 W/m2K
Kessentini: eta = 0.732 - 7.19 (Tav-Tamb)/G (ISO 9806-1, 16 points), selective eps 0.5.
"""
import sys, json
sys.path.insert(0, "/home/claude/grail_cfd/tools")
import numpy as np
import grail_cht as gc

m = gc.Materials()
out = {}

# ---- rear path
R_rear_total = m.t_pcm / m.k_pcm + m.t_vip / m.k_vip + 1.0 / m.h_rear
U_rear_grail = 1 / R_rear_total
U_vip_only = m.k_vip / m.t_vip
k_eff_meas = {"silica": [0.25 * 0.04, 0.45 * 0.04], "perlite": [0.50 * 0.04, 0.84 * 0.04]}   # U*L, 40 mm
U_rear_with_meas_k = {k: [1 / (m.t_pcm / m.k_pcm + m.t_vip / kk + 1 / m.h_rear) for kk in v] for k, v in k_eff_meas.items()}
out["rear"] = dict(grail_k_vip=m.k_vip, grail_t_vip=m.t_vip, grail_U_vip_layer=U_vip_only,
                   grail_U_rear_total=U_rear_grail, measured_k_eff_in_collector=k_eff_meas,
                   grail_U_rear_if_measured_k=U_rear_with_meas_k)

# ---- front path: GRAIL top loss per unit plate area (conduction + T^4 radiation), T_amb 303.15 K, wind 3 m/s
op = gc.Operating(T_amb=303.15, v_wind=3.0)
fake = type("S", (), {"_R_top_cond": gc.GrailCHT._R_top_cond})()
fake.m, fake.op = m, op
m.h_wind_val = op.h_wind
res = []
for dT in (20, 40, 60, 80):
    Tp = np.array([op.T_amb + dT])
    q, qc, qr, Tg = gc.GrailCHT.top_loss(fake, Tp)
    res.append(dict(dT=dT, U_top=float(q[0] / dT), cond=float(qc[0] / dT), rad=float(qr[0] / dT)))
out["front"] = dict(grail=res, measured_honeycomb_front_U=[1.95, 2.2],
                    note="Beikircher U is for a 30-40 mm honeycomb + ETFE film front; GRAIL uses 10 mm TIM + 2 air gaps + double glass, TiNOX eps 0.04")
json.dump(out, open("beikircher_check.json", "w"), indent=1, default=float)
print(json.dumps(out, indent=1, default=float))
