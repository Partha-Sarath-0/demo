# GRAIL Rev 4.1 — dependency, provenance and consistency audit

**Scope:** `mu_Pa_s`, `dp_channel_Pa`, `W_pump_W`, `energy_error_pct`.
**Sources traced:**
- `campaign.py` (`dp_channel`, `run_case`)
- `grail_cht.py` (`solve`, results dictionary)
- `campaign3.py` / `campaign4.py`
- the raw grid files `_nx110` and `_nx220`

**No data was changed.**

## Source definitions
- **μ (campaign.py, `dp_channel`)**: Vogel correlation for water, μ = 2.414e-5 · 10^(247.8/(T_m − 140)) Pa·s, with T in K. Evaluated at **T_m = ½(T_in + T_out)**, where T_out is the mixed-mean outlet of *the same model run*. It is computed after the thermal solve (post-processing); the thermal solver never uses μ. The fluid heat-transfer coefficient is h = Nu·k(T)/D_h, with Nu constant at 4.48.
- **Δp**: a calibrated analytical laminar model, Δp = DP_CAL · ∫₀ᴸ 32 μ u(ξ) / D_h(ξ)² dx, with u = ṁ_ch/(ρA(ξ)), ρ = 997, 60-point trapezoid rule, and DP_CAL = 35.31/33.31 (calibrated once against the 3-D CFD). Δp is **linear in μ** and **does not use Re**.
- **W_pump** = Δp · ṁ_total / ρ.
- **Re** (Rev 4.1) = ṁ_ch·D_h/(A·μ). It is a reported diagnostic and feeds nothing.
- **energy_error_pct** = 100·(Q_solar − Q_u − Q_top − Q_rear)/Q_solar, computed inside the solver from its internal float64 totals at the end of that grid's solve. Q_top = Q_rad + Q_conv.

## Provenance of every hydraulic and diagnostic column in Rev 4.1
| Column | Category | Traced origin |
|---|---|---|
| mu_Pa_s | C + F | nx220 run: Vogel at ½(T_in + T_out,nx220); post-processing |
| dp_channel_Pa | C + E + F | nx220 μ in the calibrated laminar integral; DP_CAL is a fixed closure (E) |
| W_pump_W | C + F | nx220 Δp × ṁ / ρ |
| Re_in, Re_out | A | Recomputed in Rev 4.1 from the stored ṁ, D_h, A and μ |
| energy_error_pct | C | nx220 solver diagnostic (stored value equals the nx220 file bit for bit) |
| residual | C | nx220 solver record |
| outer_iters | B | max(nx110, nx220): the more demanding of the two solves |
| T_out, Q_u, η, plate statistics, heats | D | Richardson 2f(220) − f(110) |
| R4, T_R4, mean_T_pow4, U_L | A/D | Rev 4.1 corrections |
| DP_CAL, Nu 4.48, ρ, c_p, optics | E | Fixed parameters |

## Reconstruction over all 300 rows
| Test | Max abs | Max rel | Mean abs | Mean rel | RMS |
|---|---|---|---|---|---|
| μ vs Vogel(½(T_in + T_out,nx220)) | 9.9e-17 | 2.5e-13 | 5.2e-17 | 9.3e-14 | 5.9e-17 |
| μ vs Vogel(½(T_in + T_out,Rev4.1)) | 1.09e-6 Pa·s | **1.70e-3** | 1.04e-7 | 1.84e-4 | 2.0e-7 |
| Δp if rescaled to the Rev 4.1 T_out | 0.030 Pa | 1.70e-3 | 0.0025 Pa | 1.84e-4 | 0.0048 |
| W_pump = Δp·ṁ/997 (stored values) | 9.4e-17 W | 8.5e-13 | — | — | — |
| Δp/μ geometry factor, nx110 vs nx220 | — | 2.4e-13 | — | — | — |
| energy_error_pct vs recomputed from nx220 columns | 3.0e-14 pp | — | — | — | — |
| energy_error_pct vs recomputed from Rev 4.1 columns | 1.9e-5 pp | — | 1.1e-6 pp | — | — |

**Affected cases:**
- Relative difference in μ above 1e-4 in 111 cases, and above 1e-3 in 10. The worst case is ALT_138.
- The largest shift in the outlet temperature between nx220 and Richardson is 0.22 K.

## Classification
| Flag | Severity | Column(s) | Actual problem? | Action |
|---|---|---|---|---|
| μ evaluated at the nx220 outlet temperature, not the Richardson one | **YELLOW** | mu_Pa_s | No. It is exact and self-consistent with its own run's T_out. The ≤ 0.17 % shift is below the uncertainty of the Δp calibration and of the Vogel correlation, and μ does not enter the thermal solution | Document |
| Δp from the nx220 μ | **YELLOW** | dp_channel_Pa | No. Exact for its source run; ≤ 0.03 Pa (≤ 0.17 %) | Document; do not recompute |
| W_pump | **GREEN** | W_pump_W | No. Exactly Δp·ṁ/ρ from the stored columns | Keep |
| Re uses the stored μ | **GREEN** | Re_in, Re_out | No. Exact to 4e-16 with the correct formula | Keep |
| energy_error_pct is the nx220 solver diagnostic | **YELLOW** | energy_error_pct | No. The error of the Richardson row itself is ≤ 1.48e-4 %, the stored value is ≤ 1.47e-4 %, and they differ by ≤ 1.9e-5 pp (rounding level). Extrapolating the error gives the recomputed value to 4e-14 | Document |
| residual is the nx220 record; outer_iters is the maximum of the two grids | **YELLOW** | residual, outer_iters | No. Solver records, not physical results | Document |

No column is ORANGE or RED.

## Distinction between numerical consistency and model validity
- **What this audit establishes:** Rev 4.1 is arithmetically consistent with its generating code.
- **What it does not establish:** the validity of the underlying model: the lumped plate, the constant Nu of 4.48, the single Δp calibration, the glazing and radiation loss model, and constant ρ and c_p.
- **Nature of the rows:** they are reduced-order conjugate-model outputs whose closure comes from 3-D CFD. They are not independent 3-D CFD solutions, and there is no experimental validation.

## Decision
**NO REV4.2 REQUIRED.**
