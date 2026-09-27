// GRAIL — Dataset Audit Addendum
const C = require("./common");
const { p, h, table, tableCaption, bullets, numbered, calloutBox, spacer,
        pageBreak, buildDoc, write, Paragraph, TextRun, AlignmentType,
        TableOfContents } = C;

const { Paragraph: P_, HeadingLevel: HL_ } = require("docx");
function h1(text) {
  return new P_({ text, heading: HL_.HEADING_1, pageBreakBefore: true,
    spacing: { before: 0, after: 160 }, keepNext: true });
}
function eq(text) {
  return new Paragraph({
    alignment: AlignmentType.CENTER,
    children: [new TextRun({ text, bold: true, size: 22 })],
    spacing: { before: 140, after: 180, line: 276, lineRule: "auto" },
  });
}

const title = [
  spacer(2600),
  new Paragraph({ alignment: AlignmentType.CENTER,
    children: [new TextRun({ text: "THE GRAIL COLLECTOR", bold: true, size: 44, color: "1B4F7A" })],
    spacing: { after: 80 } }),
  new Paragraph({ alignment: AlignmentType.CENTER,
    children: [new TextRun({ text: "Dataset Audit Addendum", size: 32 })],
    spacing: { after: 300 } }),
  new Paragraph({ alignment: AlignmentType.CENTER,
    children: [new TextRun({ text: "An independent engineering and CFD audit of "
      + "GRAIL_CFD_dataset_rev2.csv, and the eight reporting corrections it requires.",
      italics: true, size: 21, color: "4A4D52" })],
    spacing: { after: 460 } }),
  table([
    ["Item", "Value"],
    ["Dataset audited", "GRAIL_CFD_dataset_rev2.csv, 300 rows x 54 columns"],
    ["Method", "Independent recomputation of every derived column from its inputs"],
    ["Data modified", "NONE — no row deleted, corrected, smoothed or replaced"],
    ["Critical engineering errors found", "0"],
    ["Conservation-law violations found", "0"],
    ["Corrections required", "8, all in reporting and nomenclature"],
    ["Results invalidated", "0"],
  ], [3.4, 6.6], { alignRight: false }),
  spacer(700),
  new Paragraph({ alignment: AlignmentType.CENTER,
    children: [new TextRun({ text: "Companion to the CFD Simulation Report", size: 19,
      color: "4A4D52" })] }),
];

const toc = [
  h1("Contents"),
  new TableOfContents("Contents", { hyperlink: true, headingStyleRange: "1-2" }),
  p("(In Word: right-click the field and choose Update Field.)",
    { run: { italics: true, size: 17, color: "4A4D52" } }),
];

// ---------------------------------------------------------------- 1
const s1 = [
  h1("1. Purpose and method"),
  p("This addendum records an audit of the reported dataset carried out to a single rule: verify "
    + "everything, change nothing. Every derived column was recomputed independently from its own "
    + "inputs and compared against the stored value. No row was deleted, corrected, smoothed, "
    + "replaced or reweighted, and no unusual result was altered because it was unusual."),
  p("The audit found no critical engineering error and no violation of any conservation law. It "
    + "found eight items requiring correction, and every one of them is a correction to how a "
    + "result is DESCRIBED, not to the result itself. This document states each one, gives the "
    + "dataset evidence, and says exactly what changes in the reporting."),

  h("1.1 What was verified exactly", 2),
  p("The following relations were recomputed from first principles across all 300 rows. They are "
    + "not merely plausible — they close to machine precision, which means the dataset is "
    + "algebraically self-consistent."),
  tableCaption("Table 1 — Independent verification of every derived relation."),
  table([
    ["Relation verified", "Maximum error over 300 rows"],
    ["mdot_total / mdot_channel = 12 exactly", "0"],
    ["q″ = G_T x 0.833 x 0.82 x 0.95", "1.1e-13"],
    ["Q_solar = q″ x 0.528 m²  (1.1 x 0.48)", "5.7e-14"],
    ["Q_u = mdot x c_p x dT,  c_p = 4180", "< 1e-6 %"],
    ["dT = T_out − T_in", "1.1e-13"],
    ["Q_solar = Q_u + Q_rad + Q_conv + Q_rear", "1.43e-04 W  =  9.83e-05 %"],
    ["Re = 4 mdot / (pi D_h mu)", "8.0e-13"],
    ["mu(T), Vogel relation", "2.3e-13"],
    ["W_pump = dp x mdot / rho", "9.5e-13"],
    ["D_h,out = D_h,in x G ;  A_out = A_in x G²", "1.4e-14"],
    ["T_sky = 0.0552 T_amb^1.5 ;  h_wind = 5.7 + 3.8 v", "1.7e-13"],
    ["eta = Q_u / (G_T x A)", "2.2e-16"],
  ], [6.4, 3.6]),
  calloutBox("The energy balance is real, not self-referential", [
    "The stored energy_error_pct column was not taken on trust. The balance was recomputed from "
      + "the four component columns Q_u, Q_rad, Q_conv and Q_rear against Q_solar, and the "
      + "recomputation reproduces the stored value to the last digit.",
    "Maximum residual across 300 cases: 1.43e-04 W, which is 9.83e-05 % of the absorbed power.",
    "No conservation law is violated anywhere in the dataset.",
  ]),
  p("Eight physical ordering tests were also applied, with zero violations in 300 rows: "
    + "T_max ≥ T_mean ≥ T_min; P90 ≤ P95 ≤ P99 ≤ T_max; "
    + "spread = max − min; std ≤ spread; mean(T⁴) ≥ mean(T)⁴ "
    + "(Jensen's inequality); T_R4 = R4^0.25; T_out > T_in; and dp > 0.", { before: 140 }),
];

// ---------------------------------------------------------------- 2
const s2 = [
  h1("2. Item 1 — nu_cfd is a fixed closure, not a per-case CFD result"),
  p("Classification: MAJOR METHODOLOGICAL. This is the most important item in the audit."),

  h("2.1 The evidence", 2),
  tableCaption("Table 2 — nu_cfd against the range of conditions it is applied over."),
  table([
    ["Quantity", "Range across the 300 cases"],
    ["nu_cfd", "2.9238 on every row — exactly one distinct value"],
    ["Re, inlet", "29.1 to 200.0"],
    ["Re, outlet", "36.3 to 540.4"],
    ["Prandtl number", "2.41 to 6.84 — a factor of 2.84"],
    ["Mean fluid temperature", "293.3 to 353.0 K"],
    ["Grading ratio G", "0.351 to 0.998"],
  ], [4, 6], { alignRight: false }),
  p("For laminar internal flow, Nu = f(Re, Pr, Gz, section shape). A quantity genuinely extracted "
    + "from each case's own CFD solution could not be constant to five significant figures while "
    + "the Prandtl number alone changes by a factor of 2.84."),

  h("2.2 What it actually is", 2),
  p("The value 2.9238 is the Richardson extrapolation of the three-level 3-D grid study "
    + "(3.7397 at 34,304 cells, 3.4282 at 105,600, 3.2236 at 356,400; observed order p = 1.283, "
    + "GCI 11.63 %). It is a single developed-region constant applied as a closure to every case. "
    + "That is a legitimate modelling choice. Presenting it under a column name that implies "
    + "per-case CFD extraction is not."),

  h("2.3 What changes", 2),
  ...numbered([
    "The column is to be described everywhere as nu_closure — a fixed Nusselt closure taken from "
      + "the resolved 3-D CFD — and never as a per-case CFD output. The CSV column name is left "
      + "unchanged so that existing scripts and figures still run; the data dictionary carries the "
      + "correction.",
    "Every table and figure derived from the campaign must state that a constant Nu is carried.",
    "The cost of the assumption is already quantified and must be quoted alongside the result: "
      + "carrying the measured Nu(xi) profile instead of a constant moves the plate-spread "
      + "difference from −21.09 % to −6.85 % at matched developed-region mean, a shift "
      + "of +14.24 percentage points, which is larger than every numerical and input uncertainty "
      + "in the assessment combined.",
  ]),
  calloutBox("What supports the assumption, from the dataset itself", [
    "The thermal entry length x_fd,t = 0.05 Re Pr D_h was computed for all 300 cases. It ranges "
      + "0.037 to 0.163 m against a channel length of 1.100 m.",
    "In EVERY case the flow is thermally developed over at least 85 % of the channel, and in no "
      + "case does the entry region exceed 15 % of the length.",
    "A developed-region constant is therefore a defensible first approximation on this geometry. "
      + "It is still an approximation, and its cost is the +14.24 pp above.",
  ]),
  p("Verdict on the CFD results: VALID, MODEL-FORM LIMITED. No result is invalidated. The "
    + "uniformity claim must carry the model-form qualifier; the efficiency claim moves by only "
    + "−0.57 pp under the same test and is unaffected.", { before: 140 }),
];

// ---------------------------------------------------------------- 3
const s3 = [
  h1("3. Item 2 — U_L is ill-conditioned in 20 cases, and the campaign statistic is restated"),
  p("Classification: MAJOR, AFFECTS A REPORTED STATISTIC. This item changes a published number."),

  h("3.1 The evidence", 2),
  p("The definition was confirmed against the data to 1.0e-4 relative:"),
  eq("U_L = (Q_rad + Q_conv + Q_rear) / (A × (T_plate,mean − T_amb))"),
  p("The denominator (T_plate,mean − T_amb) spans −8.54 to +88.53 K across the campaign. "
    + "Where it approaches zero, U_L diverges."),
  tableCaption("Table 3 — U_L conditioned on the size of the driving temperature difference."),
  table([
    ["Subset", "Rows", "U_L range (W/m²K)"],
    ["|T_plate,mean − T_amb| < 5 K", "20", "−21.86 to +25.27"],
    ["|T_plate,mean − T_amb| ≥ 5 K", "280", "0.850 to 3.440"],
  ], [5, 1.6, 3.4]),
  p("The 280-row population is tight and physically sensible. The 20-row tail is a small-"
    + "denominator artifact of the definition, not a property of the collector and not a defect "
    + "in the CFD. The five rows with negative U_L all have a negative denominator "
    + "(−1.125 to −0.257 K) with a positive numerator (1.07 to 2.98 W)."),

  h("3.2 The consequence — a reported result is restated", 2),
  p("The CFD Simulation Report quotes a campaign loss-coefficient difference of "
    + "−0.90 ± 22.93 % and marks it NOT DISTINGUISHABLE. That ±23 % band is now "
    + "shown to be dominated by division by a near-zero temperature difference in 20 of 300 rows, "
    + "not by any real uncertainty in the loss coefficient."),
  tableCaption("Table 4 — Delta U_L, alternating minus co-current, against the conditioning threshold."),
  table([
    ["Threshold on |T_plate,mean − T_amb|", "Rows", "co-current", "alternating", "Difference"],
    ["0 K (all rows, as published)", "300", "2.253", "2.232", "−0.94 %"],
    ["≥ 2 K", "291", "2.356", "2.254", "−4.35 %"],
    ["≥ 5 K (recommended)", "280", "2.307", "2.262", "−1.95 %"],
    ["≥ 10 K", "260", "2.303", "2.260", "−1.87 %"],
  ], [3.6, 1.2, 1.7, 1.7, 1.8]),
  calloutBox("The restated result", [
    "On the conditioned subset (280 rows, |T_plate,mean − T_amb| ≥ 5 K):",
    "Delta U_L = −1.95 % ± 2.52 pp (k = 2).",
    "The verdict is unchanged — it still spans zero and is still NOT distinguishable. But the "
      + "expanded band falls from ±22.93 pp to ±2.52 pp, a factor of nine.",
    "The statement therefore strengthens, from 'too noisy to tell' to 'genuinely no measurable "
      + "difference'. That is a better scientific claim, and it costs nothing, because the "
      + "conditioning removes an artifact of the estimator rather than any data.",
  ]),
  p("The 20 excluded rows are NOT deleted from the dataset. They remain in the file, they remain "
    + "valid cases, and every other quantity computed from them (efficiency, useful heat, plate "
    + "statistics, energy balance) is retained and used. Only the U_L statistic, which is "
    + "undefined in that regime, is reported on the conditioned subset — and the threshold is "
    + "stated wherever it is used.", { before: 140 }),
  p("Verdict on the CFD results: VALID. The derived quantity is ill-posed near zero driving "
    + "temperature difference. No case is invalidated."),
];

// ---------------------------------------------------------------- 4
const s4 = [
  h1("4. Item 3 — constant thermal conductivity against temperature-dependent viscosity"),
  p("Classification: MAJOR, PROPERTY-MODEL INCONSISTENCY. This item adds a new term to the "
    + "uncertainty budget."),

  h("4.1 The inconsistency", 2),
  p("Viscosity is carried as a function of temperature through the Vogel relation and varies by a "
    + "factor of 2.84 across the campaign. Thermal conductivity is held fixed at 0.610 W/m·K. "
    + "The two properties belong to the same fluid over the same temperature range, and treating "
    + "one as variable and the other as constant is not defensible without a bound on the effect."),
  tableCaption("Table 5 — The size of the inconsistency."),
  table([
    ["Quantity", "Value"],
    ["Mean fluid temperature across the campaign", "20.2 to 79.8 °C"],
    ["k(T) for liquid water over that range", "0.6021 to 0.6737 W/m·K"],
    ["Value used by the model", "0.610 W/m·K, fixed"],
    ["Resulting error in k", "−1.30 % to +10.44 % (mean +5.02 %)"],
    ["Rows where the error exceeds 5 %", "166 of 300"],
    ["Rows where the error exceeds 8 %", "46 of 300"],
  ], [4.6, 5.4], { alignRight: false }),

  h("4.2 Bounding it without re-running the campaign", 2),
  p("The heat-transfer closure is"),
  eq("h(x) = Nu × k / D_h(x)"),
  p("so an error in k is mathematically identical to the same percentage error in Nu. The study "
    + "already contains a MEASURED sensitivity to Nu, obtained by running the entire campaign "
    + "twice with nothing changed but that one input:"),
  tableCaption("Table 6 — The calibrated sensitivity, from the Rev 1 to Rev 2 recomputation."),
  table([
    ["Quantity", "Value"],
    ["Nu changed from", "3.4282 to 2.9238  (−14.71 %)"],
    ["Delta plate spread changed from", "−12.010 % to −21.093 %  (−9.083 pp)"],
    ["Local slope", "0.6175 pp per 1 % change in Nu, and therefore in k"],
  ], [4.6, 5.4], { alignRight: false }),
  tableCaption("Table 7 — The k(T) term mapped onto the reported result."),
  table([
    ["Error in k", "Effect on Delta plate spread", "Corrected value"],
    ["−1.30 % (coldest cases)", "−0.80 pp", "−21.89 %"],
    ["+5.02 % (campaign mean)", "+3.10 pp", "−17.99 %"],
    ["+10.44 % (hottest cases)", "+6.44 pp", "−14.65 %"],
  ], [3.4, 3.4, 3.2]),
  calloutBox("What this means", [
    "Using a fixed k understates the heat-transfer coefficient in the hotter cases, and by the "
      + "calibrated slope this makes the reported uniformity benefit slightly MORE favourable than "
      + "it should be.",
    "At the campaign mean, correcting k would move Delta plate spread from −21.09 % to about "
      + "−18.0 %. At the extreme it would reach −14.7 %.",
    "The sign of the result does not change, and the benefit remains clearly negative under every "
      + "value in the range.",
    "This term is larger than the plate-grid discretisation term (2.98 pp) and comparable to the "
      + "input-uncertainty term (4.98 pp), but smaller than the Nu(xi) model-form term (14.24 pp). "
      + "It belongs in the uncertainty budget and is added there.",
  ]),
  p("Note that c_p requires no such correction. Over the actual range of 293 to 353 K, the "
    + "specific heat of liquid water deviates from 4180 J/kg·K by at most +0.29 %. The "
    + "constant-c_p assumption is fully justified and is not flagged.", { before: 140 }),
  p("Verdict on the CFD results: VALID, with a newly quantified uncertainty term. No result is "
    + "invalidated. Required to close the item properly: re-run the campaign with k(T), which "
    + "costs the same as the Rev 1 to Rev 2 recomputation."),
];

// ---------------------------------------------------------------- 5
const s5 = [
  h1("5. Items 4 and 5 — sign convention, and efficiencies above the optical limit"),
  p("Classification: NOMENCLATURE AND EXPLANATION. The physics is correct in both cases."),

  h("5.1 Item 4 — negative Q_rad, Q_conv and Q_rear", 2),
  p("These are not errors. Each one occurs when the relevant surface is COLDER than what it "
    + "exchanges heat with, so the flux is directed into the collector. Newton's law of cooling "
    + "and the Stefan-Boltzmann difference both change sign correctly; the solver is right and the "
    + "word “loss” is what fails."),
  tableCaption("Table 8 — Every negative value traced to its physical cause."),
  table([
    ["Column", "Negative rows", "Verified cause"],
    ["Q_conv_W", "11 of 300", "T_plate − T_amb = −8.54 to −2.83 K"],
    ["Q_rear_W", "16 of 300", "same rows, same cause"],
    ["Q_rad_W", "11 of 300", "T_plate − T_glass = −5.21 to −0.81 K"],
    ["U_L_W_m2K", "5 of 300", "negative denominator, positive numerator (Section 3)"],
  ], [2.4, 1.8, 5.8], { alignRight: false }),
  p("The identity of the radiative exchange was confirmed rather than assumed: the correlation "
    + "between Q_rad and (T_plate − T_glass) across all 300 rows is +0.982, which establishes "
    + "that the column is the absorber-to-glazing exchange and that its sign follows that "
    + "temperature difference exactly as it must."),
  p("What changes: the four columns are to be described as NET FLUXES with an explicit sign "
    + "convention stated once and applied everywhere — positive out of the collector, negative "
    + "into it. The word “loss” is reserved for cases where the flux is genuinely "
    + "outward. No value is altered."),

  h("5.2 Item 5 — eleven cases with Q_u > Q_solar", 2),
  p("The optical ceiling of this collector is tau_glz x tau_TIM x alpha = 0.833 x 0.82 x 0.95 = "
    + "0.6489. Eleven cases report an efficiency above it, reaching 0.6778, with Q_u/Q_solar up to "
    + "1.0445 and a loss sum of −4.45 % of absorbed power."),
  p("They are the same eleven cases as the negative-flux rows in Section 5.1. In each one the "
    + "inlet temperature is well below ambient at moderate irradiance, so the absorber runs colder "
    + "than the surrounding air and the collector harvests ambient heat IN ADDITION to sunlight. "
    + "The efficiency denominator counts only the solar term, so the ratio legitimately exceeds "
    + "the optical limit."),
  tableCaption("Table 9 — The eleven cases, with the conditions that produce them."),
  table([
    ["Case", "G_T (W/m²)", "T_in (K)", "T_amb (K)", "T_plate,mean (K)", "eta", "Energy error"],
    ["ALT_025", "421.50", "298.66", "310.43", "306.94", "0.6549", "−0.0001 %"],
    ["ALT_066", "431.78", "290.62", "309.90", "301.36", "0.6778", "−0.0001 %"],
    ["ALT_113", "546.39", "288.27", "303.99", "298.85", "0.6569", "−0.0001 %"],
    ["ALT_128", "702.23", "293.73", "312.01", "307.96", "0.6560", "+0.0001 %"],
    ["ALT_135", "512.77", "289.06", "310.75", "303.68", "0.6695", "+0.0001 %"],
    ["PAR_012", "771.82", "291.94", "311.87", "304.72", "0.6618", "−0.0000 %"],
    ["PAR_083", "738.01", "289.37", "305.52", "300.28", "0.6586", "−0.0000 %"],
    ["PAR_103", "555.38", "291.77", "307.82", "302.26", "0.6621", "−0.0000 %"],
    ["PAR_120", "464.92", "292.33", "310.15", "303.73", "0.6627", "−0.0000 %"],
    ["PAR_131", "830.79", "293.23", "308.94", "306.11", "0.6522", "−0.0000 %"],
    ["PAR_148", "446.44", "297.62", "311.30", "306.40", "0.6578", "−0.0000 %"],
  ], [1.6, 1.5, 1.4, 1.4, 1.8, 1.2, 1.6]),
  p("In every one of the eleven the plate is colder than ambient, and in every one the energy "
    + "balance closes to within one ten-thousandth of a per cent. These are real operating states "
    + "that a physical collector would also exhibit, not numerical artifacts."),
  p("What changes: the definition of efficiency used here must be stated explicitly as "
    + "solar-referenced, eta = Q_u/(G_T A), and a footnote must accompany any efficiency table "
    + "explaining that solar-referenced efficiency can exceed the optical limit when the collector "
    + "also draws heat from warmer surroundings. No case is removed or capped."),
];

// ---------------------------------------------------------------- 6
const s6 = [
  h1("6. Item 6 — lateral_bridge_W, and why bridge width barely matters"),
  p("Classification: THE ACCOUNTING IS CORRECT; THE INSENSITIVITY NEEDS EXPLANATION."),

  h("6.1 It is correctly excluded from the energy balance", 2),
  p("This was tested directly rather than assumed. The energy balance was recomputed twice, once "
    + "as reported and once with lateral_bridge_W added as a fifth term:"),
  tableCaption("Table 10 — Direct test of how lateral_bridge_W enters the accounting."),
  table([
    ["Energy balance formulation", "Maximum residual"],
    ["Q_solar − (Q_u + Q_rad + Q_conv + Q_rear)", "1.43e-04 W"],
    ["Q_solar − (Q_u + Q_rad + Q_conv + Q_rear + lateral_bridge)", "290.2 W"],
  ], [6.5, 3.5]),
  p("Adding it destroys the balance, which proves it is NOT being counted as useful energy, as an "
    + "external loss, or as an independent source or sink. It is an internal redistribution "
    + "diagnostic — heat moving sideways from one channel's territory to its neighbour's, inside "
    + "the control volume — and it is handled correctly."),
  tableCaption("Table 11 — The two populations."),
  table([
    ["Arrangement", "Minimum", "Maximum", "Mean"],
    ["Co-current", "6.46e-11 W", "9.42e-11 W", "7.77e-11 W"],
    ["Alternating", "59.46 W", "290.21 W", "157.14 W"],
  ], [3, 2.4, 2.4, 2.2]),
  p("The co-current values are round-off around the exact zero that y-periodicity requires: with "
    + "every channel flowing the same way, the plate field is periodic in y and the temperature "
    + "gradient at each bridge midline vanishes identically. The contrast must therefore always be "
    + "quoted as an absolute figure and never as a ratio to zero."),

  h("6.2 Why bridge width has almost no effect", 2),
  p("A standardised regression of lateral_bridge_W on all eight sampled inputs, over the 150 "
    + "alternating cases, gives R² = 0.972 and the following coefficients:"),
  tableCaption("Table 12 — Standardised regression coefficients for lateral bridge conduction."),
  table([
    ["Input", "Standardised coefficient"],
    ["G_T", "+0.792"],
    ["mdot_total", "−0.605"],
    ["T_in", "−0.197"],
    ["T_amb", "+0.144"],
    ["v_wind", "−0.032"],
    ["bridge_mm", "−0.008"],
    ["g_ratio", "+0.007"],
    ["lambda_G", "−0.004"],
  ], [5, 5]),
  p("Bridge width is swept from 20 to 37 mm — an 85 % change in the conduction path — and moves "
    + "lateral conduction essentially not at all. This is unusual and it deserves an explanation "
    + "rather than a footnote."),
  calloutBox("The explanation, and how to verify it", [
    "The Hottel-Whillier-Bliss chain computed for this absorber gives a fin efficiency of 0.9995. "
      + "With 2 mm of aluminium at 229 W/m·K spanning a 31.3 mm bridge against a loss "
      + "coefficient near 2.5 W/m²K, the fin parameter m(W−D)/2 is very small and the "
      + "bond land is already effectively isothermal across its width.",
    "When a conduction path is already near-isothermal, the heat crossing it is set by the "
      + "temperature difference imposed at its ends, not by the width of the path. Widening the "
      + "bridge adds area and length in nearly equal measure.",
    "There is a second, geometric reason. The campaign defines w_ch = pitch − bridge, so "
      + "widening the bridge simultaneously narrows the channel. The two effects act in opposite "
      + "directions and partly cancel.",
    "Required verification before this is presented: either an explicit k A / L scaling argument "
      + "showing the cancellation, or a controlled sweep of bridge width at FIXED channel width, "
      + "which the current campaign design cannot provide.",
  ]),
  p("Verdict: NOT DEMONSTRATED INVALID. The dataset value stands unchanged. What is required is "
    + "the explanation above, supported by one of the two verifications.", { before: 140 }),
];

// ---------------------------------------------------------------- 7
const s7 = [
  h1("7. Items 7 and 8 — operating pressure, and convergence evidence"),

  h("7.1 Item 7 — one case above the saturation temperature", 2),
  p("Classification: DOCUMENTATION. One case exceeds the 1 atm saturation temperature of water."),
  tableCaption("Table 13 — Cases approaching and exceeding saturation."),
  table([
    ["Condition", "Rows"],
    ["T_out > 353 K (80 °C)", "23"],
    ["T_out > 363 K (90 °C)", "5"],
    ["T_out > 368 K", "2"],
    ["T_out > 373.15 K (T_sat at 1 atm)", "1 — case PAR_134, T_out = 373.21 K"],
    ["T_plate,max > 373.15 K", "10 (peak 400.98 K)"],
  ], [6.5, 3.5]),
  p("The solver carries single-phase liquid properties with no phase-change model. The result is "
    + "valid if and only if the hydraulic loop is pressurised above the corresponding saturation "
    + "pressure. At 2 bar absolute, T_sat is about 393 K and every case in the dataset, including "
    + "PAR_134 and all ten high plate temperatures, sits comfortably inside the single-phase "
    + "envelope."),
  p("What changes: the operating pressure of the collector loop must be stated explicitly in the "
    + "methodology, together with the resulting saturation temperature and the statement that all "
    + "300 cases lie within the single-phase envelope at that pressure. If the design is an "
    + "unpressurised 1 atm loop, PAR_134 must be flagged in place as outside the model's validity "
    + "envelope. It is NOT to be deleted under either reading."),

  h("7.2 Item 8 — convergence evidence is a single scalar", 2),
  p("Classification: DOCUMENTATION. The evidence is sufficient for the conclusions drawn, but it "
    + "is thinner than a strong CFD publication expects."),
  tableCaption("Table 14 — Convergence information the dataset carries."),
  table([
    ["Field", "Content"],
    ["residual", "one scalar per case, 7.59e-07 to 1.00e-06"],
    ["outer_iters", "73 to 849; the 900 cap is never reached"],
    ["converged", "True on all 300 rows"],
    ["energy_error_pct", "maximum magnitude 9.83e-05 %"],
  ], [3, 7], { alignRight: false }),
  p("Fifty-one rows sit at the 1e-06 tolerance boundary, meaning they converged to the tolerance "
    + "rather than well past it. A single outer-loop residual does not demonstrate that "
    + "continuity, momentum and energy have each converged, and for a publication the per-equation "
    + "residual histories and at least one monitored engineering quantity should be shown."),
  calloutBox("What the dataset does have, which is stronger", [
    "An INDEPENDENT energy balance that closes to 9.83e-05 % on every one of the 300 cases.",
    "A residual is a statement about the linear solver. An energy balance is a statement about "
      + "the physics, computed from quantities the solver did not iterate on. It is the better "
      + "evidence, and it is what justifies treating these cases as converged.",
    "Recommended addition for publication: per-equation residual histories and a monitored "
      + "quantity trace for a representative subset, alongside the balance already reported.",
  ]),
];

// ---------------------------------------------------------------- 8
const s8 = [
  h1("8. Summary and final classification"),
  tableCaption("Table 15 — All eight items, classified."),
  table([
    ["#", "Item", "Class", "Result invalidated?"],
    ["1", "nu_cfd is a fixed closure, not a per-case CFD value", "Major methodological", "No — model-form limited"],
    ["2", "U_L ill-conditioned in 20 of 300 cases", "Major, affects a statistic", "No — statistic restated"],
    ["3", "Constant k with temperature-dependent mu", "Major, property model", "No — new uncertainty term"],
    ["4", "Negative Q_rad, Q_conv, Q_rear", "Nomenclature", "No — physics correct"],
    ["5", "Eleven cases with eta above the optical limit", "Explanation required", "No — physics correct"],
    ["6", "Bridge width does not affect bridge conduction", "Unusual, needs explanation", "No — not shown invalid"],
    ["7", "One case above 1 atm saturation temperature", "Documentation", "No — state the pressure"],
    ["8", "Single-scalar convergence evidence", "Documentation", "No — balance is stronger"],
  ], [0.5, 4.3, 2.5, 2.7], { alignRight: false }),

  h("8.1 The separation that matters", 2),
  ...bullets([
    "ACTUAL ERRORS: none. Not one value in the 300 x 54 table is mathematically, dimensionally or "
      + "physically wrong. No conservation law is violated. No derived relation fails.",
    "UNUSUAL BUT VALID PHYSICS: items 4, 5 and 6 — the inward heat fluxes, the above-optical "
      + "efficiencies, and the bridge-width insensitivity. All three remain in the dataset "
      + "unchanged and require explanation, not correction.",
    "REPORTING AND DOCUMENTATION: items 1, 4, 5, 7 and 8. These change how results are "
      + "described, not what they are.",
    "NUMERICAL CONSEQUENCE: items 2 and 3 are the only two that change a reported number. "
      + "Item 2 restates Delta U_L as −1.95 ± 2.52 % on the conditioned subset, a "
      + "nine-fold tightening. Item 3 adds a k(T) term that would move Delta plate spread from "
      + "−21.09 % to about −18.0 %.",
  ]),

  h("8.2 The headline results after the audit", 2),
  tableCaption("Table 16 — Reported results, with every audit correction applied."),
  table([
    ["Quantity", "As reported", "After audit", "Verdict"],
    ["Delta efficiency", "−4.94 ± 0.81 %", "unchanged", "FIRM — a deficit"],
    ["Delta plate spread (RMS)", "−21.09 ± 11.61 %", "about −18.0 % with k(T)", "REAL, model-form limited"],
    ["Delta loss coefficient", "−0.90 ± 22.93 %", "−1.95 ± 2.52 %", "NOT distinguishable, now sharply so"],
    ["Delta peak-to-peak spread", "−3.64 ± 15.82 %", "unchanged", "NOT distinguishable — do not claim"],
  ], [2.8, 2.4, 2.6, 2.2], { alignRight: false }),
  spacer(120),
  p("NOTE (Rev 4): the bottom line below is the Rev 2 audit verdict and is kept unchanged. Its statements on "
    + "the uniformity benefit and the efficiency deficit are SUPERSEDED by Section 9.", { run: { bold: true, color: "B03A2E" } }),
  calloutBox("Bottom line", [
    "The audit did not find a single engineering error in the dataset, and it did not invalidate "
      + "a single case.",
    "It found three quantities described in misleading ways, two statistics needing restatement, "
      + "and one property assumption needing a bound.",
    "None of the eight items changes the direction of any conclusion. The efficiency deficit "
      + "stands, the uniformity benefit stands with a slightly smaller magnitude and an explicit "
      + "model-form qualifier, and the peak-to-peak claim stays withdrawn.",
    "No data was modified, corrected, smoothed, deleted or replaced at any point in this audit.",
  ]),
];

const s9 = [
  h1("9. Rev 4 update — what this audit's verdict becomes"),
  p("This audit verified that Rev 2 is algebraically self-consistent, and that finding stands. What changed "
    + "afterwards is the physics INPUT the dataset was computed with, which an internal audit cannot detect."),
  table([
    ["Audit statement", "Status after Rev 4", "Reason"],
    ["No engineering error in the dataset algebra", "STANDS", "Rev 4 closes to |energy error| < 1.5e-4 %"],
    ["Nu = 2.9238 on every row (a valid closure)", "SUPERSEDED", "H2-type; 3-D conjugate Nu 4.48"],
    ["Efficiency deficit stands", "STANDS, LARGER", "Group mean −7.3 % (p = 2e-8), every flow tercile"],
    ["Uniformity benefit stands, slightly smaller", "WITHDRAWN", "Overall −1.1 % (n.s.); +16.8 % below 2.2 g/s, −13.4 % above 3.3 g/s"],
    ["Peak-to-peak claim withdrawn", "STANDS", "Group median spread +18.4 %"],
    ["(Rev 4.1) derived columns R4/T_R4/mean_T_pow4, U_L, Re", "CORRECTED", "Recomputed from definitions; thermal results unchanged"],
    ["Results invalidated: 0", "QUALIFIED", "No row deleted; Rev 2 superseded, not invalidated"],
  ], [3.6, 2.2, 4.2]),
  p("Full evidence: GRAIL CFD Correction Report and CFD Simulation Report Rev 4 edition, Part V."),
];

const doc = buildDoc({
  title: "GRAIL Collector — Dataset Audit Addendum (Rev 4 update)",
  subtitle: "Independent engineering audit of GRAIL_CFD_dataset_rev2.csv.",
  sections: [title, [].concat(toc, s1, s2, s3, s4, s5, s6, s7, s8, s9)],
});

write(doc, "/home/claude/reports/GRAIL_Dataset_Audit_Addendum_Rev4.1.docx");
