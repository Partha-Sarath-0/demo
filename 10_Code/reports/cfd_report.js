// GRAIL — CFD Simulation Report (the full "how it was done" document)
const C = require("./common");
const { p, h, rich, table, caption, tableCaption, figure, bullets, numbered,
        calloutBox, spacer, pageBreak, buildDoc, write,
        Paragraph, TextRun, AlignmentType, TableOfContents } = C;

const FIG = "/home/claude/grail_cfd/12_figures/";

function eq(text) {
  return new Paragraph({
    alignment: AlignmentType.CENTER,
    children: [new TextRun({ text, bold: true, size: 22 })],
    spacing: { before: 140, after: 180, line: 276, lineRule: "auto" },
  });
}
function code(lines) {
  return lines.map((l) => new Paragraph({
    children: [new TextRun({ text: l, font: "Consolas", size: 17 })],
    spacing: { before: 0, after: 0, line: 240, lineRule: "auto" },
    shading: { type: "clear", fill: "F4F6F8", color: "auto" },
  }));
}

// ===================================================== title
const title = [
  spacer(2600),
  new Paragraph({ alignment: AlignmentType.CENTER,
    children: [new TextRun({ text: "THE GRAIL COLLECTOR", bold: true, size: 48, color: "1B4F7A" })],
    spacing: { after: 80 } }),
  new Paragraph({ alignment: AlignmentType.CENTER,
    children: [new TextRun({ text: "CFD Simulation Report", size: 34, color: "1F2124" })],
    spacing: { after: 300 } }),
  new Paragraph({ alignment: AlignmentType.CENTER,
    children: [new TextRun({ text: "How every simulation in this study was set up, run, verified, "
      + "corrected and reported — in order, with every governing number.", italics: true, size: 21,
      color: "4A4D52" })],
    spacing: { after: 500 } }),

  table([
    ["Item", "Value"],
    ["Geometry", "Converging roll-bond absorber, 12 channels, G = 0.539935"],
    ["3-D solver", "OpenFOAM v1912 (ESI) — simpleFoam + scalarTransportFoam"],
    ["Conjugate solver", "GRAIL-CHT 1.0 (purpose-built, 2-D plate + 1-D per-channel fluid)"],
    ["Mesh generator", "Direct NURBS evaluation, structured pure hexahedra"],
    ["Production campaign", "300 cases, Latin Hypercube, seed 20260915, 0 rejected"],
    ["Verification framework", "ASME V&V 20-2009, Roache grid convergence index"],
    ["Reported dataset revision", "Rev 2 (nu_cfd = 2.9238)"],
    ["Hardware", "2 CPU cores, 7 GB RAM, Ubuntu 24.04.4 LTS"],
  ], [3, 7], { alignRight: false }),

  spacer(700),
  new Paragraph({ alignment: AlignmentType.CENTER,
    children: [new TextRun({ text: "B.Tech thesis supporting document", size: 19, color: "4A4D52" })] }),
];

// ===================================================== contents
const toc = [
  pageBreak(),
  h("Contents", 1),
  new TableOfContents("Contents", { hyperlink: true, headingStyleRange: "1-2" }),
  p("(In Word: right-click the field above and choose Update Field to populate the page numbers.)",
    { run: { italics: true, size: 17, color: "4A4D52" } }),
];

// ===================================================== 1
const s1 = [
  pageBreak(),
  h("1. What this document is, and how to read it", 1),
  p("This report describes the computational work behind the GRAIL collector: every simulation "
    + "that was run, in the order it was run, with the numbers each one produced. It is written to "
    + "be checked. Where a result was later found to be wrong, the wrong result is still here, "
    + "together with what replaced it and why — because a study whose corrections are invisible "
    + "cannot be audited."),
  p("The companion document, the CAD Model Report, describes the geometry. Everything in Section 3 "
    + "onwards takes that geometry as given."),

  h("1.1 The staged ladder", 2),
  p("Nothing was run at full complexity first. Each stage had to pass an acceptance test before "
    + "the next was allowed to start. This is what the report follows:"),
  table([
    ["Gate", "What it established", "Outcome"],
    ["Gate 0", "Environment and solver capability audit", "PASS — capability matrix recorded"],
    ["Gate 1", "Geometry acceptance: 12 invariants on the CAD", "PASS — 12/12"],
    ["Gate 2", "Meshing strategy: snappyHexMesh rejected, direct NURBS adopted", "PASS"],
    ["Gate 3", "3-D single-channel flow + energy verification", "PASS — mass 2.2e-16, energy -0.198 %"],
    ["Gate 4", "3-D grid convergence, Nusselt extraction", "PASS with a caveat — Nu not converged"],
    ["Gate 5", "Conjugate plate solver, limit tests", "PASS — both limits collapse to zero"],
    ["Gate 6", "Domain equivalence (how much plate is needed)", "PASS — 2-channel periodic validated"],
    ["Gate 7", "Production campaign, 300 cases", "PASS — 0 rejected"],
    ["Gate 8", "Uncertainty, sensitivity, validation, closeout", "PASS — 3 of 4 claims survive"],
    ["Gate 9", "3-D conjugate run on the meshed solid", "FAILED — reported as failed"],
  ], [1.1, 5.4, 3.5], { alignRight: false }),

  h("1.2 Rules the work was held to", 2),
  ...bullets([
    "SI units internally. Kelvin wherever an absolute temperature appears — in every fourth power, "
      + "every Stefan-Boltzmann term and every sky-temperature relation. Celsius appears only in "
      + "prose, never in a formula.",
    "No invented OpenFOAM capability. Every solver, dictionary entry, boundary condition and "
      + "function object named here was verified present in the installed v1912 binaries first.",
    "The superseded diverging-channel geometry is never used as a baseline, a validation case, "
      + "a comparison or a figure. It appears in this document only as a correction entry.",
    "No row was ever deleted to improve a result. The one place where rows went missing is "
      + "Section 10.2, and it is reported as a defect of the earlier revision, not a cleanup.",
    "Every assumed dimension or property is labelled ENGINEERING_ASSUMPTION and none is "
      + "attributed to the design roadmap.",
  ]),
];

// ===================================================== 2
const s2 = [
  pageBreak(),
  h("2. Gate 0 — the machine and what the solver could actually do", 1),
  p("The audit was performed before a single case directory was created, because the hardware "
    + "decides the campaign size and the installed solver decides which physics can be claimed."),

  tableCaption("Table 1 — Platform."),
  table([
    ["Item", "Value"],
    ["Operating system", "Ubuntu 24.04.4 LTS (x86_64)"],
    ["CPU cores", "2"],
    ["RAM", "7 GB"],
    ["Free disk", "26 GB"],
    ["MPI", "Open MPI 4.1.6"],
    ["Mesh tool", "gmsh 4.15.2"],
    ["Python stack", "numpy 2.4.4, scipy 1.17.1, pyvista 0.48.4"],
    ["OpenFOAM", "ESI v1912, package 1912.200626-2build3"],
  ], [3, 7], { alignRight: false }),

  p("The capability matrix was built by inspecting the installed binaries and libraries, not by "
    + "recalling what OpenFOAM can do in general. Everything the study would need was confirmed "
    + "present: chtMultiRegionSimpleFoam for steady conjugate heat transfer, simpleFoam for the "
    + "laminar verification stages, viewFactor / fvDOM / P1 radiation, solarLoad, "
    + "turbulentTemperatureRadCoupledMixed for the coupled interface, "
    + "externalWallHeatFluxTemperature for ambient loss with thicknessLayers, the fvOption "
    + "solidificationMeltingSource for phase change, createPatch cyclics, splitMeshRegions and "
    + "checkMesh."),
  p("Two gaps were found and routes recorded rather than papered over. Temperature-dependent "
    + "glazing transmittance is not a native boundary condition and had to be implemented as an "
    + "outer-loop controller updating the absorbed flux from the previous iterate. And v1912 solid "
    + "thermophysics is isotropic per region, so the two anisotropic materials in the database — PC "
    + "honeycomb (0.075 perpendicular / 0.16 parallel) and the graphite interface layer (300 / 5) — "
    + "are carried at their through-thickness value, which is the governing direction, with the "
    + "simplification documented rather than silently averaged."),

  calloutBox("The binding constraint", [
    "Two cores and 7 GB. This does not limit fidelity — a structured hex mesh of any level fits.",
    "It limits CAMPAIGN SIZE. The per-case cost therefore had to be measured on the real mesh "
      + "before any campaign size was committed, and it is why the 300-case production campaign "
      + "runs on the reduced-order conjugate solver of Section 9 rather than on 300 3-D cases.",
  ]),

  h("2.1 The material database", 2),
  p("Taken verbatim from the design roadmap's material table. These are handbook values for the "
    + "material class, not supplier datasheet values; the roadmap's own verification item V6 "
    + "requires confirmation against datasheets before final runs, and that has not happened. "
    + "Every uncertainty in Section 13 is therefore an ENGINEERING_ASSUMPTION."),
  tableCaption("Table 2 — Materials used by the simulations."),
  table([
    ["Material", "rho (kg/m³)", "cp (J/kg·K)", "k (W/m·K)", "Other", "Role"],
    ["Water at 300 K", "997", "4180", "0.610", "mu = 8.55e-4 Pa·s", "fluid region"],
    ["Aluminium AA1050", "2705", "900", "229", "—", "absorber sheets"],
    ["Low-iron solar glass", "2500", "750", "1.05", "eps = 0.88", "glazing"],
    ["PC honeycomb", "85", "1200", "0.075 perp", "tau = 0.82", "TIM"],
    ["TiNOX coating", "—", "—", "surface BC", "alpha 0.95, eps 0.04", "absorber surface"],
    ["RT55 + 10 % EG, solid", "880", "2000", "2.80", "L = 170 kJ/kg", "PCM"],
    ["RT55 + 10 % EG, liquid", "770", "2200", "2.40", "T_m = 51–57 °C", "PCM"],
    ["Graphite interface", "1100", "710", "5 perp", "—", "PCM contact layer"],
    ["VIP fumed silica", "190", "850", "0.006", "derate 20 % / 25 y", "rear insulation"],
  ], [2.4, 1.3, 1.3, 1.4, 1.9, 1.7], { alignRight: false }),

  h("2.2 The optical chain and the external relations", 2),
  p("Every thermal result in this study begins at the same absorbed flux. The chain is four "
    + "multiplications and it is worth stating exactly, because an earlier revision of the design "
    + "documentation carried the single-pane transmittance and would have put 8.5 % more energy "
    + "into the absorber:"),
  eq("q″ = G_T × tau_glz_sys × tau_TIM × alpha_abs = 800 × 0.833 × 0.82 × 0.95 = 519.13 W/m²"),
  p("The 0.833 is the two-pane system value. Using the superseded 0.91 would give 567.1 W/m². "
    + "The change is recorded as correction CR-02 and it invalidates any efficiency computed from "
    + "the old figure."),
  tableCaption("Table 3 — External boundary relations. Kelvin only."),
  table([
    ["Relation", "Form"],
    ["Sky temperature", "T_sky = 0.0552 · T_amb^1.5   (T_amb in K)"],
    ["Wind convection", "h_wind = 5.7 + 3.8 · v_wind   (W/m²K, v in m/s)"],
    ["Rear external, still air", "h_rear = 3 W/m²K"],
    ["Surface radiation", "q_rad = eps · sigma · (T_s⁴ − T_sur⁴),  sigma = 5.670374419e-8"],
  ], [3, 7], { alignRight: false }),
];

// ===================================================== 3
const s3 = [
  pageBreak(),
  h("3. Gate 2 — how the mesh was made, and why not snappyHexMesh", 1),
  p("The obvious route was rejected on measured evidence, not on preference."),

  h("3.1 What failed", 2),
  p("snappyHexMesh needs a surface tessellation. gmsh's 2-D mesher could not produce one. Three "
    + "attempts at progressively relaxed sizing — minimum element 0.12 mm through 0.35 mm, "
    + "curvature refinement on and off, algorithms 1, 5 and 6 — each ran for more than ten minutes "
    + "without completing a single surface, and one aborted outright with "
    + "“Impossible to mesh periodic surface”."),
  p("The diagnosis matters because it is not what it looks like. The geometry is not pathological: "
    + "the boolean that cuts the channels completes in 3.3 seconds and the cut solid has only 16 "
    + "faces. The problem is that each channel wall is a single B-spline surface 1100 mm long:"),
  ...code([
    "CH05 faces:",
    "  face 1187  Plane            x[ 550.000  550.000]  area =     7.8630",
    "  face 1188  Plane            x[-550.000 -550.000]  area =    28.0652",
    "  face 1189  BSpline surface  x[-550.000  550.000]  area = 18069.7603",
  ]),
  p("Its parametric domain is stretched 1100 mm in one direction against roughly 21 mm of section "
    + "perimeter in the other, which is pathological for Delaunay meshing in parameter space.",
    { before: 140 }),

  h("3.2 What the surface probe found instead", 2),
  p("The same wall carries a clean unit parameterisation — u around the section perimeter, v along "
    + "the channel:"),
  ...code([
    "wall face 1189   param bounds u[0, 1]  v[0, 1]",
    "  varying u  ->  dx = 0.000    dy = 8.4993   dz = 4.1021   (section perimeter)",
    "  varying v  ->  dx = 1100.000 dy = 2.0845   dz = 0.0963   (axial)",
    "  200 x 400 = 80,000 surface points evaluated in 0.05 s",
  ]),
  p("Direct evaluation is about four orders of magnitude faster than meshing the same surface, and "
    + "it lands exactly on the NURBS rather than on a tessellation of it.", { before: 140 }),

  h("3.3 The route adopted", 2),
  ...numbered([
    "Sample the channel wall on a structured (u, v) grid — u around the section, v along the flow.",
    "Build an O-grid inside each section: wall ring, then graded radial layers, then a square core. "
      + "This gives genuine boundary-layer control through radial grading rather than through "
      + "snappyHexMesh's addLayers heuristics.",
    "Sweep along v to form hexahedra.",
    "Build the solid region as conforming H-grid blocks around the channels, sharing the wall "
      + "nodes exactly, so the conjugate interface is conformal by construction.",
    "Write polyMesh directly, then splitMeshRegions -cellZones and createPatch for the cyclics.",
  ]),
  tableCaption("Table 4 — Why this was the right choice, not merely the workable one."),
  table([
    ["Criterion", "snappyHexMesh", "Structured by direct evaluation"],
    ["Geometry fidelity", "snapping error on top of tessellation error", "exact on the NURBS"],
    ["Cell type", "hex-dominant, split cells at the 0.5 mm fillet", "100 % hexahedral"],
    ["Boundary layers", "addLayers, often fails in tight fillets", "radial grading, deterministic"],
    ["Cells for given accuracy", "high — octree refines the neighbourhood too", "low — placed only where needed"],
    ["Grid-independence study", "rerun per level, quality varies", "change N; levels exactly self-similar"],
    ["Campaign regeneration", "re-export CAD per design point", "change parameters"],
    ["Cost on 2 cores", "prohibitive", "tractable"],
  ], [2.4, 3.8, 3.8], { alignRight: false }),
  p("The last two rows decide it. The campaign requires regenerable geometry, and a pure-hex mesh "
    + "is the only way this problem fits on two cores without coarsening below the resolution it "
    + "needs."),

  ...figure(FIG + "M4_swept_mesh.png",
    "Figure 1 — The swept structured mesh in a single converging channel: an O-grid section "
    + "swept along the flow, graded radially towards the wall.", 0.92),
  ...figure(FIG + "M1_section_inlet.png",
    "Figure 2 — The O-grid at the inlet station, where the section is widest (A = 28.057 mm²).", 0.7),
  ...figure(FIG + "M2_section_outlet.png",
    "Figure 3 — The same topology at the outlet, A = 7.921 mm². The levels are self-similar, "
    + "which is what makes the grid study clean.", 0.7),
];

// ===================================================== 4
const s4 = [
  pageBreak(),
  h("4. Gate 3 — the 3-D single-channel verification run", 1),
  p("This is the foundation case. It is fluid-only: the absorbed solar flux is imposed on the "
    + "channel wall and there is no solid region. Its purpose is to verify geometry, mesh, "
    + "hydraulics and energy transport before any conjugate physics is switched on, and to "
    + "measure the heat-transfer closure that the plate solver will later use."),

  tableCaption("Table 5 — Case definition."),
  table([
    ["Item", "Value"],
    ["Solver", "OpenFOAM v1912 simpleFoam (laminar, SIMPLEC), then scalarTransportFoam"],
    ["Mesh", "structured O-grid, 105,600 hexahedra, 100 % hex, checkMesh = Mesh OK"],
    ["Domain", "single channel CH05, x = −550 to +550 mm, from the verified CAD NURBS"],
    ["Turbulence model", "none — the flow is deeply laminar (see Section 4.4)"],
    ["Total mass flow", "0.0025 kg/s → 2.0833e-04 kg/s per channel"],
    ["Inlet temperature", "300 K"],
    ["Absorbed flux", "519.13 W/m² of plate → 22.8415 W per channel → 1264.07 W/m² on the wall"],
  ], [2.6, 7.4], { alignRight: false }),
  p("That last conversion is worth following. The 519.13 W/m² falls on the plate. Each channel owns "
    + "a 40 mm × 1100 mm strip of plate, which is 0.044 m², giving 22.8415 W. That power is then "
    + "applied to the channel's own wetted wall area, which is much smaller than the plate strip, "
    + "so the wall flux is 1264.07 W/m²."),

  h("4.1 Convergence — numerical and physical", 2),
  p("Residuals alone are not evidence. Two independent physical balances were checked as well:"),
  tableCaption("Table 6 — Convergence of the baseline case."),
  table([
    ["Level", "Criterion", "Achieved"],
    ["Numerical", "p, U, T residuals", "p 2.3e-08, Ux 5.6e-08, Uy 1.9e-07, T 4.6e-05"],
    ["Physical — mass", "sum of face fluxes, in + out", "2.18e-16 m³/s (0.0000 %)"],
    ["Physical — energy", "Q_u against Q_imposed", "22.7962 W against 22.8415 W → −0.198 %"],
  ], [1.8, 3.4, 4.8], { alignRight: false }),

  h("4.2 Hydraulic results", 2),
  tableCaption("Table 7 — Hydraulics at the design point."),
  table([
    ["Quantity", "CFD", "Reference", "Deviation"],
    ["Pressure drop", "35.31 Pa", "33.31 Pa (laminar, f·Re = 16)", "+6.0 %"],
    ["Pumping power", "7.3778e-06 W", "—", "—"],
    ["Peak velocity", "52.86 mm/s", "—", "—"],
    ["Outlet bulk velocity", "31.81 mm/s", "26.38 mm/s (mdot/rho·A)", "—"],
    ["Peak / bulk ratio", "2.01", "2.0, laminar duct", "+0.5 %"],
  ], [3, 2.4, 3.2, 1.4]),
  p("The +6 % on pressure drop has the right sign and a physical explanation. The reference uses "
    + "the circular-duct f·Re = 16, whereas a lenticular section with a 0.5 mm root fillet runs "
    + "higher, and the flow accelerates 4.8× through the convergence. The peak-to-bulk ratio "
    + "landing on 2.01 against the textbook laminar 2.0 is the strongest single check here: it is "
    + "a profile-shape result the mesh could not fake."),
  ...figure(FIG + "S1_hydraulics.png",
    "Figure 4 — Baseline hydraulics along the channel.", 0.95),
  ...figure(FIG + "C3_pressure_drop.png",
    "Figure 5 — Pressure drop against mass flow across the operating range.", 0.8),

  h("4.3 Thermal results", 2),
  tableCaption("Table 8 — Thermal results at the design point."),
  table([
    ["Quantity", "Value"],
    ["T_out, flux-weighted bulk", "326.1775 K (53.03 °C)"],
    ["Fluid temperature rise dT", "26.1775 K"],
    ["Analytic Q/(m·cp)", "26.230 K"],
    ["Deviation", "−0.200 %"],
    ["Wall-adjacent temperature", "300.21 min / 316.57 mean / 328.84 max K"],
    ["Useful heat Q_u", "22.7962 W"],
  ], [5, 5]),

  tableCaption("Table 9 — Section by section, at xi measured from the channel's own inlet."),
  table([
    ["xi", "x (mm)", "A (mm²)", "u_max (mm/s)", "u_mean", "p (Pa)", "T_mean (°C)", "T_max (°C)"],
    ["0.00", "−550", "27.975", "6.557", "4.458", "35.593", "26.922", "27.376"],
    ["0.10", "−440", "25.408", "16.678", "9.506", "34.000", "30.649", "35.079"],
    ["0.25", "−275", "21.787", "19.423", "11.178", "32.164", "35.351", "39.905"],
    ["0.50", "0", "16.373", "25.742", "15.094", "27.393", "42.262", "46.255"],
    ["0.75", "+275", "11.736", "35.730", "21.250", "18.514", "48.182", "51.501"],
    ["0.90", "+440", "9.325", "44.814", "26.833", "9.214", "51.258", "54.141"],
    ["1.00", "+550", "7.872", "52.857", "31.814", "0.285", "53.099", "55.686"],
  ], [1, 1.3, 1.5, 1.8, 1.4, 1.3, 1.6, 1.5]),
  p("Two physical signatures in that table are worth pointing out to a reader, because both are "
    + "correct and both would look like errors to someone skimming."),
  ...numbered([
    "Entrance development. At xi = 0 the peak velocity is 6.56 mm/s against a mean of 4.46, a "
      + "ratio of 1.47 rather than 2. That is the imposed uniform inlet profile, not yet developed. "
      + "By xi = 0.10 the ratio has reached the laminar value and holds to the outlet.",
    "Concave temperature rise. dT(xi) lies above the straight line Q·xi/(m·cp). The wall flux is "
      + "uniform, but the wetted perimeter falls from 21.59 mm to 11.29 mm, so more heat enters per "
      + "unit length upstream than downstream. The curvature is a direct consequence of the "
      + "convergence, not a numerical artefact.",
  ]),
  ...figure(FIG + "S2_thermal.png",
    "Figure 6 — Baseline thermal development along the channel.", 0.95),
  ...figure(FIG + "S4_temperature_sections.png",
    "Figure 7 — Temperature field at successive sections.", 0.95),
  ...figure(FIG + "S3_velocity_sections.png",
    "Figure 8 — Velocity field at successive sections: the flow accelerates 4.8× as the "
    + "section converges.", 0.95),

  h("4.4 Two Reynolds numbers, and why both are reported", 2),
  p("The design brief specifies Re = 4·mdot/(pi·D_h·mu). That is the circular-duct form. It equals "
    + "the physical duct Reynolds number rho·u·D_h/mu only when A = pi·D_h²/4, which this section "
    + "does not satisfy:"),
  tableCaption("Table 10 — The section is not circular, so the two definitions differ."),
  table([
    ["Station", "A actual (mm²)", "pi·D_h²/4 (mm²)", "ratio"],
    ["inlet", "28.057", "21.229", "1.322"],
    ["outlet", "7.921", "6.188", "1.280"],
  ], [3, 3, 2.5, 1.5]),
  tableCaption("Table 11 — Reynolds number across the operating range, both definitions."),
  table([
    ["mdot_total (kg/s)", "Re brief, inlet → outlet", "Re physical, inlet → outlet"],
    ["0.0010", "23.87 → 44.21", "18.06 → 34.54"],
    ["0.0025", "59.67 → 110.53", "45.15 → 86.34"],
    ["0.0045", "107.41 → 198.95", "81.27 → 155.41"],
  ], [3, 3.5, 3.5]),
  p("Deeply laminar under either definition, which is what justifies running with no turbulence "
    + "model. But any f·Re or Nusselt correlation quoted from this work must state which definition "
    + "it uses, or it is wrong by about 30 %."),
  ...figure(FIG + "C4_reynolds.png",
    "Figure 9 — Reynolds number along the channel across the campaign flow range. It rises "
    + "along the flow because the section shrinks faster than the perimeter.", 0.8),

  h("4.5 Buoyancy — checked, not assumed away", 2),
  p("The flow is slow enough that natural convection inside the channel is a fair question. It was "
    + "evaluated rather than dismissed; Figure 10 records the result."),
  ...figure(FIG + "C5_buoyancy.png",
    "Figure 10 — Buoyancy assessment for the channel flow.", 0.8),
  ...figure(FIG + "C6_3d_hydraulics.png", "Figure 11 — 3-D hydraulic field summary.", 0.9),
  ...figure(FIG + "C7_3d_thermal.png", "Figure 12 — 3-D thermal field summary.", 0.9),
  ...figure(FIG + "C8_3d_velocity.png", "Figure 13 — 3-D velocity field.", 0.9),
  ...figure(FIG + "C9_3d_temperature.png", "Figure 14 — 3-D temperature field.", 0.9),

  calloutBox("What this stage is NOT", [
    "There is no solid region here, therefore no bridge conduction, no lateral transfer between "
      + "neighbouring channels and no alternating-flow mechanism.",
    "Nothing in Section 4 speaks to the central hypothesis. It verifies the tools that will be "
      + "used to test it.",
  ]),
];

// ===================================================== 5
const s5 = [
  pageBreak(),
  h("5. Gate 4 — 3-D grid convergence, and the one number that would not converge", 1),
  p("Three grids at a refinement ratio of about 1.5 in cell count per direction, each run to its "
    + "own residual controls. The fine grid reported “SIMPLE solution converged” after 360 "
    + "iterations — it was not stopped at an endTime."),

  tableCaption("Table 12 — Three-level 3-D grid study, Roache GCI."),
  table([
    ["Quantity", "L1 (34,304)", "L2 (105,600)", "L3 (356,400)", "order p", "GCI"],
    ["Pressure drop (Pa)", "35.872", "35.592", "35.468", "2.278", "0.290 %"],
    ["Temperature rise (K)", "25.859", "25.964", "25.975", "6.311", "0.004 %"],
    ["Meshed volume (mm³)", "18,500", "18,579", "18,617", "2.159", "0.179 %"],
    ["Peak / bulk velocity", "1.8274", "2.0617", "1.9274", "1.442", "10.972 %"],
    ["Nu, developed region", "4.1272", "3.9129", "3.7519", "0.937", "11.610 %"],
  ], [2.6, 1.6, 1.6, 1.6, 1.3, 1.3]),
  p("Pressure drop, temperature rise and meshed volume are converged at second order with grid "
    + "convergence indices of 0.29 %, 0.004 % and 0.18 %. The hydraulic side of the baseline is "
    + "sound and needs no further refinement."),

  h("5.1 The Nusselt number is not converged", 2),
  p("Applying the original extraction method unchanged — developed region taken as xi > 0.15 — to "
    + "all three grids:"),
  tableCaption("Table 13 — Nusselt number against grid, and the Richardson extrapolation."),
  table([
    ["Grid", "Cells", "Nu"],
    ["L1", "34,304", "3.7397"],
    ["L2", "105,600", "3.4282"],
    ["L3", "356,400", "3.2236"],
    ["Richardson extrapolation", "—", "2.9238"],
  ], [4, 3, 3]),
  eq("observed order p = 1.283   →   GCI = 11.63 %   →   u(nu_cfd) = 9.30 %"),
  p("First order, not second. Two independent extraction methods agree on this: the alternative "
    + "gives p = 0.937 and GCI 11.61 %. The Monte Carlo of Section 13 had assumed a 5 % standard "
    + "uncertainty on this input; 9.30 % is nearly double that."),

  calloutBox("This is a bias, not merely an uncertainty", [
    "Every conjugate result in the first revision of this study ran at nu_cfd = 3.4282, the "
      + "MEDIUM-grid value. The grid-converged value is 2.9238.",
    "The solver had therefore been running +17.25 % high on the one input that Section 13 shows "
      + "controls 91 % of the uniformity difference.",
    "Rather than extrapolate a linear sensitivity model nearly three standard deviations outside "
      + "its sampled range, the corrected value was RUN. That is the Rev 1 → Rev 2 recomputation "
      + "of Section 12.",
  ]),
  ...figure(FIG + "G1_3d_grid_convergence.png",
    "Figure 15 — The three-level 3-D grid study. Pressure drop and temperature rise converge "
    + "cleanly; the Nusselt number is still falling at 356,400 cells.", 0.9),
  ...figure(FIG + "U1_grid_convergence.png",
    "Figure 16 — Grid convergence, both the 3-D study and the conjugate plate grid.", 0.9),
  p("A fourth grid level would be needed to tighten the 11.6 % band on Nu. It was estimated at "
    + "more than 20 hours on the two cores available and is declared infeasible here rather than "
    + "quietly omitted."),
];

module.exports = { title, toc, s1, s2, s3, s4, s5, FIG, eq, code };
