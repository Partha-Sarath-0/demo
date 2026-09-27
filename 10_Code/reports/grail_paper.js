// GRAIL Collector — journal manuscript draft
const C = require("./common");
const { p, h, rich, table, tableCaption, figure, bullets, spacer, buildDoc, write,
        Paragraph, TextRun, AlignmentType } = C;
const F = "/home/claude/final_pkg/GRAIL_Collector_Complete_Final/04_Figures/current/";
const S = "/home/claude/grail_cfd/24_figures_stage3to7/";

const T = "Converging-channel roll-bond absorber with a transparent-insulation stack: conjugate CFD, machine-learning surrogate, optimisation and annual performance of alternating versus parallel flow";

const front = [
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 200 },
    children: [new TextRun({ text: T, bold: true, size: 32, color: "1B4F7A" })] }),
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 60 },
    children: [new TextRun({ text: "[Author 1]ᵃ, [Author 2]ᵃ, [Supervisor]ᵃ*", size: 22 })] }),
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 60 },
    children: [new TextRun({ text: "ᵃ [Department], [Institution], [City], India", italics: true, size: 20 })] }),
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 300 },
    children: [new TextRun({ text: "* Corresponding author: [e-mail]      Draft for: Applied Thermal Engineering (Elsevier) — target to be confirmed", size: 18, color: "4A4D52" })] }),

  h("Abstract", 2),
  p("Roll-bond absorbers integrate the liquid channels in the plate and remove the tube-to-sheet bond, but published designs use parallel channels of constant section and a single glass cover. This work studies a twelve-channel aluminium roll-bond absorber whose channels converge along the flow (outlet-to-inlet hydraulic-diameter ratio G = 0.54) under a glass + honeycomb transparent-insulation (TIM) cover with a phase-change-material and vacuum-insulation rear stack, and compares alternating (counter-current) with parallel flow. Channel hydraulics were resolved by 3-D CFD (OpenFOAM) and the plate–fluid problem by a reduced-order conjugate model (GRAIL-CHT) whose Nusselt closure, 4.48 (GCI 2.1 %), was taken from 3-D conjugate CFD. A 300-case Latin-hypercube campaign showed that alternating flow lowers mean efficiency by 7.3 % (p = 2 × 10⁻⁸) at equal inputs; at matched mean plate temperature the efficiencies are equal (Δη = −0.001 points) and alternating flow is 8–11 % less uniform at the design flow, because about 40 % of the heat a channel absorbs is returned to the plate. An ANN-ensemble surrogate (test R² 0.9994–0.9998, mean error 0.14 %) drove an NSGA-II optimisation whose optima agreed with the full model within 0.13 efficiency points. ISO 9806-form curves gave η0 = 0.637, a1 = 2.10 W m⁻² K⁻¹ (parallel). Compared with tested roll-bond collectors (η0 ≈ 0.80, a1 ≈ 4.7 W m⁻² K⁻¹) the design trades optical efficiency for a heat-loss coefficient less than half as large, and gains above a reduced temperature of about 0.04–0.05 m² K W⁻¹. For Berhampur, India, a 2-module (1.06 m²) system covers 86 % of a 100 L day⁻¹ load at a heat cost of Rs 4.34 kWh⁻¹ against Rs 4.95 kWh⁻¹ for an electric geyser. All results are simulation-based; the modelling method reproduces the measured heat-loss coefficients of a published roll-bond collector within test uncertainty but over-predicts its optical efficiency by 6–8 %.", { align: AlignmentType.JUSTIFIED }),
  rich([["Keywords: ", { bold: true }], ["roll-bond absorber; converging channels; transparent insulation; counter-current flow; conjugate heat transfer; surrogate model; NSGA-II; solar water heating", {}]]),
  h("Highlights", 2),
  ...bullets([
    "Converging roll-bond absorber under a TIM + PCM + VIP stack studied by 3-D and reduced-order conjugate CFD.",
    "At matched plate temperature, alternating and parallel flow give the same efficiency; alternating is less uniform at design flow.",
    "ANN surrogate + NSGA-II optima verified in the full model within 0.13 efficiency points.",
    "Heat-loss coefficient ≈ 2 W m⁻² K⁻¹, less than half that of tested roll-bond collectors.",
    "2-module system: 86 % solar fraction and cheaper heat than an electric geyser in Odisha, India.",
  ]),
];

const intro = [
  h("1. Introduction", 1),
  p("Flat-plate collectors dominate domestic solar water heating, and their performance is set by two groups of quantities: the optical efficiency, which depends on the cover and absorber, and the heat-loss coefficient, which depends on the cover, the rear insulation and the absorber temperature. Improving one usually costs the other.", { align: AlignmentType.JUSTIFIED }),
  p("Roll-bond absorbers remove the tube-to-sheet bond by inflating the channels inside the plate. Del Col et al. [1] tested roll-bond and sheet-and-tube collectors to EN 12975-2 and found higher efficiency for the roll-bond design (η0 = 0.80, a1 = 4.7 W m⁻² K⁻¹ with black coating). Minichannel absorbers follow the same logic: Khamis Mansour [2] reported a heat-removal factor of 0.96 against 0.83 for a conventional collector, and Vahidinia and Khorasanizadeh [3] found 13.8 % higher energy efficiency, largest at low flow and high inlet temperature. Channel layout matters: Zareie et al. [4] showed with CFD and a solar-simulator experiment that branch-inspired roll-bond channels raise PVT thermal efficiency to 61.9 %.", { align: AlignmentType.JUSTIFIED }),
  p("Varying the channel section along or across the flow is established in micro-channel cooling. Ding et al. [5] showed experimentally that narrowing the intermediate channels evens out flow and temperature, and Li et al. [6] combined a tapered manifold with variable channel sections, optimised by a surrogate model and NSGA-II, reducing the substrate temperature difference from 17.5 K to 3.5 K. In solar absorbers, a converging channel raises the local heat-transfer coefficient where the fluid is hottest, but its effect on a whole collector has not been reported.", { align: AlignmentType.JUSTIFIED }),
  p("Heat loss can be reduced by transparent insulation. Zheng et al. [7] built a collector with honeycomb and silica-aerogel layers reaching 55 % efficiency at a reduced temperature of 0.08 m² K W⁻¹, and Parthiban et al. [8] simulated a honeycomb-TIM collector over a year in an oceanic climate. Phase-change material behind the absorber stores heat for the evening; Bharathiraja et al. [9] measured a collector efficiency increase from 64.7 % to 71.7 % with a nano-enhanced PCM. Surrogate modelling is increasingly used for collector design: Sakib et al. [10] trained neural networks on 1,000 CFD runs and optimised with NSGA-II, and Alawi et al. [11] trained machine-learning models on 504 experimental points.", { align: AlignmentType.JUSTIFIED }),
  p("Three gaps remain. (i) No study combines a converging-channel roll-bond absorber with a TIM cover and a PCM/vacuum rear stack. (ii) The effect of alternating (counter-current) flow in neighbouring channels on efficiency and plate uniformity has not been separated from the effect of plate temperature. (iii) Surrogate-based optimisations are rarely checked against the full model at the optimum, and rarely carried through to annual yield and cost for a specific site. This work addresses all three for a 0.528 m² module in Berhampur, Odisha, India.", { align: AlignmentType.JUSTIFIED }),
];

const methods = [
  h("2. Collector and methods", 1),
  h("2.1 Collector", 2),
  p("The absorber is a 1.10 m × 0.48 m aluminium roll-bond plate (0.528 m²) with twelve channels at 40 mm pitch. Each channel converges linearly from inlet to outlet (G = D_h,out/D_h,in = 0.539935, grading exponent λ = 1.0); the as-built bridge width between channels is 31.29 mm. The cover is glass over a honeycomb TIM (system transmittance 0.833 × 0.82) on an absorber of absorptance 0.95, giving an optical factor of 0.649. The rear is a PCM layer (sensible heat only in this work) on a vacuum insulation panel. In the alternating arrangement neighbouring channels flow in opposite directions; in the parallel arrangement all flow the same way.", { align: AlignmentType.JUSTIFIED }),
  h("2.2 3-D CFD and Nusselt closure", 2),
  p("The channel flow was solved in 3-D with OpenFOAM (simpleFoam) on structured hexahedral meshes generated directly from the CAD surfaces, and conjugate heat transfer with chtMultiRegionSimpleFoam on a frozen, separately converged flow field for a periodic two-channel strip. Three axial and three cross-section grids give a fully developed Nusselt number of 4.48 with a grid-convergence index of 2.1 % [12], consistent with the H1 value for a semicircular duct [13].", { align: AlignmentType.JUSTIFIED }),
  ...figure(F + "F01_3D_axial_grid_study.png", "Fig. 1. Axial grid study of the 3-D conjugate solution.", 0.75),
  h("2.3 Reduced-order conjugate model (GRAIL-CHT)", 2),
  p("The full plate was solved by a finite-volume conduction model of the plate coupled to a 1-D marching energy balance in each graded channel (h = Nu k/D_h), with a top loss through glass and TIM including sky radiation (T⁴, SI units), a rear loss through PCM and VIP, a temperature-dependent aluminium conductivity and a periodic lateral boundary. Results are Richardson-extrapolated from plate grids nx = 110 and 220. Against the 3-D conjugate benchmark the model reproduces the co-current plate-temperature spread within 0.6 %.", { align: AlignmentType.JUSTIFIED }),
  h("2.4 Campaign, surrogate and optimisation", 2),
  p("A 300-case Latin-hypercube campaign (150 alternating, 150 parallel, independent groups) sampled G_T 400–1000 W m⁻², T_in 288–333 K, T_amb 283–313 K, wind 0–5 m s⁻¹, total flow 1.0–4.5 g s⁻¹, bridge 20–37 mm, G 0.35–1.0 and λ 0.5–2.0 (Re_in 22–151, laminar). Every case converged with an energy error below 0.5 %; no case was removed. Ensembles of ten multilayer perceptrons (5-fold cross-validated architecture) were trained on 240 cases and tested on 60 unseen cases for efficiency, plate standard deviation, pressure drop and mean plate temperature, with a Gaussian-process regression as benchmark and SHAP [14] for interpretation. NSGA-II [15] (population 200, 250 generations) maximised efficiency and minimised plate standard deviation and pumping power over flow, bridge, G and λ for each arrangement, and eight selected optima were re-run in GRAIL-CHT.", { align: AlignmentType.JUSTIFIED }),
  h("2.5 Efficiency curves, system and annual model", 2),
  p("A virtual steady-state test of the as-built module at 2.75 g s⁻¹ (22 GRAIL-CHT points: G 500 and 900 W m⁻², four inlet temperatures, plus three held-out points) was fitted to the ISO 9806 form q = η0 G − a1 ΔT − a2 ΔT² on the mean fluid temperature [16]. The curves drive a dynamic model: one collector node (effective capacity 33.5 kJ m⁻² K⁻¹), a fully mixed 100 kg tank (UA 1.5 W K⁻¹), a differential pump controller (on 7 K, off 2 K, disabled above 358 K) and a 100 L day⁻¹ draw at 45 °C through a mixing valve with electric top-up, solved at 60 s steps. Weather is the PVGIS TMY 2005–2023 for Berhampur (19.31° N, 84.81° E) [17], transposed to a 19.3° south-facing plane with the Hay–Davies model [18]. The model was implemented independently in Python, GNU Octave and a Scilab Xcos block diagram, which agree within 0.04 %.", { align: AlignmentType.JUSTIFIED }),
  h("2.6 Verification", 2),
  ...bullets([
    "Hottel–Whillier–Bliss (HWB) model [19] against GRAIL-CHT, with U_L taken from the solver (not fitted): +0.22 % (co-current).",
    "Energy closure of every campaign case below 0.5 %; tank first law closes to 10⁻¹¹ kWh over a year.",
    "Method check on a tested collector: the HWB fin model with Klein's top-loss correlation, applied without tuning to the two roll-bond collectors of Del Col et al. [1], reproduces the measured a1 and a2 within their 95 % test uncertainty but over-predicts η0 by 0.045–0.06 (6–8 %), attributed to optical losses (frame shading, soiling, absorptance) not described in the ideal model.",
    "No experimental data for the present collector exist; no experimental validation is claimed.",
  ]),
];

const results = [
  h("3. Results and discussion", 1),
  h("3.1 Alternating versus parallel flow", 2),
  p("At equal inputs, alternating flow lowered mean efficiency by 7.3 % relative (p = 2 × 10⁻⁸) and raised the mean plate temperature by 13.9 K. Its effect on plate uniformity depended on flow: the median plate standard deviation was 13.4 % lower above 3.3 g s⁻¹ and 16.8 % higher below 2.2 g s⁻¹, and not significant overall (−1.1 %). The 3-D solutions explain the penalty: counter-flowing channels exchange heat through the plate and about 40 % of the heat a channel absorbs (9.94 of 24.80 W) is returned to the plate upstream.", { align: AlignmentType.JUSTIFIED }),
  ...figure(F + "F07_arrangement_by_flow_rev41.png", "Fig. 2. Arrangement effect on efficiency and plate uniformity by flow rate (campaign, independent groups).", 0.85),
  p("To separate the arrangement from the plate temperature, both arrangements were solved at matched mean plate temperatures of 320, 330 and 340 K (Table 1). The efficiencies are then equal, the radiative moment R4 is not reduced, and alternating flow is 8–11 % less uniform at the design flow; it needs an inlet about 15 K cooler to reach the same plate temperature. The efficiency penalty at equal inputs is therefore a plate-temperature effect, and a claim for alternating flow can rest only on uniformity at high flow.", { align: AlignmentType.JUSTIFIED }),
  table([["Plate mean", "Inlet needed alt / par (K)", "η alt / par", "Δη (points)", "ΔR4", "Plate std alt / par (K)"],
    ["320 K", "291.3 / 306.7", "0.5989 / 0.5989", "−0.001", "+0.04 %", "6.68 / 6.17"],
    ["330 K", "302.4 / 317.3", "0.5725 / 0.5725", "−0.001", "+0.04 %", "6.49 / 5.90"],
    ["340 K", "313.5 / 328.0", "0.5457 / 0.5457", "−0.001", "+0.04 %", "6.26 / 5.63"]],
    [1.1, 1.9, 1.6, 1.1, 0.9, 1.7]),
  tableCaption("Table 1. Matched mean plate temperature, as-built geometry, 2.75 g s⁻¹, G = 800 W m⁻², T_amb = 303.15 K."),
  h("3.2 Surrogate and optimisation", 2),
  p("The ANN ensemble predicted efficiency on the 60 unseen cases with R² 0.9994–0.9998 for single networks and a mean absolute error of 0.14 %; a Gaussian process was slightly more accurate, and a linear model reached only R² 0.89. SHAP ranks inlet temperature, ambient temperature, flow and arrangement as the drivers of efficiency, while flow and irradiance drive plate uniformity and G and flow drive pressure drop. The eight NSGA-II optima re-run in GRAIL-CHT agreed within 0.13 efficiency points, 2.4 % in plate standard deviation and 5.8 % in pressure drop. The optimum lies at the upper flow bound with G approaching 1; at maximum flow the converging channel therefore serves plate uniformity rather than efficiency.", { align: AlignmentType.JUSTIFIED }),
  ...figure(S + "F15_ann_parity.png", "Fig. 3. ANN-ensemble parity on the 60 held-out cases.", 0.85),
  ...figure(S + "F17_pareto.png", "Fig. 4. NSGA-II Pareto fronts for both arrangements with GRAIL-CHT verification points.", 0.85),
  h("3.3 Efficiency curves and comparison with tested roll-bond collectors", 2),
  table([["Collector", "η0", "a1 (W m⁻² K⁻¹)", "a2 (W m⁻² K⁻²)", "Source"],
    ["This work, parallel", "0.637", "2.10", "0", "model (22 GRAIL-CHT points)"],
    ["This work, alternating", "0.597", "2.00", "0.0004", "model"],
    ["Roll-bond, black coating", "0.800 ± 0.011", "4.69 ± 0.79", "0.029 ± 0.012", "measured, EN 12975 [1]"],
    ["Roll-bond, semi-selective", "0.741 ± 0.011", "4.55 ± 0.69", "0.013 ± 0.010", "measured, EN 12975 [1]"]],
    [2.4, 1.3, 1.6, 1.6, 2.6]),
  tableCaption("Table 2. Steady-state efficiency coefficients (mean-fluid-temperature basis, G = 1000 W m⁻²)."),
  p("Held-out points were within 0.24 efficiency points of the fit, and wind changed efficiency by less than 0.3 points. The TIM + VIP stack costs 0.10–0.20 in optical efficiency against a single-glazed roll-bond collector but halves the heat-loss coefficient, so the curves cross at a reduced temperature of 0.036–0.050 m² K W⁻¹ (about 36–50 K above ambient at 1000 W m⁻²), above which the present design is better. The crossover lies at the upper edge of the fitted range (T_m − T_a ≤ 40 K), and in view of the method check (Section 2.6) the optical efficiency carries an uncertainty of up to about 7 %.", { align: AlignmentType.JUSTIFIED }),
  ...figure(S + "F18_efficiency_curves.png", "Fig. 5. Efficiency curves of the module for both arrangements.", 0.8),
  h("3.4 Annual performance and economics, Berhampur", 2),
  p("The plane receives 1,976 kWh m⁻² yr⁻¹ (the processing agrees with an independent PVGIS report within 1.5 %). At a constant 40 °C inlet the module yields 1,030 (parallel) and 965 (alternating) kWh m⁻² yr⁻¹. For the 100 L day⁻¹ load, two modules (1.06 m²) give the lowest cost of heat: solar fractions of 86 % (parallel) and 83 % (alternating), a levelised cost of heat of Rs 4.34 and 4.49 kWh⁻¹ against Rs 4.95 kWh⁻¹ for an electric geyser at the TPSODL domestic tariff of Rs 4.70 kWh⁻¹, and a simple payback of 7.4 and 7.6 years (capital cost an engineering assumption, 15-year life, 8 % discount rate). Four modules stagnate above 420 K and would need overheat protection.", { align: AlignmentType.JUSTIFIED }),
  ...figure(S + "F19_annual_monthly.png", "Fig. 6. Monthly yield, sizing and cost of heat, Berhampur.", 0.95),
];

const concl = [
  h("4. Limitations", 1),
  ...bullets([
    "Simulation only: no measurement of the present collector exists. The modelling method reproduces measured heat-loss coefficients of a published roll-bond collector but over-predicts its optical efficiency by 6–8 %.",
    "PCM latent heat, 3-D radiation/optics and manifold flow distribution were not modelled; manifold dimensions are not yet fixed.",
    "The annual model uses a single collector node and a fully mixed tank; capital costs are assumptions.",
  ]),
  h("5. Conclusions", 1),
  ...bullets([
    "At equal inputs alternating flow lowers efficiency by 7.3 %; at matched plate temperature the arrangements have equal efficiency and alternating flow is 8–11 % less uniform at design flow. The penalty is caused by heat returned to the plate (≈ 40 %), not by extra radiative loss.",
    "An ANN surrogate trained on 240 conjugate-CFD cases (test R² ≥ 0.9994) supports a verified NSGA-II optimisation; at the optimum the converging channel serves uniformity rather than efficiency.",
    "The TIM + VIP stack gives a heat-loss coefficient of about 2 W m⁻² K⁻¹, less than half that of tested roll-bond collectors, and outperforms them above ≈ 0.04–0.05 m² K W⁻¹.",
    "In Berhampur a 2-module system covers 83–86 % of a 100 L day⁻¹ load and delivers heat cheaper than an electric geyser, with a payback of about 7.5 years.",
    "Experimental testing of a prototype, including optical losses and PCM latent storage, is the next step.",
  ]),
  h("Data availability", 2),
  p("The 300-case dataset, all scripts and the system models (Python, GNU Octave, Scilab Xcos, MATLAB/Simulink build code) are available from the authors."),
  h("References", 1),
  ...[
    "[1] D. Del Col, A. Padovan, M. Bortolato, M. Dai Prè, E. Zambolin, Thermal performance of flat plate solar collectors with sheet-and-tube and roll-bond absorbers, Energy 58 (2013) 258–269.",
    "[2] M. Khamis Mansour, Thermal analysis of novel minichannel-based solar flat-plate collector, Energy 60 (2013) 333–343. https://doi.org/10.1016/j.energy.2013.08.013",
    "[3] F. Vahidinia, H. Khorasanizadeh, Comparative energy, exergy and entropy generation study of a minichannel and a conventional solar flat plat collectors, Energy 304 (2024) 132232.",
    "[4] Z. Zareie, R. Ahmadi, M. Asadi, A comprehensive numerical investigation of a branch-inspired channel in roll-bond type PVT system using design of experiments approach, Energy 286 (2024) 129452.",
    "[5] Y. Ding, M. Liu, Q. Jin, Experimental and numerical investigation of the influence of varying micro-channel width on flow and heat transfer uniformity, Int. J. Therm. Sci. 208 (2025) 109394.",
    "[6] J.-B. Li, T.-Y. Zhang, Z.-D. Li, L. Chen, W.-Q. Tao, Multi-objective parameter optimization design of tapered-type manifold/variable cross-section microchannel heat sink, Appl. Therm. Eng. 251 (2024) 123587.",
    "[7] J. Zheng, R. Febrer, J. Castro, D. Kizildag, J. Rigola, A new high-performance flat plate solar collector. Numerical modelling and experimental validation, Appl. Energy 355 (2024) 122221.",
    "[8] A. Parthiban, C. Fogarty, D. McCloskey, Transparent insulation integration in solar thermal collector: Advancing performance for domestic water heating in oceanic climates of Western Europe, Appl. Therm. Eng. 258 (2025) 124715.",
    "[9] R. Bharathiraja, T. Ramkumar, M. Selvakumar, K. Sasikumar, Experimental and numerical analysis of hybrid nano-enhanced phase change material (PCM) based flat plate solar collector, J. Energy Storage 96 (2024) 112649.",
    "[10] N. Sakib, P.R. Paul, N.A. Pratik, S. Sarker, T. Talukder, P. Debnath, M.H. Ali, Novel prediction modeling of flat plate solar collector using Kolmogorov–Arnold Networks (KAN) and multi-objective performance optimization via NSGA-II, Energy Convers. Manage.: X 31 (2026) 102073.",
    "[11] O.A. Alawi, H.M. Kamar, S.Q. Salih, et al., Development of optimized machine learning models for predicting flat plate solar collectors thermal efficiency associated with Al2O3-water nanofluids, Eng. Appl. Artif. Intell. 133 (2024) 108158.",
    "[12] I.B. Celik, U. Ghia, P.J. Roache, C.J. Freitas, H. Coleman, P.E. Raad, Procedure for estimation and reporting of uncertainty due to discretization in CFD applications, J. Fluids Eng. 130 (2008) 078001.",
    "[13] R.K. Shah, A.L. London, Laminar Flow Forced Convection in Ducts, Academic Press, New York, 1978.",
    "[14] S.M. Lundberg, S.-I. Lee, A unified approach to interpreting model predictions, Adv. Neural Inf. Process. Syst. 30 (2017).",
    "[15] K. Deb, A. Pratap, S. Agarwal, T. Meyarivan, A fast and elitist multiobjective genetic algorithm: NSGA-II, IEEE Trans. Evol. Comput. 6 (2002) 182–197.",
    "[16] ISO 9806:2017, Solar energy — Solar thermal collectors — Test methods, International Organization for Standardization, Geneva, 2017.",
    "[17] European Commission Joint Research Centre, Photovoltaic Geographical Information System (PVGIS), typical meteorological year 2005–2023, https://re.jrc.ec.europa.eu/pvg_tools/",
    "[18] J.E. Hay, J.A. Davies, Calculation of the solar radiation incident on an inclined surface, in: Proc. First Canadian Solar Radiation Data Workshop, 1980, pp. 59–72.",
    "[19] J.A. Duffie, W.A. Beckman, Solar Engineering of Thermal Processes, 4th ed., Wiley, Hoboken, 2013.",
  ].map((r) => p(r, { run: { size: 18 } })),
];

const doc = buildDoc({ title: "GRAIL converging roll-bond absorber — manuscript draft", subtitle: "Journal manuscript draft",
  sections: [[].concat(front, intro, methods, results, concl)] });
write(doc, "/home/claude/reports/GRAIL_paper_draft.docx");
