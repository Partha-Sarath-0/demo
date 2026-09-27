// GRAIL Roadmap Rev I — completion status at the close of the CFD phase
const C = require("./common");
const { p, h, table, tableCaption, bullets, calloutBox, spacer, buildDoc, write,
        Paragraph, TextRun, AlignmentType, TableOfContents } = C;
const { Paragraph: P_, HeadingLevel: HL_ } = require("docx");
const h1 = (t) => new P_({ text: t, heading: HL_.HEADING_1, pageBreakBefore: true, spacing: { before: 0, after: 160 } });

const title = [
  spacer(2400),
  new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text: "THE GRAIL COLLECTOR", bold: true, size: 44, color: "1B4F7A" })], spacing: { after: 80 } }),
  new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text: "Roadmap Rev I — Completion Status (updated, Rev 4.2)", size: 32 })], spacing: { after: 300 } }),
  new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text: "Item-by-item status of the Design and Simulation Roadmap (Rev I, corrected) after the CFD phase and Stages 3, 5, 6 and 7 (ANN, NSGA-II, system model, annual analysis). The roadmap itself is not rewritten; this document records what was done, how, and what remains.", italics: true, size: 21, color: "4A4D52" })], spacing: { after: 420 } }),
  table([
    ["Item", "Value"],
    ["Roadmap version", "Rev I (corrected), 64 pages"],
    ["Phases closed", "CFD (Sections 4–8, 12, 15); ANN (10); system model and annual analysis (11, via Python, GNU Octave, Scilab Xcos; Simulink code written)"],
    ["Not done", "Section 9 topology optimisation (replaced by NSGA-II parameter optimisation on the ANN surrogate)"],
    ["Final dataset", "GRAIL_CFD_dataset_FINAL_rev4.2.csv — 300 cases, audited (Rev 4.1 data, three columns renamed)"],
    ["Main deviation", "COMSOL 6.2 → OpenFOAM v1912 (3-D) + GRAIL-CHT reduced-order conjugate model"],
    ["Experimental validation", "None yet — V5 OPEN: Gunjo 2017 rejected; new references being supplied"],
  ], [3.2, 6.8]),
];
const toc = [h1("Contents"), new TableOfContents("Contents", { hyperlink: true, headingStyleRange: "1-2" })];

const s1 = [
  h1("1. Section-by-section status"),
  table([
    ["Roadmap section", "Status", "What was done / why not"],
    ["1–3 Thesis, gaps, prior art", "REFERENCE", "Background; not a work item"],
    ["4 Design parameter set", "USED", "Groups A, B, E sampled: G_T, T_in, T_amb, v_wind, ṁ, bridge, G, λ_G, f_interdig"],
    ["5 Architecture, BOM, properties", "USED", "Material database recorded; V6 supplier datasheets not obtained"],
    ["6 Fusion 360 modelling", "DONE", "Grail_Collector_2.step, 129 solids; Gate A 12/12 invariants PASS"],
    ["7 Fusion → COMSOL", "REPLACED", "Direct NURBS evaluation and structured hex meshing for OpenFOAM"],
    ["8.1–8.6 CFD methodology", "DONE (deviation)", "OpenFOAM simpleFoam + chtMultiRegionSimpleFoam (frozenFlow); GRAIL-CHT for the campaign"],
    ["8.7 Validation", "PARTIAL", "Code-to-code (3-D conjugate) and code-to-correlation (H1 Nu, HWB); Gunjo 2017 rejected; Sun et al. not obtained"],
    ["8.8 Campaign", "DONE", "300 LHS cases, 0 rejected (Rev 4.1); log fields as specified"],
    ["9 Topology optimisation", "NOT DONE", "Replaced by NSGA-II parameter optimisation on the ANN surrogate (Stage 5); 8 optima re-run in GRAIL-CHT"],
    ["10 ANN / hybrid ANN", "DONE", "Stage 3: 10-seed MLP ensemble, test R² 0.9994–0.9998 (η), GPR benchmark, SHAP"],
    ["11 MATLAB/Simulink", "DONE (deviation)", "Stage 6/7 system model in Python, GNU Octave (PASS vs Python) and Scilab Xcos block diagram (0.04 % vs Octave); Simulink model built and run in MATLAB Online by the user (reported PASS)"],
    ["12 Results and figures", "MOSTLY DONE", "See Section 3"],
    ["13 Patent strategy", "NOT ACTIONED", "Engineering cross-check only; V1, V10 open"],
    ["14 Schedule and risk", "REFERENCE", "—"],
    ["15 Rev H corrections", "DONE", "Converging geometry (C1) used throughout; C7, C8 open (manufacturing dimensions)"],
  ], [2.8, 1.6, 5.6]),
];

const s2 = [
  h1("2. Verification register V1–V10"),
  table([
    ["#", "Item", "Status", "Evidence / note"],
    ["V1", "Prior-art null results", "OPEN", "Not run; required before any filing"],
    ["V2", "COMSOL licence", "NOT APPLICABLE", "COMSOL not used"],
    ["V3", "MATLAB licence", "DONE", "Section 11 in GNU Octave, Scilab Xcos and MATLAB/Simulink; the user ran GRAIL_simulink_complete.m in MATLAB Online and reported the result as matching (PASS vs Xcos); the printed output is to be archived in 17_Simulink_MATLAB_model"],
    ["V4", "COMSOL feature names", "NOT APPLICABLE", "OpenFOAM v1912; every solver option verified in the installed binary"],
    ["V5", "Baseline validation < 8 %", "OPEN", "Gunjo et al. 2017 assessed and rejected (its own CFD exceeds solar input; error on absolute K). New references (2024–2026) being supplied by the user for screening; no experimental validation claimed until then"],
    ["V6", "Supplier datasheets", "OPEN", "Literature properties used"],
    ["V7", "Counter-current effect on R4, matched mean T", "DONE", "GRAIL-CHT at matched plate mean 320/330/340 K (29_v7): Δη = −0.001 points, ΔR4 = +0.04 %, plate std +8 to +11 % for alternating; alternating needs ~15 K cooler inlet for the same plate temperature"],
    ["V8", "η0, a1, a2 fit", "DONE", "Stage 6 ISO 9806 fit on 22 GRAIL-CHT runs: alternating η0 0.597, a1 2.00 W/m²K; parallel η0 0.637, a1 2.10 W/m²K; held-out errors ≤ 0.24 points"],
    ["V9", "TO geometry re-simulated", "NOT APPLICABLE", "No TO"],
    ["V10", "Patent-agent review", "OPEN", "—"],
  ], [0.6, 2.8, 2.2, 4.4]),
];

const s3 = [
  h1("3. Figures (roadmap 12.1)"),
  table([
    ["#", "Figure", "Status", "Delivered as"],
    ["F1", "Grid independence", "DONE", "F01 (3-D axial), F02 (cross-section Nu), F04 (ROM axial)"],
    ["F2", "Validation curve vs Gunjo/Sun", "NOT POSSIBLE", "Reference rejected; F10 Nu envelope and F05 ROM-vs-3-D instead"],
    ["F3", "Efficiency curves conventional vs GRAIL", "PARTIAL", "GRAIL curves done (F18, Stage 6); no conventional collector modelled"],
    ["F4", "Geometry family incl. TO", "PARTIAL", "CAD report figures; no TO"],
    ["F5 / F8", "Temperature contours; counter-current side by side", "DONE", "F09 3-D rear-surface maps, same scale"],
    ["F6", "Velocity field", "DONE", "CAD/CFD report figures S3, S6; videos"],
    ["F7", "Plate/fluid T along flow", "DONE", "F08"],
    ["F9", "Temperature histogram", "DONE", "F09b"],
    ["F10", "R4 vs bridge width", "DONE", "F10b (T_R4 − T_mean vs bridge)"],
    ["F11", "Loss breakdown", "DONE", "F11"],
    ["F12", "Correlation heatmap", "DONE", "F12"],
    ["F13 / F14", "Grading result and penalty", "DONE", "F13_F14"],
  ], [0.9, 3.2, 1.6, 4.3]),
];

const s4 = [
  h1("4. The three headline numbers (roadmap 12.3)"),
  table([
    ["#", "Roadmap sentence", "Answer from the closed CFD phase"],
    ["1", "Counter-current reduced R4 by __ % at unchanged mean T, raising η by __ points",
      "ANSWERED (V7): at matched mean plate temperature counter-current changes R4 by +0.04 % (not a reduction) and η by −0.001 points (no change); plate std is 8–11 % higher. At unchanged inputs alternating runs +13.9 K hotter and −7.3 % less efficient because it needs a ~15 K cooler inlet to reach the same plate temperature"],
    ["2", "TO absorber delivered __ % more", "NOT APPLICABLE — no TO"],
    ["3", "Annual kWh/m²/year", "DONE (Stage 7, Berhampur TMY): collector yield at 40 °C inlet 1,030 (parallel) / 965 (alternating) kWh/m²/yr; POA 1,976 kWh/m²/yr"],
  ], [0.5, 3.8, 5.7]),
  calloutBox("Consequence for Filing 1", [
    "The roadmap (15.8) warns that Filing 1 is a claim about a flatter temperature field. The corrected CFD shows a flatter field only at high flow; at matched mean plate temperature (V7) the arrangements have the same efficiency and alternating is slightly less uniform at the design flow. Claim language must match this evidence.",
  ]),
];

const s5 = [
  h1("5. Roadmap 15.8 corrected sequence"),
  table([
    ["Step", "Status"],
    ["1 Re-export STEP with suppressions", "DONE (as direct geometry evaluation)"],
    ["2 Isothermal mass check within 0.1 %", "DONE — mass imbalance ~1e-9"],
    ["3 Reynolds 23.9–198.8", "DONE — Rev 4.1 Re_in 21.8–151.3 (correct non-circular definition; low end below range because ṁ bound 1.0 g/s)"],
    ["4 Validation gate 8.7", "OPEN — no experimental reference accepted yet; see V5"],
    ["5 Variants; counter-current at matched mean T", "DONE — see V7 (29_v7)"],
    ["6 w_bridge 20–60 mm with r_fillet 0.5–2.0 mm", "PARTIAL — 20–37 mm (geometric hard limit at 40 mm pitch); fillet not swept. DESIGN_REVIEW_REQUIRED"],
  ], [4.0, 6.0]),
];

const s6 = [
  h1("6. Remaining open items"),
  ...bullets([
    "V5: experimental comparison — the user is supplying 2024–2026 papers; each will be screened (tabulated data, energy check, stated boundary inputs) before use.",
        "V1 and V10: prior-art search and patent-agent review, only if a filing is planned.",
    "V6: supplier datasheets (literature properties used).",
    "C7, C8: frame wall thickness and manifold dimensions — design inputs from the user.",
    "Bridge range above 37 mm (needs a different pitch) and the fillet sweep.",
    "Design decisions recorded: 2 modules is the system design (4 modules stagnate above 420 K — overheating protection needed for larger arrays); the NSGA-II optimum at the flow bound with G → 1 means the converging channel is argued for plate uniformity, not efficiency.",
    "Deferred by choice: PCM latent heat, radiation / optical 3-D model, full 3-D campaign.",
  ]),
];

const doc = buildDoc({ title: "GRAIL Collector — Roadmap Rev I Completion Status", subtitle: "Status after CFD phase and Stages 3–7 (Rev 4.2).", sections: [title, [].concat(toc, s1, s2, s3, s4, s5, s6)] });
write(doc, "/home/claude/reports/GRAIL_Roadmap_RevI_Completion_Status_Rev4.2.docx");
