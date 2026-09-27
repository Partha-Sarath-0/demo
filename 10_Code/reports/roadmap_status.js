// GRAIL Roadmap Rev I — completion status at the close of the CFD phase
const C = require("./common");
const { p, h, table, tableCaption, bullets, calloutBox, spacer, buildDoc, write,
        Paragraph, TextRun, AlignmentType, TableOfContents } = C;
const { Paragraph: P_, HeadingLevel: HL_ } = require("docx");
const h1 = (t) => new P_({ text: t, heading: HL_.HEADING_1, pageBreakBefore: true, spacing: { before: 0, after: 160 } });

const title = [
  spacer(2400),
  new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text: "THE GRAIL COLLECTOR", bold: true, size: 44, color: "1B4F7A" })], spacing: { after: 80 } }),
  new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text: "Roadmap Rev I — Completion Status", size: 32 })], spacing: { after: 300 } }),
  new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text: "Item-by-item status of the Design and Simulation Roadmap (Rev I, corrected) at the close of the CFD phase. The roadmap itself is not rewritten; this document records what was done, how, and what remains.", italics: true, size: 21, color: "4A4D52" })], spacing: { after: 420 } }),
  table([
    ["Item", "Value"],
    ["Roadmap version", "Rev I (corrected), 64 pages"],
    ["Phase closed", "CFD (roadmap Sections 4–8, 12, 15)"],
    ["Stop point", "Sections 9–11 (topology optimisation, ANN, Simulink) deliberately NOT started"],
    ["Final dataset", "GRAIL_CFD_dataset_FINAL_rev4.1.csv — 300 cases, audited"],
    ["Main deviation", "COMSOL 6.2 → OpenFOAM v1912 (3-D) + GRAIL-CHT reduced-order conjugate model"],
    ["Experimental validation", "None — V5 reference assessed and rejected"],
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
    ["9 Topology optimisation", "NOT STARTED", "Outside the CFD-phase scope (stop rule)"],
    ["10 ANN / hybrid ANN", "NOT STARTED", "Outside scope"],
    ["11 MATLAB/Simulink", "NOT STARTED", "Outside scope"],
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
    ["V3", "MATLAB licence", "NOT APPLICABLE", "Section 11 not started"],
    ["V4", "COMSOL feature names", "NOT APPLICABLE", "OpenFOAM v1912; every solver option verified in the installed binary"],
    ["V5", "Baseline validation < 8 %", "CLOSED — REFERENCE REJECTED", "Gunjo et al. 2017 internally inconsistent (its own CFD exceeds solar input; error on absolute K). DESIGN_REVIEW_REQUIRED if an experimental check is mandatory"],
    ["V6", "Supplier datasheets", "OPEN", "Literature properties used"],
    ["V7", "Counter-current effect on R4, matched mean T", "PARTIAL", "Arrangement effect quantified group-wise (Rev 4.1) and in the 3-D benchmark at matched flow and inputs; NOT at matched mean plate temperature as specified"],
    ["V8", "η0, a1, a2 fit", "PARTIAL", "HWB linear fits: parallel η = 0.601 − 2.00x (r 0.96), alternating 0.557 − 1.92x (r 0.78)"],
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
    ["F3", "Efficiency curves conventional vs GRAIL", "PARTIAL", "HWB fits in the report; no conventional collector modelled"],
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
      "CANNOT BE COMPLETED AS WORDED. At unchanged inputs (not matched mean T) the alternating arrangement RAISES the mean plate temperature (+13.9 K) and T_R4 (+13.9 K) and LOWERS η (−7.3 % relative). Plate std: −13.4 % above 3.3 g/s, +16.8 % below 2.2 g/s, n.s. overall"],
    ["2", "TO absorber delivered __ % more", "NOT APPLICABLE — no TO"],
    ["3", "Annual kWh/m²/year", "NOT APPLICABLE — no Simulink / annual model"],
  ], [0.5, 3.8, 5.7]),
  calloutBox("Consequence for Filing 1", [
    "The roadmap (15.8) warns that Filing 1 is a claim about a flatter temperature field. The corrected CFD shows a flatter field only at high flow, and hotter plates and lower efficiency throughout. Claim language must match this evidence.",
  ]),
];

const s5 = [
  h1("5. Roadmap 15.8 corrected sequence"),
  table([
    ["Step", "Status"],
    ["1 Re-export STEP with suppressions", "DONE (as direct geometry evaluation)"],
    ["2 Isothermal mass check within 0.1 %", "DONE — mass imbalance ~1e-9"],
    ["3 Reynolds 23.9–198.8", "DONE — Rev 4.1 Re_in 21.8–151.3 (correct non-circular definition; low end below range because ṁ bound 1.0 g/s)"],
    ["4 Validation gate 8.7", "CLOSED WITHOUT EXPERIMENT — see V5"],
    ["5 Variants; counter-current at matched mean T", "Variants DONE; matched-mean-T comparison NOT DONE"],
    ["6 w_bridge 20–60 mm with r_fillet 0.5–2.0 mm", "PARTIAL — 20–37 mm (geometric hard limit at 40 mm pitch); fillet not swept. DESIGN_REVIEW_REQUIRED"],
  ], [4.0, 6.0]),
];

const s6 = [
  h1("6. Remaining open items"),
  ...bullets([
    "V1 and V10: prior-art search and patent-agent review before any filing.",
    "V5: an experimental reference that tabulates data and passes an energy check, if an experimental validation is required.",
    "V7 as specified: counter-current vs parallel at matched mean plate temperature; and matched-input counterfactual runs if case-by-case statistics are wanted.",
    "Bridge range above 37 mm (needs a different pitch) and the fillet sweep.",
    "C7, C8: frame wall thickness and manifold dimensions.",
    "Sections 9–11 (TO, ANN, Simulink): not started by design.",
  ]),
];

const doc = buildDoc({ title: "GRAIL Collector — Roadmap Rev I Completion Status", subtitle: "Status at close of the CFD phase.", sections: [title, [].concat(toc, s1, s2, s3, s4, s5, s6)] });
write(doc, "/home/claude/reports/GRAIL_Roadmap_RevI_Completion_Status.docx");
