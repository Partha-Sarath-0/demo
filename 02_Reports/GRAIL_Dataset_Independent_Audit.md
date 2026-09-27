# Independent scientific audit — GRAIL CFD dataset (final Rev 4)

**File audited:** `GRAIL_CFD_dataset_FINAL_rev4.csv` (identical to `GRAIL_CFD_dataset_rev4_richardson.csv`).
**Method:**
- Every derived column was recomputed from its inputs in float64.
- Where the CSV alone could not settle a definition, it was checked against the generating source code (`grail_cht.py`, `campaign.py`) and the two raw-grid files (`_nx110`, `_nx220`) that the final file was built from.
- **No value was modified.**

**Nature of the data:** the rows are outputs of GRAIL-CHT, a reduced-order conjugate model (a 2-D plate coupled to 1-D channel flow). The 3-D CFD supplies its Nusselt closure (4.48) and its pressure-drop calibration. The rows are therefore **not 3-D CFD solutions**, and the paper must say so.

---
## 1. Data integrity
| Check | Result |
|---|---|
| Rows × columns | 300 × 59 |
| NaN / infinite values | 0 / 0 |
| Duplicate rows / case IDs / operating points | 0 / 0 / 0 |
| Type mixing, parsing problems | None; `converged` is Boolean, every other column has a consistent type |
| Constant columns | 12. Ten are metadata: geometry_version, solver, converged, nu_cfd, nu_basis, dataset_rev, k_model, outer_cap, plate_nx, plate_ny. Two are geometry: Dh_in_mm and A_in_mm2, constant by design because every channel shares the same inlet section |
| Categorical values | arrangement ∈ {alternating, parallel}, with f_interdig = 1 / 0 in exact one-to-one correspondence; 150 rows each |
| Metadata | `plate_nx` holds a text label ("richardson_2x220_minus_110") in a column that is numeric in the raw files. This is **documentation only** |

**Verdict: PASS**

## 2. Ranges (full statistics in `audit_part1.txt`)
All inputs lie inside the documented sampling bounds:

| Input | Range |
|---|---|
| G_T | 400–999 W/m² |
| T_in | 288–333 K |
| T_amb | 283–313 K |
| v_wind | 0.007–4.99 m/s |
| Total flow | 1.01–4.49 g/s |
| Bridge | 20.0–37.0 mm |
| g_ratio | 0.351–0.998 |
| λ_G | 0.50–2.00 |

Outputs:

| Output | Range |
|---|---|
| T_out | 298–373 K |
| T_plate | 290.7–412.6 K |
| η | 0.342–0.673 |
| Δp | 2.1–158.6 Pa |
| Pumping power | ≤ 0.51 mW |

None is physically impossible. The hottest cases are ALT_064, ALT_114 and ALT_138 (plate maximum up to 412.6 K). They combine low flow, high irradiance and alternating flow, and they sit on the physical trend, not off it.

## 3. Reconstruction of derived quantities
| Relation | Max abs error | Max rel error | Verdict |
|---|---|---|---|
| mdot_channel = mdot_total / 12 | 9e-17 | 9e-13 | exact |
| dT = T_out − T_in | 1e-13 | 8e-15 | exact |
| spread = T_max − T_min | 1e-13 | 9e-15 | exact |
| Q_u = ṁ·4180·dT | 2e-11 W | 9e-14 | exact |
| q_abs = G·0.833·0.82·0.95 | 1e-13 | 2e-16 | exact |
| Q_solar = q_abs·0.528 | 6e-14 | 3e-16 | exact |
| η = Q_u/(G_T·0.528) | 2e-16 | 4e-16 | exact |
| W_pump = Δp·ṁ_total/997 | 8e-17 | 9e-13 | exact |
| T_sky = 0.0552·T_amb^1.5 ; h_wind = 5.7 + 3.8·v | ≤ 2e-13 | — | exact |
| P90 ≤ P95 ≤ P99 ≤ T_max ; T_min ≤ T_mean ≤ T_max | 0 violations | — | consistent |
| R4_K4 = T_R4_K⁴ | 1.5e-5 | 1e-15 | exact |
| **mean_T_pow4_K4 = (T_plate_mean)⁴** | 1.98e8 K⁴ | **8.9e-3** | **INCONSISTENT** (exact in the raw nx220 file) |
| **T_R4 ≥ T_plate_mean** (a power mean can never be below the arithmetic mean) | 120 violations, down to −0.12 K | — | **INCONSISTENT** |
| **U_L = (Q_solar − Q_u)/(0.528·(T_mean − T_amb))** | 0.148 W/m²K | **2.2 %** | **INCONSISTENT** (exact in raw nx220) |
| **Re = 4ṁ_ch/(π·D_h·μ)** | formula reproduced exactly | — | **wrong definition for this duct** (Section 10) |

**Cause of the three inconsistencies.**
- The final file was built by Richardson extrapolation, 2·f(220) − f(110), column by column.
- Eighteen columns were extrapolated: the temperatures, heats, η and U_L.
- R4_K4, mean_T_pow4_K4, T_R4_K, energy_error_pct, μ, Re, Δp and W_pump were **copied from the nx220 run and not recomputed**.
- U_L was **extrapolated as if it were an independent quantity**, although it is a nonlinear function of other extrapolated columns.

Each row therefore mixes quantities from two different grid levels. In the raw files every one of these relations holds to machine precision, so the fault lies in how the final file was assembled, not in the solver.

## 4. Energy balance
**Governing equation, confirmed from the source code:** Q_solar = Q_u + Q_rad + Q_conv + Q_rear.

| Term | Meaning |
|---|---|
| Q_solar | **Absorbed** power: G·τ_glz·τ_TIM·α·A |
| Q_rad | Plate→glazing radiation (signed) |
| Q_conv | Plate→glazing conduction/convection across the gap and the TIM (signed) |
| Q_rear | Plate→ambient through the rear (signed) |

Residual statistics:

| Statistic | Value |
|---|---|
| Minimum / maximum | −2.13e-4 W / +2.22e-4 W |
| Mean absolute | 1.27e-4 W |
| RMS | 1.49e-4 W |
| Maximum imbalance | **1.48e-4 %** |

No case approaches a meaningful tolerance, and no case violates conservation. The balance still closes after extrapolation because the extrapolation is linear and every term was extrapolated together. The `energy_error_pct` column is the nx220 value, which differs from the recomputed value by at most 1.9e-5 percentage points. **Verdict: PASS**

## 5. Sign convention
The heat terms are **signed net heat flows out of the plate**, not positive-definite losses:
- q_rad = h_r(T_p − T_g) and q_cond = (T_p − T_g)/R, integrated cell by cell.
- q_rear = (T_p − T_amb)/R_rear.

| Term | Negative cases | Physically consistent? |
|---|---|---|
| Q_rear < 0 | 16 | **Yes.** All 16 have T_plate_mean < T_amb, and the sign matches sign(T_p − T_amb) in 300/300 rows. The plate is below ambient and gains heat from the surroundings |
| Q_conv < 0 | 12 | **Yes.** The sign matches sign(T_p,mean − T_g,mean) in 300/300 rows |
| Q_rad < 0 | 11 | **Yes.** The sign matches sign(T_p − T_g) in 299/300 rows. Q_rad is plate→glass, NOT glass→sky, so comparing it with T_sky is the wrong test |
| PAR_011 | Q_rad +0.042 W, Q_conv −0.102 W | **Valid.** T_p,mean − T_g,mean = −0.11 K, with a 30 K spread across the plate. Both terms carry the local sign, but h_r grows with T³, so the hot regions weigh more in Q_rad. Two small integrals of different weighting can take opposite signs |

**Verdict: NEEDS DOCUMENTATION.** The sign convention is consistent, but the paper must state that these are signed net flows.

## 6. U_L ≤ 0 (4 cases)
| Case | T_plate_mean (K) | T_amb (K) | Q_rad (W) | Q_conv (W) | Q_rear (W) | U_L (W/m²K) |
|---|---|---|---|---|---|---|
| PAR_001 | 309.816 | 310.780 | 0.265 | 1.495 | −0.139 | −3.152 |
| PAR_016 | 295.482 | 297.107 | 0.325 | 2.369 | −0.234 | −2.867 |
| PAR_060 | 307.617 | 309.032 | 0.306 | 1.647 | −0.204 | −2.320 |
| PAR_088 | 299.324 | 300.890 | 0.088 | 0.514 | −0.225 | −0.453 |

**How the negative values arise:**
- U_L = total loss / (A·(T_p − T_amb)).
- In all four cases the plate is *below* ambient while the net loss is positive: the plate still sheds heat upward to glass that is colder than ambient, because the sky is cold.
- The negative sign therefore follows exactly from the definition. It is **not a numerical error**, but U_L is **meaningless** when |T_p − T_amb| is only a few kelvin.

**The same singularity inflates positive values:**

| Case | U_L (W/m²K) | T_p − T_amb (K) |
|---|---|---|
| PAR_066 | 14.43 | 0.37 |
| PAR_062 | 11.92 | 0.71 |

Eleven cases have |T_p − T_amb| < 2 K.

**Recommendation:**
- Do not modify these values.
- Exclude cases with |T_p − T_amb| < 5 K from any U_L statistic or plot, and state that rule in the paper.

## 7. Efficiency definition
- **Reported:** η = Q_u / (G_T·A), with A = 0.528 m². This is the standard ASHRAE/ISO collector efficiency based on **incident** irradiance.
- **Conventional-looking alternative:** η_conv = Q_u / Q_solar is *not* the same thing, because Q_solar is **absorbed** power.
- **Relation:** η / (Q_u/Q_solar) = 0.833 × 0.82 × 0.95 = **0.6489** in every row (error 3e-16). This is the optical efficiency, τ_glazing·τ_TIM·α_absorber.
- **Verdict:** the definition is correct but the column name misleads. **NEEDS DOCUMENTATION.**
- **For the manuscript:** define η on incident G_T and gross aperture 0.528 m², and rename Q_solar as "absorbed solar power". Q_u/Q_solar may be reported separately as the "thermal (post-optical) efficiency".

## 8. Temperature and radiative quantities
- **Source definitions** (`grail_cht.py` line 377):
  - `R4_K4` = mean(T⁴)
  - `T_R4_K` = R4^¼, the effective radiative temperature
  - `mean_T_pow4_K4` = (mean T)⁴
- **Naming:** the name `mean_T_pow4` reads as mean(T⁴), but it holds the opposite quantity. **Documentation: rename it `Tmean_pow4_K4`.**
- **Physics check (raw nx220 file):**
  - T_R4 − T_mean ranges from 0.010 to 1.370 K.
  - It correlates with 1.5·σ²/T̄ at r = 0.99995, ratio 0.996. That is exactly the second-order expansion of a fourth-power mean.
  - The quantity is physically correct and definition-consistent.
- **In the final file** it is broken: the two temperatures come from different grid levels (Section 3), which produces 120 impossible negative differences.

## 9. Convergence (reduced-order model iterations)
- **Residuals:** all ≤ 1.0e-6 (maximum 9.9996e-7); converged = True in 300/300 rows. The flag is consistent with the residual.
- **High iteration counts:** 35 rows needed more than 900 outer iterations (maximum 1541, cap 3000, never reached).
  - All 35 are alternating cases at ≤ 1.89 g/s.
  - Iteration count correlates with flow at −0.94 in the alternating group. That is physical stiffness (strong counter-flow coupling at low flow), not failure.
  - Energy error in these rows is ≤ 1.45e-4 %.
- **Caveat:** the criterion is a change in the outer-iteration update below 1e-6, not a solution-error bound. Combined with the independent energy balance, it is adequate.
- **Verdict: PASS**

## 10. Dimensionless numbers and hydraulics
**Re definition error (every row):**
- The code uses Re = 4ṁ/(π·D_h·μ), which equals ρuD_h/μ **only for a circular duct**.
- For this semicircular section, A = 28.057 mm² while π·D_h²/4 = 21.228 mm².
- As a result, **Re_in and Re_out are overstated by a factor of 1.3217 in every row** (a constant ratio, verified).
- The correct value is Re = ṁ·D_h/(A·μ), giving a maximum of 409. The flow stays laminar, and no thermal result depends on Re, because Nu is constant.
- **Verdict: definitely wrong as a Reynolds number.**

**Other checks:**

| Quantity | Finding |
|---|---|
| μ | The Vogel correlation evaluated at ½(T_in + T_out) reproduces the column exactly, but with the nx220 T_out, not the extrapolated one. The effect is ≤ 0.17 % in μ: minor |
| Δp | A laminar integral (32μu/D_h²) along the self-similar section (A/A_in = (D_h/D_h,in)², verified exact), multiplied by a constant calibrated to the 3-D CFD. It is a **model result**, not a 3-D CFD result, and should be described as calibrated. The large Δp and Re_out outliers (ALT_007, ALT_043, PAR_094, …) are the smallest outlets (g_ratio ≈ 0.35) at high flow, which is consistent |
| Pr | 2.45–6.95, plausible for water at 288–373 K |
| Nu | A constant model input (4.48), not a per-row result; it must not be presented as a CFD output per case |

## 11. Fairness of the arrangement comparison
**Group-level fairness.** The alternating and parallel groups are two separate Latin-Hypercube draws with the same seed stream. Their input distributions are statistically indistinguishable: KS p = 1.00 for all eight inputs, and every mean agrees to 0.1 %. **The group-level comparison is fair.**

**Critical finding: ALT_n and PAR_n are NOT matched pairs.**
- Case ALT_n and case PAR_n do not share inputs. For example, G_T differs by up to 560 W/m² and flow by up to 3.3 g/s within the same index.
- **Every "paired" statistic built by matching ALT_n with PAR_n is invalid.** That covers the paired comparisons in the Rev 3/Rev 4 comparison files and the correction and CFD reports produced in this project, including:
  - "lower η in 69 % of pairs"
  - "alternating more uniform in 51 % of pairs"
  - "median +80 % / −34 % in plate std by flow tercile"
  - the Rev 3 "−27.9 % median"
- **The dataset itself is not wrong. The analysis built on it is.**

**Valid unpaired comparison** (the same data, compared group against group):

| | Alternating vs parallel | Significance |
|---|---|---|
| Mean η, all | **−7.3 %** (0.5209 vs 0.5620) | Mann–Whitney p = 2e-8 |
| Median plate std, all | −1.1 % | p = 0.76, **not significant** |
| 1.0–2.2 g/s | η −12.7 %; std median **+16.8 %** | p = 0.03 |
| 2.2–3.3 g/s | η −6.0 %; std median +7.9 % | p = 0.14 |
| 3.3–4.5 g/s | η −3.5 %; std median **−13.4 %** | p = 0.02 |

- **Directions are confirmed:** an efficiency penalty, and uniformity that is worse at low flow and better at high flow.
- **Magnitudes are much smaller** than reported, and the overall uniformity effect is **not significant**.
- **For a case-by-case comparison:** re-run the model with each alternating case's inputs under parallel flow, giving 150 matched counterfactuals. At about 1 minute per case this is inexpensive.

## 12. Correlations (Spearman)
| Relationship | ρ | Consistent with physics? |
|---|---|---|
| G_T → Q_u | +0.93 | Yes |
| ṁ → dT | −0.75 | Yes |
| T_in → η | −0.68 | Yes |
| T_amb → η | +0.41 | Yes |
| T_p → Q_rad | +0.93 | Yes |
| T_p → Q_conv | +0.87 | Yes |
| v → h_wind | 1.00 | By construction |
| v → U_L | +0.07 | Weak |
| Re → Δp | +0.36 | Weak, because Δp is dominated by the outlet section (g_ratio) |

**v → U_L:** weak because the wind acts on the glazing behind a TIM and gap resistance that dominate the loss path. This is physically plausible for this design, but it needs the glazing model to confirm.

**Hottel-Whillier fits on (T_in − T_amb)/G:**

| Arrangement | Fit | r |
|---|---|---|
| Parallel | η = 0.601 − 2.00·x | 0.96 |
| Alternating | η = 0.557 − 1.92·x | 0.78 |

The weaker fit for the alternating group reflects its flow-dependent recirculation. No impossible relationship was found.

## 13. Outliers
IQR, z-score > 3 and robust MAD tests flag:
- Δp and W_pump (26–31 rows): small outlets at high flow
- U_L (56 rows): the singular denominator
- ALT_064, ALT_114, ALT_138: hottest plates
- dT extremes: PAR_009, PAR_050, PAR_054, PAR_123 (lowest flow)
- `lateral_bridge_W` ≈ 1e-10 W in every parallel row: bridge conduction vanishes by symmetry when all channels flow the same way. This is physically correct, and it is round-off, not data

Every outlier is mathematically consistent and energy-balanced, converged, and on a physical trend. **None is an error.**

## 14. Case-by-case anomalies
| Case | Variable | Value | Problem | Severity | Scientific explanation |
|---|---|---|---|---|---|
| 120 rows (Appendix A) | T_R4_K vs T_plate_mean_K | down to −0.12 K | T_R4 < T_mean is impossible | **MAJOR** | T_R4 comes from nx220, T_mean from the extrapolation; mixed grid levels |
| All 300 | mean_T_pow4_K4 | error up to 0.89 % | ≠ (T_mean)⁴ | **MAJOR** | Same cause: not recomputed |
| All 300 | R4_K4, T_R4_K | — | nx220 values in a file labelled Richardson | **MAJOR** | Provenance mismatch |
| All 300 (worst PAR_066, PAR_062, ALT_121) | U_L_W_m2K | error up to 0.148 (2.2 %) | ≠ its own definition | **MAJOR** | A nonlinear quantity was extrapolated linearly |
| All 300 | Re_in, Re_out | ×1.3217 | Circular-duct formula on a semicircular duct | **MAJOR** | Wrong definition; no thermal effect |
| All 300 | energy_error_pct, μ, Δp, W_pump, residual | — | Taken from nx220 | MINOR | ≤ 0.17 % in μ; ≤ 2e-5 pp in the error |
| 150 pairs | ALT_n vs PAR_n | — | Not matched pairs | **CRITICAL (for the reported conclusions, not the data)** | Two independent LHS draws |
| PAR_001, PAR_016, PAR_060, PAR_088 | U_L | −3.15 to −0.45 | Negative | DOCUMENTATION ONLY | T_p < T_amb with positive net loss; follows from the definition |
| 11 cases with \|T_p − T_a\| < 2 K | U_L | up to 14.4 | Singular denominator | DOCUMENTATION ONLY | Exclude from U_L statistics |
| 16 / 12 / 11 cases | Q_rear / Q_conv / Q_rad < 0 | ≥ −4.5 W | Negative heat flow | NO ISSUE | Signed net flows; signs match the temperatures |
| PAR_011 | Q_rad vs Q_conv | +0.04 / −0.10 W | Opposite signs | NO ISSUE | Different weighting of near-zero integrals |
| 9 cases | T_out < T_amb | — | — | NO ISSUE | Cold inlet; the collector still gains heat (Q_u > 0) |
| 35 alternating low-flow cases | outer_iters | 900–1541 | High | NO ISSUE | Converged below the cap; physically stiff |
| ALT_064, ALT_114, ALT_138 | T_plate_max | up to 412.6 K | Hot | NO ISSUE | Low flow + high G + alternating flow |
| All parallel | lateral_bridge_W | ~1e-10 W | ≈ 0 | NO ISSUE | Symmetry |
| — | Clipping, rounding, duplicated outputs | — | None found | NO ISSUE | — |

## 15. Classification
**A. Definitely wrong**
1. `T_R4_K`, `R4_K4` and `mean_T_pow4_K4` are inconsistent with the other temperature columns in all 300 rows. In 120 rows T_R4 < T_mean, which is mathematically impossible.
2. `U_L_W_m2K` in all 300 rows departs from its own definition by up to 2.2 %.
3. `Re_in` and `Re_out` are overstated by 32.17 % in every row, because the circular-duct formula was used.
4. **The ALT_n/PAR_n pairing used in the reports:** every paired statistic is invalid. This is analysis, not data.

**B. Possibly wrong: needs model or CFD information**
- The glazing and radiation loss model, and the T_sky and h_wind correlations. They are consistently applied but not 3-D tested.
- The Δp calibration constant, which was calibrated once against 3-D CFD.

**C. Physically valid but unusual**
- The negative Q_rear, Q_conv and Q_rad values; the negative U_L values; T_out < T_amb.
- The hottest cases (ALT_064, ALT_114, ALT_138), the high iteration counts, the Δp and Re_out extremes, and the zero bridge conduction in parallel flow.

**D. Valid, but the paper must document it**
- η is based on incident G_T and 0.528 m². Q_solar is absorbed power, with an optical factor of 0.6489.
- The heat terms are signed net flows out of the plate.
- U_L is undefined when T_p ≈ T_amb.
- The meaning of mean_T_pow4 (it is (mean T)⁴).
- The statistics are unweighted cell statistics (population std, percentiles) on a uniform grid.
- The rows are reduced-order-model outputs with a constant, CFD-derived Nu, not 3-D CFD.
- 35 rows needed more than 900 iterations.

**E. Clean**
- Integrity; all inputs; ṁ; dT; T_out; Q_u; η; q_abs; Q_solar.
- The energy balance, the plate temperature statistics and their ordering, the percentiles.
- The heat terms, the convergence flags, W_pump, T_sky, h_wind.

## 16. Data modification
None. No row was deleted, no value replaced, no outlier removed, and no sign changed. The CSV is byte-identical to the one supplied.

## 17. Final verdict
| Category | Verdict |
|---|---|
| DATA INTEGRITY | **PASS** |
| MATHEMATICAL CONSISTENCY | **FAIL** (T_R4 / R4 / mean_T_pow4 and U_L provenance; Re definition) |
| ENERGY CONSERVATION | **PASS** (max 1.5e-4 %) |
| CFD CONVERGENCE | **PASS** (reduced-order solver; residual ≤ 1e-6 in all rows) |
| PHYSICAL PLAUSIBILITY | **PASS** |
| SIGN CONVENTIONS | **NEEDS DOCUMENTATION** |
| EFFICIENCY DEFINITION | **NEEDS DOCUMENTATION** |
| **OVERALL DATASET** | **REQUIRES CORRECTION** |

The correction is limited: recompute the derived columns and the Re definition, and redo the arrangement statistics without pairing. The core solved quantities, the temperatures, the heats and η, are sound.

**1. Values that are definitely wrong**
- T_R4_K, R4_K4 and mean_T_pow4_K4 (all rows; 120 impossible).
- U_L_W_m2K (all rows; up to 0.148 W/m²K).
- Re_in and Re_out (all rows; ×1.3217).

**2. Values that are unusual but valid:** everything listed in 15C.

**3. Definitions the manuscript must clarify:** everything listed in 15D, plus the correct Reynolds definition.

**4. Cases needing further verification**
- No individual case needs new CFD.
- A **matched counterfactual run** (parallel flow at each alternating case's inputs) is needed before any case-by-case or "share of cases" claim can be made.

**5. Should the CSV stay unchanged?**
- Yes, this file should be kept exactly as it is, as the record of what was produced.
- A new file, Rev 4.1, should be issued in which:
  - T_R4, R4 and mean_T_pow4 are recomputed from their definitions, or taken consistently from one grid level;
  - U_L is recomputed from the extrapolated Q_solar, Q_u, T_p and T_amb;
  - Re is recomputed as ṁ·D_h/(A·μ);
  - nothing else is touched.
- The conclusions in the reports that relied on ALT_n/PAR_n pairing must be rewritten.
## Appendix A — case lists

**T_R4_K < T_plate_mean_K (power-mean inequality violated, 120 rows):** ALT_000, ALT_001, ALT_002, ALT_003, ALT_004, ALT_005, ALT_006, ALT_007, ALT_008, ALT_011, ALT_012, ALT_013, ALT_014, ALT_015, ALT_016, ALT_017, ALT_018, ALT_020, ALT_021, ALT_022, ALT_024, ALT_025, ALT_026, ALT_027, ALT_028, ALT_029, ALT_030, ALT_031, ALT_032, ALT_034, ALT_036, ALT_038, ALT_039, ALT_040, ALT_041, ALT_042, ALT_043, ALT_044, ALT_046, ALT_047, ALT_048, ALT_049, ALT_050, ALT_051, ALT_052, ALT_053, ALT_055, ALT_056, ALT_057, ALT_058, ALT_059, ALT_060, ALT_061, ALT_062, ALT_063, ALT_066, ALT_067, ALT_069, ALT_071, ALT_072, ALT_073, ALT_074, ALT_075, ALT_076, ALT_078, ALT_079, ALT_080, ALT_081, ALT_082, ALT_083, ALT_084, ALT_085, ALT_087, ALT_088, ALT_089, ALT_090, ALT_093, ALT_095, ALT_096, ALT_100, ALT_101, ALT_102, ALT_103, ALT_104, ALT_105, ALT_106, ALT_107, ALT_108, ALT_109, ALT_110, ALT_112, ALT_113, ALT_115, ALT_116, ALT_117, ALT_118, ALT_120, ALT_121, ALT_123, ALT_126, ALT_127, ALT_128, ALT_129, ALT_130, ALT_131, ALT_133, ALT_134, ALT_135, ALT_137, ALT_139, ALT_140, ALT_141, ALT_142, ALT_143, ALT_144, ALT_145, ALT_146, ALT_147, ALT_148, ALT_149

**T_out < T_amb (9 rows):** ALT_025, ALT_066, ALT_113, ALT_121, ALT_128, ALT_135, PAR_012, PAR_083, PAR_148

**Q_rear < 0 (16 rows, all with T_plate_mean < T_amb):** ALT_025, ALT_066, ALT_113, ALT_128, ALT_135, PAR_001, PAR_011, PAR_012, PAR_016, PAR_060, PAR_083, PAR_088, PAR_103, PAR_120, PAR_131, PAR_148

**Q_conv < 0 (12 rows):** ALT_025, ALT_066, ALT_113, ALT_128, ALT_135, PAR_011, PAR_012, PAR_083, PAR_103, PAR_120, PAR_131, PAR_148

**Q_rad < 0 (11 rows):** ALT_025, ALT_066, ALT_113, ALT_128, ALT_135, PAR_012, PAR_083, PAR_103, PAR_120, PAR_131, PAR_148

**outer_iters > 900 (35 rows, all alternating, total flow ≤ 1.89 g/s):** ALT_004, ALT_013, ALT_015, ALT_019, ALT_022, ALT_023, ALT_029, ALT_031, ALT_035, ALT_037, ALT_045, ALT_047, ALT_054, ALT_056, ALT_064, ALT_068, ALT_069, ALT_070, ALT_072, ALT_075, ALT_082, ALT_090, ALT_091, ALT_093, ALT_097, ALT_099, ALT_114, ALT_119, ALT_120, ALT_122, ALT_125, ALT_132, ALT_136, ALT_138, ALT_144

**U_L mismatch > 0.01 W/m²K vs its own definition:** ALT_121 (0.101), PAR_001 (0.033), PAR_060 (0.022), PAR_062 (0.143), PAR_066 (0.148)

