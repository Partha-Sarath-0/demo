> **NOTE (Rev 4.1, final):** Any ALT_n-vs-PAR_n "pair" statistic in this file is WITHDRAWN. The cases are independent samples. Use the group-wise results in 08_Tables/final/T3 and T4 and in the CFD Report Rev 4.1, Part V.

# GRAIL — Dataset Rev 4: conjugate Nusselt closure, converged plate grid

## What changed from Rev 3 (and only this)
| item | Rev 3 | Rev 4 |
|---|---|---|
| Nu closure | 2.9238 (fluid-only, H2-type) | **4.48** (3-D conjugate, cross-section extrapolated; band 4.46–4.65) |
| plate grid | 110 × 120 | 110 × 120 AND 220 × 120, plus per-row Richardson 2f(220) − f(110) |
| outer-iteration cap | 900 | 3000 (tolerance unchanged, 1e-6, asserted) |
| everything else | — | identical: seed, LHS, bounds, geometry gate, k(T), acceptance gates |

Files: `GRAIL_CFD_dataset_rev4_nx110.csv`, `_nx220.csv`, `_richardson.csv` (300 rows each),
`failures_rev4_nx110.csv`, `_nx220.csv` (0 rejected each), `rev3_vs_rev4.json`,
`rev4_regime_breakdown.json`. Rev 1, 2, 3 are untouched.

Acceptance: 300 / 300 at both grids. 34 (nx110) / 35 (nx220) rows needed > 900 outer
iterations; they meet the same 1e-6 tolerance. They are ALL alternating low-flow cases: excluding
them selectively removes the cases least favourable to the alternating arrangement, so the
"≤ 900" subset is biased and is reported only for comparability with Rev 3, never as the result.

## Paired arrangement comparison (ALT_n vs PAR_n), Richardson dataset, 150 pairs
| | Rev 3 (Nu 2.92, 110) | Rev 4 Richardson |
|---|---|---|
| Δη mean / median | −4.07 % / −5.28 % | **−6.34 % / −7.20 %** |
| Δ plate std mean / median | +2.28 % / −27.9 % | **+35.6 % / −0.7 %** |
| pairs where alternating has lower std | 64 % | **51 %** |
| Δ spread median | −11.4 % | **+18.4 %** |
| Δ P90 mean | +6.97 K | **+12.6 K** |
| Δ mean plate T | +9.83 K | **+13.9 K** |

## The result depends on flow rate (Rev 4 Richardson, terciles of total flow)
| total flow | n | Δ std median | alt lower std | Δη median |
|---|---|---|---|---|
| 1.01 – 2.17 g/s | 50 | **+80 %** | 16 % | −13.5 % |
| 2.17 – 3.34 g/s | 50 | −7.6 % | 58 % | −6.3 % |
| 3.34 – 4.49 g/s | 50 | **−33.9 %** | 78 % | −2.9 % |

Correlation of Δ std with flow −0.57, with irradiance +0.27, with bridge width 0.03.
Physical reading (from the 3-D mechanism): heat recirculation between counter-flowing
neighbours through the metal grows as the flow's thermal capacity falls; at low flow it
dominates and the alternating plate is LESS uniform; at high flow the counter-flow averaging
wins.

## Model-form uncertainty carried on these numbers
From the 3-D benchmark at design flow: the ROM overstates the alternating uniformity benefit by
≈ 2.0 pp in Δ std and understates the efficiency penalty by ≈ 0.5 pp; the constant Nu
understates std by up to 2.1 % at the top of the flow range. The benchmark uses a linear loss
model; the campaign's glazing/radiation model is not 3-D validated (V5 open).

## Correction (same day): efficiency is not lower in every pair
Share of pairs with lower alternating efficiency: 69 % overall; 80 / 72 / 56 % by flow tercile.
Median Δη is negative in every tercile, but 31 % of pairs show a gain. An earlier draft sentence
"lowers efficiency across the whole design space" was wrong and has been replaced.
