# GRAIL Collector — complete package (Rev 4.2)

- **Dataset:** `06_Datasets/GRAIL_CFD_dataset_FINAL_rev4.2.csv`: 300 cases, audited and frozen.
  - It holds the same data as Rev 4.1; three columns were renamed (see `06_Datasets/archive/…rev4.2_change_log.md`).
  - Rev 4.1 is kept in `archive/`.
- **Reports:**
  - CFD: `02_Reports/GRAIL_CFD_Simulation_Report_Rev4.1` (Part V is final).
  - Stages 3–7: `12_Stages_3-5-6-7/report/GRAIL_Stages_3-5-6-7_Report.docx`.
  - Roadmap status: `01_Roadmap/GRAIL_Roadmap_RevI_Completion_Status_Rev4.2`.
- **Scope:**
  - The CFD phase is closed.
  - The ANN (Stage 3), NSGA-II (Stage 5), system model (Stage 6) and annual/techno-economic analysis (Stage 7) are done.
  - Topology optimisation was replaced by NSGA-II parameter optimisation.
- **Validation:** model-to-model, model-to-textbook, and method/component checks against published measurements (Del Col 2013, Beikircher 2015). **No experimental validation of this collector is claimed**; V5 is complete at method level (see below).

## Start here
- **In VS Code:** `START_HERE_VSCode.md`, then `15_Run_in_VSCode/README.md`.
- **Headline results:** "Final results" below.

## Folders
| Folder | Contents |
|---|---|
| 01_Roadmap | Roadmap Rev I (PDF). **Completion Status Rev 4.2** gives the status of every roadmap section, V1–V10 and the open items |
| 02_Reports | CFD, CAD, correction and audit reports, the simple engineering report (`GRAIL_Engineering_Report_Simple`), the journal paper draft (`GRAIL_paper_draft`) and the day-wise project diary (`GRAIL_Project_Diary`) |
| 03_CAD | Grail_Collector_2 (.f3d, .step), strip STEP files, gate JSON files, geometry scripts |
| 04_Figures | `current/`: F01–F14; `legacy_rev2_reference/`: earlier figures (geometry and mesh figures still valid; thermal numbers superseded) |
| 05_Videos | 3-D conjugate CFD video (current) and solver videos (see the table below) |
| 06_Datasets | Rev 4.2 dataset, data dictionary, **`GRAIL_CFD_dataset_rev4.2_with_Stages3-7.xlsx`** (dataset unchanged plus Stage 3–7 results linked to their source files), `archive/` |
| 07_Results_JSON | 3-D benchmark, Nu profiles, ROM runs, per-case convergence, validation and uncertainty |
| 08_Tables | `final/`: T1–T6 as CSV |
| 09_Records_MD | Provenance records and audit outputs |
| 10_Code | Model, CFD, post-processing, figure and report scripts |
| 11_Validation_V5 | Screening of 16 papers and the final V5 record `V5_FINAL_closure.md` (partial pass, method level) |
| 12_Stages_3-5-6-7 | Stage 3 ANN surrogate, Stage 5 NSGA-II, Stage 6 efficiency correlations, Stage 7 annual (Berhampur) and economics, figures F15–F19, code, report |
| 13_Octave_system_model | The same system model in GNU Octave/MATLAB (`.m`). `compare_with_python.m` gives PASS |
| 14_Xcos_block_diagram_model | The system as a Scilab Xcos block diagram (`GRAIL_system.zcos`); agrees with Octave within 0.04 % |
| 15_Run_in_VSCode | One launcher for every re-runnable stage; re-runs reproduce the delivered results exactly |
| 16_JSON_Python_Mirror | Exact Python copies of all 65 JSON files, plus a provenance map of the script that made each one |
| 17_Simulink_MATLAB_model | Simulink model. Use `GRAIL_simulink_complete_FINAL_v21.m` (data embedded, no CSV needed; clean print layout; all 4 cases PASS vs Xcos). `GRAIL_simulink_complete_FINAL_v22.m` is the same model with a tidier diagram (optional). V20 was also run by the user (`V20_run_record.md`) |
| 18_V7_matched_mean_T | Roadmap V7: alternating vs parallel at matched mean plate temperature |
| 20_Patent_prior_art | V1 first-pass prior-art search (patents + literature), feature map and engineering assessment. Not legal advice |
| 21_V5_Beikircher_component_check | GRAIL loss models vs Beikircher 2015 measurements: front (TIM) loss inside measured range; rear VIP optimistic (a1 may be 0.16–0.42 W/m²K higher). see V5_FINAL_closure.md |
| 19_V5_DelCol_method_check | Modelling method applied to the tested roll-bond collectors of Del Col et al. (2013): heat loss (a1, a2) reproduced within test uncertainty, optical efficiency η0 over-predicted by 6–8 %. see V5_FINAL_closure.md |

**Reports (02_Reports)**

| File | What it is |
|---|---|
| GRAIL_CFD_Simulation_Report_Rev4.1 | The full CFD report. Sections 1–17 keep the Rev 2 text for provenance; Part V is final |
| GRAIL_CAD_Model_Report_Final | The CAD report, with Section 8 on the final status of the geometry |
| GRAIL_CFD_Correction_Report | The nine deliverables, the Rev 4.1 correction and the V5 assessment |
| GRAIL_Dataset_Audit_Addendum_Rev4.1 | The dataset audit |
| Thesis_Abstract_FINAL.md | The abstract (CFD phase) |
| **GRAIL_paper_draft.docx / .pdf** | Journal manuscript draft (all stages, updated with the Beikircher check, a1 range and Simulink result). Author names, affiliation and target journal to be filled in by the authors |

**Videos (05_Videos)**

| File | What it shows | Validity |
|---|---|---|
| **GRAIL_3D_conjugate_rev41.mp4** | Converged 3-D conjugate CFD at NX 240, co-current vs alternating | Current |
| GRAIL_CFD_solver_*.mp4 | Solver progress | Velocity and residual panels valid; the plate panel uses the superseded Nu 3.43 (qualitative only) |
| Older GRAIL_CFD_*.mp4 | Earlier videos | Qualitative only |

## Final results

**CFD (Rev 4.2)**
- **Nusselt number:** 4.48 from 3-D conjugate CFD, grid-extrapolated with a GCI of 2.1 %. It replaces 2.92.
- **Independent check:** Hottel-Whillier-Bliss model vs solver, +0.22 % (co-current).
- **Arrangement comparison at equal inputs** (150 + 150 independent cases; ALT_n is NOT paired with PAR_n):

| | Alternating vs parallel |
|---|---|
| Efficiency | Mean −7.3 % (p = 2e-8); lower at every flow rate |
| Plate uniformity, overall | Median plate std −1.1 %, not significant |
| Plate uniformity by flow | +16.8 % below 2.2 g/s (worse); −13.4 % above 3.3 g/s (better) |
| Plate temperature | Mean +13.9 K |

- **Mechanism:** in the 3-D benchmark about 40 % of the heat each channel absorbs is returned to the plate (9.94 of 24.80 W).
- **At matched mean plate temperature (V7):**
  - Efficiency is the same (Δη −0.001 points).
  - R4 is not reduced (+0.04 %).
  - Alternating is 8–11 % less uniform at the design flow.
  - Alternating needs an inlet about 15 K cooler to reach the same plate temperature. That is why it is less efficient at equal inputs.

**Stages 3–7**
- **ANN surrogate:** efficiency test R² 0.9994–0.9998 on 60 held-out cases, mean error 0.14 %. SHAP drivers: inlet temperature, ambient temperature, flow, arrangement. A GPR model is slightly more accurate.
- **NSGA-II:** 8 optimum designs re-run in GRAIL-CHT agree within 0.13 points of efficiency and 2.4 % on plate std.
- **Efficiency curves (ISO 9806 form, 22 GRAIL-CHT runs):**
  - alternating η0 0.597, a1 2.00 W/m²K;
  - parallel η0 0.637, a1 2.10 W/m²K (2.3–2.5 with measured in-collector VIP conductivity, folder 21);
  - held-out points within 0.24 points.
- **Annual, Berhampur (PVGIS TMY 2005–2023):**
  - 1,976 kWh/m²/yr on the collector plane (PVGIS cross-check −1.5 %).
  - Yield at 40 °C inlet: 1,030 (parallel) / 965 (alternating) kWh/m²/yr.
- **Economics (100 L/day at 45 °C):**
  - Best size is 2 modules (1.06 m²).
  - Solar covers 86 % (parallel) / 83 % (alternating) of the heating.
  - Solar heat costs Rs 4.34–4.49/kWh vs Rs 4.95 for an electric geyser; payback about 7.5 years.
  - Tariff: TPSODL domestic, Rs 4.70/kWh.

## Design decisions recorded
- **System size: 2 modules.** 4 modules stagnate above 420 K, so larger arrays need overheating protection (heat dump or drain-back).
- **Converging channel.** The NSGA-II optimum sits at the upper flow bound with the convergence ratio G → 1. The converging channel is therefore argued for plate uniformity, not for efficiency.

## Open items
- **V5: COMPLETE (partial pass, method level).** 16 papers screened. Del Col 2013: a1, a2 within test uncertainty, η0 within 8 %. Beikircher 2015: TIM front loss matches. Not an experimental test of GRAIL (`11_Validation_V5/V5_FINAL_closure.md`).
- **DESIGN_REVIEW_REQUIRED: VIP k.** GRAIL uses catalogue k 0.006 W/mK; measured in-collector values are 0.010–0.018. State a1 as 2.1 (+0.16 to +0.42) W/m²K in the thesis.
- **V1, V10:** first-pass prior-art search done (folder 20); professional search and patent-agent review only if a filing is planned. Do not publish before deciding.
- **V6:** supplier datasheets.
- **C7, C8:** manifold dimensions and frame wall thickness.
- **Deferred by choice:** PCM latent heat, radiation/optical 3-D model, full 3-D campaign.

## Superseded content (kept only for the record)
- Dataset Rev 1–3, Rev 4 and Rev 4.1. Rev 4.1 has the same data as 4.2, with the old column names.
- Any statistic that pairs ALT_n with PAR_n, including `07_Results_JSON/rev3_vs_rev4.json` ("69 % / 51 % of pairs", "+80 % / −34 %").
- The Rev 2 uncertainty headline.
- The diverging-channel geometry. It is never used.
