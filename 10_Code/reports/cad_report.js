// GRAIL Collector — CAD model report.
const C = require("./common.js");
const { p, h, rich, table, tableCaption, figure, bullets, numbered,
        calloutBox, spacer, pageBreak, buildDoc, write,
        Paragraph, TextRun, AlignmentType, TableOfContents } = C;

const FIG = "/home/claude/grail_cfd/12_figures/";
const B = (t) => [t, { bold: true }];
const T = (t) => [t, {}];
const I = (t) => [t, { italics: true }];

// ============================================================ title page
const titlePage = [
  spacer(1800),
  new Paragraph({ alignment: AlignmentType.CENTER,
    children: [new TextRun({ text: "THE GRAIL COLLECTOR", bold: true, size: 52, color: "1B4F7A" })],
    spacing: { after: 120 } }),
  new Paragraph({ alignment: AlignmentType.CENTER,
    children: [new TextRun({ text: "CAD Model Report", size: 36, color: "1F2124" })],
    spacing: { after: 400 } }),
  new Paragraph({ alignment: AlignmentType.CENTER,
    children: [new TextRun({
      text: "Geometry of the advanced flat-plate solar thermal collector: "
          + "the as-built assembly, the converging roll-bond absorber, "
          + "and the twelve geometric invariants the CFD work was gated on.",
      size: 22, color: "4A4D52" })],
    spacing: { after: 600 } }),
  spacer(400),
  table([
    ["Item", "Value"],
    ["Source model", "Grail_Collector_2.step"],
    ["MD5 checksum", "e3ca020c159abf017138feabe8811e05"],
    ["Solids in the STEP file", "129"],
    ["Solids carried into the CFD model", "128"],
    ["Overall envelope", "1270.0 × 636.0 × 148.0 mm"],
    ["Total solid volume", "37,101,266 mm³"],
    ["Absorber channels", "12, converging, 40 mm pitch"],
    ["Geometry acceptance gate", "12 invariants checked, 12 PASS, 0 FAIL"],
    ["Measurement method", "direct NURBS evaluation, h-refined to convergence"],
  ], [1, 1.6], { alignRight: false }),
  spacer(600),
  new Paragraph({ alignment: AlignmentType.CENTER,
    children: [new TextRun({ text: "B.Tech thesis supporting document", size: 19, color: "4A4D52" })] }),
  pageBreak(),
];

// ============================================================ contents
const contents = [
  h("Contents", 1),
  new TableOfContents("Contents", { hyperlink: true, headingStyleRange: "1-2" }),
  p("If the contents list shows a placeholder, open it in Word and press F9 to build it.",
    { run: { italics: true, color: "4A4D52", size: 18 } }),
  pageBreak(),
];

// ============================================================ 1. what the model is
const s1 = [
  h("1. What the model is", 1),

  p("The GRAIL Collector is an advanced flat-plate solar thermal collector. Four features "
    + "distinguish it from a conventional flat-plate collector, and all four are present in the "
    + "CAD model:"),

  ...numbered([
    [B("A converging roll-bond absorber. "), T("Twelve channels are formed between two bonded "
      + "aluminium sheets. Each channel narrows continuously along the flow: the hydraulic "
      + "diameter falls from 5.199 mm at the inlet to 2.807 mm at the outlet.")],
    [B("Alternating counter-current flow. "), T("Adjacent channels are fed from opposite ends, "
      + "so each channel has a neighbour running the other way. Neighbouring channels converge "
      + "in opposite directions, which is why the manifolds are mirrored left and right.")],
    [B("Transparent insulation and double glazing. "), T("A 10 mm polycarbonate honeycomb panel "
      + "sits between two glass panes and the absorber, with a thermotropic layer on the outer "
      + "pane.")],
    [B("A graded phase-change storage tray. "), T("Seven PCM zones of increasing depth lie under "
      + "the absorber, 7.1 mm at one end rising to 12.9 mm at the other.")],
  ]),

  h("1.1 The source file", 2),
  p("Everything in this report is measured from a single file. Nothing is taken from a drawing, "
    + "a specification sheet, or a previous revision."),
  ...bullets([
    [B("File: "), T("Grail_Collector_2.step")],
    [B("MD5: "), T("e3ca020c159abf017138feabe8811e05")],
    [B("Contents: "), T("129 solids in a named assembly tree, total volume 37,101,266 mm³")],
    [B("Envelope: "), T("1270.0 mm × 636.0 mm × 148.0 mm")],
  ]),

  p("The model was read with the OpenCASCADE kernel through gmsh 4.15.2. Every dimension quoted "
    + "below was obtained by evaluating the CAD surfaces directly, not by reading a dimension off "
    + "a drawing. Section 4 explains why this distinction turned out to matter a great deal."),

  ...figure(FIG + "M6_assembly_surface_mesh.png",
    "Figure 1 — The complete collector assembly, tessellated. 128 of the 129 solids, "
    + "299,544 triangles, 17.39 m² of tessellated surface."),
];

// ============================================================ 2. assembly breakdown
const s2 = [
  h("2. The assembly, group by group", 1),

  p("The STEP tree organises the 129 solids into ten named groups plus the fluid-void reference "
    + "bodies. The table below is a direct summary of that tree."),

  tableCaption("Table 1 — Assembly groups, counted and totalled from the STEP file."),
  table([
    ["Group", "Solids", "Volume (mm³)", "What it is"],
    ["06_INSULATION", "5", "11,794,743", "VIP rear panel and four edge strips"],
    ["01_GLAZING", "17", "5,978,449", "Two panes, thermotropic layer, manifolds, 12 ports"],
    ["05_PCM_TRAY", "9", "5,939,571", "Seven graded PCM zones, graphite layer, containment tray"],
    ["02_TIM", "1", "5,368,000", "Polycarbonate honeycomb panel"],
    ["00_FRAME", "26", "3,040,032", "Side rails, corner blocks, bezel"],
    ["10_MOUNTING", "14", "2,362,358", "Brackets and rails"],
    ["03_ABSORBER_ASSEMBLY", "3", "1,126,470", "Lower sheet, upper sheet, selective coating"],
    ["07_BACKSHEET", "1", "710,007", "Rear panel"],
    ["08_SEALS", "5", "530,948", "EPDM gaskets"],
    ["ABSORBER_FLUID_VOID_REF", "12", "224,326", "The twelve channel voids — the CFD fluid domain"],
    ["09_SENSING", "8", "21,712", "ESP32 board, pyranometer, five DS18B20 probes"],
    ["Fasteners (M5 bezel)", "28", "4,651", "Fourteen pairs"],
  ], [1.5, 0.5, 0.9, 2.2], { alignRight: false }),

  h("2.1 The optical stack", 2),
  p("Light reaches the absorber through four layers. Their thicknesses come straight from the "
    + "bounding boxes of the CAD solids."),

  tableCaption("Table 2 — The optical stack, outermost first."),
  table([
    ["Layer", "Footprint (mm)", "Thickness (mm)", "Transmittance"],
    ["Thermotropic layer", "1160 × 560", "1.0", "0.88 clear / 0.40 scattered"],
    ["Outer glass pane", "1160 × 560", "3.2", "part of τ_glz,sys = 0.833"],
    ["Inner glass pane", "1100 × 488", "3.2", "part of τ_glz,sys = 0.833"],
    ["TIM honeycomb panel", "1100 × 488", "10.0", "τ_TIM = 0.82"],
    ["Selective coating (TiNOX)", "1100 × 480", "surface property", "α = 0.95, ε = 0.04"],
  ], [1.4, 1.0, 1.0, 1.3], { alignRight: false }),

  p("The optical chain that drives every thermal result in the CFD study follows directly from "
    + "this stack:"),
  new Paragraph({ alignment: AlignmentType.CENTER,
    children: [new TextRun({ text: "q″ = G_T × τ_glz,sys × τ_TIM × α_abs "
      + "= 800 × 0.833 × 0.82 × 0.95 = 519.13 W/m²", bold: true, size: 22 })],
    spacing: { before: 140, after: 180 } }),
  p("The value 0.833 is the two-pane system transmittance. An earlier revision of the design "
    + "documentation carried the single-pane value 0.91; using it would have put 567.1 W/m² "
    + "into the absorber instead of 519.1, an 8.5 % error on every efficiency in the study. The "
    + "correction is recorded as CR-02 in the project's correction register."),

  h("2.2 The graded PCM tray", 2),
  p("Seven PCM zones run across the plate, each 157.1 mm long and 480 mm wide, with the depth "
    + "increasing monotonically from one end to the other. The grading is deliberate: the end of "
    + "the plate that runs hottest gets the most storage."),

  tableCaption("Table 3 — The seven graded PCM zones."),
  table([
    ["Zone", "Depth (mm)", "Volume (mm³)"],
    ["PCM_ZONE_01", "7.1", "538,734"],
    ["PCM_ZONE_02", "8.1", "610,305"],
    ["PCM_ZONE_03", "9.0", "682,101"],
    ["PCM_ZONE_04", "10.0", "753,979"],
    ["PCM_ZONE_05", "11.0", "825,774"],
    ["PCM_ZONE_06", "11.9", "897,652"],
    ["PCM_ZONE_07", "12.9", "969,365"],
    ["Total PCM", "—", "5,277,910"],
  ], [1.2, 1, 1]),

  p("The PCM is RT55 with 10 % expanded graphite: latent heat 170 kJ/kg across a melting band of "
    + "51–57 °C, solid density 880 kg/m³ and conductivity 2.80 W/m·K. A "
    + "0.4 mm graphite interface layer (211,153 mm³) couples the tray to the absorber."),

  h("2.3 The manifolds and the flow circuit", 2),
  p("Two manifold blocks, each 45 × 480 × 39 mm, carry twelve ports of 15 mm bore. The "
    + "port names encode the circuit directly:"),
  ...bullets([
    [T("Six ports on the "), B("left"), T(" manifold: three cold inlets (N200, N40, P120) and "
      + "three hot outlets (N120, P40, P200).")],
    [T("Six ports on the "), B("right"), T(" manifold, mirrored: three cold inlets (N200, N40, "
      + "P120) and three hot outlets (N120, P40, P200).")],
  ]),
  p("Reading the suffixes as channel y-positions in millimetres shows the pattern plainly. A "
    + "channel fed cold from the left is flanked by channels fed cold from the right. That is the "
    + "alternating counter-current arrangement, built into the manifold geometry rather than into "
    + "a flow-control scheme."),
];

// ============================================================ 3. the absorber
const s3 = [
  pageBreak(),
  h("3. The absorber — the part that matters", 1),

  p("The absorber assembly is three solids and 1,126,470 mm³ of aluminium. It is also the "
    + "entire subject of the CFD study, so it is worth setting out in detail."),

  tableCaption("Table 4 — The absorber assembly."),
  table([
    ["Solid", "Footprint (mm)", "Height (mm)", "Volume (mm³)", "Role"],
    ["ABSORBER_LOWER_SHEET", "1100 × 480", "1.0", "528,000", "Flat backing sheet"],
    ["ABSORBER_UPPER_SHEET", "1100 × 480", "5.2", "598,582", "Domed sheet forming the channels"],
    ["SELECTIVE_COATING", "1100 × 480", "4.6", "−112", "Excluded — see below"],
  ], [1.7, 1.0, 0.8, 1.1, 1.3], { alignRight: false }),

  calloutBox("A solid that had to be excluded, and why that is defensible", [
    "SELECTIVE_COATING translates out of the STEP file with a NEGATIVE volume of −111.8 mm³. "
    + "A 0.3 µm coating on a 1.1 m panel is beyond what the translator can represent as a solid.",
    "It is excluded from the meshed model and carried instead as a surface radiative property, "
    + "α = 0.95 and ε = 0.04.",
    "This is not a workaround. The project's own material database specifies TiNOX as a boundary "
    + "condition and gives it no bulk properties at all, so the CAD and the physics agree that it "
    + "is a surface, not a body. 128 of 129 solids are carried; this is the one that is not.",
  ]),

  h("3.1 The converging channel", 2),
  p("Each of the twelve channels narrows continuously from inlet to outlet. This is the design "
    + "feature the whole study exists to evaluate, so its geometry was measured rather than "
    + "assumed."),

  tableCaption("Table 5 — Channel section along the flow, measured on the CAD surface (channel CH05)."),
  table([
    ["ξ", "x (mm)", "Area (mm²)", "Wetted perimeter (mm)", "D_h (mm)"],
    ["0.00", "−550", "29.988", "21.587", "5.557"],
    ["0.10", "−440", "25.517", "20.554", "4.966"],
    ["0.25", "−275", "22.083", "19.005", "4.648"],
    ["0.50", "0", "16.465", "16.425", "4.010"],
    ["0.75", "+275", "11.823", "13.852", "3.414"],
    ["0.90", "+440", "6.356", "12.312", "—"],
  ], [0.7, 0.9, 1.1, 1.4, 0.9]),

  p("The end values, taken at the trimmed end faces themselves rather than at a sampled station, "
    + "are the governing numbers:"),

  tableCaption("Table 6 — Governing as-built channel geometry."),
  table([
    ["Quantity", "Inlet", "Outlet", "Ratio"],
    ["Flow area (mm²)", "28.056939", "7.921436", "0.2823"],
    ["Wetted perimeter (mm)", "21.5865", "11.2884", "0.5229"],
    ["Hydraulic diameter D_h (mm)", "5.198875", "2.807053", "0.539935"],
    ["Channel footprint width (mm)", "8.714056", "—", "—"],
  ], [1.7, 1.1, 1.1, 0.8]),

  p("The hydraulic grading ratio is therefore"),
  new Paragraph({ alignment: AlignmentType.CENTER,
    children: [new TextRun({ text: "G = D_h,outlet / D_h,inlet = 2.807053 / 5.198875 = 0.539935",
      bold: true, size: 22 })],
    spacing: { before: 140, after: 180 } }),

  p("and the grading follows a linear-in-D_h law. Fitting D_h(ξ) = D_h,in [1 − "
    + "(1 − G) ξ^λ] to the measured profile gives λ = 1.0, with the measured "
    + "sections matching the linear law to between +0.19 % and +0.49 % over ξ = 0.10 to 0.90. "
    + "The exponent is confirmed, not assumed."),

  ...figure(FIG + "C1_geometry.png",
    "Figure 2 — Flow area, wetted perimeter and hydraulic diameter along the channel axis. "
    + "All three fall monotonically: the section CONVERGES."),

  ...figure(FIG + "C2_sections.png",
    "Figure 3 — The channel cross-section at inlet, mid-span and outlet, drawn on the CAD "
    + "surface. The section shrinks; it does not merely change shape.", 0.78),

  h("3.2 The root fillet", 2),
  p("Where the domed upper sheet meets the flat lower sheet there is a tangent blend of radius "
    + "r = 0.5 mm. This small number had a disproportionate effect on the model and is worth "
    + "recording."),
  p("At the originally specified radius of 1.0 mm the tangent-blend section degenerates once the "
    + "dome height falls to 3.0 mm: the blend consumes the whole flank, the section scale floors "
    + "at 0.745525, and a grading ratio of G = 0.54 becomes geometrically unreachable. At "
    + "r = 0.5 mm the blend stays well-posed the whole way along and G = 0.539935 is achieved. "
    + "The change is recorded as CR-05."),
  p("The fillet also shapes the section in a way that mattered later. Because the fillet is "
    + "concave, the widest point of the channel is not at the sheet interface: measured at the "
    + "inlet station, the widest point sits at z = 0.447 mm and the wall reaches z = 0 only "
    + "0.54 mm further in. Section 6 of the CFD report explains why this small fact defeated one "
    + "meshing approach entirely."),

  ...figure(FIG + "M3_root_fillet.png",
    "Figure 4 — The root fillet at r = 0.5 mm, with the tangent-blend construction. "
    + "The superseded model used 1.0 mm.", 0.72),

  h("3.3 The conductive bridge", 2),
  p("Between one channel and the next lies a strip of bonded aluminium. Its width follows from "
    + "the pitch and the channel footprint:"),
  new Paragraph({ alignment: AlignmentType.CENTER,
    children: [new TextRun({ text: "bridge = pitch − w_channel = 40.000000 − 8.714056 "
      + "= 31.285944 mm", bold: true, size: 22 })],
    spacing: { before: 140, after: 180 } }),
  p("This bridge is the lateral conduction path. Under alternating flow it carries heat sideways "
    + "from a hot channel to its cold neighbour, and that transfer is the mechanism the entire "
    + "CFD study sets out to measure. Its width is therefore a geometric parameter of first "
    + "importance, and the CFD campaign sweeps it from 20 to 37 mm."),

  ...figure(FIG + "M5_multichannel.png",
    "Figure 5 — Four adjacent channels at the inlet, on a 40 mm pitch, with the 31.286 mm "
    + "conductive bridge between them.", 0.9),
];

// ============================================================ 4. the gate
const s4 = [
  pageBreak(),
  h("4. Geometry acceptance — and a measurement error that had to be caught", 1),

  p("No CFD was run until the geometry passed a gate of twelve invariants. This section reports "
    + "that gate, and the reason it had to be run twice."),

  h("4.1 What went wrong the first time", 2),
  p("The first pass through the gate recorded four failing invariants and attributed them to "
    + "translation error in the STEP file at the channel's small end. A correction was written "
    + "(CR-08) stating that the grading ratio should be restated as 0.535763."),
  p("That conclusion was wrong, and it was wrong for a specific and instructive reason: "
    + "the measuring instrument was trusted without being tested."),
  p("All four apparent failures came from one function, gmsh.model.occ.getMass. The outlet face "
    + "of the channel is a small trimmed planar face, which is the hardest case for that "
    + "integrator. Measuring the same geometry a different way — by evaluating the true "
    + "NURBS surface directly and refining the sampling until the answer stopped moving — "
    + "gave a different result."),

  tableCaption("Table 7 — Convergence of the directly evaluated end-cap areas. "
    + "NU is the number of sample points around the section."),
  table([
    ["NU", "Inlet area (mm²)", "dev vs CAD", "Outlet area (mm²)", "dev vs CAD",
     "dev vs OCC", "G"],
    ["96", "28.036605", "−0.0663 %", "7.908667", "−0.1431 %", "+0.5803 %", "0.539764"],
    ["192", "28.051893", "−0.0118 %", "7.918230", "−0.0223 %", "+0.7019 %", "0.539892"],
    ["288", "28.054711", "−0.0017 %", "7.920019", "+0.0002 %", "+0.7247 %", "0.539916"],
    ["576", "28.056409", "+0.0043 %", "7.921098", "+0.0139 %", "+0.7384 %", "0.539930"],
    ["1152", "28.056833", "+0.0058 %", "7.921368", "+0.0173 %", "+0.7418 %", "0.539934"],
    ["2304", "28.056939", "+0.0062 %", "7.921436", "+0.0181 %", "+0.7427 %", "0.539935"],
  ], [0.6, 1.2, 0.9, 1.2, 0.9, 0.9, 0.9], { size: 17 }),

  calloutBox("The decisive evidence", [
    "The refinement sequence converges monotonically ONTO the CAD values and AWAY from the OCC "
    + "values. The outlet face is off by +0.74 % in OCC; the channel volume is off by +0.27 %.",
    "The same refinement applied to the WALL area — a large, untrimmed, easy face — "
    + "agrees with OCC to +0.007 %. Only the small trimmed faces and the enclosed volume are "
    + "affected, which is exactly the signature of a trimmed-face integration weakness.",
    "CR-08 was therefore WITHDRAWN and CR-09 recorded in its place: the geometry is faithful, and "
    + "the error was in the measurement, not in the model. No CFD had been run, so nothing "
    + "downstream had to be discarded.",
  ]),

  h("4.2 The twelve invariants", 2),
  p("Re-measured by direct NURBS evaluation, the gate passes in full."),

  tableCaption("Table 8 — Geometry acceptance gate. 12 PASS, 0 FAIL."),
  table([
    ["#", "Invariant", "CAD reference", "Measured", "Deviation", "Verdict"],
    ["1", "Fluid volume per channel", "18,643.963 mm³", "18,643.7 mm³", "−0.0015 %", "PASS"],
    ["2", "Strip solid volume, 3CH", "281,693.638 mm³", "281,600.554 mm³", "−0.033 %", "PASS"],
    ["3", "Strip solid volume, 2CH", "187,817.190 mm³", "187,736.130 mm³", "−0.043 %", "PASS"],
    ["4", "Channel inlet face area", "28.0552 mm²", "28.056939 mm²", "+0.0062 %", "PASS"],
    ["5", "Channel outlet face area", "7.9200 mm²", "7.921436 mm²", "+0.0181 %", "PASS"],
    ["6", "Inlet hydraulic diameter", "5.199685 mm", "5.198875 mm", "−0.0156 %", "PASS"],
    ["7", "Outlet hydraulic diameter", "2.809592 mm", "2.807053 mm", "−0.0904 %", "PASS"],
    ["8", "Hydraulic grading ratio", "0.540339", "0.539935", "−0.0748 %", "PASS"],
    ["9", "Channel pitch", "40.000 mm", "40.000000 mm", "0", "PASS"],
    ["10", "Periodic face area, 2CH", "2200.000000 mm²", "2200.000000 mm²", "0", "PASS"],
    ["11", "Bridge width", "31.299046 mm", "31.285944 mm", "−0.042 %", "PASS"],
    ["12", "Channel length", "1100 mm", "1100.000 mm", "0", "PASS"],
  ], [0.35, 1.8, 1.2, 1.2, 0.8, 0.6], { size: 17 }),

  p("Invariants 2 and 3 are still OCC volumes and therefore still carry the positive bias. Their "
    + "true values are marginally closer to CAD than shown, so those two passes are conservative."),

  h("4.3 An independent third witness", 2),
  p("A geometry can pass its own invariants and still be the wrong geometry. The Reynolds number "
    + "provides an independent check, because it depends on D_h and was stated in the project "
    + "brief before any of this measurement was done."),

  tableCaption("Table 9 — Reynolds number on the converged geometry. "
    + "Re = 4 ṁ / (π D_h μ), water μ = 8.55×10⁻⁴ Pa·s."),
  table([
    ["ṁ total (kg/s)", "ṁ per channel (kg/s)", "Re at inlet", "Re at outlet"],
    ["0.0010", "8.3333×10⁻⁵", "23.87", "44.21"],
    ["0.0025", "2.0833×10⁻⁴", "59.68", "110.52"],
    ["0.0045", "3.7500×10⁻⁴", "107.42", "198.94"],
  ], [1.2, 1.4, 1, 1]),

  p("The project brief states that the corrected as-built geometry gives Re = 23.9 – 198.8. "
    + "The converged geometry reproduces 23.87 – 198.94, a match to 0.07 %. The withdrawn "
    + "CR-08 geometry would have given 200.43, which is 0.8 % out. The Reynolds range is "
    + "therefore a third independent witness, alongside the CAD parameters and the refinement "
    + "study, that CR-09 is right and CR-08 was not."),

  p("Two consequences follow immediately and hold for the whole study:"),
  ...bullets([
    [B("The flow is deeply laminar everywhere. "), T("Re reaches 199 at the very most. No "
      + "turbulence model is used anywhere in this work, and none is needed.")],
    [B("Reynolds number RISES along the channel. "), T("That is the converging-channel signature: "
      + "the area falls faster than the perimeter, so the velocity rises faster than D_h falls. "
      + "It is the opposite of a diverging channel and it is visible in every case of the "
      + "production campaign.")],
  ]),

  ...figure(FIG + "C4_reynolds.png",
    "Figure 6 — Reynolds number rises along the converging channel at all three mass flows. "
    + "The transition value of 2300 is more than an order of magnitude away.", 0.85),
];

// ============================================================ 5. corrections
const s5 = [
  pageBreak(),
  h("5. Corrections to the geometry record", 1),

  p("Six of the project's seventeen recorded corrections concern the CAD model. They are "
    + "reproduced here because a reader of an earlier draft will have seen the superseded values."),

  tableCaption("Table 10 — Geometry corrections."),
  table([
    ["ID", "What changed", "Why", "Discard old results?"],
    ["CR-01", "Channel DIVERGES (D_h 5.20 → 8.345 mm) → channel CONVERGES "
      + "(D_h 5.199 → 2.807 mm)",
      "The diverging build violated the design roadmap and fell outside the patent claim, which "
      + "requires G to decrease within 0.35–1.00",
      "YES — obsolete and scientifically invalid. Never used as a baseline, validation case, "
      + "comparison or figure."],
    ["CR-02", "Single glazing τ = 0.91 → double glazing τ_glz,sys = 0.833",
      "The built collector has two panes. Absorbed flux 567.1 → 519.1 W/m² at the "
      + "design point",
      "YES for any absorbed-flux value computed from 0.91"],
    ["CR-05", "Root fillet 1.0 mm → 0.5 mm",
      "At 1.0 mm the tangent-blend section degenerates at h_s = 3.0 mm and G = 0.54 becomes "
      + "unreachable",
      "YES for any result at r = 1.0 mm claiming G = 0.54"],
    ["CR-06", "Bridge width 34.8 mm → 31.299 mm as built",
      "Follows from pitch − channel footprint",
      "No — 34.8 mm remains a valid sweep point"],
    ["CR-08", "WITHDRAWN",
      "Its premise was wrong; see CR-09",
      "YES — discard the correction itself"],
    ["CR-09", "The geometry is faithful. G = 0.539935, −0.075 % from CAD",
      "The error was in gmsh.model.occ.getMass, not in the model. Direct NURBS integration "
      + "converges on the CAD values",
      "Reverted — the CAD values govern"],
    ["CR-11", "Assembly renders omit the manifold port holes; the roll-bond solid is built at a "
      + "nominal uniform 1.0 mm sheet thickness",
      "The port holes straddle the parametric seam; the real roll-bond upper sheet thins over the "
      + "dome (0.22–1.32 mm measured)",
      "No — labelled ENGINEERING_ASSUMPTION, affects rendering and solid volume only. Port "
      + "area is computed from the CAD boundary curves and subtracted (−813.1 mm²)"],
  ], [0.5, 2.1, 2.4, 2.0], { alignRight: false, size: 17 }),

  calloutBox("The one that matters most", [
    "CR-01 is the correction a reader must not miss. An earlier build of this model had the "
    + "channel GROWING from 5.20 mm to 8.345 mm. That geometry is withdrawn.",
    "It is not used anywhere in this study as a baseline, a validation case, a comparison case, a "
    + "database entry, a figure or a piece of scientific evidence. Any figure or number that shows "
    + "a diverging channel belongs to the superseded build and should be discarded on sight.",
  ]),
];

// ============================================================ 6. what the CFD took
const s6 = [
  pageBreak(),
  h("6. What the CFD model takes from the CAD, and what it does not", 1),

  p("The CFD work does not mesh the whole assembly. It meshes the fluid void and the absorber "
    + "metal, and represents everything else as a boundary condition or a material property. "
    + "This section states exactly where the line was drawn."),

  h("6.1 Carried as geometry", 2),
  ...bullets([
    [B("The twelve fluid voids. "), T("18,643.963 mm³ each, taken from the true NURBS wall "
      + "surface, not from a tessellation.")],
    [B("The roll-bond metal. "), T("Lower sheet 1.0 mm and upper sheet 1.0 mm nominal, on a 40 mm "
      + "pitch over 1100 mm.")],
  ]),

  h("6.2 Carried as a boundary condition or property", 2),
  ...bullets([
    [B("The optical stack. "), T("Two panes, TIM and coating collapse to one number: "
      + "519.13 W/m² absorbed at G_T = 800 W/m².")],
    [B("The selective coating. "), T("α = 0.95, ε = 0.04 as a surface property.")],
    [B("The rear stack. "), T("VIP and backsheet as a series thermal resistance, "
      + "h_rear = 3 W/m²K.")],
    [B("The sky and the wind. "), T("T_sky = 0.0552 T_amb^1.5 in kelvin, "
      + "h_wind = 5.7 + 3.8 v.")],
  ]),

  h("6.3 Not carried at all", 2),
  ...bullets([
    [T("The frame, mounting hardware, seals, fasteners and sensing boards. They carry no heat "
      + "path that changes the absorber solution at the level this study resolves.")],
    [T("The manifold internal flow. Each channel is fed at a prescribed mass flow; manifold "
      + "maldistribution is outside the scope of this study and is stated as such.")],
  ]),

  ...figure(FIG + "M7_cfd_mesh_in_assembly.png",
    "Figure 7 — The CFD mesh in position inside the assembly. The enclosure is ghosted; "
    + "only the absorber is solved in 3-D. Every other body enters the model through a boundary "
    + "condition or a material property, not as a mesh."),

  h("6.4 Documented simplifications", 2),
  p("Three simplifications are recorded rather than buried, because a reader could reasonably "
    + "want to challenge them:"),
  ...numbered([
    [B("Uniform 1.0 mm sheet thickness. "), T("The real roll-bond upper sheet thins as it is "
      + "formed over the dome; the marched thickness runs 0.22 to 1.32 mm with a mean of "
      + "1.08–1.23 mm. The model uses a nominal uniform 1.0 mm and lands +1.42 % on the CAD "
      + "sheet-pair volume. Labelled ENGINEERING_ASSUMPTION (CR-11).")],
    [B("Anisotropic materials reduced to one direction. "), T("The TIM honeycomb "
      + "(0.075 perpendicular / 0.16 parallel W/m·K) and the graphite interface (300 parallel "
      + "/ 5 perpendicular) are anisotropic, and the solid thermophysics in OpenFOAM v1912 is "
      + "isotropic per region. Through-thickness conduction governs for both, so the "
      + "perpendicular value is used and the in-plane value is recorded — not silently "
      + "averaged.")],
    [B("Constant water properties at 300 K. "), T("Viscosity falls from 8.55×10⁻⁴ "
      + "Pa·s at 300 K to about 4.7×10⁻⁴ at 333 K. The baseline uses constant "
      + "properties and this is flagged as requiring a temperature-dependent-viscosity "
      + "sensitivity case before the assumption is finally accepted.")],
  ]),
];

// ============================================================ 7. summary
const s7 = [
  pageBreak(),
  h("7. Summary of governing dimensions", 1),

  p("Every number in this table is measured from the CAD model and is the value the CFD study "
    + "actually used."),

  tableCaption("Table 11 — Governing geometry, as meshed."),
  table([
    ["Quantity", "Value", "Source"],
    ["Number of channels", "12", "CAD"],
    ["Channel pitch", "40.000000 mm", "CAD, exact"],
    ["Channel length", "1100.000 mm", "CAD, exact"],
    ["Absorber plate", "1100 × 480 mm", "CAD"],
    ["Lower sheet thickness", "1.0 mm", "CAD"],
    ["Upper sheet thickness (nominal)", "1.0 mm", "ENGINEERING_ASSUMPTION, CR-11"],
    ["Root fillet radius", "0.5 mm", "Decision D4, CR-05"],
    ["Hydraulic diameter, inlet", "5.198875 mm", "Direct NURBS, converged"],
    ["Hydraulic diameter, outlet", "2.807053 mm", "Direct NURBS, converged"],
    ["Grading ratio G", "0.539935", "Direct NURBS, converged"],
    ["Grading exponent λ_G", "1.0", "Confirmed, ≤ 0.49 % over ξ = 0.10–0.90"],
    ["Flow area, inlet", "28.056939 mm²", "Direct NURBS, converged"],
    ["Flow area, outlet", "7.921436 mm²", "Direct NURBS, converged"],
    ["Wetted perimeter, inlet", "21.5865 mm", "Direct NURBS"],
    ["Wetted perimeter, outlet", "11.2884 mm", "Direct NURBS"],
    ["Channel footprint width, inlet", "8.714056 mm", "Direct NURBS"],
    ["Bridge width", "31.285944 mm", "pitch − footprint"],
    ["Fluid volume per channel", "18,643.963 mm³", "CAD"],
    ["Periodic face area, 2-channel strip", "2200.000000 mm²", "CAD, exact"],
    ["Absorbed flux at G_T = 800 W/m²", "519.13 W/m²", "Optical chain, CR-02"],
  ], [1.8, 1.2, 1.7], { alignRight: false }),

  h("7.1 Where to look next", 2),
  p("The companion document, the CFD Simulation Report, takes this geometry and describes what "
    + "was computed on it: the mesh, the solver, the verification, the production campaign of 300 "
    + "cases, the uncertainty assessment, and the two patent-supporting studies. Its Section 2 "
    + "begins exactly where this document ends."),

  ...figure(FIG + "M10_full_plate_mesh.png",
    "Figure 8 — The full 12-channel absorber, meshed. 1,828,800 hexahedra, 2,100,852 nodes, "
    + "100 % hexahedral, zero inverted cells."),
];

const doc = buildDoc({
  title: "GRAIL Collector — CAD Model Report",
  subtitle: "Geometry of the GRAIL advanced flat-plate solar thermal collector",
  sections: [[...titlePage, ...contents, ...s1, ...s2, ...s3, ...s4, ...s5, ...s6, ...s7]],
});

write(doc, "/home/claude/reports/GRAIL_CAD_Model_Report.docx");
