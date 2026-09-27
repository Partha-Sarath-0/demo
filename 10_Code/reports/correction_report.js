// GRAIL — CFD Scientific Correction & Targeted Repair: the nine deliverables
const fs = require("fs");
const C = require("./common");
const { p, h, rich, table, tableCaption, bullets, numbered, calloutBox, spacer,
        buildDoc, write, Paragraph, TextRun, AlignmentType, TableOfContents } = C;
const { Paragraph: P_, HeadingLevel: HL_ } = require("docx");
function h1(text) {
  return new P_({ text, heading: HL_.HEADING_1, pageBreakBefore: true,
    spacing: { before: 0, after: 160 }, keepNext: true });
}
const D = "/home/claude/grail_cfd/10_dataset/";
const cmp = JSON.parse(fs.readFileSync(D + "rev3_vs_rev4.json"));
const f = (x, d = 2) => (x >= 0 ? "+" : "−") + Math.abs(x).toFixed(d);
function cmpRow(label, key, sub) {
  const x = cmp[key][sub];
  return [label, String(x.n_pairs), f(x.eta.mean) + " / " + f(x.eta.median) + " %",
    f(x.plate_std_K.mean, 1) + " / " + f(x.plate_std_K.median, 1) + " %",
    (100 * x.plate_std_K.frac_alt_lower).toFixed(0) + " %",
    f(x.plate_spread_K.median, 1) + " %", f(x.P90_K.mean, 1) + " K"];
}

// ------------------------------------------------------------------ title
const title = [
  spacer(2400),
  new Paragraph({ alignment: AlignmentType.CENTER,
    children: [new TextRun({ text: "THE GRAIL COLLECTOR", bold: true, size: 44, color: "1B4F7A" })],
    spacing: { after: 80 } }),
  new Paragraph({ alignment: AlignmentType.CENTER,
    children: [new TextRun({ text: "CFD Scientific Correction & Targeted Repair", size: 32 })],
    spacing: { after: 300 } }),
  new Paragraph({ alignment: AlignmentType.CENTER,
    children: [new TextRun({ text: "Root cause, repaired 3-D conjugate CFD, corrected Nusselt closure, "
      + "Dataset Rev 4, and the claims that can and cannot be made.",
      italics: true, size: 21, color: "4A4D52" })],
    spacing: { after: 420 } }),
  table([
    ["Item", "Value"],
    ["Decision-tree outcome", "B — targeted additional CFD (executed)"],
    ["3-D conjugate solutions converged", "12 (was 0)"],
    ["Nusselt closure", "2.9238 (H2-type) → 4.48 (3-D conjugate, grid-extrapolated)"],
    ["Dataset", "Rev 4.1: 300 / 300; Rev 4 plus three audited derived-column corrections"],
    ["Rows deleted / altered", "0 — Rev 1, 2, 3 untouched and reproducible"],
    ["Experimental validation", "NONE claimed — all comparisons are code-to-code or code-to-reference"],
    ["Roadmap V5", "Gunjo et al. 2017 assessed and rejected (DESIGN_REVIEW_REQUIRED) — see Section 10"],
  ], [3.4, 6.6]),
  spacer(500),
  new Paragraph({ alignment: AlignmentType.CENTER,
    children: [new TextRun({ text: "Supersedes the arrangement conclusions of the CFD Simulation Report "
      + "(Rev 2) and the Dataset Audit Addendum", size: 19, color: "4A4D52" })] }),
];
const toc = [
  h1("Contents"),
  new TableOfContents("Contents", { hyperlink: true, headingStyleRange: "1-2" }),
  p("(In Word: right-click the field and choose Update Field.)",
    { run: { italics: true, size: 17, color: "4A4D52" } }),
];

// ------------------------------------------------------------------ summary
const s0 = [
  h1("Summary"),
  p("The production campaign's conclusions rested on a reduced-order conjugate model (GRAIL-CHT) whose "
    + "Nusselt closure had never been tested against a 3-D conjugate solution, because every 3-D conjugate "
    + "attempt had diverged. This work found why the 3-D solver diverged, repaired it with an exact "
    + "method, produced the first converged 3-D conjugate solutions, and used them to test the model."),
  p("The model's structure passed. Its Nusselt input did not: the campaign value 2.9238 came from a "
    + "boundary condition (uniform peripheral heat flux, H2) that the aluminium plate does not impose. The "
    + "3-D conjugate value is 4.48 after grid extrapolation, close to the published H1 value 4.088–4.089 "
    + "for a semicircular duct. A second error was found in the model's own axial grid (110 cells, "
    + "first-order): it overstated the uniformity benefit by about 3 pp."),
  p("With both corrected (Dataset Rev 4), the efficiency penalty of the alternating arrangement is "
    + "larger (mean −7.3 %, Mann–Whitney p = 2e-8, group-wise), and the plate-uniformity benefit is no longer a general "
    + "result: overall the median plate standard deviation changes by only −1.1 % (p = 0.76, not significant); it improves at "
    + "high flow (−13.4 % above 3.3 g/s, p = 0.02) and worsens at low flow (+16.8 % below 2.2 g/s, p = 0.03). All comparisons "
    + "are between the two independent 150-case groups; ALT_n and PAR_n are NOT matched pairs."),
  calloutBox("What this means for the thesis", [
    "The CFD phase is complete and defensible, but the headline claim changes from 'alternating flow "
      + "improves uniformity' to 'alternating flow trades efficiency for uniformity only above a "
      + "flow threshold, and costs both below it'.",
    "This is reported because it is what the corrected physics gives. No parameter was tuned, and "
      + "every decision (Nu value, grid, acceptance gates) was fixed before any Rev 4 row was seen.",
  ]),
];

// ------------------------------------------------------------------ 1
const s1 = [
  h1("1. Root-cause analysis"),
  p("Every weakness is listed with its evidence and its effect. Items 1–4 are scientific; 5–7 are "
    + "numerical; 8 is procedural and recorded for honesty."),
  tableCaption("Table 1 — Root causes."),
  table([
    ["#", "Weakness", "Evidence", "Effect on results"],
    ["1", "Nu closure 2.9238 from an H2-type case", "Fluid-only 3-D study imposed flux uniform around the "
      + "perimeter; conjugate 3-D gives 4.6 (NU 64), 4.48 extrapolated; H1 reference 4.088 (Erdoğan & Imrak "
      + "2005), 4.089 (Shah & London table in Hesselgreaves 2001)", "Overstated uniformity benefit ~3×; "
      + "understated the efficiency penalty"],
    ["2", "3-D CHT divergence (chtMultiRegionSimpleFoam)", "buoyant p_rgh SIMPLE fails on the fluid region "
      + "alone and on the validated single-channel mesh; face fluxes correct, cell velocities wrong ~10⁵ in "
      + "the transverse plane", "No 3-D conjugate evidence existed; the ROM was unverified"],
    ["3", "Solar input applied per curved area in the old CHT case", "solid_top 0.098723 m² vs plan "
      + "0.088000 m²", "+12.2 % heat input (old case only; repaired with h = U·n_z)"],
    ["4", "Taper has no thermal effect under constant Nu", "hP = Nu·k·P/Dh with P/Dh invariant; "
      + "co-taper vs CAD-taper η identical to 5 digits", "The ROM cannot represent a geometric "
      + "taper benefit; any such claim is unsupported"],
    ["5", "ROM axial grid 110 cells, first-order", "p = 1.01; Δstd −10.51 / −8.91 / −8.12 % at "
      + "110 / 220 / 440", "~3 pp overstatement of uniformity benefit in Rev 1–3"],
    ["6", "3-D mass flow −0.30 % below nominal", "meshed inlet 27.9726 vs CAD 28.0569 mm²",
      "Handled by running the ROM at the 3-D flow; negligible"],
    ["7", "Limit cycle at fluid relaxation 1.0", "fluid minimum flipping 300.000 / 299.334 K",
      "Removed at 0.8; steady answer unaffected"],
    ["8", "Operator errors in this work", "empty substitution deleted a converged flow (re-run, dp "
      + "37.929 Pa reproduced); unverified mapFields -fields option (failed safely)",
      "None on results; recorded in 14_provenance"],
  ], [0.4, 2.4, 4.2, 2.8]),
  h("1.1 What was NOT wrong", 2),
  ...bullets([
    "The dataset's internal algebra: every derived column closes to machine precision (audit).",
    "The energy balances: 3-D independent balances 0.003–0.05 %; ROM < 2e-4 %.",
    "The ROM's structure (lumped plate, lateral conduction, channel march): with the right Nu it "
      + "reproduces the co-current 3-D solution to 0.01 % in η and 0.6 % in std.",
    "The mesh: simpleFoam converges on the same meshes; the failure is the buoyant formulation.",
  ]),
];

// ------------------------------------------------------------------ 2
const s2 = [
  h1("2. CFD status matrix"),
  p("Status: VALID — usable as evidence; QUALIFIED — usable with the stated limit; SUPERSEDED — kept "
    + "for provenance, not to be cited for the conclusion it was produced for; INVALID — not to be used."),
  tableCaption("Table 2 — Every CFD product."),
  table([
    ["Product", "Status", "Reason / limit"],
    ["Single-channel fluid-only GCI study (simpleFoam)", "VALID", "Hydraulics, dp, flow development"],
    ["Nu = 2.9238 from that study", "SUPERSEDED", "H2-type; not the plate's condition"],
    ["Old CHT attempts (trial2/trial3, buoyant)", "INVALID", "Diverged; +12.2 % solar input"],
    ["3-D frozen-flow CHT, NX 60/120/240, NU 48/64/96", "VALID", "Converged, balances ≤ 0.05 %; "
      + "exact for constant properties only"],
    ["3-D CHT envelope 1.0 / 4.5 g/s (co-current)", "VALID", "Nu flow-independence; entry effect"],
    ["NX 60 ROM-vs-3-D agreement (−8.91 vs −8.96 %)", "SUPERSEDED", "Coincidence of two coarse grids"],
    ["Dataset Rev 1, Rev 2, Rev 3", "SUPERSEDED", "Nu 2.9238 and 110-cell plate grid; kept, "
      + "bit-reproducible"],
    ["Dataset Rev 4.1 (Rev 4 + 3 derived-column corrections)", "QUALIFIED", "Model-form uncertainty from the 3-D "
      + "benchmark (≈ 2 pp on Δ std); campaign loss model not 3-D tested (V5 open)"],
    ["Uncertainty record (efficiency −5.55 %, RMS spread −11.52 %)", "SUPERSEDED", "Built on Rev 2"],
    ["Roadmap V5 (Gunjo et al. 2017)", "REJECTED", "Reference internally inconsistent; Section 10"],
  ], [4.0, 1.5, 4.5]),
];

// ------------------------------------------------------------------ 3
const s3 = [
  h1("3. Targeted CFD plan — as executed"),
  p("Decision B: the evidence (a validated structure with one wrong input) called for targeted "
    + "3-D runs, not a rebuild. Every run below was completed; none was dropped."),
  tableCaption("Table 3 — Runs executed."),
  table([
    ["Purpose", "Runs", "Result"],
    ["Repair and first solution", "co + alt, NU 64, NX 60", "Converged; balance 0.005 / 0.035 %"],
    ["Axial grid", "co + alt, NX 120, NX 240", "Δη converged (−18.91 %); Δ std oscillatory "
      + "(−8.96 / −4.88 / −5.37 %)"],
    ["Cross-section grid", "co + alt, NU 48 / NR 4 and NU 96 / NR 8", "Nu 4.646 / 4.602 / 4.556 → "
      + "4.48 (p 1.12, GCI 2.1 %)"],
    ["Nu envelope", "co, 1.0 and 4.5 g/s", "Developed Nu 4.60 at all flows; entry Nu 6.1–6.35 at 4.5 g/s"],
    ["ROM counterpart", "Nu 4.088 / 4.48 / 4.6 / Nu(ξ); plate 110–880", "p = 1.01; model-form gap 2.0 pp"],
    ["Campaign", "Rev 4 at plate 110 and 220", "300 / 300 accepted at both"],
  ], [2.6, 3.4, 4.0]),
];

// ------------------------------------------------------------------ 4
const s4 = [
  h1("4. 3-D CHT repair"),
  p("Controlled experiments, one change each, located the divergence in the buoyant solver's "
    + "p_rgh formulation on this O-grid mesh family: it fails identically on the fluid region alone "
    + "(no solid, no interface) and on the previously validated single-channel mesh. Pressure "
    + "reference, wall pressure condition, bad cells, relaxation, schemes and correctors were each "
    + "eliminated. The corrected face fluxes satisfy continuity while the cell velocities are wrong by "
    + "~10⁵ in the cross-section plane, which is consistent with a failure in rebuilding cell velocity "
    + "from face flux on cells micrometres thick and millimetres long. The source line could not be "
    + "quoted, so this last step is stated as consistent with the evidence, not proven."),
  h("4.1 The repair: frozen-flow one-way coupling", 2),
  p("With constant ρ, μ, k and cp, the momentum and continuity equations contain no temperature. The "
    + "steady flow (simpleFoam, which converges) is therefore independent of the energy solution, and "
    + "solving energy on that frozen flow with chtMultiRegionSimpleFoam's frozenFlow switch is the same "
    + "steady solution as a fully coupled solve. frozenFlow was verified in the installed v1912 binary; "
    + "0 pressure and 0 momentum solves were confirmed; the supplied flux was confirmed unchanged "
    + "(1.5e-8 relative)."),
  p("Limit: the repair is exact only for constant properties. The Rev 3/4 campaign uses k(T); the 3-D "
    + "benchmark therefore tests the closure and the coupling, not the k(T) path."),
  h("4.2 Benchmark definition", 2),
  ...bullets([
    "2-channel periodic strip, 1100 × 80 mm, the CAD plate (taper alternates channel to channel).",
    "Top: q″ 519.1256 W/m² minus U_top 4.191176 W/m²K × (T − 298.15 K), per unit plan area.",
    "Rear: 3.0 W/m²K to 298.15 K. Inlet 300 K, 2.077072e-4 kg/s per channel.",
    "Linear loss model by design (ENGINEERING_ASSUMPTION): it isolates the coupling physics.",
  ]),
];

// ------------------------------------------------------------------ 5
const s5 = [
  h1("5. Nusselt correction"),
  tableCaption("Table 4 — Conjugate Nu, developed region (15–85 % of length), co-current."),
  table([
    ["Grid / condition", "Nu channel a / b", "Mean"],
    ["NU 64, NX 60", "4.603 / 4.582", "4.592"],
    ["NU 64, NX 120", "4.614 / 4.590", "4.602"],
    ["NU 64, NX 240", "4.614 / 4.590", "4.602"],
    ["NU 48, NX 120", "4.658 / 4.633", "4.646"],
    ["NU 96, NX 120", "4.567 / 4.545", "4.556"],
    ["NU 64, NX 120, 1.0 g/s", "4.604 / 4.595", "4.599"],
    ["Extrapolated (cross-section, p 1.12)", "—", "4.48, GCI 2.1 %"],
    ["Reference H1, semicircular duct", "—", "4.088 / 4.089"],
    ["Campaign Rev 1–3 (H2-type)", "—", "2.9238"],
  ], [4.2, 3.2, 2.6]),
  p("Nu is axially converged and flow-independent in the developed region. It still moves with "
    + "cross-section refinement, and the extrapolated value 4.48 is used for Rev 4 with a band of "
    + "4.46–4.65. The conjugate value sits above the ideal H1 value because the wall is not perfectly "
    + "isothermal around the perimeter and the flat base and domed top see different fluxes."),
  p("In the alternating arrangement Nu is undefined where q′ and T_w − T_b change sign together "
    + "(Nu ≈ 47 at ξ ≈ 0.61). h itself stays near 4–5 on both sides. A constant Nu therefore cannot "
    + "represent the alternating channel exactly; this is the origin of the 2 pp model-form gap."),
  p("The H2 value for a semicircular duct (≈ 2.92) is recalled from Shah & London 1978 and has NOT been "
    + "verified from the source. No conclusion depends on it."),
];

// ------------------------------------------------------------------ 6
const s6 = [
  h1("6. Dataset correction — Rev 4 and Rev 4.1"),
  p("Only the Nu closure and the plate grid change. Seed, Latin Hypercube, bounds, geometry gate, k(T) "
    + "and acceptance gates (tolerance 1e-6, |energy error| < 0.5 %, 250 < T_plate < 500 K) are "
    + "identical to Rev 3. The outer-iteration cap was raised from 900 to 3000; the tolerance was not "
    + "loosened (it is asserted in code). All 300 rows passed at both grids. No row was deleted."),
  tableCaption("Table 5 — Arrangement comparison, Dataset Rev 4.1, two independent groups (unpaired)."),
  table([
    ["Quantity", "Parallel (n = 150)", "Alternating (n = 150)", "Difference", "Mann–Whitney p"],
    ["η, mean", "0.5620", "0.5209", "−7.3 %", "2e-8"],
    ["Plate std, median (K)", "5.013", "4.960", "−1.1 %", "0.76 (n.s.)"],
    ["Plate spread, median (K)", "16.57", "19.61", "+18.4 %", "0.001"],
    ["Mean plate T (K)", "—", "—", "+13.9 K (mean)", "2e-10"],
    ["P90 (K)", "—", "—", "+12.6 K (mean)", "2e-6"],
  ], [2.6, 1.8, 1.9, 1.7, 1.6]),
  p("Rev 3 (Nu 2.92, plate 110) under the same unpaired test gave η −5.1 % and plate std −29.3 % (p = 5e-5): the corrected "
    + "closure and grid remove almost all of the apparent uniformity benefit. The input distributions of the two groups are "
    + "statistically identical (KS p = 1.00 for all eight inputs), so the group comparison is fair. Earlier drafts of this "
    + "report paired ALT_n with PAR_n; those cases do not share inputs, and every paired statistic has been withdrawn."),
  tableCaption("Table 6 — Rev 4.1 by total flow rate (terciles, unpaired)."),
  table([
    ["Total flow", "n alt / par", "Δ mean η", "Δ median plate std", "p (std)"],
    ["1.0 – 2.2 g/s", "50 / 50", "−12.7 %", "+16.8 %", "0.03"],
    ["2.2 – 3.3 g/s", "50 / 50", "−6.0 %", "+7.9 %", "0.14 (n.s.)"],
    ["3.3 – 4.5 g/s", "50 / 50", "−3.5 %", "−13.4 %", "0.02"],
  ], [2.2, 1.6, 1.8, 2.2, 1.8]),
  h("6.1 Rev 4.1 — independent audit and surgical correction", 2),
  p("An independent audit of Rev 4 found three derived-column groups inconsistent with their own definitions: R4_K4 / "
    + "T_R4_K / mean_T_pow4_K4 (copied from the nx220 run into a Richardson file; 120 rows had T_R4 < T_mean), U_L "
    + "(extrapolated linearly although it is a nonlinear function of other columns; up to 2.2 %), and Re_in / Re_out "
    + "(circular-duct formula on a semicircular duct; ×1.3217). Rev 4.1 recomputes only these six columns: R4 = 2R4(220) − "
    + "R4(110), T_R4 = R4^¼, mean_T_pow4 = T_mean⁴, U_L = (Q_solar − Q_u)/(0.528(T_mean − T_amb)), Re = ṁD_h/(Aμ). The other "
    + "53 columns are byte-for-byte identical; no row, sign or thermal result changed. A final provenance audit found μ, Δp "
    + "and energy_error_pct exact for their source (nx220) run, differing from a Richardson-consistent recomputation by at "
    + "most 0.17 % and 1.9e-5 pp — documented, not changed. Status: internally consistent within the audited model "
    + "definitions and assumptions; ready to freeze."),
];

// ------------------------------------------------------------------ 7
const s7 = [
  h1("7. Report correction plan"),
  tableCaption("Table 7 — KEEP / REWRITE / QUALIFY / REMOVE."),
  table([
    ["Document / statement", "Action", "Replacement"],
    ["CAD Model Report", "KEEP", "Geometry unaffected"],
    ["CFD Report: hydraulics, mesh study, dp", "KEEP", "—"],
    ["CFD Report: 'Nu = 2.9238 validated closure'", "REWRITE", "H2-type fluid-only value; superseded "
      + "by 3-D conjugate 4.48"],
    ["CFD Report: 'no conjugate 3-D solution possible'", "REWRITE", "Diagnosed and repaired; Sections 1, 4"],
    ["CFD Report: '0 rejected' (Rev 2)", "QUALIFY", "True for Rev 2; Rev 3 rejected 2; Rev 4 0 at cap 3000"],
    ["Audit Addendum: 'the uniformity benefit stands'", "REMOVE", "Flow-dependent; see Section 9"],
    ["Uncertainty record headline (−5.55 % η, −11.52 % RMS)", "REWRITE", "Rev 4 values with model-form term"],
    ["Mechanism tables (Rev 1)", "REWRITE", "3-D heat-recirculation budget (40 % returned)"],
    ["Paper abstract: 'without simplifying assumptions'", "REMOVE", "Lumped plate, constant Nu, linear "
      + "benchmark losses are assumptions"],
    ["Paper abstract: 'closures integrated'", "REWRITE", "'closure derived from 3-D conjugate CFD'"],
    ["Paper abstract: 'rigorous mesh independence'", "QUALIFY", "Δη converged; Δ std oscillatory / "
      + "non-asymptotic, bounded ± 1 pp"],
    ["Paper abstract: mixed Nu bases across numbers", "REWRITE", "Every number from Rev 4"],
    ["Any sentence calling a comparison 'experimental validation'", "REMOVE", "'benchmark against 3-D "
      + "CFD' or 'comparison with published correlation'"],
  ], [4.4, 1.3, 4.3]),
];

// ------------------------------------------------------------------ 8
const s8 = [
  h1("8. Final CFD architecture"),
  ...numbered([
    "Level 1 — single-channel fluid-only CFD (simpleFoam, GCI): hydraulics and flow development.",
    "Level 2 — 3-D conjugate CFD on the 2-channel periodic strip (simpleFoam flow, frozen-flow "
      + "chtMultiRegionSimpleFoam energy), grid-studied on three axial and three cross-section levels: "
      + "supplies the Nu closure and benchmarks the ROM.",
    "Level 3 — GRAIL-CHT reduced-order conjugate model with the Level-2 closure (Nu 4.48), k(T), "
      + "plate grid 110 and 220 with Richardson: runs the 300-case design space (Dataset Rev 4).",
    "Level 4 — reference comparisons: H1 correlation (Erdoğan & Imrak 2005; Shah & London via "
      + "Hesselgreaves 2001). Roadmap V5 (Gunjo et al. 2017) assessed and rejected as a reference (Section 10).",
  ]),
  tableCaption("Table 8 — Uncertainty budget on the arrangement difference at design flow."),
  table([
    ["Source", "Δη", "Δ std"],
    ["3-D discretisation (axial + cross-section)", "± 0.1 pp", "± 1.0 pp (bound)"],
    ["ROM axial discretisation after Richardson", "< 0.1 pp", "≈ 0.4 pp"],
    ["ROM model form (constant Nu, alternating)", "0.5 pp (ROM less negative)", "2.0 pp (ROM more negative)"],
    ["Nu band 4.46–4.65", "≈ 0.1 pp", "≈ 1.1 pp"],
    ["Entry-region Nu at high flow", "< 0.1 %", "≤ 2.1 % of std"],
    ["Campaign loss model (glazing, radiation)", "not quantified", "not quantified (V5 open)"],
  ], [4.6, 2.6, 2.8]),
];

// ------------------------------------------------------------------ 9
const s9 = [
  h1("9. Final research claims"),
  h("9.1 Claims supported", 2),
  ...bullets([
    "Alternating counter-current flow in the converging roll-bond absorber lowers thermal efficiency: "
      + "group mean −7.3 % (p = 2e-8), at every flow tercile (−12.7 / −6.0 / −3.5 %). At design flow the 3-D benchmark "
      + "gives −18.9 % under benchmark losses.",
    "Mechanism: counter-flow heat recirculation through the plate — in the 3-D benchmark about 40 % of the heat "
      + "a channel absorbs (9.94 of 24.80 W) is returned to the plate over 41 % of its length; the budget closes "
      + "against ṁc_pΔT to 0.1 %.",
    "Plate uniformity depends on flow rate: alternating flow lowers the median plate std at high flow "
      + "(−13.4 % above 3.3 g/s, p = 0.02) and raises it at low flow (+16.8 % below 2.2 g/s, p = 0.03); over the "
      + "whole space the difference (−1.1 %) is not significant.",
    "The alternating plate runs hotter on average (+13.9 K mean; +12.6 K mean P90 across the space).",
    "The 3-D conjugate Nu for the channel is 4.48 (grid-extrapolated), consistent with the H1 "
      + "condition, not the H2 condition used in earlier revisions.",
    "A reduced-order conjugate model with this closure reproduces the 3-D co-current solution to "
      + "0.01 % in η and 0.6 % in std; for the alternating arrangement it overstates the uniformity "
      + "benefit by ≈ 2 pp.",
  ]),
  h("9.2 Claims that must NOT be made", 2),
  ...bullets([
    "That alternating flow improves plate uniformity in general, or 'at no cost'.",
    "Any statistic built by pairing ALT_n with PAR_n (\"69 % / 51 % of pairs\", \"+80 % / −34 %\"): they are independent samples.",
    "Any Rev 1–3 number as a final result (efficiency −4.33 %, −5.24 %, −5.55 %; RMS spread −11.52 %; "
      + "Δ std −27.9 % median).",
    "That the converging taper improves heat transfer: under a constant Nu the ROM cannot see it.",
    "That the peak-to-peak (max − min) plate temperature is reduced: group median +18.4 %, 3-D +3 %.",
    "'Experimental validation' of any kind: there is none. The comparisons are 3-D-CFD-to-ROM and "
      + "CFD-to-correlation.",
    "'Mesh-independent' Δ std from the 3-D study: it converges oscillatorily / non-asymptotically "
      + "and is bounded, not extrapolated.",
    "That the 3-D benchmark validates the campaign's glazing, radiation, PCM or VIP models: it uses "
      + "a linear loss model and constant properties.",
    "Any result from the old diverging-channel geometry.",
  ]),
  h("9.3 Experimental validation", 2),
  p("None. Roadmap V5 was assessed and rejected with documented reasons (Section 10). The thesis "
    + "claims verification against 3-D conjugate CFD and published laminar-duct correlations only."),
  spacer(80),
  calloutBox("Integrity statement", [
    "No row was deleted, altered or reweighted. Rev 1–3 remain bit-reproducible.",
    "The Nu value, plate grids and gates were fixed and recorded before any Rev 4 row was seen.",
    "Results unfavourable to the alternating arrangement are reported with the same prominence as "
      + "favourable ones.",
    "Stop point: CFD phase complete. No ANN, surrogate, optimisation or systems modelling was done.",
  ]),
];

const s10 = [
  h1("10. Roadmap V5 — Gunjo et al. 2017 assessed"),
  p("Paper: D.G. Gunjo, P. Mahanta, P.S. Robi, CFD and experimental investigation of flat plate solar water "
    + "heating system under steady state condition, Renewable Energy (2017), doi:10.1016/j.renene.2016.12.041. "
    + "It was read in full. Values below are read from its plots (± about 1 K); it gives no data tables."),
  tableCaption("Table 9 — Why the reference cannot be used."),
  table([
    ["#", "Finding", "Evidence"],
    ["1", "Its simulation violates energy conservation", "Noon: simulated ΔT ≈ 33 K needs ≈ 1.7 kW at 0.0125 kg/s "
      + "and ≈ 3.4 kW at 0.025 kg/s; total solar input is ≈ 1.53 kW (930 W/m² × 1.65 m²)"],
    ["2", "Its accuracy claim comes from the error definition", "Error taken on absolute kelvin: 336 vs 317 K is "
      + "“5.7 %”, but the temperature rise is off by more than 100 %"],
    ["3", "Measured outlet ignores flow rate", "Figs 9a/9b nearly identical at double flow; implies η ≈ 95 % "
      + "against the paper's own 56 % maximum"],
    ["4", "Inputs missing or contradictory", "No wind speed, no (ατ); tube wall 0.7 mm vs 7 mm; strip 0.100 m vs "
      + "pitch 0.1125 m"],
    ["5", "Different collector", "Round tubes brazed to a sheet, not a roll-bond channel plate"],
  ], [0.4, 3.4, 6.2]),
  p("Decision: DESIGN_REVIEW_REQUIRED — reference rejected, V5 closed with this documented reason. No GRAIL result "
    + "was compared with it, tuned to it, or described as validated by it. A replacement experimental reference, "
    + "if one is required, must tabulate its data, pass an independent energy balance and state every boundary input."),
];

const doc = buildDoc({
  title: "GRAIL Collector — CFD Scientific Correction & Targeted Repair",
  subtitle: "Nine deliverables of the correction master prompt.",
  sections: [title, [].concat(toc, s0, s1, s2, s3, s4, s5, s6, s7, s8, s9, s10)],
});
write(doc, "/home/claude/reports/GRAIL_CFD_Correction_Report.docx");
