// GRAIL CFD Simulation Report — sections 6 onwards
const C = require("./common");
const { p, h, table, tableCaption, figure, bullets, numbered,
        calloutBox, spacer, pageBreak, Paragraph, TextRun, AlignmentType } = C;
const { FIG, eq, code } = require("./cfd_report");

// ===================================================== 6
const s6 = [
  pageBreak(),
  h("6. Gate 5 — the conjugate plate solver", 1),
  p("The central hypothesis is about what happens across the whole 12-channel absorber when "
    + "alternate channels run in opposite directions. A single 3-D channel cannot answer it, and "
    + "300 three-dimensional conjugate cases do not fit on two cores. A purpose-built conjugate "
    + "solver, GRAIL-CHT 1.0, was written to close that gap."),

  h("6.1 What it solves", 2),
  table([
    ["Region", "Physics"],
    ["Plate", "2-D steady conduction over the whole absorber, with anisotropic sheet thickness, "
      + "solar gain, top loss through the real glazing stack with explicit radiation, rear loss "
      + "through PCM and VIP, and local convective coupling to each channel"],
    ["Fluid", "1-D energy per channel, marched in that channel's OWN flow direction, so an "
      + "alternating arrangement is represented exactly rather than approximated"],
    ["Closure", "h(x) = Nu · k / D_h(x), with Nu taken from the resolved 3-D OpenFOAM solution"],
  ], [1.5, 8.5], { alignRight: false }),
  p("Everything is SI internally and Kelvin appears wherever a fourth power does. The geometry "
    + "class carries the Gate 1 measured values directly: A_in 28.056939 mm², A_out 7.921436 mm², "
    + "P_in 21.5865 mm, P_out 11.2884 mm, D_h,in 5.198875 mm, D_h,out 2.807053 mm, "
    + "w_ch,in 8.714056 mm, G = 0.539935, lambda_G = 1.0, pitch 40 mm, L 1100 mm, plate 1100 × "
    + "480 mm, both sheets 1.0 mm."),
  p("The section law is the one confirmed on the CAD:"),
  eq("D_h(xi) = D_h,in · [1 − (1 − G) · xi^lambda_G],   A(xi) = A_in · s²,   P(xi) = P_in · s,   "
    + "s = D_h(xi)/D_h,in"),

  h("6.2 Verification before any conclusion", 2),
  p("The difference between the two flow arrangements must vanish in two independent limits: when "
    + "lateral conduction cannot act at all, and when it acts perfectly. If a solver does not "
    + "reproduce both, whatever difference it reports is numerical. Both limits were tested by "
    + "sweeping the plate conductivity over eight orders of magnitude."),
  tableCaption("Table 14 — Plate-conductivity limit test. The effect must and does collapse at both ends."),
  table([
    ["k_plate (W/m·K)", "dQ_u", "dR4", "Comment"],
    ["0.01", "+0.0006 %", "−0.0008 %", "no lateral path → arrangements identical"],
    ["1", "−0.126 %", "+0.217 %", ""],
    ["22.9", "−2.618 %", "+7.861 %", ""],
    ["229 (AA1050)", "−5.415 %", "+17.048 %", "the real material"],
    ["2290", "−3.456 %", "+10.384 %", ""],
    ["2.29e6", "−0.009 %", "+0.024 %", "isothermal plate → arrangements identical"],
  ], [2.2, 1.7, 1.7, 4.4]),
  p("Both limits collapse to zero and the effect peaks at finite conductivity, which is the "
    + "signature of a genuinely conduction-mediated mechanism. The energy balance closes to 1e-5 % "
    + "in every case in this table, and the outer-loop tolerance is 1e-8."),
  ...figure(FIG + "C14_mechanism_fields.png",
    "Figure 17 — Plate temperature fields, co-current against alternating, on the full "
    + "12-channel absorber.", 0.95),
];

// ===================================================== 7
const s7 = [
  pageBreak(),
  h("7. The mechanism, tested link by link", 1),
  p("The claim behind Filing 1 is a chain of seven steps: opposite flow creates opposing "
    + "gradients, metal carries heat sideways, the absorber field flattens, hot regions shrink, "
    + "the mean of T⁴ falls, radiative loss falls, and efficiency rises. Each link was tested "
    + "separately, because a chain reported only at its end cannot be diagnosed."),
  p("These runs were made at nu_cfd = 3.428 — the Rev 1 value. Section 10 gives the corrected "
    + "campaign numbers. The chain's verdicts are unchanged by the correction; the magnitudes in "
    + "Table 16 are Rev 1 magnitudes and are labelled as such."),

  tableCaption("Table 15 — The causal chain, link by link."),
  table([
    ["#", "Hypothesised link", "Verdict", "Evidence"],
    ["1", "Opposite flow → opposing local gradients", "CONFIRMED",
      "per-channel outlets spread 319.97–326.45 K instead of a uniform 324.11 K"],
    ["2", "Lateral heat transfer through the metal bridge", "CONFIRMED, LARGE",
      "218.35 W across the 11 bridge planes; lateral:axial conduction ratio 175.8"],
    ["3", "Absorber temperature homogenisation", "CONFIRMED",
      "T_p standard deviation −8.8 % at matched mean (−13.8 % at matched flow)"],
    ["4", "Reduction of high-temperature regions", "NOT CONFIRMED",
      "P99 only −1.05 %; the plate spread actually RISES +10.8 %"],
    ["5", "Reduction in mean(T⁴)", "NEGLIGIBLE", "−0.045 % at matched mean"],
    ["6", "Reduction in radiative loss", "NEGLIGIBLE",
      "Q_rad 2.62906 → 2.62384 W, −0.20 %, i.e. 5.2 mW out of 274 W"],
    ["7", "Improvement in useful heat", "NO",
      "+0.001 % at matched mean; −5.4 % at matched mass flow"],
  ], [0.5, 3.0, 1.9, 4.6], { alignRight: false }),

  h("7.1 The fair test: matched mean plate temperature", 2),
  p("Comparing two arrangements at the same mass flow compares two different operating states. "
    + "The inlet temperature was therefore tuned to 285.689 K so that both cases sit at exactly "
    + "the same mean absorber temperature, 315.10 K, and only the field SHAPE differs."),
  tableCaption("Table 16 — Matched-mean comparison (Rev 1 magnitudes)."),
  table([
    ["Quantity", "Co-current", "Alternating", "Change"],
    ["T_p mean (K)", "315.0961", "315.0980", "+0.0006 %"],
    ["T_p standard deviation (K)", "6.7240", "6.1307", "−8.82 %"],
    ["Plate spread dT_p (K)", "21.9319", "24.3024", "+10.81 %"],
    ["P99 (K)", "325.5911", "322.1869", "−1.05 %"],
    ["mean(T⁴) (K⁴)", "9.884533e+09", "9.880069e+09", "−0.045 %"],
    ["Q_rad (W)", "2.62906", "2.62384", "−0.20 %"],
    ["Q_u (W)", "251.9842", "251.9870", "+0.001 %"],
    ["Efficiency", "0.59655", "0.59656", "+0.001 %"],
    ["mean(T⁴) / mean(T)⁴", "1.002731", "1.002253", "—"],
  ], [3.4, 2.2, 2.2, 2.2]),

  calloutBox("The crux is the last row", [
    "Nonuniformity contributes only 0.27 % to mean(T⁴) in the co-current case. Flattening the "
      + "field removes part of that 0.27 %. There is nothing else to win.",
    "The selective coating has already won. With TiNOX at eps = 0.04, radiative loss is 2.63 W "
      + "out of 274.10 W absorbed — under 1 %. Eliminating radiation entirely would gain less "
      + "than one per cent, and a mechanism whose purpose is to reduce radiative loss has almost "
      + "nothing left to reduce.",
    "Jensen's inequality still holds: at fixed mean, a flatter field has strictly lower mean(T⁴). "
      + "The direction is right and the model confirms it. The magnitude is 0.045 %.",
  ]),
  p("The honest reading for the filings is that the flattening is real and measurable — 218 W "
    + "crosses the bridges and the standard deviation falls — but the step from flattening to "
    + "reduced loss does not pay on THIS collector, because the loss it targets is already "
    + "negligible. The claim should rest on the demonstrated homogenisation. The same mechanism "
    + "on a NON-selective absorber, where eps is 0.9 rather than 0.04, is the configuration in "
    + "which it should pay, and that case has not been simulated."),
  ...figure(FIG + "F8_mechanism_fields.png",
    "Figure 18 — The mechanism in the field: co-current, alternating, and the difference.", 0.95),
  ...figure(FIG + "C16_bridge_conduction.png",
    "Figure 19 — Lateral conduction across the eleven bridge planes.", 0.9),

  h("7.2 A correction to how the bridge contrast is quoted", 2),
  p("An earlier statement in this project read “170.84 W against 0.0000 W”. That is "
    + "arithmetically true and rhetorically misleading, and it has been corrected (CR-12)."),
  p("The co-current figure is exactly zero BY SYMMETRY, not merely small. With every channel "
    + "flowing the same way the plate field is periodic in y and the temperature gradient at the "
    + "bridge midline vanishes identically. The campaign reads 6.5e-11 to 9.1e-11 W, which is "
    + "round-off. The grid study reads 0.000, 8.892, 0.000 and 3.345 W across four levels — those "
    + "nonzero values are a sampling artefact that appears when the midline does not coincide with "
    + "a cell face, not physics."),
  p("The contrast is real, but the denominator is zero. It must be quoted as an absolute figure — "
    + "alternating reads 67 to 303 W across the campaign, about 20 W per midline at the design "
    + "point — and never as a ratio."),
];

// ===================================================== 8
const s8 = [
  pageBreak(),
  h("8. Gate 6 — how much of the plate has to be simulated", 1),
  p("A reduced domain would make future work far cheaper, but only if it reproduces the full "
    + "plate. This was measured rather than assumed, and the measurement overturned the original "
    + "plan."),

  h("8.1 Glide symmetry, not mirror symmetry", 2),
  p("Under alternating flow the neighbour across a bridge midline runs in the OPPOSITE direction. "
    + "The field is therefore glide-symmetric, not mirror-symmetric, and its period is TWO "
    + "channels, not one. An ordinary symmetry plane at the midline is adiabatic, and an adiabatic "
    + "midline suppresses exactly the lateral conduction the whole hypothesis depends on."),
  p("Five domains were run at identical cell size, with co-current as a control in which all four "
    + "reduced domains must — and do — reproduce the full plate exactly."),
  tableCaption("Table 17 — Domain equivalence, alternating arrangement, against the full 12-channel plate."),
  table([
    ["Domain", "Δ efficiency", "Δ plate spread", "Bridge conduction (W)", "Verdict"],
    ["Full 12-channel plate", "—", "—", "20.23", "reference"],
    ["2-channel periodic", "−0.308 %", "+2.513 %", "19.412 (−4.06 %)", "VALID"],
    ["2-channel adiabatic", "—", "—", "33.729 (+66.7 %)", "INVALID"],
    ["3-channel strip", "—", "—", "1.050", "INVALID — wrong period"],
  ], [3, 1.9, 1.9, 2.4, 1.5], { alignRight: false }),
  p("An adiabatic symmetry plane inflates lateral bridge conduction by +66.70 %. A 3-channel strip "
    + "is invalid under either boundary condition because the glide period is two channels, not "
    + "three. The 2-channel periodic domain reproduces the full plate to −0.31 % on efficiency, "
    + "+2.51 % on plate spread and −4.06 % on bridge conduction, and is validated for future use."),
  calloutBox("Nothing reported in this study used a reduced domain", [
    "The campaign, the mechanism study and every figure were computed on the full 12-channel "
      + "plate. Section 8 is a result for future work, not a shortcut taken in this one.",
  ]),
  ...figure(FIG + "D1_domain_equivalence.png",
    "Figure 20 — Domain equivalence across the five domains.", 0.9),
  ...figure(FIG + "D2_domain_fields.png",
    "Figure 21 — The fields each domain produces. The adiabatic 2-channel case is visibly "
    + "different at the midline.", 0.95),
];

// ===================================================== 9
const s9 = [
  pageBreak(),
  h("9. Gate 7 — the production campaign", 1),
  p("Three hundred cases: 150 co-current and 150 alternating, each half an independent Latin "
    + "Hypercube draw over the same eight design and operating variables, with a fixed seed so the "
    + "whole campaign is reproducible."),

  tableCaption("Table 18 — Campaign design."),
  table([
    ["Item", "Value"],
    ["Sampler", "scipy.stats.qmc.LatinHypercube, d = 8, seed = 20260915"],
    ["Cases per arrangement", "150"],
    ["Plate grid", "110 × 120 = 13,200 cells"],
    ["Outer-loop tolerance", "1e-6, maximum 900 outer iterations"],
    ["Geometry version tag", "GateA_converged_v1"],
    ["Cases rejected in Rev 2", "0 of 300"],
  ], [3.4, 6.6], { alignRight: false }),

  tableCaption("Table 19 — The eight sampled variables and their bounds."),
  table([
    ["Variable", "Lower", "Upper", "Why this range"],
    ["G_T (W/m²)", "400", "1000", "documented operating envelope"],
    ["T_in (K)", "288", "333", "inlet range of interest"],
    ["T_amb (K)", "283", "313", "ambient range"],
    ["v_wind (m/s)", "0.0", "5.0", "still air to moderate wind"],
    ["mdot_total (kg/s)", "0.0010", "0.0045", "pump operating range"],
    ["bridge (mm)", "20.0", "37.0", "hard geometric limit: bridge = pitch − w_ch < 40 mm"],
    ["g_ratio", "0.35", "1.00", "capped at 1.00 by Filing 1 dependent claim 1"],
    ["lambda_G", "0.5", "2.0", "grading exponent, around the confirmed baseline of 1.0"],
  ], [2.3, 1.3, 1.3, 5.1], { alignRight: false }),

  p("A pre-run validation gate rejects impossible geometry before the solver is called, so an "
    + "unphysical sample never becomes a failed case that has to be explained afterwards."),

  h("9.1 The pressure-drop closure", 2),
  p("Pressure drop is not solved in the campaign; it is integrated along the converging channel "
    + "and calibrated once against the resolved 3-D CFD:"),
  ...code([
    "mu(T)  = 2.414e-5 * 10 ** (247.8 / (T_mean - 140.0))      # water, Vogel relation",
    "dp     = integral over x of  32 * mu * u(x) / Dh(x)**2    # laminar, 60 stations",
    "DP_CAL = 35.31 / 33.31 = 1.0600                           # CFD / laminar integral",
  ]),
  p("The calibration factor is the +6.0 % of Table 7 and it is applied uniformly. Viscosity is "
    + "evaluated at the mean fluid temperature of each case, so the campaign carries a "
    + "temperature-dependent viscosity even though the baseline 3-D case did not.", { before: 140 }),

  h("9.2 What each row carries", 2),
  p("Fifty-two columns per case. Every row carries its own geometry provenance tag, its "
    + "convergence flag, its outer-iteration count, its final residual and its independent energy "
    + "balance error, so no number can be quoted without its quality flags travelling with it. The "
    + "recorded quantities include, per case: the eight inputs; the derived geometry (D_h in and "
    + "out, A in and out, Re in and out, mu); hydraulics (dp_channel, pumping power); the absorbed "
    + "flux, sky temperature and wind coefficient; the fluid result (T_out, dT, Q_u, efficiency); "
    + "the plate statistics (mean, max, min, spread, standard deviation, P90, P95, P99); the "
    + "radiative quantities (mean of T⁴, mean(T)⁴, the equivalent radiative temperature); the "
    + "full loss balance (Q_solar, Q_rad, Q_conv, Q_rear, U_L, mean glass temperature); and the "
    + "lateral bridge conduction."),
  ...figure(FIG + "C22_quality.png",
    "Figure 22 — Campaign quality: convergence, residuals and energy-balance error across all "
    + "300 cases.", 0.9),
  ...figure(FIG + "C15_distribution.png",
    "Figure 23 — Distribution of the sampled inputs across the campaign.", 0.9),
  ...figure(FIG + "C20_distributions.png",
    "Figure 24 — Distribution of the campaign outputs.", 0.9),
  ...figure(FIG + "C10_efficiency.png",
    "Figure 25 — Efficiency across the campaign, both arrangements.", 0.9),
  ...figure(FIG + "C12_temperature_rise.png",
    "Figure 26 — Fluid temperature rise against mass flow.", 0.85),
  ...figure(FIG + "C13_wind.png",
    "Figure 27 — Effect of wind speed through h_wind = 5.7 + 3.8·v.", 0.85),
  ...figure(FIG + "C17_correlation.png",
    "Figure 28 — Correlation structure of the campaign.", 0.9),
  ...figure(FIG + "C18_grading.png",
    "Figure 29 — Effect of the grading ratio G and exponent lambda_G.", 0.9),
  ...figure(FIG + "C19_bridge.png",
    "Figure 30 — Effect of bridge width over the 20–37 mm sweep.", 0.85),
  ...figure(FIG + "C21_mechanism_campaign.png",
    "Figure 31 — The mechanism across the whole campaign rather than at a single design point.", 0.9),
];

// ===================================================== 10
const s10 = [
  pageBreak(),
  h("10. The campaign was recomputed — Rev 1 to Rev 2", 1),
  p("Section 5 established that the solver had been running +17.25 % high on nu_cfd. Section 10 "
    + "is what was done about it."),

  h("10.1 A one-variable recomputation", 2),
  p("Same seed, same Latin Hypercube, same bounds, same gates, same grid. ONLY nu_cfd changed, "
    + "from 3.4282 to the Richardson-extrapolated 2.9238. Because nothing else moved, every Rev 2 "
    + "row pairs one-to-one with its Rev 1 twin and the difference between them is attributable "
    + "to nothing else."),
  tableCaption("Table 20 — Paired, case by case: what the correction did."),
  table([
    ["Quantity", "Co-current", "Alternating"],
    ["Plate spread, RMS", "−0.036 K", "−0.473 K"],
    ["Plate peak-to-peak", "−0.194 K", "−1.822 K"],
    ["Efficiency", "−0.0009", "+0.0022"],
    ["Mean plate temperature", "+0.288 K", "−0.722 K"],
  ], [4, 3, 3]),
  p("The correction moves the alternating cases and barely touches the co-current ones, which is "
    + "exactly what a bias on the wall-to-fluid coupling coefficient should do. Rev 1 is kept on "
    + "disk in full, with its own figures, and is not deleted."),

  h("10.2 Rev 1's campaign average had been censored", 2),
  p("Rev 1 lost 9 rows to the convergence gate. Rev 2 loses none, because the lower Nusselt number "
    + "leaves the coupled solve better conditioned. That makes the 9 recoverable, and recovering "
    + "them showed they were not a random 9:"),
  ...bullets([
    "All 9 were ALTERNATING cases.",
    "All 9 were the lowest-flow cases in the whole sample: mean 1.10 g/s against a campaign mean "
      + "of 2.75 g/s, and none above 1.19 g/s.",
    "Their mean plate spread was 10.97 K against 4.69 K for alternating overall — they were the "
      + "hardest cases in the draw.",
  ]),
  p("Averaging a sample with its own hardest cases removed flatters the arrangement those cases "
    + "belonged to. The headline number therefore changes:"),
  tableCaption("Table 21 — Δ plate spread, alternating minus co-current."),
  table([
    ["Basis", "Value"],
    ["Rev 1, the 291 rows both revisions share", "−20.09 %"],
    ["Rev 2, the same 291 rows", "−27.60 %"],
    ["Rev 2, all 300 rows — the figure to quote", "−20.83 ± 12.09 % (k = 2)"],
  ], [6, 4]),
  p("Two corrections of opposite sign and similar size, which nearly cancel. The uncensored figure "
    + "is the one to use, because it is the only average taken over the sample that was actually "
    + "drawn. No row was ever removed to improve a result; the censoring is reported as a defect "
    + "of Rev 1."),

  h("10.3 The mass-flow threshold is withdrawn", 2),
  p("Rev 1 supported a claim that below about 1.81 g/s the alternating arrangement is WORSE than "
    + "co-current. In Rev 2 every one of the eight mass-flow bins from 1.23 to 4.27 g/s favours "
    + "alternating. In Rev 1 the lowest bin read +7.75 %."),
  p("Both causes are in Sections 10.1 and 10.2: the biased Nusselt number, and the fact that the "
    + "censored rows were precisely the low-flow ones that set the threshold. There is no minimum "
    + "operating flow claim to make, and the threshold is withdrawn."),
  p("One caution on reading the bins: the co-current and alternating halves are two INDEPENDENT "
    + "Latin Hypercube draws, so bin-to-bin scatter is sampling noise. Only the sign, which is "
    + "consistent across all eight bins, is robust."),
  ...figure(FIG + "R1_rev1_vs_rev2.png",
    "Figure 32 — Rev 1 against Rev 2: the paired shift, the recovered rows, and the withdrawn "
    + "threshold.", 0.95),
  ...figure(FIG + "U4_campaign_correction.png",
    "Figure 33 — The campaign grid correction, measured on ten operating points at three grid "
    + "levels.", 0.9),

  h("10.4 The campaign grid correction", 2),
  p("The campaign runs on the coarsest plate grid tested. Ten campaign operating points, "
    + "stratified by mass flow, were re-run at three levels to measure that correction directly "
    + "rather than assume it."),
  tableCaption("Table 22 — Grid correction measured on ten campaign points."),
  table([
    ["Case", "mdot (g/s)", "Δstd @110×120", "@156×170", "@220×240", "shift (pp)"],
    ["PAR_065", "1.23", "+5.584 %", "+6.756 %", "+7.754 %", "+2.17"],
    ["PAR_117", "1.41", "+3.905 %", "+5.163 %", "+6.012 %", "+2.11"],
    ["PAR_091", "1.94", "−3.757 %", "−2.691 %", "−1.831 %", "+1.93"],
    ["PAR_120", "2.14", "−5.324 %", "−4.304 %", "−3.594 %", "+1.73"],
    ["PAR_079", "2.50", "−14.316 %", "−12.951 %", "−12.431 %", "+1.88"],
    ["PAR_112", "2.94", "−20.469 %", "−19.528 %", "−19.092 %", "+1.38"],
    ["PAR_018", "3.33", "−26.222 %", "−25.670 %", "−25.227 %", "+0.99"],
    ["PAR_005", "3.57", "−30.048 %", "−29.547 %", "−29.156 %", "+0.89"],
    ["PAR_010", "3.92", "−35.065 %", "−34.409 %", "−34.058 %", "+1.01"],
    ["PAR_020", "4.21", "−38.318 %", "−38.183 %", "−37.816 %", "+0.50"],
  ], [1.8, 1.6, 2.2, 1.6, 1.6, 1.3]),
  p("The correction is ADDITIVE, not multiplicative. Expressed as a ratio it ranges from 0.49 to "
    + "1.54 and is meaningless, because Δstd changes sign across the range. The clean description "
    + "is a linear map, which fits to R² = 0.99990:"),
  eq("Δstd(220×240) = 1.0349 × Δstd(110×120) + 2.0314"),
];

module.exports = { s6, s7, s8, s9, s10 };
