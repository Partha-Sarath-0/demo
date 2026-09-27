"""
Rev 4.1 — surgical correction of three derived-column groups in GRAIL_CFD_dataset_FINAL_rev4.csv.
Nothing else is touched. The Rev 4 file is only read.

A. R4_K4, T_R4_K, mean_T_pow4_K4
   R4 = mean over plate cells of T^4 is a plate-averaged functional of the field, exactly like
   T_plate_mean (the mean of T). The per-cell Richardson field was never stored, so mean(T_rich^4)
   cannot be formed from it. The consistent choice is to Richardson-extrapolate the functional
   itself, R4 = 2 R4(220) - R4(110): each grid's R4 is computed exactly on that grid's own field,
   so the fourth power is never applied to an extrapolated or averaged temperature. This is the
   same operation, at the same order, that produced T_plate_mean. Then:
       T_R4_K         = R4_K4 ** 0.25
       mean_T_pow4_K4 = T_plate_mean_K ** 4      (source definition: (mean T)^4)
B. U_L_W_m2K = (Q_solar_W - Qu_W) / (A_c * (T_plate_mean_K - T_amb_K)),  A_c = 0.528 m^2
C. Re_in  = mdot_channel * Dh_in  / (A_in  * mu)
   Re_out = mdot_channel * Dh_out / (A_out * mu)      (SI: mm -> m, mm^2 -> m^2)
"""
import pandas as pd, numpy as np, sys
D = "/home/claude/grail_cfd/10_dataset/"
SRC = sys.argv[1]; OUT = sys.argv[2]
d = pd.read_csv(SRC)
a = pd.read_csv(D + "GRAIL_CFD_dataset_rev4_nx110.csv").set_index("case_id").loc[d.case_id]
b = pd.read_csv(D + "GRAIL_CFD_dataset_rev4_nx220.csv").set_index("case_id").loc[d.case_id]
# the raw grids must be the ones this file was built from: every Richardson column must reproduce
for c in ["T_plate_mean_K", "plate_std_K", "Qu_W", "eta"]:
    assert np.allclose(d[c].values, 2 * b[c].values - a[c].values, rtol=0, atol=1e-9), c
AC = 0.528
new = {}
new["R4_K4"] = 2 * b["R4_K4"].values - a["R4_K4"].values
new["T_R4_K"] = new["R4_K4"] ** 0.25
new["mean_T_pow4_K4"] = d["T_plate_mean_K"].values ** 4
new["U_L_W_m2K"] = (d["Q_solar_W"].values - d["Qu_W"].values) / (AC * (d["T_plate_mean_K"].values - d["T_amb_K"].values))
new["Re_in"] = d["mdot_channel_kg_s"].values * (d["Dh_in_mm"].values / 1e3) / ((d["A_in_mm2"].values / 1e6) * d["mu_Pa_s"].values)
new["Re_out"] = d["mdot_channel_kg_s"].values * (d["Dh_out_mm"].values / 1e3) / ((d["A_out_mm2"].values / 1e6) * d["mu_Pa_s"].values)
# text-level rewrite: every other cell is copied character for character
import csv
rows = list(csv.reader(open(SRC, newline="")))
hdr = rows[0]; idx = {c: hdr.index(c) for c in new}
for i, r in enumerate(rows[1:]):
    assert r[0] == d.case_id.iloc[i]
    for c, j in idx.items():
        r[j] = repr(float(new[c][i]))
with open(OUT, "w", newline="") as f:
    csv.writer(f).writerows(rows)
print("wrote", OUT, len(rows) - 1, "rows", len(hdr), "cols")
