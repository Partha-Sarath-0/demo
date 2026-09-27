# Change log — GRAIL_CFD_dataset_FINAL_rev4.1.csv

| Item | Value |
|---|---|
| 1. Original file | `GRAIL_CFD_dataset_FINAL_rev4.csv` (MD5 d0a19463f8c04744d9d71ec21d7d18b5). It was only read, and its MD5 is unchanged after the correction |
| 2. New file | `GRAIL_CFD_dataset_FINAL_rev4.1.csv` (MD5 f07ab54542bfba2cae703edcc6e3368c) |
| 3. Date/time | 2026-09-22 14:31 UTC |
| 4. Rows | 300 (unchanged; same order, same case IDs) |
| 5. Columns | 59 (unchanged; same names, same order, same types) |
| Script | `tools/make_rev41.py` |
| Fresh audit | `audit_rev41.py`, output in `audit_rev41_output.txt` |

**Nature of the data (unchanged by this correction).** The rows are outputs of a reduced-order conjugate model (GRAIL-CHT: a 2-D plate with 1-D channel flow). Its Nusselt closure (4.48) and its pressure-drop calibration come from 3-D CFD. The rows are not 300 independent 3-D CFD simulations.

**Method.** The correction was applied at the text level. Only the cells of the six columns below were rewritten. Every other cell, 53 columns × 300 rows, is copied character for character, and the comparison confirms it is byte-for-byte identical.

## 6–10. Modified columns
| Column | Reason | Formula | Rows changed | Max change | Max % change |
|---|---|---|---|---|---|
| R4_K4 | Was the nx220 value in a file whose temperatures are Richardson-extrapolated (mixed provenance) | R4 = 2·R4(nx220) − R4(nx110); see A | 300 | 2.12e8 K⁴ | 0.94 % |
| T_R4_K | Same, and followed R4 | T_R4 = R4^(1/4) | 300 | 0.904 K | 0.23 % |
| mean_T_pow4_K4 | Was the nx220 (T_mean)⁴, while T_mean is Richardson | T_plate_mean_K⁴ (source definition: (mean T)⁴) | 300 | 1.98e8 K⁴ | 0.89 % |
| U_L_W_m2K | Was Richardson-extrapolated as if it were independent, though it is a nonlinear function of other columns | (Q_solar − Q_u) / (0.528·(T_plate_mean − T_amb)) | 300 | 0.148 W/m²K | 2.15 % |
| Re_in | Used the circular-duct formula 4ṁ/(π·D_h·μ) on a semicircular duct | ṁ_ch·D_h,in / (A_in·μ) | 300 | 48.7 | 24.34 % |
| Re_out | Same | ṁ_ch·D_h,out / (A_out·μ) | 300 | 131.5 | 24.34 % |

- For both Reynolds numbers, old/new = 1.321696 in every row. That equals 4A/(πD_h²) for this section, as expected.
- The collector area 0.528 m² is `Ac` from the source model; it also reproduces η exactly.

### A. Why R4 is extrapolated as a functional, not recomputed from a temperature
- R4 = mean over plate cells of T⁴. Like T_plate_mean (the mean of T), it is a plate-averaged functional of the temperature field.
- The per-cell Richardson field was never stored, so mean(T_rich⁴) cannot be formed. Option 1 of the brief is therefore not available exactly.
- On each grid, R4 was computed exactly from that grid's own field. Extrapolating that functional, 2f(220) − f(110), is the same operation at the same order that produced T_plate_mean. The fourth power is never applied to an extrapolated or averaged temperature, so this is **not** a blind extrapolation of a nonlinear quantity.
- **Independent check:** T_R4 − T_mean agrees with the second-order estimate 1.5·σ²/T̄, built from the extrapolated T̄ and σ, to within 0.047 K in every row.

## Dependency trace
| Column | Changed? | Reason |
|---|---|---|
| R4_K4, T_R4_K, mean_T_pow4_K4 | YES | Correction A |
| U_L_W_m2K | YES | Correction B |
| Re_in, Re_out | YES | Correction C |
| dp_channel_Pa | NO | Computed from μ, ṁ and geometry by a laminar integral; it does not take Re as an input |
| W_pump_W | NO | Δp·ṁ_total/ρ; no Re |
| mu_Pa_s | NO | An input to Re, not a result of it |
| Any thermal column (T_out, dT, Q_u, η, T_plate_*, P90–P99, Q_rad, Q_conv, Q_rear, T_glass, lateral_bridge) | NO | The model solution does not use T_R4, R4 or U_L (they are reporting quantities) or Re (Nu is a constant closure) |
| energy_error_pct, residual, outer_iters, converged | NO | Solver records, not dependent on any changed column |
| All inputs, geometry and metadata | NO | Not dependent |

**No other column depends on any corrected column.**

## Not corrected here (out of scope, documented)
These remain as reported in the Rev 4 audit; each is ≤ 0.17 % or a solver record:
- μ, Δp and W_pump were evaluated with the nx220 outlet temperature (μ changes by at most 0.17 % if recomputed).
- energy_error_pct and residual are the nx220 solver records.
- The name `mean_T_pow4_K4` holds (mean T)⁴, not mean(T⁴).

## 11–14. Confirmations
- **No rows were deleted:** 300 in, 300 out, identical case IDs and order.
- **No outliers were removed.**
- **No signs were changed:**

| Term | Negatives in Rev 4 | Negatives in Rev 4.1 | Sign changes |
|---|---|---|---|
| Q_rad | 11 | 11 | 0 |
| Q_conv | 12 | 12 | 0 |
| Q_rear | 16 | 16 | 0 |
| U_L | 4 (PAR_001, PAR_016, PAR_060, PAR_088) | 4 (same cases) | 0 |

- **No core thermal result was modified.** T_out, dT, Q_u, Q_solar, Q_rad, Q_conv, Q_rear, η, every plate temperature and percentile, the inputs, the convergence data and the metadata are all byte-for-byte identical.
- **The ALT/PAR sampling structure is untouched.** No re-pairing, reordering or manufactured cases.
