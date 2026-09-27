# V5 component check: GRAIL loss models vs Beikircher et al. (2015) measurements

**Source:** Beikircher, Möckl, Osgyan, Streib, *Sol. Energy Mater. Sol. Cells* 141 (2015) 398–406 (ZAE Bayern).
**Script:** `beikircher_check.py` (calls GRAIL-CHT's own `top_loss` and `Materials`; nothing changed or tuned).
**Results:** `beikircher_check.json`.

## 1. Front (TIM cover): PASS

| | U front (W/m²K) |
|---|---|
| Beikircher, measured, honeycomb + ETFE film, 30 / 40 mm | 2.2 / 1.95 |
| GRAIL-CHT, T_plate − T_amb = 20 / 40 / 60 / 80 K (wind 3 m/s) | 2.06 / 1.96 / 1.95 / 1.96 |

GRAIL's front loss lies inside the measured range for honeycomb TIM covers.
Caveat: the builds differ (GRAIL: 10 mm TIM + two thin air gaps + double glass + TiNOX ε 0.04), so this
is a plausibility check of the level, not a validation of the exact stack.

## 2. Rear (VIP): GRAIL is optimistic — DESIGN_REVIEW_REQUIRED

| | Effective k (W/mK) | Rear U, GRAIL stack (W/m²K) |
|---|---|---|
| GRAIL input (catalogue fumed-silica VIP) | 0.006 | **0.27** |
| Beikircher, measured in a collector, silica VSI, 40 mm, 70–120 °C | 0.010–0.018 | 0.43–0.69 |
| Beikircher, measured, perlite VSI | 0.020–0.034 | 0.75–1.07 |

- Inside a hot collector (70–120 °C, envelope and edge effects) the measured vacuum insulation is
  1.7–3× worse than GRAIL's catalogue k.
- **Effect (ENGINEERING_ASSUMPTION: rear-U increase added directly to a1):** a1 rises by about
  0.16–0.42 W/m²K, i.e. parallel a1 ≈ 2.26–2.52 instead of 2.10 (still about half of Del Col's
  roll-bond collectors, 4.6–4.7).
- **Crossover with Del Col roll-bond collectors** moves from Tm* 0.036–0.043 to 0.037–0.046 m²K/W.
  The conclusion does not change.
- Also measured by Beikircher: VSI improves a1 by ≥ 0.5 W/m²K over 40 mm mineral wool. GRAIL's
  benefit is the same order.
- The dataset and the delivered results are **not** changed. This is reported as a sensitivity and
  a design-review item: use a measured in-collector VIP k (0.010–0.018 W/mK) in the thesis
  uncertainty statement.

## 3. Kessentini et al. (CTTC/UPC) honeycomb-TIM collector: comparison only

Measured (ISO 9806-1): η = 0.732 − 7.19 (Tav − Tamb)/G. Its high a1 is due to its poor coating
(ε = 0.5, stated by the authors); GRAIL uses ε = 0.04. Glass τ, gaps and insulation are not
stated, so a method check like Del Col's cannot be run. Cite as a measured TIM collector.

## Status

Front loss: consistent with measurement. Rear loss: under-estimated, now quantified.
This is a component check on other collectors, **not** an experimental validation of GRAIL.
**V5 stays OPEN.**
