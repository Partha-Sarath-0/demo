# GRAIL CFD — Rev 3: temperature-dependent thermal conductivity

Raised by the Rev 2 dataset audit, item 3 (property-model inconsistency). Closes it by
measurement rather than by estimate.

## What changed, and only this

Viscosity was already carried as mu(T) through the Vogel relation and varies by a factor of
2.84 across the campaign. Thermal conductivity was held fixed at **0.610 W/m·K**, which is the
value at **26.6 °C** — near the cold end of a campaign whose mean fluid temperature reaches
79.8 °C. Because the closure is

```
  h(x) = Nu * k / Dh(x)
```

an error in k is mathematically identical to the same percentage error in Nu, and Nu is the one
input the sensitivity analysis found controls 91 % of the uniformity difference.

Rev 3 replaces the constant with `k_water(T)`, a least-squares cubic through the handbook values
at 0, 20, 40, 60, 80 and 100 °C (0.5562, 0.5984, 0.6305, 0.6540, 0.6700, 0.6791 W/m·K), maximum
deviation **0.016 %**. It is evaluated at the local fluid temperature and refreshed inside the
existing outer iteration, so it converges with the rest of the fixed-point solve.

Same seed, same Latin Hypercube, same bounds, same pre-run geometry gate, same grid, same Nusselt
closure (2.9238), **same acceptance gates** — nothing was loosened to admit more rows.

## Reproducibility gate, passed before the campaign was launched

The new behaviour sits behind `k_of_T`, default **False**, so Rev 1 and Rev 2 remain
bit-reproducible. Verified on five Rev 2 cases chosen at the extremes of the sample:

| case | why it was chosen | d_eta | d_T_plate_mean | d_plate_std |
|---|---|---|---|---|
| PAR_000 | first co-current row | 0.000e+00 | 0.000e+00 | 0.000e+00 |
| PAR_134 | the only row above T_sat at 1 atm | 0.000e+00 | 0.000e+00 | 0.000e+00 |
| ALT_000 | first alternating row | 0.000e+00 | 0.000e+00 | 0.000e+00 |
| ALT_066 | highest efficiency in the campaign | 0.000e+00 | 0.000e+00 | 0.000e+00 |
| ALT_101 | highest Reynolds number in the campaign | 0.000e+00 | 0.000e+00 | 0.000e+00 |

A separate check confirmed the flag cannot leak back into the default path.

## What k(T) actually did

| | Rev 2 | Rev 3 |
|---|---|---|
| k | 0.610 fixed | 0.5986 – 0.6698, mean **0.6384** |
| mean relative change | — | **+4.66 %** |

The audit had estimated +5.02 % from the Rev 2 outlet temperatures; the realised figure on the
Rev 3 solution is +4.66 %, slightly lower because raising k raises h, which lowers the fluid
temperature a little, which lowers k. The feedback is mild and negative, as it should be.

## Paired result, case by case, on the 298 rows both revisions share

| quantity | co-current | alternating |
|---|---|---|
| plate spread, RMS | −0.0112 K | **+0.1558 K** |
| plate peak-to-peak | −0.0177 K | **+0.5576 K** |
| efficiency | +0.0003 | −0.0009 |
| mean plate temperature | −0.0876 K | +0.2812 K |
| outlet temperature | +0.0108 K | −0.0436 K |

As with the Rev 1 → Rev 2 correction, the change moves the alternating cases and barely touches
the co-current ones, which is what a change to the wall-to-fluid coupling should do.

## Headline, both revisions on the SAME 298 rows

| quantity | Rev 2 | Rev 3 | shift |
|---|---|---|---|
| **Delta plate spread (RMS)** | −22.072 % | **−19.288 %** | **+2.784 pp** |
| Delta efficiency | −4.898 % | **−5.093 %** | −0.195 pp |
| Delta loss coefficient, all rows | −0.918 % | −4.787 % | −3.869 pp |
| Delta outlet temperature | −0.694 % | −0.710 % | −0.016 pp |
| Delta mean plate temperature | +2.944 % | +3.059 % | +0.115 pp |

**The linear sensitivity model held for the second time.** Scaling the calibrated Rev 1 → Rev 2
slope of 0.6175 pp per 1 % of Nu by the realised +4.66 % change in k predicts **+2.88 pp**. The
measured shift is **+2.78 pp** — agreement to 3.4 %. (The Rev 1 → Rev 2 check was
−9.15 predicted against −9.08 measured.)

## Rev 3 loses two rows, and they are NOT random — the CR-14 test repeated

Rev 2 lost no rows. Rev 3 loses **ALT_029** and **ALT_114**, both to the convergence gate. The
same test applied in CR-14 was applied here, and it fails the same way:

| | the 2 lost rows | alternating overall |
|---|---|---|
| mass flow | 0.0010 kg/s (the sample minimum) | 0.0027 kg/s |
| T_in − T_amb | +31.8 and +31.4 K | +12.5 K |
| plate spread | 10.12 K | 4.69 K |

Both are alternating, both are at the lowest flow in the draw, and both run their inlet far above
ambient. They are among the hardest cases in the sample, and raising h makes the coupled solve
stiffer at low flow.

**Therefore the Rev 3 campaign average is censored, exactly as Rev 1's was.** The censoring is
quantified rather than ignored: removing those same two rows from Rev 2 moves its average from
−20.83 % to −22.07 %, an offset of **+1.24 pp**. Applying that offset to Rev 3 gives an estimated
uncensored figure of about **−18.0 %**, but this is an ESTIMATE and is labelled as one — the two
cases do not converge under k(T), so the uncensored Rev 3 average cannot be measured.

The clean, measured statement is the paired one: **k(T) is worth +2.78 pp on the uniformity
difference**, measured on 298 identically-sampled pairs.

## Quality of Rev 3

| check | result |
|---|---|
| rows | 298 of 300, 2 rejected by the unchanged convergence gate |
| converged | True on all 298 |
| residual | maximum 1.0e-06, at the unchanged tolerance |
| energy balance | maximum residual 1.52e-04 W = **1.0e-04 %** |

## With uncertainty bands (bootstrap, k = 2)

| basis | Delta plate spread | Delta efficiency |
|---|---|---|
| Rev 2, all 300 rows | −20.83 ± 12.14 pp | −5.24 ± 2.36 pp |
| Rev 2, the common 298 | −22.07 ± 12.61 pp | −4.90 ± 2.32 pp |
| **Rev 3, 298 rows** | **−19.29 ± 12.66 pp** | **−5.09 ± 2.31 pp** |

## What this does and does not change

- The **sign is unchanged**. The alternating arrangement still flattens the absorber field, and
  the benefit still clears zero.
- The **magnitude shrinks** by 2.78 percentage points, and about 1.2 pp more of the Rev 3 figure
  is censoring rather than physics.
- The **efficiency deficit is unchanged**: −5.09 % against −4.90 %, a shift of 0.195 pp, well
  inside its own band. Alternating remains less efficient at matched flow.
- The **model-form term is still larger than this one**. Carrying Nu(xi) instead of a constant is
  worth +14.24 pp; k(T) is worth +2.78 pp. The uniformity claim remains model-form limited, and
  Nu(xi) remains the largest outstanding item.

## Status of the dataset revisions

| revision | Nu | k | rows | status |
|---|---|---|---|---|
| Rev 1 | 3.4282 | 0.610 fixed | 291 | superseded, kept on disk |
| Rev 2 | 2.9238 | 0.610 fixed | 300 | superseded for the closure, kept on disk |
| **Rev 3** | 2.9238 | **k(T)** | 298 | **current** |

No row was deleted from any revision. Rev 1 and Rev 2 remain bit-reproducible.
