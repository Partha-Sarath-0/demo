// GRAIL Collector - Stages 3, 5, 6, 7 report (ANN surrogate, NSGA-II, system model, annual/techno-economic)
const C = require("./common");
const { p, h, table, tableCaption, bullets, calloutBox, spacer, buildDoc, write, figure,
        Paragraph, TextRun, AlignmentType, TableOfContents } = C;
const { Paragraph: P_, HeadingLevel: HL_ } = require("docx");
const fs = require("fs");
const h1 = (t) => new P_({ text: t, heading: HL_.HEADING_1, pageBreakBefore: true, spacing: { before: 0, after: 160 } });
const R = "/home/claude/grail_cfd/";
const J = (f) => JSON.parse(fs.readFileSync(R + f));
const s3 = J("21_surrogate/stage3_report.json");
const s6 = J("22_system/efficiency_correlations.json");
const s7 = J("20_annual/stage7_results.json");
const F = R + "24_figures_stage3to7/";
const f3 = (x, d = 3) => Number(x).toFixed(d);
const csv = (f) => { const L = fs.readFileSync(R + f, "utf8").trim().split("\n"); const H = L[0].split(",");
  return L.slice(1).map((l) => { const v = l.split(","); const o = {}; H.forEach((k, i) => (o[k] = v[i])); return o; }); };
const ver = csv("23_optimisation/verification_vs_GRAIL-CHT.csv");
const sel = csv("23_optimisation/selected_points_surrogate.csv");
const sw = csv("20_annual/sizing_sweep.csv");

const title = [
  spacer(2200),
  new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text: "THE GRAIL COLLECTOR", bold: true, size: 44, color: "1B4F7A" })], spacing: { after: 80 } }),
  new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text: "Stages 3, 5, 6 and 7", size: 32 })], spacing: { after: 60 } }),
  new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text: "ANN surrogate · NSGA-II optimisation · System model · Annual and techno-economic analysis, Berhampur (Odisha)", italics: true, size: 21, color: "4A4D52" })], spacing: { after: 400 } }),
  table([
    ["Item", "Value"],
    ["Input dataset", "GRAIL_CFD_dataset_FINAL_rev4.2.csv (read-only, md5 " + s3.dataset_md5.slice(0, 8) + "…)"],
    ["Solver used for checks", "GRAIL-CHT, Rev 4.2 settings, Richardson 2f(220) − f(110)"],
    ["Weather", "PVGIS TMY 19.313 N 84.810 E, 2005–2023, 8760 h (md5 63855e6f…)"],
    ["Tariff", "TPSODL LT domestic, 470 paise/kWh (51–200 kWh slab), FY 2025-26, retained FY 2026-27"],
    ["Stage 4 (topology optimisation)", "Removed from scope (future work)"],
    ["Experimental validation", "None claimed. All results are model results"],
  ], [3.2, 6.8]),
];
const toc = [h1("Contents"), new TableOfContents("Contents", { hyperlink: true, headingStyleRange: "1-2" })];

const summary = [
  h1("1. Summary"),
  table([
    ["Stage", "Result"],
    ["3 ANN surrogate", "Test R² 0.9994–0.9998 on 60 unseen cases (η MAPE 0.14 %). GPR slightly better (R² ≥ 0.9999); ANN kept as the roadmap model, GPR reported as the check"],
    ["5 NSGA-II", "Fronts for both arrangements. All 8 selected points re-run in GRAIL-CHT: η error ≤ 0.13 points, std ≤ 2.4 %, Δp ≤ 5.8 %. Parallel dominates on efficiency; alternating reaches the lowest plate std (2.83 K) at the top flow"],
    ["6 System model", "η0 " + f3(s6.alternating.eta0) + " / a1 " + f3(s6.alternating.a1_W_m2K, 2) + " W/m²K (alternating); η0 " + f3(s6.parallel.eta0) + " / a1 " + f3(s6.parallel.a1_W_m2K, 2) + " W/m²K (parallel). Fit error ≤ 0.23 points RMS; held-out points ≤ 0.24 points"],
    ["7 Annual, Berhampur", "Collector yield at 40 °C inlet: " + f3(s7.parallel.collector_only_Tin_313_K.kWh_m2_yr, 0) + " kWh/m²/yr parallel, " + f3(s7.alternating.collector_only_Tin_313_K.kWh_m2_yr, 0) + " alternating (−6.3 %)"],
    ["7 Techno-economic", "Best size for 100 L/day: 2 modules (1.06 m²). Solar fraction 86 % / 83 %, cost of solar heat Rs 4.34 / 4.49 per kWh vs Rs 4.95 for an electric geyser, simple payback about 7.4 / 7.6 years (parallel / alternating)"],
  ], [2.4, 7.6]),
  spacer(),
  calloutBox("Findings that the thesis must state as they are", [
    "1. Efficiency: parallel flow beats alternating in every stage — the dataset (−7.3 %), the Pareto fronts, the fitted curves and the annual yield (−6.3 %). Alternating only wins on plate uniformity at high flow, as Rev 4.1 found.",
    "2. Converging channels: the optimiser pushes the grading ratio to its upper bound, 1.0 (a straight channel), and SHAP gives the grading inputs almost no effect on efficiency. Within the studied range, converging the channels does not raise efficiency; it raises pressure drop. DESIGN_REVIEW_REQUIRED for any claim that convergence improves thermal performance.",
    "3. Pumping power in the channels is below 0.1 mW at every point, so it is not a real objective. Manifold and pump losses dominate in practice, and they are not modelled (manifold dimensions are still ENGINEERING_ASSUMPTION).",
    "4. Optimum efficiency lies on the upper flow bound (4.5 g/s). The optimisation cannot say what happens beyond the sampled range.",
    "5. Stagnation: with 4 modules the collector node reaches 427–442 K (154–168 °C) for up to 486 h/yr, outside the fitted range and probably above the TIM and PCM material limits. DESIGN_REVIEW_REQUIRED (overheat protection or smaller array). With the recommended 2 modules the maximum is 349–353 K.",
  ]),
];

const st3 = [
  h1("2. Stage 3 — ANN surrogate"),
  h("2.1 Method", 2),
  ...bullets([
    "Inputs (9, sampled model inputs only, no derived columns): G_T, T_in, T_amb, wind, total mass flow, bridge width, grading ratio, grading exponent, arrangement flag.",
    "Targets: η, plate std, ln(Δp), mean plate temperature.",
    "Split: 240 training / 60 test cases, stratified by arrangement, seed 42. The test set was not used in any tuning step.",
    "Tuning: 5-fold cross-validated grid over 6 architectures × 5 L2 penalties; tanh activation, L-BFGS training, standardised inputs and targets.",
    "Final model: 10-member ensemble of the tuned network (different seeds); the ensemble spread is kept as an uncertainty indicator.",
    "Baselines on the same split: linear regression and Gaussian-process regression.",
  ]),
  h("2.2 Results", 2),
  table([["Target", "Architecture, α", "CV R²", "ANN test R²", "ANN MAPE %", "GPR test R²", "Linear test R²"]].concat(
    Object.entries(s3.targets).map(([k, v]) => [k, "[" + v.best_architecture.join(", ") + "], " + v.best_alpha, f3(v.cv_R2_mean, 4),
      f3(v.ann_ensemble_test.R2, 4), f3(v.ann_ensemble_test_MAPE_pct, 2), f3(v.gpr_test.R2, 4), f3(v.linear_test.R2, 4)])),
    [1.8, 1.7, 1.0, 1.2, 1.1, 1.2, 1.2]),
  tableCaption("Table 1. Surrogate accuracy on the 60-case hold-out set"),
  p("The linear model reaches only R² 0.85–0.97, so the response is clearly non-linear; the ANN captures it. The GPR is marginally more accurate on this smooth 300-case dataset. Both are far inside the solver's own numerical uncertainty, so the choice does not change any conclusion."),
  ...figure(F + "F15_ann_parity.png", "Figure 15. Parity plots, test set", 1.0),
  h("2.3 SHAP", 2),
  p("Mean |SHAP| on the test set. Efficiency is driven by T_in, T_amb, flow and arrangement. The three geometric inputs (bridge, grading ratio, grading exponent) are two orders of magnitude weaker. Plate uniformity is driven by flow and irradiance. Pressure drop is driven by grading ratio and flow — the only place where the converging geometry matters strongly."),
  ...figure(F + "F16_shap_importance.png", "Figure 16. SHAP importance", 1.0),
];

const st5 = [
  h1("3. Stage 5 — NSGA-II optimisation"),
  ...bullets([
    "Variables inside the campaign bounds: flow 1.0–4.5 g/s, bridge 20–37 mm, grading ratio 0.35–1.0, grading exponent 0.5–2.0. Each arrangement was optimised separately and the fronts were merged.",
    "Reference point (ENGINEERING_ASSUMPTION, Berhampur clear-sky noon): G 800 W/m², T_in 313.15 K, T_amb 303.15 K, wind 3 m/s.",
    "Objectives: maximise η, minimise plate std, minimise pumping power. Population 200, 250 generations, seed 7.",
  ]),
  ...figure(F + "F17_pareto.png", "Figure 17. Pareto fronts", 1.0),
  table([["Arrangement", "Pick", "Flow g/s", "Bridge mm", "Grading ratio", "Exponent", "η ANN", "η GRAIL-CHT", "std ANN K", "std CHT K", "Δp error %"]].concat(
    ver.map((v, i) => [v.arrangement, v.pick, f3(sel[i].mdot_total_kg_s * 1000, 2), f3(sel[i].bridge_mm, 1), f3(sel[i].g_ratio, 3), f3(sel[i].lambda_G, 2),
      f3(v.eta_ann, 4), f3(v.eta_cht, 4), f3(v.std_ann, 2), f3(v.std_cht, 2), f3(v.dp_err_pct, 1)])),
    [1.1, 0.8, 0.7, 0.8, 0.8, 0.8, 0.8, 1.0, 0.8, 0.8, 0.8]),
  tableCaption("Table 2. Selected points re-run with GRAIL-CHT (all converged, energy error < 0.5 %)"),
  p("Every selected point was re-run with the solver; the surrogate holds to 0.13 efficiency points. The as-built design sits almost on each front. Moving it along the front is mainly a matter of flow: more flow gives higher efficiency and a flatter plate."),
];

const st6 = [
  h1("4. Stage 6 — System model"),
  h("4.1 Efficiency correlations (virtual steady-state test)", 2),
  p("The as-built geometry (bridge 31.29 mm, G 0.539935, λ 1.0) at the design flow of 2.75 g/s was run in GRAIL-CHT at 22 points: G ∈ {500, 900} W/m² × T_in ∈ {293, 308, 323, 332} K for the fit, and 3 held-out points (wind 0.5 and 4.9 m/s, T_amb 288 K). The ISO 9806 steady form was fitted on the mean fluid temperature."),
  table([["Arrangement", "η0", "a1 W/m²K", "a2 W/m²K²", "Fit RMS (points)", "Held-out errors (points)", "Wind 0.5 → 4.9 m/s"]].concat(
    ["alternating", "parallel"].map((a) => [a, f3(s6[a].eta0, 4), f3(s6[a].a1_W_m2K, 3), f3(s6[a].a2_W_m2K2, 5), f3(s6[a].fit_rms_pp, 2),
      s6[a].holdout.map((x) => f3(x.err_pp, 2)).join(", "), Object.values(s6[a].wind_sensitivity_eta).map((x) => f3(x, 4)).join(" → ")])),
    [1.2, 0.8, 1.0, 1.0, 1.1, 1.8, 2.1]),
  tableCaption("Table 3. Collector efficiency correlations (aperture 0.528 m², incident irradiance)"),
  p("Parallel's unconstrained a2 was slightly negative (−0.0006), which is unphysical. It was refitted with a2 = 0; both fits are on record. The heat-loss coefficient a1 ≈ 2 W/m²K is very low because of the TIM, PCM and VIP stack. η0 ≈ 0.60–0.64 is set mainly by the optical factor 0.6489. Wind changes efficiency by less than 0.3 points, so no wind term was fitted. The fit covers Tm − Ta from −3 to 40 K."),
  ...figure(F + "F18_efficiency_curves.png", "Figure 18. Efficiency curves", 0.62),
  h("4.2 Dynamic collector and tank model", 2),
  ...bullets([
    "Collector: one thermal node in the ISO 9806 quasi-dynamic form. Effective capacity 33.5 kJ/m²K from the stack masses (PCM counted as sensible heat only — PCM latent heat is deferred).",
    "Incidence angle modifier: Kb = 1 − 0.10(1/cos θ − 1), diffuse 0.90 (ENGINEERING_ASSUMPTION; the solver has no angular optics).",
    "Tank: 100 kg, fully mixed, UA 1.5 W/K. Pump control: on at ΔT > 7 K, off below 2 K, off above 358 K. 60 s step. The tank first law closes to 0.000 kWh/yr.",
    "Load: 100 L/day delivered at 318.15 K through a mixing valve, drawn 40/20/40 % morning/noon/evening; mains water at the 24 h mean ambient temperature; electric top-up at 95 % efficiency.",
  ]),
];

const st7 = [
  h1("5. Stage 7 — Annual and techno-economic analysis, Berhampur"),
  h("5.1 Weather processing", 2),
  ...bullets([
    "The time alignment was tested, not assumed: GHI = DNI cos z + DHI closes to 0.17 W/m² when the solar position is taken at the stated UTC timestamp, against 14.3 W/m² with a half-hour shift.",
    "Plane of array: 19.3° tilt, facing south, Hay-Davies, albedo 0.2 → " + f3(s7.weather.POA_kWh_m2, 0) + " kWh/m²/yr. Isotropic model 1955, Perez 2001; tilts between 15° and 25° are within 0.5 %.",
    "Cross-check: at 35° tilt the result is 1935 kWh/m²/yr, against 1965 in the PVGIS PV report you downloaded (a different database) — 1.5 % apart.",
  ]),
  table([["Arrangement", "Yield at 40 °C inlet (kWh/m²/yr)", "Yield at 60 °C inlet", "Annual efficiency on POA at 40 °C"]].concat(
    ["parallel", "alternating"].map((a) => [a, f3(s7[a].collector_only_Tin_313_K.kWh_m2_yr, 0), f3(s7[a].collector_only_Tin_333_K.kWh_m2_yr, 0),
      f3(s7[a].collector_only_Tin_313_K.annual_eff_on_POA * 100, 1) + " %"])), [2.0, 2.8, 2.0, 3.2]),
  tableCaption("Table 4. Collector-only annual yield at fixed inlet temperature"),
  ...figure(F + "F19_annual_monthly.png", "Figure 19. Monthly yield, sizing and cost of heat", 1.0),
  h("5.2 Household system sizing and economics", 2),
  table([["Arrangement", "Modules", "Area m²", "Solar fraction", "Solar heat kWh/yr", "Max collector K", "Capex Rs", "Payback yr", "NPV Rs", "Cost of heat Rs/kWh"]].concat(
    sw.map((r) => [r.arrangement, r.n_modules, f3(r.aperture_m2, 2), f3(r.solar_fraction * 100, 1) + " %", f3(r.Q_solar_kWh, 0), f3(r.max_collector_K, 0),
      f3(r.capex_Rs, 0), f3(r.simple_payback_yr, 1), f3(r.NPV_Rs, 0), f3(r.LCOH_Rs_kWh, 2)])),
    [1.1, 0.7, 0.7, 0.9, 1.0, 0.9, 0.9, 0.8, 0.9, 1.0]),
  tableCaption("Table 5. Sizing sweep for a 100 L/day household (15 years, 8 % discount rate, 1 % O&M, 15 W pump)"),
  ...bullets([
    "Tariff: TPSODL domestic 470 paise/kWh (51–200 kWh slab), unchanged for FY 2026-27; electricity duty excluded (conservative). At the 570 paise slab, savings rise by 21 %.",
    "Capex: ENGINEERING_ASSUMPTION of Rs 12,000 fixed + Rs 4,500 per module, anchored to market flat-plate systems (Rs 20,000–30,000 for 100 L/day plus Rs 3,000–10,000 installation). The GRAIL prototype cost is unknown; the base case (4 modules) is also run at Rs 22,000 and Rs 45,000 in stage7_results.json.",
    "Two modules minimise the cost of heat. Four modules are oversized: the tank sits at its limit for 533–726 h/yr, 40 % of the collected heat is lost from the tank, and the collector stagnates at high temperature.",
  ]),
];

const assum = [
  h1("6. Assumptions, open items and files"),
  table([["Tag", "Item"],
    ["ENGINEERING_ASSUMPTION", "Tilt 19.3° S; IAM b0 0.10; C_eff 33.5 kJ/m²K; tank 100 kg, UA 1.5 W/K; 100 L/day at 45 °C; draw profile; mains = 24 h mean ambient; pump 15 W; geyser 95 %; capex model; 15 yr, 8 %, 1 % O&M"],
    ["ENGINEERING_ASSUMPTION", "NSGA-II reference operating point; design flow 2.75 g/s for the annual runs"],
    ["DESIGN_REVIEW_REQUIRED", "Converging-channel benefit (not supported for efficiency within the range studied)"],
    ["DESIGN_REVIEW_REQUIRED", "Stagnation temperature against TIM and PCM limits for arrays of 3 or more modules; overheat protection"],
    ["Deferred (your decision)", "PCM latent heat, 3-D radiation and optical model, full 3-D campaign; manifold dimensions"],
    ["Limitation", "Annual results rely on the fitted correlation outside its fitted range only during stagnation hours; wind above 5 m/s (1,605 h) is outside the trained range but has less than 0.3 points of effect"],
  ], [2.6, 7.4]),
  spacer(),
  table([["Folder", "Contents"],
    ["21_surrogate", "ann_surrogate.pkl, stage3_report.json, test parity CSVs, SHAP arrays"],
    ["23_optimisation", "pareto_fronts.csv, selected_points_surrogate.csv, verification_vs_GRAIL-CHT.csv"],
    ["22_system", "virtual_test_matrix.csv, efficiency_correlations.json"],
    ["20_annual", "weather file (unchanged), closure test, stage7_results.json, sizing_sweep.csv, hourly SDHW CSVs, monthly yield"],
    ["24_figures_stage3to7", "F15–F19"],
    ["tools", "stage3_ann.py, stage5_nsga2.py, stage5_verify.py, cht_point.py, stage6_testmatrix.py, stage6_fit.py, stage7_weather.py, stage7_annual.py, stage3to7_figures.py"],
  ], [2.6, 7.4]),
];

const doc = buildDoc({ title: "GRAIL Collector — Stages 3, 5, 6, 7", subtitle: "Surrogate, optimisation, system model, annual and techno-economic analysis",
  sections: [title, [].concat(toc, summary, st3, st5, st6, st7, assum)] });
write(doc, "/home/claude/reports/GRAIL_Stages_3-5-6-7_Report.docx");
