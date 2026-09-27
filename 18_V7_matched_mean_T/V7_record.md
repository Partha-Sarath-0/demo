# Roadmap V7: alternating vs parallel at matched mean plate temperature

**Question (roadmap V7 / headline number 1):** at the same mean plate temperature, does the
alternating (counter-current) arrangement reduce R4 = mean(T⁴) and raise efficiency?

## Method

- **Solver:** GRAIL-CHT, with the same settings as the Rev 4.2 campaign (Richardson 2·f(nx220) − f(nx110)).
- **Geometry:** as-built (bridge 31.286 mm, G 0.539935, λ 1.0).
- **Operating point:** design flow 2.75 g/s, G = 800 W/m², T_amb = 303.15 K, wind 3 m/s.
- **Matching:** for each target mean plate temperature (320, 330, 340 K), the inlet temperature of
  each arrangement was found by a secant search until the plate mean matched the target within
  0.001 K. Nothing else differs between the two arrangements.
- **Checks:** every run converged and met the energy-balance check (|error| < 0.5 %).
- **Inlet range:** all inlet temperatures are inside the campaign range, 288–333 K.
- **Code:** `tools/v7_matched_mean_T.py`. It only calls `cht_point.run`, and no solver code was changed.
- **Outputs:** `v7_matched_mean_T.csv` (full results), `v7_summary.csv`, and per-run search logs
  `v7_*.json`.

## Result (`v7_summary.csv`)

| Target plate mean | Inlet needed, alt / par | η alt / par | Δη (points) | ΔR4 | ΔT_R4 | Plate std alt / par |
|---|---|---|---|---|---|---|
| 320 K | 291.3 / 306.7 K | 0.59889 / 0.59890 | −0.001 | +0.036 % | +0.03 K | 6.68 / 6.17 K (+8.3 %) |
| 330 K | 302.4 / 317.3 K | 0.57245 / 0.57246 | −0.001 | +0.038 % | +0.03 K | 6.49 / 5.90 K (+9.9 %) |
| 340 K | 313.5 / 328.0 K | 0.54567 / 0.54568 | −0.001 | +0.037 % | +0.03 K | 6.26 / 5.63 K (+11.2 %) |

## Answer

At matched mean plate temperature:

1. **Efficiency is the same.** The difference is 0.001 points, far below the model uncertainty.
   Efficiency is set by the mean plate temperature, not by the arrangement.
2. **R4 is not reduced.** Alternating gives R4 0.04 % higher (T_R4 0.03 K higher), because its plate
   is slightly less uniform.
3. **Plate uniformity is worse with alternating** at this design flow: plate std is 8–11 % higher and
   the spread is about 6 K larger.
4. **Why alternating looked worse at equal inputs.** To reach the same plate temperature, the
   alternating arrangement needs an inlet about 15 K cooler. At equal inlet temperature it therefore
   runs hotter and less efficiently, which is the −7.3 % seen in the campaign. The cause is the
   heat returned from each channel to the plate (the 40 % recirculation found in the 3-D benchmark),
   not extra radiative loss.

**Headline 1 of the roadmap therefore cannot be filled in as worded.** At the same mean plate
temperature, counter-current reduces R4 by about 0 % (it rises by 0.04 %) and changes efficiency by
about 0 points. Any claim about the alternating arrangement must rest on something other than R4
or efficiency at this flow. This is consistent with the campaign finding that alternating is more
uniform only above about 3.3 g/s.

This is model-only; no experimental validation is claimed.
