# GRAIL — Mechanism study: does alternating counter-current flow work?

Solver: GRAIL-CHT, conjugate 2-D plate conduction + 1-D per-channel fluid, full 12-channel
absorber. Heat-transfer closure Nu = 3.428 taken from the resolved 3-D OpenFOAM solution.
Energy balance closes to **1e-5 %** in every case below.

## Solver verification before any conclusion was drawn
The difference between the two arrangements must vanish when lateral conduction cannot act,
and again when it acts perfectly. Both limits were tested:

| k_plate (W/m·K) | dQ_u | dR4 | comment |
|---|---|---|---|
| 0.01 | **+0.0006 %** | −0.0008 % | no lateral path → arrangements identical |
| 1 | −0.126 % | +0.217 % | |
| 22.9 | −2.618 % | +7.861 % | |
| **229 (AA1050)** | **−5.415 %** | **+17.048 %** | |
| 2290 | −3.456 % | +10.384 % | |
| 2.29e6 | **−0.009 %** | +0.024 % | isothermal plate → arrangements identical |

Both limits collapse to zero and the effect peaks at finite conductivity. The solver is
behaving; the effect is genuinely conduction-mediated.

## The causal chain, tested link by link
| # | Hypothesised link | Verdict | Evidence |
|---|---|---|---|
| 1 | Opposite flow → opposing local gradients | **CONFIRMED** | per-channel outlets spread 319.97–326.45 K instead of a uniform 324.11 K |
| 2 | Lateral heat transfer through the metal bridge | **CONFIRMED, LARGE** | **218.35 W** across the 11 bridge planes, against **0.0000 W** in parallel flow. Lateral:axial conduction ratio **175.8** |
| 3 | Absorber temperature homogenisation | **CONFIRMED** | T_p std −8.8 % at matched mean (−13.8 % at matched flow) |
| 4 | Reduction of high-temperature regions | **NOT CONFIRMED** | P99 only −1.05 %; dT_p actually **rises** +10.8 % |
| 5 | Reduction in R4 | **NEGLIGIBLE** | **−0.045 %** at matched mean |
| 6 | Reduction in radiative loss | **NEGLIGIBLE** | Q_rad 2.62906 → 2.62384 W, **−0.20 %**, i.e. 5.2 mW out of 274 W |
| 7 | Improvement in useful heat | **NO** | +0.001 % at matched mean; **−5.4 %** at matched mass flow |

## Matched-mean comparison (the fair test)
Inlet temperature tuned to 285.689 K so both cases sit at T_p,mean = 315.10 K.

| quantity | parallel | alternating | change |
|---|---|---|---|
| T_p,mean (K) | 315.0961 | 315.0980 | +0.0006 % |
| T_p std (K) | 6.7240 | 6.1307 | **−8.82 %** |
| dT_p (K) | 21.9319 | 24.3024 | +10.81 % |
| P99 (K) | 325.5911 | 322.1869 | −1.05 % |
| R4 | 9.884533e+09 | 9.880069e+09 | **−0.045 %** |
| Q_rad (W) | 2.62906 | 2.62384 | −0.20 % |
| Q_u (W) | 251.9842 | 251.9870 | +0.001 % |
| efficiency | 0.59655 | 0.59656 | +0.001 % |
| R4 / mean(T)^4 | 1.002731 | 1.002253 | — |

That last row is the crux. The nonuniformity contributes only **0.27 %** to R4 in the parallel
case. Flattening removes part of that 0.27 %. There is nothing else to win.

## Why the mechanism cannot pay off on this collector
**The selective coating has already won.** With TiNOX at eps = 0.04, radiative loss is
**2.63 W out of 274.10 W absorbed — under 1 %**. Even eliminating radiation entirely would
gain less than one per cent. A mechanism whose whole purpose is to reduce radiative loss has
almost nothing left to reduce.

Jensen's inequality still holds: at fixed mean, a flatter field has strictly lower mean(T^4).
The direction is right and the model confirms it. The magnitude is 0.045 %.

## Caveat on the matched-flow penalty
At equal mass flow the alternating case runs 12.7 K hotter on average and loses 5.4 % of
efficiency. That is a secondary finding from a reduced-order model and should be confirmed by
3-D conjugate CFD before it is relied upon. The matched-mean result — that the flattening is
real but worth 0.045 % of R4 — is the robust one, and it does not depend on that caveat.

## What this means for the filings
Filing 1 claims a collector that works by flattening the absorber temperature field. The
flattening is real and measurable: 218 W crosses the bridges and the standard deviation falls
8.8 %. What the CFD does not support is the step from flattening to reduced loss, because the
loss it targets is already negligible. The claim should rest on the demonstrated
homogenisation, not on an efficiency or radiative-loss gain this collector cannot deliver.

An arrangement that flattens the field may still be worth claiming for other reasons — thermal
stress, coating durability, stagnation behaviour, or performance with a **non-selective**
absorber, where eps is 0.9 rather than 0.04 and radiation is a real loss term. That last case
is worth simulating: it is the configuration in which this mechanism should pay.
