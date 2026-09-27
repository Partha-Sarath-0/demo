// GRAIL CFD Simulation Report — sections 11 onwards
const C = require("./common");
const { p, h, table, tableCaption, figure, bullets, numbered,
        calloutBox, spacer, pageBreak, Paragraph, TextRun, AlignmentType } = C;
const { FIG, eq, code } = require("./cfd_report");

// ===================================================== 11
const s11 = [
  pageBreak(),
  h("11. Gate 8a — uncertainty assessment", 1),
  p("Framework: ASME V&V 20-2009. Three contributions are quantified separately and combined in "
    + "quadrature — discretisation (Roache grid convergence index), input uncertainty (paired "
    + "Monte Carlo), and iterative convergence. Round-off is not carried: the solver is float64 "
    + "and the independent energy balance closes to 1e-7 %."),

  h("11.1 Discretisation on the conjugate plate grid", 2),
  p("Four levels at a refinement ratio of 1.41 in cells per direction, both arrangements on every "
    + "level."),
  tableCaption("Table 23 — Four-level plate grid study."),
  table([
    ["Grid", "Cells", "h (mm)", "co-current η", "alternating η", "co std (K)", "alt std (K)", "Δstd"],
    ["110 × 120 (campaign)", "13,200", "6.3246", "0.596553", "0.564249", "6.7240", "5.7964", "−13.795 %"],
    ["156 × 170", "26,520", "4.4620", "0.596641", "0.563951", "6.7368", "5.8887", "−12.590 %"],
    ["220 × 240", "52,800", "3.1623", "0.596697", "0.563771", "6.7370", "5.9277", "−12.013 %"],
    ["311 × 339", "105,429", "2.2379", "0.596735", "0.563627", "6.7407", "5.9643", "−11.517 %"],
  ], [2.4, 1.3, 1.1, 1.5, 1.5, 1.2, 1.2, 1.3]),
  tableCaption("Table 24 — Observed orders and GCI, from the two independent triplets."),
  table([
    ["Quantity", "p (fine triplet)", "p (coarse triplet)", "GCI", "Asymptotic?"],
    ["Δ plate standard deviation", "0.446", "2.087", "32.34 %", "no"],
    ["Δ efficiency", "0.766", "1.385", "2.24 %", "no"],
    ["Δ loss coefficient", "0.905", "1.347", "1.40 %", "yes"],
    ["Δ peak-to-peak spread", "1.208", "0.429", "98.40 %", "no"],
  ], [3.4, 1.9, 1.9, 1.4, 1.4]),
  p("Only ΔU_L is cleanly in the asymptotic range. Δη is borderline, but its GCI is 2.2 %, so the "
    + "practical conclusion is unaffected. ΔT_p,std is the problem: its two triplets give observed "
    + "orders of 0.45 and 2.09 and Richardson extrapolations of −8.54 % and −11.46 %. The LARGER "
    + "of the two GCIs is carried and the disagreement is reported, rather than resolved by "
    + "choosing the flattering triplet."),
  p("Co-current quantities are essentially grid-independent (GCI 0.003 to 0.19 %). All of the grid "
    + "sensitivity sits on the alternating side, where the lateral gradient across each bridge is "
    + "what the grid has to resolve. That is a physically sensible place for it to sit."),

  h("11.2 Input uncertainty — a paired Monte Carlo", 2),
  p("Two hundred samples, all accepted, on the campaign grid. Every draw is run through BOTH "
    + "arrangements with identical inputs. The pairing is not a convenience: the claim is a "
    + "DIFFERENCE, and a difference between two runs sharing one property draw and one grid has "
    + "most of its systematic error cancelled."),
  tableCaption("Table 25 — What the pairing is worth."),
  table([
    ["Quantity", "Paired sd", "sd if unpaired", "Factor"],
    ["Δ efficiency", "0.304 pp", "3.959 pp", "13.0×"],
    ["Δ plate standard deviation", "3.092 pp", "6.857 pp", "2.2×"],
    ["Δ loss coefficient", "0.848 pp", "4.682 pp", "5.5×"],
    ["Δ peak-to-peak spread", "3.464 pp", "6.696 pp", "1.9×"],
  ], [3.6, 2.2, 2.4, 1.8]),
  p("Treating the two arrangements as independent would inflate the efficiency-difference band by "
    + "thirteen times and would have made a firm result look indistinguishable from noise."),

  tableCaption("Table 26 — The thirteen sampled inputs. Every entry is an ENGINEERING_ASSUMPTION."),
  table([
    ["Input", "Nominal", "Standard uncertainty", "Basis"],
    ["k_al", "229 W/m·K", "2.0 % (rel)", "AA1050 handbook; temper and purity spread"],
    ["nu_cfd", "3.428", "5.0 % (rel)", "from this study's own 3-D CFD — see the revision below"],
    ["alpha_abs", "0.95", "0.01 (abs)", "TiNOX datasheet tolerance"],
    ["eps_abs", "0.04", "0.01 (abs)", "TiNOX datasheet tolerance"],
    ["tau_glz_sys", "0.833", "0.01 (abs)", "two-pane system"],
    ["tau_tim", "0.82", "0.02 (abs)", "homogenised PC honeycomb"],
    ["k_tim", "0.075 W/m·K", "5.0 % (rel)", "handbook, perpendicular direction"],
    ["k_vip", "0.006 W/m·K", "13.0 % (rel)", "fumed-silica VIP, 20 % derate over 25 y"],
    ["h_wind_fac", "1", "15.0 % (rel)", "scatter of the linear wind-convection correlation"],
    ["h_rear", "3 W/m²K", "0.5 (abs)", "still-air external coefficient"],
    ["mdot_total", "0.0025 kg/s", "2.0 % (rel)", "pump and flowmeter class"],
    ["G_T", "800 W/m²", "2.0 % (rel)", "class-A pyranometer"],
    ["T_amb", "298.15 K", "0.5 (abs)", "ambient measurement"],
  ], [1.8, 1.9, 2.2, 4.1], { alignRight: false }),
  p("None of these tolerances comes from a supplier datasheet, because the material table does not "
    + "carry any. They are stated here rather than buried, and the sensitivity ranking below shows "
    + "which of them actually matter."),
  ...figure(FIG + "U2_input_uncertainty.png",
    "Figure 34 — Input uncertainty: the Monte Carlo distributions.", 0.9),

  h("11.3 Sensitivity — which inputs control which answer", 2),
  tableCaption("Table 27 — Standardised regression coefficients, variance shares."),
  table([
    ["Output", "Dominant inputs (share of variance)", "Linear-model R²"],
    ["Efficiency", "tau_tim 68 %, tau_glz_sys 19 %, alpha_abs 12 %", "0.9998"],
    ["Uniformity difference", "nu_cfd 91 %, mdot_total 9 %", "0.9991"],
  ], [2.6, 5.4, 2.0], { alignRight: false }),
  p("Two things follow, and both shaped the rest of the study."),
  ...numbered([
    "Efficiency is an OPTICAL result. Ninety-nine per cent of its variance is the transmittance "
      + "chain and the absorptance — not anything thermal. No amount of thermal cleverness moves "
      + "it much; the glazing and the coating decide it.",
    "The uniformity difference is almost entirely controlled by nu_cfd, the single constant "
      + "Nusselt number carried from the 3-D CFD into the plate solver. That is the one input "
      + "worth improving, and its assumed ±5 % covers discretisation but NOT the modelling "
      + "assumption that one constant Nu represents a graded, developing channel.",
  ]),
  ...figure(FIG + "U3_sensitivity.png",
    "Figure 35 — Sensitivity: variance shares for efficiency and for the uniformity difference.",
    0.9),

  h("11.4 Iterative convergence", 2),
  tableCaption("Table 28 — Iterative contributions, three orders below the other two."),
  table([
    ["Solver", "Measure", "Value"],
    ["Conjugate plate", "outer-loop tolerance", "1e-8"],
    ["Conjugate plate", "energy balance (independent check)", "< 1e-6 %"],
    ["simpleFoam baseline", "Ux initial residual", "5.3461e-11"],
    ["simpleFoam baseline", "p initial residual", "1.5287e-08"],
    ["simpleFoam baseline", "continuity", "2.4805e-10"],
  ], [2.6, 4.4, 3.0]),
  p("Three orders of magnitude below the other two contributions, so it is not carried into the "
    + "combined band."),

  h("11.5 The final combined result", 2),
  p("Uncertainty is recombined using the MEASURED local sensitivity dQ/d(Nu) from the two "
    + "campaign revisions, rather than the Monte Carlo's rescaled coefficient, plus the "
    + "contribution of all other inputs, plus the plate-grid discretisation term."),
  tableCaption("Table 29 — Final uncertainty statement, design point, k = 2."),
  table([
    ["Quantity", "Value", "u_input", "u_numerical", "Expanded, k = 2", "Verdict"],
    ["Δ plate spread (RMS)", "−21.09 %", "4.983 pp", "2.979 pp", "± 11.61 pp", "distinguishable"],
    ["Δ efficiency", "−4.94 %", "0.393 pp", "0.099 pp", "± 0.81 pp", "distinguishable"],
    ["Δ loss coefficient", "−7.07 %", "0.442 pp", "0.087 pp", "± 0.90 pp", "distinguishable"],
    ["Δ peak-to-peak spread", "−3.64 %", "5.595 pp", "5.590 pp", "± 15.82 pp", "NOT distinguishable"],
  ], [2.8, 1.4, 1.2, 1.4, 1.7, 1.7]),
  calloutBox("What survives and what does not", [
    "The efficiency DEFICIT is firm: −4.94 % ± 0.81 pp. The alternating arrangement is less "
      + "efficient at matched flow, and that is not noise.",
    "The loss-coefficient benefit is firm: −7.07 % ± 0.90 pp.",
    "The RMS uniformity benefit survives with a wide band: −21.09 % ± 11.61 pp at the design "
      + "point, −20.83 ± 12.09 % as a campaign average.",
    "The PEAK-TO-PEAK uniformity claim does NOT survive. Its 95 % interval spans zero under every "
      + "grid and every Nusselt value tested. It should not be claimed.",
  ]),
  p("It is worth recording that an earlier version of this assessment, written before the fine "
    + "3-D grid finished, concluded that the uniformity benefit was “not yet demonstrated to "
    + "be distinguishable from zero”. With the Nusselt bias corrected, that statement is "
    + "superseded. It was correct given what was then known and wrong given what is known now, and "
    + "it is left in the project record rather than edited, so the reasoning stays traceable."),
];

// ===================================================== 12
const s12 = [
  pageBreak(),
  h("12. The largest remaining term: one Nusselt number for a graded channel", 1),
  p("The sensitivity analysis put 91 % of the uniformity difference on nu_cfd. A grid study can "
    + "bound the discretisation part of that input. It cannot bound the modelling choice of "
    + "collapsing a varying Nu(xi) to a single constant — so that choice was tested directly."),
  p("The same solver was run at 220 × 240 three ways: with a constant Nu, with the measured L3 "
    + "profile, and with that profile rescaled to the constant's developed-region mean. The third "
    + "run is what separates the cost of the profile's SHAPE from the cost of its LEVEL."),
  tableCaption("Table 30 — Closeout check A: constant Nu against the measured profile."),
  table([
    ["Nusselt model", "Δ plate spread", "Δ efficiency"],
    ["constant, 2.9238", "−21.09 %", "−4.94 %"],
    ["measured profile, rescaled to the same mean", "−6.85 %", "−5.51 %"],
    ["measured profile, as measured", "−2.14 %", "−5.88 %"],
  ], [5, 2.5, 2.5]),
  calloutBox("This is the honest limit of the uniformity claim", [
    "Collapsing Nu(xi) to one number is worth +14.24 percentage points on the uniformity "
      + "difference — LARGER than every numerical and input uncertainty in this assessment "
      + "combined.",
    "It costs only −0.57 pp on efficiency, so the efficiency result is untouched.",
    "The sign of the uniformity result does not change. Its magnitude is model-form limited, and "
      + "it must be quoted that way: the campaign carries a constant Nu, and a campaign carrying "
      + "Nu(xi) has not been run.",
  ]),
  p("For context on how much variation is being collapsed: local Nu runs from 3.29 to 3.65 over "
    + "the developed region and reaches 29.8 at the inlet, where the thermal boundary layer has "
    + "not yet formed."),
];

// ===================================================== 13
const s13 = [
  pageBreak(),
  h("13. Gate 8b — validation", 1),
  p("A word used carefully here. Agreement with the project's own design targets is "
    + "SELF-CONSISTENCY. Agreement with a model that shares none of this solver's discretisation "
    + "is closer to validation. No experimental data was used in this study, and nothing here is "
    + "claimed as experimental validation."),

  h("13.1 Against Hottel-Whillier-Bliss", 2),
  p("Matching someone else's measurement on a different collector validates the combination of "
    + "their geometry, their instrument and this model, and cannot separate the three. "
    + "Hottel-Whillier-Bliss is the standard closed-form flat-plate model, it is the accepted "
    + "reference for a bonded-fin absorber, and it shares NONE of this solver's discretisation. "
    + "Agreement with it tests the fin and flow solution directly."),
  ...code([
    "fin efficiency        F   = tanh(m (W-D)/2) / (m (W-D)/2),   m = sqrt(U_L / (k delta))",
    "collector eff. factor F'  = (1/U_L) / ( W [ 1/(U_L (D + (W-D) F)) + 1/(h_fi P) ] )",
    "heat removal factor   F_R = (mdot cp/(Ac U_L)) [1 - exp(-Ac U_L F'/(mdot cp))]",
    "efficiency            eta = F_R (tau alpha) - F_R U_L (T_in - T_amb) / G_T",
  ]),
  p("The channel is graded, so W−D, D_h, P and h_fi all vary along the flow. F and F' are "
    + "evaluated at 400 stations and averaged over the flow path; averaging the geometry first "
    + "would bias F, which is nonlinear in D. U_L is NOT fitted — it is taken from the solver's "
    + "own loss balance, so the comparison tests the fin and flow solution rather than the loss "
    + "model, which both share.", { before: 140 }),
  tableCaption("Table 31 — Solver against Hottel-Whillier-Bliss."),
  table([
    ["Arrangement", "Solver η", "HWB η", "Deviation", "U_L used"],
    ["co-current", "0.596697", "0.597995", "+0.218 %", "2.4731 W/m²K"],
    ["alternating", "0.563771", "0.601730", "+6.733 %", "2.2817 W/m²K"],
  ], [2.4, 1.9, 1.9, 1.9, 1.9]),
  p("Co-current agrees to +0.218 %. For a model with no shared discretisation and no fitted "
    + "parameter, that is a strong result, and it validates the conjugate solver's fin and flow "
    + "treatment on this geometry."),
  p("Alternating differs by +6.733 %, and that is expected and informative rather than a failure. "
    + "Hottel-Whillier-Bliss assumes every tube is alike and every fin is symmetric about its own "
    + "channel; it has no way to represent neighbours flowing in opposite directions. The 6.7 % "
    + "gap is a measure of how far the alternating arrangement departs from the classical model — "
    + "it is the part of the physics the standard model cannot see. HWB OVER-predicts, because it "
    + "cannot represent the mean-temperature rise that costs the alternating arrangement its "
    + "efficiency."),
  tableCaption("Table 32 — The analytical chain, co-current."),
  table([
    ["Quantity", "Value"],
    ["fin efficiency F, inlet", "0.9996"],
    ["fin efficiency F, outlet", "0.9994"],
    ["collector efficiency factor F'", "0.9883"],
    ["heat removal factor F_R", "0.9297"],
    ["(tau·alpha)", "0.6489"],
    ["η₀ = F_R (tau·alpha)", "0.6033"],
  ], [6, 4]),
  calloutBox("The single most physically important number in this report", [
    "The fin efficiency is 0.9995 — essentially unity. With 2 mm of aluminium at 229 W/m·K "
      + "spanning a 31.3 mm bridge against a loss coefficient near 2.5 W/m²K, the fin parameter "
      + "m(W−D)/2 is tiny and the bond land is very nearly isothermal.",
    "THIS is why the absorber conducts laterally so readily, and it is the physical basis of the "
      + "alternating mechanism. It is also why flattening the field wins so little: a plate that "
      + "conducts this well is already nearly flat.",
  ]),
  ...figure(FIG + "V1_hwb_validation.png",
    "Figure 36 — Validation against Hottel-Whillier-Bliss.", 0.9),
  ...figure(FIG + "C11_hottel_whillier.png",
    "Figure 37 — The Hottel-Whillier-Bliss efficiency curve against the campaign.", 0.9),

  h("13.2 The efficiency-curve estimator", 2),
  p("Six inlet temperatures from 288 to 338 K, fitted as the ISO 9806 / ASHRAE 93 straight line:"),
  tableCaption("Table 33 — Closeout check C: the fitted efficiency curve."),
  table([
    ["Arrangement", "η₀", "F_R·U_L (W/m²K)", "R²"],
    ["co-current", "0.60010", "1.9227", "0.999932"],
    ["alternating", "0.57053", "1.8500", "0.999939"],
  ], [3, 2.3, 2.7, 2.0]),
  p("The roadmap's design targets are η₀ = 0.60 and F_R·U_L = 2.00. The co-current fit lands on "
    + "0.60010 and 1.92. That also settles an earlier 15 % discrepancy between two estimators of "
    + "F_R·U_L: the curve-slope value is the one to quote, and the Hottel-Whillier-Bliss "
    + "point-wise product (2.2993 W/m²K) is a DIFFERENT quantity evaluated at a single operating "
    + "point. Neither should be called “the” loss coefficient without saying which "
    + "estimator produced it."),
  p("This is self-consistency with the design intent, not experimental validation, and it is "
    + "labelled as such."),

  h("13.3 The metal itself — a 2-D finite-element conduction check", 2),
  p("The plate solver lumps the two roll-bond sheets into a single conducting layer. That "
    + "assumption, and the bridge conduction it predicts, were checked against an independent "
    + "discretisation: a 2-D finite-element conduction solution in the ACTUAL roll-bond "
    + "cross-section, over one glide period, with cyclic boundaries."),
  tableCaption("Table 34 — Section conduction check."),
  table([
    ["Check", "Result"],
    ["Through-thickness temperature difference", "0.021 – 0.057 K"],
    ["Area-averaged T against the plate solver", "within −0.44 to +0.21 K"],
    ["Energy balance", "0.000 W/mm exactly"],
    ["Co-current bridge flux", "−0.00012 to +0.00013 W/mm (zero, as symmetry requires)"],
    ["Alternating bridge flux", "−0.0244 to +0.0240 W/mm → 174 W for the plate"],
    ["Campaign value for comparison", "154 W (agreement to 13 %)"],
    ["Smoothing by the metal", "15.2 K reduced to 2.01 K, a factor of 7.5"],
    ["Metal cross-section area, as meshed", "−2.33 % against CAD (known fillet deficit)"],
    ["Through-thickness value, grid convergence", "NOT converged: 0.0420 → 0.0540 K, 29 %"],
  ], [5, 5], { alignRight: false }),
  p("The three things this establishes: the plate solver's absorber temperature is right to "
    + "0.44 K; its lumped-thickness assumption is right to 0.06 K; and the alternating bridge "
    + "magnitude it predicts is confirmed to 13 % by a completely different discretisation. The "
    + "through-thickness difference itself is not grid-converged, but it is two orders of "
    + "magnitude smaller than anything that depends on it."),
  ...figure(FIG + "V2_section_conduction.png",
    "Figure 38 — The 2-D section conduction solution over one glide period.", 0.9),
  ...figure(FIG + "F10_bridge_conduction.png",
    "Figure 39 — Bridge conduction: the lateral heat path that the mechanism depends on.", 0.9),
  ...figure(FIG + "F9_temperature_distribution.png",
    "Figure 40 — Absorber temperature distribution, both arrangements.", 0.9),
];

module.exports = { s11, s12, s13 };
