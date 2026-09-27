// GRAIL CFD Simulation Report — Rev 4 edition.
// Sections 1–17 are the Rev 2 report, kept word for word for provenance (nothing removed).
// A supersession notice is placed before them and Part V (Sections 18–24) is appended.
const fs = require("fs");
const C = require("./common");
const { p, h, table, tableCaption, figure, bullets, numbered, calloutBox, spacer, pageBreak,
        buildDoc, write, Paragraph, TextRun, AlignmentType, TableOfContents } = C;
const R1 = require("./cfd_report");
const R2 = require("./cfd_report2");
const R3 = require("./cfd_report3");
const R4 = require("./cfd_report4");
const F = "/home/claude/grail_cfd/16_figures/";
const cmp = JSON.parse(fs.readFileSync("/home/claude/grail_cfd/10_dataset/rev3_vs_rev4.json"));

const title = [
  spacer(2200),
  new Paragraph({ alignment: AlignmentType.CENTER,
    children: [new TextRun({ text: "THE GRAIL COLLECTOR", bold: true, size: 44, color: "1B4F7A" })],
    spacing: { after: 80 } }),
  new Paragraph({ alignment: AlignmentType.CENTER,
    children: [new TextRun({ text: "CFD Simulation Report — Rev 4.1 edition", size: 34, color: "1F2124" })],
    spacing: { after: 300 } }),
  new Paragraph({ alignment: AlignmentType.CENTER,
    children: [new TextRun({ text: "Sections 1–17: the Rev 2 report, unchanged, kept for provenance. "
      + "Part V (Sections 18–24): the repaired 3-D conjugate CFD, the corrected closure, Dataset Rev 4 "
      + "and the final claims. Where they differ, Part V governs.", italics: true, size: 21, color: "4A4D52" })],
    spacing: { after: 420 } }),
  table([
    ["Item", "Value"],
    ["Geometry", "Converging roll-bond absorber, 12 channels, G = 0.539935"],
    ["3-D solvers", "OpenFOAM v1912: simpleFoam; chtMultiRegionSimpleFoam (frozenFlow)"],
    ["Reduced-order conjugate model", "GRAIL-CHT (2-D plate + 1-D per-channel fluid)"],
    ["Current dataset", "Rev 4.1 — Nu 4.48, Richardson plate grid, audited; 300 / 300"],
    ["Superseded dataset", "Rev 2 (Nu 2.9238), reported in Sections 1–17"],
    ["3-D conjugate solutions", "12 converged (Section 19)"],
    ["Experimental validation", "None claimed; V5 reference rejected (Section 23)"],
    ["Hardware", "2 CPU cores, 7 GB RAM"],
  ], [3, 7]),
];

const toc = [
  pageBreak(), h("Contents", 1),
  new TableOfContents("Contents", { hyperlink: true, headingStyleRange: "1-2" }),
  p("(In Word: right-click the field and choose Update Field.)", { run: { italics: true, size: 17, color: "4A4D52" } }),
];

const notice = [
  pageBreak(),
  h("Supersession notice — read first", 1),
  p("Nothing in Sections 1–17 was deleted or edited. The statements below were correct descriptions of "
    + "what had been done at Rev 2 but are no longer the project's conclusions. Each is replaced by the "
    + "section shown."),
  tableCaption("Table R1 — Statements in Sections 1–17 that Part V supersedes."),
  table([
    ["Statement in Sections 1–17", "Status", "Now"],
    ["Nu = 2.9238 is the grid-converged closure", "SUPERSEDED", "H2-type value; conjugate Nu 4.48 (Sec. 20)"],
    ["Reported dataset Rev 2, 0 rejected", "SUPERSEDED", "Rev 4, 300 / 300 at two grids (Sec. 21)"],
    ["Efficiency difference −4.94 / −4.33 %", "SUPERSEDED", "Group mean −7.3 %, p = 2e-8 (Sec. 21)"],
    ["RMS uniformity benefit survives (−21.09 %, −11.52 %)", "WITHDRAWN", "Overall −1.1 %, n.s.; flow-dependent (Sec. 21)"],
    ["Section 14: the 3-D conjugate run did not converge", "RESOLVED", "Root cause found, repaired (Sec. 18)"],
    ["Plate grid 110 × 120 adequate", "SUPERSEDED", "First-order, ~3 pp error; Richardson used (Sec. 21)"],
    ["Uncertainty headline (Section 16)", "SUPERSEDED", "Rev 4 budget (Sec. 22)"],
  ], [4.2, 1.5, 4.3]),
];

const pv = [
  pageBreak(), h("PART V — Rev 4 / 4.1: repaired conjugate CFD and corrected results", 1),

  h("18. Root cause of the 3-D conjugate divergence, and the repair", 1),
  p("Controlled one-change experiments showed the divergence reported in Section 14 comes from the buoyant "
    + "p_rgh SIMPLE formulation on this O-grid mesh family. buoyantSimpleFoam diverges identically on the "
    + "fluid region alone (no solid, no interface) and on the previously validated single-channel mesh; "
    + "pressure reference, wall pressure condition, cell quality, relaxation, schemes and correctors were each "
    + "eliminated. After one iteration the face fluxes satisfy continuity but the cell velocities are wrong by "
    + "~10⁵ in the cross-section plane, consistent with an ill-conditioned rebuild of cell velocity from face "
    + "flux on cells micrometres thick and millimetres long (stated as consistent with the evidence; the "
    + "source line was not quoted)."),
  p("Repair: with constant ρ, μ, k and cp the steady flow does not depend on temperature. The flow is solved "
    + "with simpleFoam (which converges), then the conjugate energy equation with chtMultiRegionSimpleFoam's "
    + "frozenFlow switch — the same steady solution as a coupled solve. Verified: frozenFlow present in the "
    + "installed binary; zero pressure and momentum solves; supplied flux unchanged to 1.5e-8. Two further "
    + "errors in the old case were corrected: solar input had been applied per curved area (+12.2 %), now per "
    + "plan area (h = U·n_z); the meshed inlet carries 0.30 % less flow, so the ROM is run at the 3-D flow."),

  h("19. The 3-D conjugate benchmark", 1),
  p("Domain: 2-channel periodic strip, 1100 × 80 mm, the CAD plate. Top q″ 519.1256 W/m² minus 4.191176 "
    + "W/m²K × (T − 298.15 K) per plan area; rear 3.0 W/m²K; inlet 300 K, 2.077072e-4 kg/s per channel. A "
    + "linear loss model by design (ENGINEERING_ASSUMPTION): the benchmark tests coupling, not glazing."),
  tableCaption("Table R2 — 3-D conjugate results, alternating vs co-current."),
  table([
    ["Grid", "η co / alt", "std co / alt (K)", "Δη", "Δ std", "Δ spread", "balance"],
    ["NX 60, NU 64", "0.51484 / 0.42212", "5.771 / 5.254", "−18.01 %", "−8.96 %", "−2.52 %", "≤ 0.035 %"],
    ["NX 120, NU 64", "0.51597 / 0.41817", "5.791 / 5.508", "−18.95 %", "−4.88 %", "+3.40 %", "—"],
    ["NX 240, NU 64", "0.51594 / 0.41840", "5.784 / 5.474", "−18.91 %", "−5.37 %", "+3.07 %", "≤ 0.049 %"],
    ["NX 120, NU 48", "0.51605 / 0.41786", "5.792 / 5.526", "−19.03 %", "−4.59 %", "+3.42 %", "≤ 0.030 %"],
    ["NX 120, NU 96", "0.51586 / 0.41849", "5.789 / 5.481", "−18.88 %", "−5.32 %", "+3.20 %", "≤ 0.037 %"],
    ["Best estimate", "—", "—", "−18.9 ± 0.1 %", "≈ −6.6 ± 1.0 %", "+3.1 %", "—"],
  ], [1.9, 2.0, 1.7, 1.2, 1.3, 1.0, 1.0]),
  ...figure(F + "F01_3D_axial_grid_study.png", "Figure R1 — 3-D axial grid study: Δη converges, Δ std oscillates.", 0.95),
  ...figure(F + "F09_plate_T_maps_3D.png", "Figure R2 — 3-D rear-surface temperature, NX 240.", 0.95),
  p("Mechanism: the two counter-flowing channels form a counter-flow heat exchanger through the metal. In "
    + "the alternating case 40 % of the heat a channel absorbs (9.94 of 24.80 W) is handed back to the plate "
    + "over 41 % of its length; the fluid peaks mid-channel (328.6 K) and leaves cooler (317.1 K) than in "
    + "co-current flow (320.9 K)."),
  ...figure(F + "F08_heat_recirculation_alt.png", "Figure R3 — Heat recirculation, alternating, NX 60.", 0.95),

  h("20. The corrected Nusselt closure", 1),
  p("Nu 2.9238 (Sections 1–17) came from a fluid-only case with heat flux uniform around the perimeter — "
    + "the H2 condition. The aluminium wall is close to isothermal around the perimeter (H1). The 3-D "
    + "conjugate developed-region Nu is 4.646 / 4.602 / 4.556 on NU 48 / 64 / 96 (p = 1.12), extrapolated "
    + "to 4.48 (GCI 2.1 %); it is axially converged (4.592 / 4.602 / 4.602) and flow-independent (4.599 at "
    + "1.0 g/s). Reference H1, semicircular duct: 4.088 (Erdoğan & Imrak 2005), 4.089 (Shah & London table in "
    + "Hesselgreaves 2001). The H2 value ≈ 2.92 is recalled, not verified; nothing depends on it."),
  ...figure(F + "F02_Nu_cross_section_study.png", "Figure R4 — Cross-section grid study of the conjugate Nu.", 0.75),
  ...figure(F + "F03_Nu_profiles.png", "Figure R5 — Local Nu along the channel: grid levels and flow envelope.", 0.95),
  ...figure(F + "F10_Nu_envelope.png", "Figure R6 — Co-current plate std, 3-D vs ROM across the flow envelope.", 0.7),
  p("ROM check: with the conjugate Nu, GRAIL-CHT reproduces the co-current 3-D solution to 0.01 % in η and "
    + "0.6 % in std. For the alternating arrangement it overstates the uniformity benefit by ≈ 2.0 pp and "
    + "understates the efficiency penalty by ≈ 0.5 pp, because local Nu is undefined where q′ changes sign."),
  ...figure(F + "F04_ROM_vs_3D_axial.png", "Figure R7 — ROM axial convergence (p = 1.01) against the 3-D result.", 0.75),
  ...figure(F + "F05_ROM_vs_3D_bars.png", "Figure R8 — ROM vs 3-D per arrangement, design point.", 0.9),

  h("21. Dataset Rev 4", 1),
  p("Changed from Rev 3: Nu 2.9238 → 4.48, and plate grid 110 → 110 and 220 with per-row Richardson "
    + "2f(220) − f(110). Unchanged: seed, Latin Hypercube, bounds, geometry gate, k(T), acceptance gates "
    + "(tolerance 1e-6 asserted, |energy error| < 0.5 %, 250 < T_plate < 500 K). Iteration cap 900 → 3000. "
    + "300 / 300 accepted at both grids; no row deleted; Rev 1–3 untouched."),
  p("Rev 4.1 then corrected three derived-column groups found by an independent audit (radiative temperature "
    + "quantities, U_L, Reynolds number); every thermal result is unchanged. Details: Correction Report §6.1 and the "
    + "Rev 4.1 change log."),
  tableCaption("Table R3 — Arrangement comparison, Rev 4.1, two independent 150-case groups (unpaired)."),
  table([
    ["Quantity", "Parallel", "Alternating", "Difference", "Mann–Whitney p"],
    ["η, mean", "0.5620", "0.5209", "−7.3 %", "2e-8"],
    ["Plate std, median (K)", "5.013", "4.960", "−1.1 %", "0.76 (n.s.)"],
    ["Plate spread, median (K)", "16.57", "19.61", "+18.4 %", "0.001"],
    ["Mean plate T", "—", "—", "+13.9 K", "2e-10"],
  ], [2.6, 1.6, 1.7, 1.7, 1.8]),
  tableCaption("Table R4 — Rev 4.1 by total flow rate (unpaired)."),
  table([
    ["Total flow", "Δ mean η", "Δ median plate std", "p (std)"],
    ["1.0 – 2.2 g/s", "−12.7 %", "+16.8 %", "0.03"],
    ["2.2 – 3.3 g/s", "−6.0 %", "+7.9 %", "0.14 (n.s.)"],
    ["3.3 – 4.5 g/s", "−3.5 %", "−13.4 %", "0.02"],
  ], [2.2, 2, 2.4, 2]),
  p("ALT_n and PAR_n come from two independent Latin-Hypercube draws and do not share inputs; the groups are "
    + "statistically identical in every input (KS p = 1.00). All comparisons are therefore group-wise. Paired statistics "
    + "in earlier drafts are withdrawn."),
  ...figure(F + "F06_arrangement_groups_rev41.png", "Figure R9 — Arrangement groups, Rev 4.1 (unpaired).", 0.95),
  ...figure(F + "F07_arrangement_by_flow_rev41.png", "Figure R10 — Arrangement differences by flow tercile, Rev 4.1 (unpaired).", 0.95),
  ...figure(F + "F09b_F10b_distribution_bridge_rev41.png", "Figure R11 — Plate-std distributions and radiative excess temperature vs bridge width, Rev 4.1.", 0.95),
  ...figure(F + "F11_loss_breakdown_rev41.png", "Figure R12 — Loss breakdown, group means (signed net flows).", 0.6),
  ...figure(F + "F12_correlation_heatmap_rev41.png", "Figure R13 — Pearson correlation, inputs vs outputs.", 0.8),
  ...figure(F + "F13_F14_grading_rev41.png", "Figure R14 — Efficiency and pressure drop against grading ratio G.", 0.95),
  p("The 35 rows needing more than 900 iterations are all alternating low-flow cases; a subset that excludes "
    + "them is biased in favour of the alternating arrangement and is not used as a result."),

  h("22. Uncertainty budget (Rev 4, design flow)", 1),
  table([
    ["Source", "Δη", "Δ std"],
    ["3-D discretisation", "± 0.1 pp", "± 1.0 pp (bound)"],
    ["ROM axial after Richardson", "< 0.1 pp", "≈ 0.4 pp"],
    ["ROM model form (alternating)", "0.5 pp", "2.0 pp"],
    ["Nu band 4.46 – 4.65", "≈ 0.1 pp", "≈ 1.1 pp"],
    ["Entry-region Nu at 4.5 g/s", "< 0.1 %", "≤ 2.1 % of std"],
    ["Glazing / radiation loss model", "not quantified", "not quantified"],
  ], [4.6, 2.6, 2.8]),

  h("23. Roadmap V5 — experimental reference assessed", 1),
  p("Gunjo, Mahanta & Robi, Renewable Energy 2017 (doi:10.1016/j.renene.2016.12.041) was read in full and "
    + "rejected as a reference (DESIGN_REVIEW_REQUIRED): its simulated outlet rise (≈ 33 K at noon) needs "
    + "1.7–3.4 kW against ≈ 1.53 kW of total solar input; its error is taken on absolute kelvin, hiding a "
    + "> 100 % error on the temperature rise; its measured outlet does not respond to a doubled flow rate "
    + "(implying η ≈ 95 % against its own 56 %); wind speed and (ατ) are not given and tube thickness is "
    + "stated two ways; and it is a sheet-and-tube, not roll-bond, collector. No GRAIL result is compared "
    + "with it. There is no experimental validation in this study."),

  h("24. Final claims", 1),
  h("24.1 Supported", 2),
  p("The 40 % heat-return figure: 9.94 of 24.80 W per channel returned over 41 % of the length (3-D, NX 60, design point); net 14.86 W against ṁc_pΔT = 14.85 W. It needs the full channel length including end segments; quote as ≈ 40 %."),
  ...bullets([
    "Alternating flow lowers efficiency: group mean −7.3 % (p = 2e-8), lower in every flow tercile.",
    "Plate uniformity depends on flow rate: better at high flow (−13.4 % median std above 3.3 g/s), worse at low "
      + "flow (+16.8 % below 2.2 g/s); overall −1.1 %, not significant.",
    "The alternating plate runs hotter: +13.9 K mean, +12.6 K mean P90.",
    "Mechanism: counter-flow heat recirculation through the plate (40 % of absorbed heat returned).",
    "The conjugate channel Nu is 4.48 (H1-type), not 2.92.",
    "GRAIL-CHT with that closure matches 3-D co-current flow closely; it overstates the alternating "
      + "uniformity benefit by ≈ 2 pp.",
  ]),
  h("24.2 Not to be claimed", 2),
  ...bullets([
    "A general uniformity benefit of alternating flow, or one 'at no cost'.",
    "Any ALT_n-vs-PAR_n paired statistic (they are independent samples).",
    "Any Rev 1–3 arrangement number as final.",
    "A geometric taper benefit (a constant-Nu model cannot see one).",
    "A reduced peak-to-peak plate temperature (group median +18.4 %).",
    "Experimental validation of any kind.",
    "Mesh-independent Δ std from the 3-D study (bounded, not extrapolated).",
    "3-D validation of the glazing, radiation, PCM or VIP models.",
  ]),
  calloutBox("Scope", [
    "CFD phase complete. No ANN, surrogate, optimisation or systems modelling was performed.",
  ]),
];

const doc = buildDoc({
  title: "GRAIL Collector — CFD Simulation Report (Rev 4.1 edition)",
  subtitle: "Rev 2 report retained for provenance, with Part V: repaired conjugate CFD and Rev 4.",
  sections: [title, [].concat(toc, notice, R1.s1, R1.s2, R1.s3, R1.s4, R1.s5,
    R2.s6, R2.s7, R2.s8, R2.s9, R2.s10, R3.s11, R3.s12, R3.s13,
    R4.s14, R4.s15, R4.s16, R4.s17, pv)],
});
write(doc, "/home/claude/reports/GRAIL_CFD_Simulation_Report_Rev4.1.docx");
