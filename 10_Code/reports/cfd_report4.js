// GRAIL CFD Simulation Report — sections 14 onwards + build
const C = require("./common");
const { p, h, table, tableCaption, figure, bullets, numbered,
        calloutBox, spacer, pageBreak, buildDoc, write,
        Paragraph, TextRun, AlignmentType } = C;
const R1 = require("./cfd_report");
const R2 = require("./cfd_report2");
const R3 = require("./cfd_report3");
const { FIG, eq, code } = R1;

// ===================================================== 14
const s14 = [
  pageBreak(),
  h("14. Gate 9 — the 3-D conjugate run that did not converge", 1),
  p("This section reports a failure. It is here because the alternative — listing it as an "
    + "“open item” and letting a reader assume it was simply not reached — would "
    + "misrepresent what was done."),

  h("14.1 What was built and verified", 2),
  p("A two-region mesh of the roll-bond absorber: the fluid channels and the surrounding metal, "
    + "sharing wall nodes exactly so the conjugate interface is conformal by construction."),
  tableCaption("Table 35 — The two-region mesh: every acceptance test passed."),
  table([
    ["Check", "Result"],
    ["Inverted cells", "0 at every level tested (NU 64, 96, 192)"],
    ["Conjugate interface", "conformal at exactly NU × NX × 2 faces"],
    ["Fluid skewness", "0.63, against 1.24 on the validated baseline mesh"],
    ["Coincident-node weld", "427 nodes welded by KD-tree union-find, tolerance 1e-6"],
    ["Metal cross-section area", "83.29 mm² at NU 96 → 83.33 mm² at NU 192 (converging)"],
    ["Known deficit", "−2.2 % as meshed, −3.14 % as a converged continuum integral (corner fillet)"],
  ], [3.6, 6.4], { alignRight: false }),
  p("Building that mesh took a sequence of non-obvious fixes, each of which is a real lesson about "
    + "this geometry:"),
  ...bullets([
    "Ring resampling had to be distribution-preserving, not uniform-arc. Uniform-arc resampling "
      + "took fluid skewness from 1.24 to 3.34; pinning the corners as fixed node indices and "
      + "preserving each branch's original node spacing brought it to 0.63.",
    "The channel corner is not a node. Because the root fillet is CONCAVE, the widest point of "
      + "the section sits at z = 0.447 mm and the wall reaches z = 0 only 0.54 mm further in. A "
      + "monotonicity assertion built on the assumption that the corner is a node failed at "
      + "station 0 by 0.9 micrometres in y and 0.155 mm in z.",
    "The two channels had to be snapped to a uniform station ladder. They run in OPPOSITE "
      + "directions, so a 1.4e-5 mm mismatch in x meant the coincident-node weld found 14 of 427 "
      + "nodes instead of all of them.",
    "The inlets initially fed BOTH channels at the narrow end, because the feed ends were assumed "
      + "rather than read from the mesh metadata. The generator now records feed_ends and asserts "
      + "the two inlet x-coordinates differ.",
  ]),

  h("14.2 What failed", 2),
  p("chtMultiRegionSimpleFoam diverges from the first iteration: maximum |U| reaches 155 m/s "
    + "against an expected 0.00745 m/s. Six OpenFOAM dictionary errors were found and fixed first "
    + "(constant/g at the case root, turbulenceProperties, 0/solid/p, the top-level system "
    + "fvSchemes and fvSolution, and a leading + on a scalar), so the case is well-formed. Seven "
    + "further solver-setting changes were then tried, including transplanting the exact scheme "
    + "and relaxation set from the validated baseline case. None fixed it."),
  calloutBox("The diagnosis, and why it is stated as open", [
    "simpleFoam on the IDENTICAL fluid region is stable, with maximum |U| of 0.098 m/s. The mesh "
      + "is therefore solvable; the compressible segregated multi-region solver on it is not.",
    "No conjugate result is reported anywhere in this study. The attempt is documented in full in "
      + "the project record.",
    "The question this run was meant to close was answered instead by the independent 2-D "
      + "finite-element conduction solution of Section 13.3 — which confirms the plate solver's "
      + "absorber temperature to 0.44 K, its lumped-thickness assumption to 0.06 K, and its "
      + "alternating bridge magnitude to 13 %.",
  ]),
  ...figure(FIG + "M7_cfd_mesh_in_assembly.png",
    "Figure 41 — The CFD mesh in its place in the full assembly.", 0.95),
  ...figure(FIG + "M8_cutaway.png",
    "Figure 42 — Cutaway of the meshed absorber.", 0.95),
  ...figure(FIG + "M9_inlet_end.png",
    "Figure 43 — Detail at the inlet end.", 0.85),
];

// ===================================================== 15
const s15 = [
  pageBreak(),
  h("15. The two patent-supporting studies", 1),
  p("Filings 2 and 3 concern the graded PCM tray and the thermotropic glazing layer. Both were "
    + "simulated on the same conjugate plate solver, in transient mode for the PCM and in steady "
    + "state for the thermotropic layer."),

  h("15.1 The graded PCM tray (Filing 2)", 2),
  p("RT55 with 10 % expanded graphite: solid 880 / 2000 / 2.80, liquid 770 / 2200 / 2.40, latent "
    + "heat 170 kJ/kg across 51–57 °C. The apparent-heat-capacity form is used, "
    + "c_eff = c_p(f) + L·df/dT, with a linear liquid fraction over the 6 K interval — the form "
    + "the design roadmap itself specifies. The tray is one lumped node per plate cell, eliminated "
    + "analytically each time step so the plate-tray coupling stays fully implicit."),
  p("Each scenario is run TWICE: once with latent capacity, and once with the tray as a pure "
    + "resistance with no capacity. The difference between the two is what the PCM actually buys."),
  tableCaption("Table 36 — PCM transient scenarios."),
  table([
    ["Scenario", "Peak plate T with tray", "Without", "Benefit", "Largest difference", "Stored"],
    ["Charge, cold start at design point, 4 h", "59.0 °C", "61.5 °C", "−2.5 K",
      "+10.7 K at 900 s", "1.07 MJ/m², f_liq 0.471"],
    ["Cloud, irradiance to zero for 2 h", "53.5 °C", "54.7 °C", "−1.2 K",
      "+18.9 K at 1200 s", "−0.00 MJ/m², f_liq 0.000"],
    ["Stagnation, flow cut to 2 %, 1000 W/m², 4 h", "205.3 °C", "263.8 °C", "−58.5 K",
      "+134.4 K at 4200 s", "4.23 MJ/m², f_liq 1.000"],
  ], [3.0, 1.7, 1.1, 1.1, 1.6, 1.8], { alignRight: false }),
  p("Stagnation is where the tray earns its place: peak plate temperature falls from 264 °C to "
    + "205 °C while the tray absorbs 4.23 MJ/m² and melts completely. During charging it is nearly "
    + "free, and on cloud passage it buffers and gives back exactly what it stored — liquid "
    + "fraction returns to 0.000 and stored energy to −0.001 MJ/m²."),
  calloutBox("The caveat that decides how this may be claimed", [
    "At stagnation the model runs the tray to 200 °C. RT55 is a paraffin and would have "
      + "decomposed long before that. The apparent-heat-capacity formulation contains no "
      + "degradation, no vapour pressure and no upper service limit, so it will report protection "
      + "a real tray could not deliver more than once.",
    "That is itself the design finding. The 58 K stagnation benefit is real in the model and "
      + "CONDITIONAL in hardware: it holds only if the tray stays below its decomposition "
      + "temperature, which on this collector means the stagnation problem must be solved by "
      + "something else before the PCM can be relied on for it.",
    "The charge and cloud results, which stay inside 51–62 °C, are not subject to this caveat.",
  ]),
  p("Numerics: grid 110 × 120, dt = 10 s, implicit Euler. The time step was verified in closeout "
    + "check B at dt = 20, 10 and 5 s. Refining 20 → 10 s moves the mean plate temperature by "
    + "+0.068 K and the stored energy by +1.55 %; refining 10 → 5 s moves them by +0.033 K and "
    + "+0.76 %. Both ratios are close to one half, which is the first-order convergence backward "
    + "Euler requires, and Richardson extrapolation puts dt = 5 s within 0.033 K of converged. "
    + "The PCM time step is adequate and no PCM result changes."),
  p("One stated simplification: lateral conduction inside the PCM is neglected. k_pcm × t_pcm is "
    + "0.028 W/K against the absorber's 0.458 W/K, so the tray carries about 6 % of the plate's "
    + "in-plane conductance and cannot redistribute heat on these timescales."),
  ...figure(FIG + "P1_pcm_transient.png",
    "Figure 44 — PCM transients: charge, cloud passage and stagnation.", 0.95),
  ...figure(FIG + "P3_pcm_state.png",
    "Figure 45 — PCM state: liquid fraction and stored energy through each scenario.", 0.9),

  h("15.2 The thermotropic glazing layer (Filing 3)", 2),
  p("The question asked was not “does scattering reduce absorbed flux” — it must — but "
    + "two sharper ones: does the layer ever reach its own switching band in service, and what "
    + "does it cost when switching is not wanted? Both matter because the layer is passive and "
    + "cannot tell overheating from a good day."),
  p("Modelling note: what is applied is the RATIO tau(T)/tau_clear multiplying the established "
    + "system transmittance, not tau(T) itself. That keeps the clear-state baseline exactly as "
    + "established (tau_glz_sys = 0.833, q″ = 519.1 W/m² at 800 W/m²) and applies only the "
    + "switching effect."),
  tableCaption("Table 37 — Result 1: the layer never switches where it is currently placed."),
  table([
    ["G_T (W/m²)", "Flow", "Peak glazing T", "Peak absorber T"],
    ["400", "trickle", "32.2 °C", "117.6 °C"],
    ["400", "stagnation", "35.5 °C", "142.1 °C"],
    ["600", "trickle", "38.2 °C", "161.7 °C"],
    ["600", "stagnation", "42.9 °C", "194.6 °C"],
    ["800", "design", "25.2 °C", "61.5 °C"],
    ["800", "quarter", "35.3 °C", "141.1 °C"],
    ["800", "trickle", "44.2 °C", "203.5 °C"],
    ["800", "stagnation", "50.2 °C", "242.0 °C"],
    ["1000", "trickle", "50.3 °C", "242.7 °C"],
    ["1000", "stagnation", "57.3 °C", "284.9 °C"],
    ["1200", "trickle", "56.4 °C", "279.5 °C"],
    ["1200", "stagnation", "64.3 °C", "323.7 °C"],
  ], [2, 2.6, 2.7, 2.7]),
  p("Across the whole envelope — up to 1200 W/m² at stagnation — the glazing peaks at 64.3 °C, "
    + "below its own 72 °C switching threshold. It never switches, anywhere."),
  p("The reason is the transparent insulation, and it is doing exactly its job: at 1200 W/m² "
    + "stagnation the absorber reaches 324 °C while the glass sits 259 K below it. A layer that "
    + "senses GLASS temperature is blind to the condition it exists to protect against."),
  tableCaption("Table 38 — Result 2: the same layer, moved onto the absorber."),
  table([
    ["Operating point", "Glazing-mounted", "Absorber-mounted"],
    ["design", "dTp_max +0.0 K, dη +0.00 %", "dTp_max +0.0 K, dη +0.00 %"],
    ["high irradiance (1000 W/m², design flow)", "dTp_max +0.0 K, dη +0.00 %",
      "dTp_max +0.0 K, dη +0.00 %"],
    ["trickle", "dTp_max +0.0 K, dη +0.00 %", "dTp_max −112.8 K, dη −52.51 %"],
    ["stagnation", "dTp_max +0.0 K, dη +0.00 %", "dTp_max −127.9 K, dη −49.57 %"],
  ], [3.6, 3.2, 3.2], { alignRight: false }),
  p("At the design point and at 1000 W/m² with design flow, BOTH placements do nothing at all — "
    + "exactly 0.000 K and 0.000 %. The absorber peaks at 70.3 °C there, just under the 72 °C "
    + "threshold, so an absorber-coupled layer costs nothing during normal collection. At trickle "
    + "flow it removes 112.8 K of peak plate temperature, and at stagnation 127.9 K."),
  p("The efficiency figures for those two cases should not be read as a loss worth weighing: at "
    + "trickle flow efficiency is already 0.175, and at stagnation it is 0.002. Halving a number "
    + "that small is not a cost; it is the point."),
  calloutBox("Verdict for the filing, and one unresolved question", [
    "The mechanism works and the PLACEMENT decides everything. In the glazing stack, following "
      + "glass temperature, the layer is inert across the entire operating envelope. Coupled to "
      + "the absorber, it gives passive overheating protection worth 128 K at stagnation for zero "
      + "cost in normal collection.",
    "This is a steady-state result. Switching speed, cycling, and the transient into stagnation "
      + "are not modelled.",
    "DESIGN_REVIEW_REQUIRED: tau_glz_sys = 0.833 is two panes of low-iron glass (0.91² = 0.828) "
      + "and does not visibly account for a thermotropic layer, yet the CAD carries "
      + "THERMOTROPIC_LAYER_T2 as a separate body. Either 0.833 already absorbs the layer's "
      + "clear-state transmittance, or the baseline optical chain omits a real optical element "
      + "and overstates absorbed flux by roughly 12 %. This cannot be resolved from the roadmap "
      + "and needs a human decision. The ratio formulation used here is the conservative reading.",
  ]),
  ...figure(FIG + "P2_thermotropic.png",
    "Figure 46 — Thermotropic layer: glazing and absorber temperatures across the envelope.", 0.95),
  ...figure(FIG + "P4_thermotropic_effect.png",
    "Figure 47 — The effect of the layer at each placement and operating point.", 0.9),
];

// ===================================================== 16
const s16 = [
  pageBreak(),
  h("16. The correction register", 1),
  p("Seventeen corrections were raised during this work. Each records the old assumption, the "
    + "corrected one, the reason, what it affects, and — the column that matters — whether prior "
    + "results had to be discarded."),
  tableCaption("Table 39 — Correction register, summarised."),
  table([
    ["ID", "What changed", "Discard old results?"],
    ["CR-01", "Channel DIVERGES → channel CONVERGES, D_h 5.199 → 2.807 mm", "YES — scientifically invalid"],
    ["CR-02", "Single glazing 0.91 → two-pane system 0.833; q″ 567.1 → 519.1 W/m²",
      "YES for anything computed from 0.91"],
    ["CR-03", "Symmetry planes are not valid under alternating flow", "Closed by Gate 6 — no"],
    ["CR-04", "lambda_G confirmed = 1.0 against the as-built geometry", "No"],
    ["CR-05", "Root fillet 1.0 → 0.5 mm; at 1.0 mm G = 0.54 is unreachable",
      "YES for any G = 0.54 result at 1.0 mm"],
    ["CR-06", "Bridge 34.8 mm → 31.286 mm as built; sweep 20–37 mm", "No"],
    ["CR-07", "Manifold pockets deliberately reduced by ~452.9 mm³", "No — deliberate"],
    ["CR-08", "WITHDRAWN — its premise was wrong", "—"],
    ["CR-09", "The geometry is faithful; the MEASUREMENT TOOL was wrong (OCC, −0.72 %)",
      "YES — discard CR-08 itself"],
    ["CR-10", "Assembly renders rebuilt on the corrected STEP", "YES — old renders withdrawn"],
    ["CR-11", "Manifold barrels rendered without port holes; solid at nominal 1.0 mm",
      "No — rendering only, quantified"],
    ["CR-12", "Bridge contrast must be quoted absolutely, never as a ratio to zero", "No"],
    ["CR-13", "nu_cfd 3.4282 → 2.9238; the whole campaign recomputed",
      "No — Rev 1 kept; Rev 2 supersedes"],
    ["CR-14", "Rev 1's campaign average was censored by 9 low-flow alternating rows",
      "No result discarded; the headline changes"],
    ["CR-15", "The 1.81 g/s mass-flow threshold is withdrawn", "YES — withdraw the claim"],
    ["CR-16", "Constant Nu is the largest model-form term: +14.24 pp",
      "No — but the claim is model-form limited"],
    ["CR-17", "The 3-D conjugate run was attempted and failed, not merely pending",
      "No — nothing was reported from it"],
  ], [1, 6.2, 2.8], { alignRight: false }),
];

// ===================================================== 17
const s17 = [
  pageBreak(),
  h("17. What this study establishes, and what is still open", 1),

  h("17.1 The four claims, as they finally stand", 2),
  tableCaption("Table 40 — Final statement of results, k = 2."),
  table([
    ["Claim", "Design point", "Campaign average", "Verdict"],
    ["Efficiency difference", "−4.94 ± 0.81 %", "−4.33 ± 2.34 %", "FIRM — a deficit, not a gain"],
    ["Loss-coefficient difference", "−7.07 ± 0.90 %", "—", "FIRM"],
    ["Plate spread, RMS", "−21.09 ± 11.61 %", "−20.83 ± 12.09 %", "REAL, but model-form limited"],
    ["Plate spread, peak-to-peak", "−3.64 ± 15.82 %", "−11.57 ± 12.06 %", "NOT distinguishable — do not claim"],
    ["Mean plate temperature", "—", "+2.62 ± 1.11 %", "alternating runs hotter"],
    ["Loss coefficient U_L", "—", "−0.90 ± 22.93 %", "NOT distinguishable over the campaign"],
  ], [3.0, 2.2, 2.2, 2.6], { alignRight: false }),
  p("The plain-language version: the alternating arrangement really does flatten the absorber "
    + "temperature field, and roughly 20 W per bridge midline of lateral conduction is what does "
    + "it. But at matched mass flow it costs about 5 % of efficiency, and the radiative loss it "
    + "was meant to reduce is already under 1 % of the absorbed energy because the selective "
    + "coating has taken it. The homogenisation is the defensible claim. The efficiency gain is "
    + "not, and the peak-to-peak uniformity gain is not."),

  h("17.2 What is still open", 2),
  ...bullets([
    "Nu(xi) in the campaign. Section 12 bounds the effect at +14.24 pp but does not remove it. "
      + "This is the largest single outstanding item.",
    "A fourth 3-D grid level, to tighten the 11.6 % GCI on Nu. Estimated at more than 20 hours on "
      + "two cores and declared infeasible here rather than quietly skipped.",
    "A converged 3-D conjugate run. The mesh is built and verified; the solver is not.",
    "No experimental validation. Every “validation” in Section 13 is either "
      + "self-consistency with the design targets or agreement with an independent analytical "
      + "model. No measurement of a real GRAIL collector has been used.",
    "The alternating mechanism on a NON-selective absorber (eps = 0.9 instead of 0.04), which is "
      + "the configuration in which it should actually pay.",
    "DESIGN_REVIEW_REQUIRED: whether tau_glz_sys = 0.833 already includes the thermotropic layer.",
    "Temperature-dependent viscosity in the 3-D baseline. It does not enter the thermal result "
      + "while Nu is held constant, so it affects pressure drop and pumping power only — but that "
      + "is an assumption, not a proof, and it is untested.",
  ]),

  h("17.3 Scope boundary", 2),
  p("This report ends where the CFD phase ends. No artificial neural network, machine-learning "
    + "surrogate, optimisation, topology optimisation, systems simulation or annual-performance "
    + "model was built, and none is implied by anything above."),
];

// ===================================================== build
const doc = buildDoc({
  title: "GRAIL Collector — CFD Simulation Report",
  subtitle: "Complete methodology, results and verification of the GRAIL CFD study.",
  sections: [
    R1.title,
    [].concat(R1.toc, R1.s1, R1.s2, R1.s3, R1.s4, R1.s5,
              R2.s6, R2.s7, R2.s8, R2.s9, R2.s10,
              R3.s11, R3.s12, R3.s13,
              s14, s15, s16, s17),
  ],
});

module.exports = { s14, s15, s16, s17 };
if (require.main === module) write(doc, "/home/claude/reports/GRAIL_CFD_Simulation_Report.docx");
