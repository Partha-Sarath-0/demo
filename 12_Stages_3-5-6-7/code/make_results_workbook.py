"""Build GRAIL_CFD_dataset_rev4.2_with_Stages3-7.xlsx.

Sheet Dataset_rev4.2 is the 300-case CSV copied cell for cell (the CSV itself is not touched).
Every Stage 3-7 number is read from the result file named next to it; derived numbers are Excel
formulas. Nothing is rounded before writing (rounding is display format only).
"""
import json, hashlib
import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

R = "/home/claude/grail_cfd/"
CSV = R + "19_rev41/GRAIL_CFD_dataset_FINAL_rev4.2.csv"
PVG = "/root/.claude/uploads/09cdd886-3a71-5b52-bd3e-e373da90433a/18f57c61-1790154509587_PVdata_19.309_84.792_E5_crystSi_1kWp_14_35deg_0deg.csv"
OUT = "/home/claude/grail_cfd/27_workbook/GRAIL_CFD_dataset_rev4.2_with_Stages3-7.xlsx"

F = "Arial"
H = Font(name=F, bold=True, color="FFFFFF")
HF = PatternFill("solid", fgColor="1F4E78")
T = Font(name=F, bold=True, size=13)
N = Font(name=F)
BLUE = Font(name=F, color="0000FF")          # value read from a result file
GREEN = Font(name=F, color="008000")         # link to another sheet
BLACK = Font(name=F)                         # formula
NOTE = Font(name=F, italic=True, color="555555")
thin = Side(style="thin", color="BFBFBF")
BOX = Border(left=thin, right=thin, top=thin, bottom=thin)

P = {  # package locations of the source files (same bytes as the working-tree files)
    "s3": "12_Stages_3-5-6-7/surrogate/stage3_report.json",
    "s5": "12_Stages_3-5-6-7/optimisation/verification_vs_GRAIL-CHT.csv",
    "s6": "12_Stages_3-5-6-7/system_model/efficiency_correlations.json",
    "s7": "12_Stages_3-5-6-7/annual/stage7_results.json",
    "sw": "12_Stages_3-5-6-7/annual/sizing_sweep.csv",
    "wc": "12_Stages_3-5-6-7/annual/stage7_weather_check.txt",
    "pv": "12_Stages_3-5-6-7/annual/weather/PVGIS_PVreport_35deg_crosscheck.csv",
}

s3 = json.load(open(R + "21_surrogate/stage3_report.json"))
s5 = pd.read_csv(R + "23_optimisation/verification_vs_GRAIL-CHT.csv")
s6 = json.load(open(R + "22_system/efficiency_correlations.json"))
s7 = json.load(open(R + "20_annual/stage7_results.json"))
sw = pd.read_csv(R + "20_annual/sizing_sweep.csv")
ds = pd.read_csv(CSV)
md5 = hashlib.md5(open(CSV, "rb").read()).hexdigest()
assert md5 == s3["dataset_md5"]

wb = Workbook()
EXACT = {}   # sheet -> cell -> exact text of every numeric constant (openpyxl/LibreOffice shorten floats)


def keep(ws, c, v):
    if isinstance(v, (int, float)) and not isinstance(v, bool):
        EXACT.setdefault(ws.title, {})[c.coordinate] = repr(v)


def header(ws, row, names, col=1):
    for j, n in enumerate(names):
        c = ws.cell(row=row, column=col + j, value=n)
        c.font, c.fill, c.border = H, HF, BOX
        c.alignment = Alignment(wrap_text=True, vertical="center")


def put(ws, row, col, v, font=N, fmt=None):
    c = ws.cell(row=row, column=col, value=v)
    keep(ws, c, v)
    c.font, c.border = font, BOX
    if fmt:
        c.number_format = fmt
    return c


def widths(ws, w):
    for i, x in enumerate(w, 1):
        ws.column_dimensions[get_column_letter(i)].width = x


# ---------------------------------------------------------------- README
ws = wb.active
ws.title = "README"
lines = [
    ("GRAIL Collector - CFD dataset rev 4.2 with Stage 3-7 results", T),
    ("", N),
    ("Dataset_rev4.2: the 300 GRAIL-CHT cases, copied cell for cell from GRAIL_CFD_dataset_FINAL_rev4.2.csv.", N),
    ("   The CSV file itself is unchanged (MD5 %s, the MD5 recorded by Stage 3)." % md5, N),
    ("   Nothing was added to, removed from or edited in the 300 rows.", N),
    ("Summary: the headline Stage 3-7 results, each linked to its detail sheet.", N),
    ("Stage3_ANN, Stage5_NSGA2, Stage6_Correlations, Stage7_Annual, Economics: detail sheets.", N),
    ("", N),
    ("Colour code", Font(name=F, bold=True)),
    ("   blue   = number read from the result file named in the 'Source file' column", BLUE),
    ("   black  = Excel formula computed in this workbook", BLACK),
    ("   green  = link to another sheet", GREEN),
    ("", N),
    ("Numbers are stored at full precision; the displayed decimals are formatting only.", N),
    ("Source paths are relative to the GRAIL_Collector_Complete_Final package folder.", N),
    ("Model results only: no experimental validation is claimed (see V5 record).", N),
    ("DESIGN_REVIEW_REQUIRED: 4 modules stagnate above 420 K; Stage 5 optimum at the flow bound and g_ratio -> 1.", N),
]
for i, (t, f) in enumerate(lines, 1):
    ws.cell(row=i, column=1, value=t).font = f
widths(ws, [120])

# ---------------------------------------------------------------- dataset (exact copy)
wd = wb.create_sheet("Dataset_rev4.2")
header(wd, 1, list(ds.columns))
raw = pd.read_csv(CSV, dtype=str, keep_default_na=False)   # exact text, to keep ints/strings as in CSV
for i, row in enumerate(raw.itertuples(index=False), 2):
    for j, v in enumerate(row, 1):
        if v == "":
            val = None
        else:
            try:
                val = int(v) if v.lstrip("-").isdigit() else float(v)
            except ValueError:
                val = v
        c = wd.cell(row=i, column=j, value=val)
        c.font = N
        if val is not None and not isinstance(val, str):
            EXACT.setdefault(wd.title, {})[c.coordinate] = v   # the CSV text itself
wd.freeze_panes = "B2"
for j in range(1, len(ds.columns) + 1):
    wd.column_dimensions[get_column_letter(j)].width = 14

# ---------------------------------------------------------------- Stage 3
w3 = wb.create_sheet("Stage3_ANN")
w3["A1"] = "Stage 3 - ANN surrogate (10-seed MLP ensemble) vs GPR and linear baseline"; w3["A1"].font = T
w3["A2"] = "Train %d cases / test %d held-out cases; inputs: %s" % (s3["n_train"], s3["n_test"], ", ".join(s3["inputs"]))
w3["A2"].font = NOTE
cols = ["Target", "ANN ensemble test R2", "Single-ANN test R2 min", "Single-ANN test R2 max",
        "ANN test MAPE (%)", "ANN test RMSE", "GPR test R2", "Linear test R2", "Best hidden layers", "Source file"]
header(w3, 4, cols)
r = 5
for k, v in s3["targets"].items():
    put(w3, r, 1, k)
    put(w3, r, 2, v["ann_ensemble_test"]["R2"], BLUE, "0.00000")
    put(w3, r, 3, v["ann_single_test_R2_range"][0], BLUE, "0.00000")
    put(w3, r, 4, v["ann_single_test_R2_range"][1], BLUE, "0.00000")
    put(w3, r, 5, v.get("ann_ensemble_test_MAPE_pct"), BLUE, "0.000")
    put(w3, r, 6, v["ann_ensemble_test"]["RMSE"], BLUE, "0.00000")
    put(w3, r, 7, v["gpr_test"]["R2"], BLUE, "0.00000")
    put(w3, r, 8, v["linear_test"]["R2"], BLUE, "0.0000")
    put(w3, r, 9, str(v["best_architecture"]))
    put(w3, r, 10, P["s3"], NOTE)
    r += 1
S3_ETA_ROW = 5
r += 1
w3.cell(row=r, column=1, value="SHAP mean |SHAP| on the test set (efficiency eta), ranked").font = Font(name=F, bold=True)
r += 1
header(w3, r, ["Rank", "Input", "mean |SHAP| (eta)", "Source file"])
SHAP0 = r + 1
for i, (k, v) in enumerate(sorted(s3["shap_mean_abs_test"]["eta"].items(), key=lambda t: -t[1]), 1):
    r += 1
    put(w3, r, 1, i); put(w3, r, 2, k); put(w3, r, 3, v, BLUE, "0.000000"); put(w3, r, 4, P["s3"], NOTE)
widths(w3, [16, 20, 20, 20, 16, 14, 14, 14, 18, 52])

# ---------------------------------------------------------------- Stage 5
w5 = wb.create_sheet("Stage5_NSGA2")
w5["A1"] = "Stage 5 - NSGA-II optimum points re-run in GRAIL-CHT (surrogate vs full model)"; w5["A1"].font = T
cols = list(s5.columns) + ["|eta err| (points)", "|plate std err| (%)", "Source file"]
header(w5, 3, cols)
for i, row in enumerate(s5.itertuples(index=False), 4):
    for j, v in enumerate(row, 1):
        v = v.item() if hasattr(v, "item") else v
        put(w5, i, j, v, BLUE if isinstance(v, float) else N, "0.0000" if isinstance(v, float) else None)
    ce = get_column_letter(cols.index("eta_err_pp") + 1)
    cs = get_column_letter(cols.index("std_err_pct") + 1)
    put(w5, i, len(s5.columns) + 1, "=ABS(%s%d)" % (ce, i), BLACK, "0.000")
    put(w5, i, len(s5.columns) + 2, "=ABS(%s%d)" % (cs, i), BLACK, "0.000")
    put(w5, i, len(s5.columns) + 3, P["s5"], NOTE)
last = 3 + len(s5)
ea, sa = get_column_letter(len(s5.columns) + 1), get_column_letter(len(s5.columns) + 2)
w5.cell(row=last + 2, column=1, value="Largest |eta error| (points)").font = Font(name=F, bold=True)
put(w5, last + 2, 2, "=MAX(%s4:%s%d)" % (ea, ea, last), BLACK, "0.000")
w5.cell(row=last + 3, column=1, value="Largest |plate std error| (%)").font = Font(name=F, bold=True)
put(w5, last + 3, 2, "=MAX(%s4:%s%d)" % (sa, sa, last), BLACK, "0.00")
S5_ETA, S5_STD = "B%d" % (last + 2), "B%d" % (last + 3)
w5.cell(row=last + 5, column=1, value="DESIGN_REVIEW_REQUIRED: the optimum sits at the flow upper bound and at g_ratio -> 1.0.").font = NOTE
widths(w5, [14, 11] + [11] * (len(s5.columns) - 2) + [14, 14, 52])

# ---------------------------------------------------------------- Stage 6
w6 = wb.create_sheet("Stage6_Correlations")
w6["A1"] = "Stage 6 - ISO 9806 steady-state efficiency, q = eta0 G - a1 dT - a2 dT^2 (dT = Tm - Ta)"; w6["A1"].font = T
header(w6, 3, ["Quantity", "Alternating", "Parallel", "Unit", "Source file"])
rows6 = [("eta0", "eta0", "-", "0.0000"), ("a1", "a1_W_m2K", "W/m2K", "0.000"), ("a2", "a2_W_m2K2", "W/m2K2", "0.00000"),
         ("Fit RMS error", "fit_rms_pp", "points", "0.000"), ("Fit max error", "fit_max_pp", "points", "0.000")]
for i, (lab, key, u, fmt) in enumerate(rows6, 4):
    put(w6, i, 1, lab); put(w6, i, 2, s6["alternating"][key], BLUE, fmt); put(w6, i, 3, s6["parallel"][key], BLUE, fmt)
    put(w6, i, 4, u); put(w6, i, 5, P["s6"], NOTE)
i = 4 + len(rows6)
put(w6, i, 1, "a2 constraint"); put(w6, i, 2, s6["alternating"]["a2_constraint"]); put(w6, i, 3, s6["parallel"]["a2_constraint"])
put(w6, i, 4, ""); put(w6, i, 5, P["s6"], NOTE)
i += 1
put(w6, i, 1, "Unconstrained a2 (parallel)"); put(w6, i, 2, None); put(w6, i, 3, s6["parallel"]["unconstrained_fit"]["a2"], BLUE, "0.00000")
put(w6, i, 4, "W/m2K2"); put(w6, i, 5, "negative (unphysical), so refitted with a2 = 0; both fits on record", NOTE)
S6 = {"eta0": 4, "a1": 5}
i += 2
w6.cell(row=i, column=1, value="Held-out GRAIL-CHT points (not used in the fit)").font = Font(name=F, bold=True)
i += 1
hk = list(s6["alternating"]["holdout"][0].keys())
header(w6, i, ["Arrangement"] + hk + ["|error| (points)", "Source file"])
h0 = i + 1
for arr in ("alternating", "parallel"):
    for h in s6[arr]["holdout"]:
        i += 1
        put(w6, i, 1, arr)
        for j, k in enumerate(hk, 2):
            put(w6, i, j, h[k], BLUE, "0.0000" if isinstance(h[k], float) else None)
        ec = get_column_letter(1 + len(hk))
        put(w6, i, len(hk) + 2, "=ABS(%s%d)" % (ec, i), BLACK, "0.000")
        put(w6, i, len(hk) + 3, P["s6"], NOTE)
ac = get_column_letter(len(hk) + 2)
i += 2
w6.cell(row=i, column=1, value="Largest held-out error (points)").font = Font(name=F, bold=True)
put(w6, i, 2, "=MAX(%s%d:%s%d)" % (ac, h0, ac, i - 2), BLACK, "0.000")
S6_HOLD = "B%d" % i
i += 1
w6.cell(row=i, column=1, value="Fit based on 22 GRAIL-CHT runs (G 500/900 W/m2 x 4 inlet temperatures, both arrangements) plus these held-out points.").font = NOTE
widths(w6, [30, 14, 14, 12, 12, 12, 12, 12, 16, 52])

# ---------------------------------------------------------------- Stage 7
w7 = wb.create_sheet("Stage7_Annual")
w7["A1"] = "Stage 7 - Annual performance, Berhampur (PVGIS TMY 2005-2023, tilt 19.3 deg S, Hay-Davies)"; w7["A1"].font = T
header(w7, 3, ["Quantity", "Value", "Unit", "Source file"])
wx = s7["weather"]
rows7 = [("Global horizontal irradiation (GHI)", wx["GHI_kWh_m2"], "kWh/m2/yr", P["s7"]),
         ("Plane-of-array irradiation (POA)", wx["POA_kWh_m2"], "kWh/m2/yr", P["s7"]),
         ("POA after incidence-angle losses", wx["POA_eff_after_IAM_kWh_m2"], "kWh/m2/yr", P["s7"]),
         ("Collector yield, 40 C (313.15 K) inlet - parallel", s7["parallel"]["collector_only_Tin_313_K"]["kWh_m2_yr"], "kWh/m2/yr", P["s7"]),
         ("Collector yield, 40 C (313.15 K) inlet - alternating", s7["alternating"]["collector_only_Tin_313_K"]["kWh_m2_yr"], "kWh/m2/yr", P["s7"]),
         ("Collector yield, 60 C (333.15 K) inlet - parallel", s7["parallel"]["collector_only_Tin_333_K"]["kWh_m2_yr"], "kWh/m2/yr", P["s7"]),
         ("Collector yield, 60 C (333.15 K) inlet - alternating", s7["alternating"]["collector_only_Tin_333_K"]["kWh_m2_yr"], "kWh/m2/yr", P["s7"])]
for i, (a, b, c, d) in enumerate(rows7, 4):
    put(w7, i, 1, a); put(w7, i, 2, b, BLUE, "#,##0.0"); put(w7, i, 3, c); put(w7, i, 4, d, NOTE)
S7_POA, S7_YP, S7_YA = "B5", "B7", "B8"
i = 4 + len(rows7) + 1
w7.cell(row=i, column=1, value="Weather cross-check at 35 deg tilt against the PVGIS PV report (PVGIS-ERA5)").font = Font(name=F, bold=True)
i += 1
header(w7, i, ["Month", "PVGIS H(i)_m (kWh/m2)", "", "Source file"])
pv = [l.split() for l in open(PVG).read().splitlines()[10:22]]
m0 = i + 1
for mrow in pv:
    i += 1
    put(w7, i, 1, int(mrow[0])); put(w7, i, 2, float(mrow[4]), BLUE, "0.00"); put(w7, i, 4, P["pv"], NOTE)
i += 1
put(w7, i, 1, "PVGIS year (sum)"); put(w7, i, 2, "=SUM(B%d:B%d)" % (m0, i - 1), BLACK, "#,##0.0"); put(w7, i, 3, "kWh/m2/yr")
pvs = i
i += 1
put(w7, i, 1, "This model at 35 deg"); put(w7, i, 2, 1935.5, BLUE, "#,##0.0"); put(w7, i, 3, "kWh/m2/yr"); put(w7, i, 4, P["wc"] + " (tilt 35 line)", NOTE)
i += 1
put(w7, i, 1, "Difference"); put(w7, i, 2, "=B%d/B%d-1" % (i - 1, pvs), BLACK, "0.0%")
S7_PVDIFF = "B%d" % i
i += 2
w7.cell(row=i, column=1, value="SDHW sizing sweep: 100 L/day delivered at 45 C (318.15 K)").font = Font(name=F, bold=True)
i += 1
header(w7, i, list(sw.columns) + ["Source file"])
sw0 = i + 1
for row in sw.itertuples(index=False):
    i += 1
    for j, v in enumerate(row, 1):
        v = v.item() if hasattr(v, "item") else v
        put(w7, i, j, v, BLUE if isinstance(v, (int, float)) and j > 1 else N,
            "0.000" if isinstance(v, float) else None)
    put(w7, i, len(sw.columns) + 1, P["sw"], NOTE)
sw_rows = {(r_.arrangement, int(r_.n_modules)): sw0 + k for k, r_ in enumerate(sw.itertuples(index=False))}
col = {c: get_column_letter(k + 1) for k, c in enumerate(sw.columns)}
i += 2
w7.cell(row=i, column=1, value="DESIGN_REVIEW_REQUIRED: with 4 modules the collector stagnates above 420 K (max_collector_K).").font = NOTE
widths(w7, [48, 16, 12, 16] + [13] * (len(sw.columns) - 3) + [44])

# ---------------------------------------------------------------- Economics
we = wb.create_sheet("Economics")
we["A1"] = "Economics - 2-module system (1.056 m2), 100 L/day at 45 C, Berhampur"; we["A1"].font = T
header(we, 3, ["Input", "Value", "Unit", "Basis / source"])
eco = s7["economics_inputs"]
ins = [("Electricity tariff", eco["tariff_Rs_kWh"], "Rs/kWh", eco["tariff_basis"]),
       ("Electric geyser efficiency", s7["assumptions"]["geyser_efficiency"], "-", P["s7"]),
       ("Capex fixed part", 12000, "Rs", "ENGINEERING_ASSUMPTION (Stage 7 sizing sweep)"),
       ("Capex per module", 4500, "Rs/module", "ENGINEERING_ASSUMPTION (Stage 7 sizing sweep)"),
       ("Modules", 2, "-", "best size from the sizing sweep"),
       ("Life", eco["life_yr"], "yr", P["s7"]),
       ("Discount rate", eco["discount"], "-", P["s7"]),
       ("O&M per year (fraction of capex)", eco["om_frac_per_yr"], "-", P["s7"])]
for i, (a, b, c, d) in enumerate(ins, 4):
    put(we, i, 1, a); put(we, i, 2, b, BLUE, "0.00" if isinstance(b, float) else None); put(we, i, 3, c); put(we, i, 4, d, NOTE)
i = 4 + len(ins) + 1
put(we, i, 1, "Capex (formula)"); put(we, i, 2, "=B6+B7*B8", BLACK, "#,##0"); put(we, i, 3, "Rs")
put(we, i, 4, "12,000 + 4,500 per module; checked against capex_Rs in the sizing sweep below", NOTE)
capex_row = i
i += 1
put(we, i, 1, "Capex check vs sizing sweep"); put(we, i, 2, "=IF(B%d='Stage7_Annual'!%s%d,\"OK\",\"MISMATCH\")" % (capex_row, col["capex_Rs"], sw_rows[("parallel", 2)]), BLACK)
i += 1
put(we, i, 1, "Cost of heat from an electric geyser"); put(we, i, 2, "=B4/B5", BLACK, "0.00"); put(we, i, 3, "Rs/kWh"); put(we, i, 4, "tariff / geyser efficiency", NOTE)
geyser = "B%d" % i
i += 2
header(we, i, ["Result (2 modules)", "Parallel", "Alternating", "Unit"])
res = [("Solar fraction", "solar_fraction", "0.0%", "-"), ("Solar heat delivered", "Q_solar_kWh", "#,##0.0", "kWh/yr"),
       ("Cost of solar heat (LCOH)", "LCOH_Rs_kWh", "0.00", "Rs/kWh"), ("Simple payback", "simple_payback_yr", "0.0", "yr"),
       ("Discounted payback", "discounted_payback_yr", "0", "yr"), ("Net saving per year", "net_saving_Rs", "#,##0", "Rs/yr"),
       ("NPV over life", "NPV_Rs", "#,##0", "Rs")]
e0 = i + 1
for k, (lab, c, fmt, u) in enumerate(res):
    i += 1
    put(we, i, 1, lab)
    put(we, i, 2, "='Stage7_Annual'!%s%d" % (col[c], sw_rows[("parallel", 2)]), GREEN, fmt)
    put(we, i, 3, "='Stage7_Annual'!%s%d" % (col[c], sw_rows[("alternating", 2)]), GREEN, fmt)
    put(we, i, 4, u)
E = {c: e0 + k for k, (_, c, _, _) in enumerate(res)}
i += 1
put(we, i, 1, "Solar heat cheaper than the geyser?")
put(we, i, 2, "=IF(B%d<%s,\"yes\",\"no\")" % (E["LCOH_Rs_kWh"], geyser), BLACK)
put(we, i, 3, "=IF(C%d<%s,\"yes\",\"no\")" % (E["LCOH_Rs_kWh"], geyser), BLACK)
widths(we, [40, 16, 16, 12, 70])

# ---------------------------------------------------------------- Summary
wsum = wb.create_sheet("Summary", 1)
wsum["A1"] = "GRAIL Stages 3-7 - headline results (every number links to its detail sheet)"; wsum["A1"].font = T
header(wsum, 3, ["Stage", "Result", "Value", "Unit", "How it was checked"])
rows = [
    ("3. ANN surrogate", "Mean absolute % error in efficiency (60 held-out cases)", "='Stage3_ANN'!E%d" % S3_ETA_ROW, "0.000", "%",
     "60 cases never seen in training; GPR slightly more accurate (Stage3_ANN)"),
    ("3. ANN surrogate", "Efficiency test R2, single ANNs - lowest", "='Stage3_ANN'!C%d" % S3_ETA_ROW, "0.0000", "-", ""),
    ("3. ANN surrogate", "Efficiency test R2, single ANNs - highest", "='Stage3_ANN'!D%d" % S3_ETA_ROW, "0.0000", "-", ""),
    ("3. ANN surrogate", "GPR efficiency test R2", "='Stage3_ANN'!G%d" % S3_ETA_ROW, "0.0000", "-", "stated in the report"),
    ("3. ANN surrogate", "SHAP rank 1-4 for efficiency", "='Stage3_ANN'!B%d&\", \"&'Stage3_ANN'!B%d&\", \"&'Stage3_ANN'!B%d&\", \"&'Stage3_ANN'!B%d" % (SHAP0, SHAP0 + 1, SHAP0 + 2, SHAP0 + 3), None, "-", "f_interdig = arrangement"),
    ("5. NSGA-II", "Largest efficiency error of 8 designs re-run in GRAIL-CHT", "='Stage5_NSGA2'!%s" % S5_ETA, "0.000", "points", "full GRAIL-CHT re-run"),
    ("5. NSGA-II", "Largest plate-spread (std) error of the same 8 designs", "='Stage5_NSGA2'!%s" % S5_STD, "0.00", "%", ""),
    ("6. System model", "eta0 alternating", "='Stage6_Correlations'!B4", "0.000", "-", "22 GRAIL-CHT runs"),
    ("6. System model", "a1 alternating", "='Stage6_Correlations'!B5", "0.00", "W/m2K", ""),
    ("6. System model", "eta0 parallel", "='Stage6_Correlations'!C4", "0.000", "-", ""),
    ("6. System model", "a1 parallel", "='Stage6_Correlations'!C5", "0.00", "W/m2K", ""),
    ("6. System model", "Largest error at points left out of the fit", "='Stage6_Correlations'!%s" % S6_HOLD, "0.00", "points", "tank energy balance closes (1e-12 kWh)"),
    ("7. Annual, Berhampur", "Sunlight on the collector (POA)", "='Stage7_Annual'!%s" % S7_POA, "#,##0", "kWh/m2/yr", ""),
    ("7. Annual, Berhampur", "Yield at 40 C inlet - parallel", "='Stage7_Annual'!%s" % S7_YP, "#,##0", "kWh/m2/yr", ""),
    ("7. Annual, Berhampur", "Yield at 40 C inlet - alternating", "='Stage7_Annual'!%s" % S7_YA, "#,##0", "kWh/m2/yr", ""),
    ("7. Annual, Berhampur", "Weather processing vs PVGIS PV report (35 deg)", "='Stage7_Annual'!%s" % S7_PVDIFF, "0.0%", "-", "independent PVGIS report"),
    ("7. Economics", "Best size for 100 L/day at 45 C", "='Economics'!B8", "0", "modules", "sizing sweep 1-4 modules"),
    ("7. Economics", "Solar fraction - parallel", "='Economics'!B%d" % E["solar_fraction"], "0.0%", "-", ""),
    ("7. Economics", "Solar fraction - alternating", "='Economics'!C%d" % E["solar_fraction"], "0.0%", "-", ""),
    ("7. Economics", "Cost of solar heat - parallel", "='Economics'!B%d" % E["LCOH_Rs_kWh"], "0.00", "Rs/kWh", ""),
    ("7. Economics", "Cost of solar heat - alternating", "='Economics'!C%d" % E["LCOH_Rs_kWh"], "0.00", "Rs/kWh", ""),
    ("7. Economics", "Cost of heat from an electric geyser", "='Economics'!%s" % geyser, "0.00", "Rs/kWh", "tariff / 0.95"),
    ("7. Economics", "Simple payback - parallel", "='Economics'!B%d" % E["simple_payback_yr"], "0.0", "yr", ""),
    ("7. Economics", "Simple payback - alternating", "='Economics'!C%d" % E["simple_payback_yr"], "0.0", "yr", ""),
    ("7. Economics", "Tariff (TPSODL domestic, FY 2026-27)", "='Economics'!B4", "0.00", "Rs/kWh", "unchanged from FY 2025-26"),
]
for i, (a, b, f, fmt, u, n) in enumerate(rows, 4):
    put(wsum, i, 1, a); put(wsum, i, 2, b); put(wsum, i, 3, f, GREEN, fmt); put(wsum, i, 4, u); put(wsum, i, 5, n, NOTE)
widths(wsum, [22, 58, 30, 12, 50])

import os
os.makedirs(os.path.dirname(OUT), exist_ok=True)
wb.save(OUT)
json.dump(EXACT, open(OUT + ".exact.json", "w"))
print("saved", OUT)
