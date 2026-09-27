# Roadmap V5 — assessment of Gunjo et al. 2017 as an experimental reference

**Paper**: D.G. Gunjo, P. Mahanta, P.S. Robi, "CFD and experimental investigation of flat plate
solar water heating system under steady state condition", Renewable Energy (2017),
doi:10.1016/j.renene.2016.12.041 (accepted manuscript, supplied by the user).

**Decision: DESIGN_REVIEW_REQUIRED — reference assessed and NOT used for validation.**
No GRAIL result is compared with it and no claim of experimental validation is made.

## What the paper contains
- Sheet-and-tube collector: copper plate 1.65 × 1.0 m × 0.5 mm, k 386; 10 round risers Ø12.5 mm,
  pitch 112.5 mm, brazed under the plate; single acrylic cover; glass-wool back insulation 40 mm.
- Their CFD: one riser + plate strip, top = constant flux (ατ)·I, bottom = h_b = 2.8 + 3·V_w,
  no top-loss boundary, ~400,000 elements, commercial code.
- Data: inputs (T_in, T_a, I) and outputs (T_out, T_p) ONLY as plots (Figs 6, 7, 9, 10); no tables.

## Why it cannot serve as V5 (values read from the published plots, ± ~1 K)
| # | Finding | Evidence |
|---|---|---|
| 1 | The paper's own simulation violates energy conservation | Noon, Fig. 9: simulated T_out ≈ 336 K, T_in ≈ 303 K → ΔT ≈ 33 K. At 0.0125 kg/s that is ≈ 1.7 kW; at 0.025 kg/s ≈ 3.4 kW; the maximum solar input is I·A ≈ 930 × 1.65 ≈ 1.53 kW, before any optical or thermal loss |
| 2 | The stated accuracy is an artefact of the error definition | Error is computed on absolute kelvin (Eq. 6). Sim ≈ 336 K vs exp ≈ 317 K is "5.7 %" but the error on the temperature RISE (33 K vs 14 K) exceeds 100 % |
| 3 | Measured outlet does not respond to flow rate | Figs 9(a) and 9(b) experimental curves nearly identical although flow doubles; at 0.025 kg/s ΔT ≈ 14 K implies η ≈ 95 % on the absorber area, against the paper's own reported maximum of 56 % |
| 4 | Inputs missing or contradictory | wind speed V_w never stated; (ατ) not stated; tube wall 0.7 mm (Table 1) vs 7 mm (text); modelled strip 0.100 m vs stated pitch 0.1125 m |
| 5 | Different collector type | round tubes brazed to a flat sheet, not a roll-bond channel plate; even a match would test only the general method |

## Consequence
- V5 is closed as "reference rejected with documented scientific reason", not as "passed" and not
  silently dropped.
- The thesis states: CFD verified against 3-D conjugate CFD (grid-studied) and against published
  laminar-duct correlations; **no experimental validation**.
- If an experimental comparison is required, a replacement reference must (a) tabulate its data,
  (b) pass an independent energy balance, (c) state all boundary inputs.
