"""Fresh independent audit of Rev 4.1 and Rev 4 -> Rev 4.1 comparison. Reads files only."""
import pandas as pd, numpy as np, csv, json
from scipy import stats
O, N = "GRAIL_CFD_dataset_FINAL_rev4.csv", "GRAIL_CFD_dataset_FINAL_rev4.1.csv"
o, n = pd.read_csv(O), pd.read_csv(N)
ro, rn = list(csv.reader(open(O, newline=""))), list(csv.reader(open(N, newline="")))
R = {}
print("== integrity")
print("shape", n.shape, "| NaN", int(n.isna().sum().sum()), "| inf", int(np.isinf(n.select_dtypes("number")).sum().sum()),
      "| dup rows", int(n.duplicated().sum()), "| dup ids", int(n.case_id.duplicated().sum()))
print("columns identical & same order:", list(o.columns) == list(n.columns), "| row order identical:", (o.case_id == n.case_id).all())
print("dtypes identical:", (o.dtypes == n.dtypes).all())
print("\n== Rev4 -> Rev4.1 cell-level comparison")
hdr = ro[0]; changed = {}
for j, c in enumerate(hdr):
    diff = [i for i in range(1, len(ro)) if ro[i][j] != rn[i][j]]
    if diff: changed[c] = len(diff)
unchanged = [c for c in hdr if c not in changed]
print("changed columns:", changed)
print("unchanged columns (byte-for-byte identical text in all 300 rows):", len(unchanged), "of", len(hdr))
comp = []
for c in changed:
    x, y = o[c], n[c]; ad = (y - x).abs(); pct = (ad / x.abs()) * 100
    comp.append([c, changed[c], x.min(), x.max(), y.min(), y.max(), ad.max(), ad.mean(), pct.max()])
    print("%-16s rows %3d | old %.6g..%.6g | new %.6g..%.6g | max|d| %.4g mean|d| %.4g max%% %.4g" % tuple(comp[-1]))
print("\n== verifications on Rev4.1 (float64, unrounded)")
AC, CP = 0.528, 4180.0
def chk(name, x, y):
    e = np.abs(x - y); r = e / np.abs(y).clip(1e-300)
    print("%-44s maxabs %.3e meanabs %.3e maxrel %.3e" % (name, e.max(), e.mean(), r.max())); return float(r.max())
chk("mdot_ch = mdot/12", n.mdot_total_kg_s / 12, n.mdot_channel_kg_s)
chk("dT = Tout - Tin", n.T_out_K - n.T_in_K, n.dT_fluid_K)
chk("Qu = mdot*4180*dT", n.mdot_total_kg_s * CP * n.dT_fluid_K, n.Qu_W)
chk("q_abs = G*0.833*0.82*0.95", n.G_T_W_m2 * 0.833 * 0.82 * 0.95, n.q_abs_W_m2)
chk("Q_solar = q_abs*0.528", n.q_abs_W_m2 * AC, n.Q_solar_W)
chk("eta = Qu/(G*0.528)", n.Qu_W / (n.G_T_W_m2 * AC), n.eta)
chk("W_pump = dp*mdot/997", n.dp_channel_Pa * n.mdot_total_kg_s / 997, n.W_pump_W)
chk("R4 = T_R4^4", n.T_R4_K ** 4, n.R4_K4)
chk("mean_T_pow4 = T_mean^4", n.T_plate_mean_K ** 4, n.mean_T_pow4_K4)
chk("U_L = (Qs-Qu)/(0.528(Tp-Ta))", (n.Q_solar_W - n.Qu_W) / (AC * (n.T_plate_mean_K - n.T_amb_K)), n.U_L_W_m2K)
UL = (n.Q_solar_W - n.Qu_W) / (AC * (n.T_plate_mean_K - n.T_amb_K)); e = (UL - n.U_L_W_m2K).abs()
print("   U_L reconstruction: max abs %.3e, max rel %.3e, mean abs %.3e" % (e.max(), (e / n.U_L_W_m2K.abs()).max(), e.mean()))
chk("Re_in = mdot_ch Dh/(A mu)", n.mdot_channel_kg_s * n.Dh_in_mm / 1e3 / (n.A_in_mm2 / 1e6 * n.mu_Pa_s), n.Re_in)
chk("Re_out = mdot_ch Dh/(A mu)", n.mdot_channel_kg_s * n.Dh_out_mm / 1e3 / (n.A_out_mm2 / 1e6 * n.mu_Pa_s), n.Re_out)
print("Re_old/Re_new: min %.6f max %.6f (expected 4A/(pi Dh^2))" % ((o.Re_in / n.Re_in).min(), (o.Re_out / n.Re_out).max()))
for nm, c in [("T_min<=T_mean", n.T_plate_min_K <= n.T_plate_mean_K), ("T_mean<=T_max", n.T_plate_mean_K <= n.T_plate_max_K),
              ("P90<=P95", n.P90_K <= n.P95_K), ("P95<=P99", n.P95_K <= n.P99_K), ("P99<=T_max", n.P99_K <= n.T_plate_max_K),
              ("T_R4>=T_mean", n.T_R4_K >= n.T_plate_mean_K), ("R4>=mean_T_pow4", n.R4_K4 >= n.mean_T_pow4_K4),
              ("T_R4<=T_max", n.T_R4_K <= n.T_plate_max_K), ("T_out>T_in", n.T_out_K > n.T_in_K)]:
    print("%-18s violations %d" % (nm, int((~c).sum())))
dr = n.T_R4_K - n.T_plate_mean_K
print("T_R4 - T_mean: min %.4f max %.4f K; vs 1.5 std^2/T_mean max|diff| %.4f K" % (dr.min(), dr.max(), (dr - 1.5 * n.plate_std_K ** 2 / n.T_plate_mean_K).abs().max()))
print("\n== energy balance")
res = n.Q_solar_W - (n.Qu_W + n.Q_rad_W + n.Q_conv_W + n.Q_rear_W); pct = 100 * res / n.Q_solar_W
print("residual W: min %.3e max %.3e meanabs %.3e rms %.3e | max |imbalance| %.3e %%" % (res.min(), res.max(), res.abs().mean(), np.sqrt((res ** 2).mean()), pct.abs().max()))
reso = o.Q_solar_W - (o.Qu_W + o.Q_rad_W + o.Q_conv_W + o.Q_rear_W); print("identical to Rev4 residual:", bool((res == reso).all()))
print("\n== signs / convergence / ranges")
for q in ["Q_rad_W", "Q_conv_W", "Q_rear_W", "U_L_W_m2K"]:
    print("%-10s negatives Rev4 %d Rev4.1 %d | sign changes vs Rev4 %d" % (q, int((o[q] < 0).sum()), int((n[q] < 0).sum()), int((np.sign(o[q]) != np.sign(n[q])).sum())))
print("U_L<=0 cases:", n.case_id[n.U_L_W_m2K <= 0].tolist(), "| |Tp-Ta|<2K:", int(((n.T_plate_mean_K - n.T_amb_K).abs() < 2).sum()))
print("converged all", bool(n.converged.all()), "| residual max", n.residual.max(), "| iters max", n.outer_iters.max(), "cap", n.outer_cap.iloc[0])
print("Re_out max %.1f (laminar < 2300)" % n.Re_out.max(), "| Re_in range %.2f-%.2f" % (n.Re_in.min(), n.Re_in.max()))
for c in ["R4_K4", "T_R4_K", "mean_T_pow4_K4", "U_L_W_m2K", "Re_in", "Re_out"]:
    print("%-16s min %.6g max %.6g" % (c, n[c].min(), n[c].max()))
json.dump({"changed": changed, "comparison": comp}, open("rev41_comparison.json", "w"), indent=1, default=float)
