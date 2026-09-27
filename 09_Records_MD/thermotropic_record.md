# GRAIL CFD — Thermotropic glazing. Filing 3.

## The two questions worth asking

Not 'does scattering reduce absorbed flux' - it must - but:

1. does the layer ever reach its own switching band in service?
2. what does it cost when switching is not wanted?

Both matter because the layer is passive: it cannot tell overheating from a good day.

## Modelling note

What is applied is the **ratio** tau(T)/tau_clear multiplying the established system
transmittance, not tau(T) itself. That keeps the clear-state baseline exactly as established
(tau_glz_sys = 0.833, q" = 519.1 W/m2 at 800 W/m2) and applies only the switching effect.

**DESIGN_REVIEW_REQUIRED.** The roadmap's tau_glz_sys = 0.833 is two panes of low-iron glass
(0.91^2 = 0.828) and does not visibly account for a thermotropic layer, yet the CAD carries
THERMOTROPIC_LAYER_T2 as a separate body in the glazing stack. Either 0.833 already absorbs the
layer's clear-state transmittance, or the baseline optical chain omits a real optical element
and overstates absorbed flux by roughly 12 %. This is not resolved here. The ratio formulation
is the conservative reading.

## Result 1 — the layer never switches where it is

| G_T (W/m2) | flow | peak glazing T | peak absorber T |
|---|---|---|---|
| 400 | trickle | 32.2 C | 117.6 C |
| 400 | stagnation | 35.5 C | 142.1 C |
| 600 | trickle | 38.2 C | 161.7 C |
| 600 | stagnation | 42.9 C | 194.6 C |
| 800 | design | 25.2 C | 61.5 C |
| 800 | quarter | 35.3 C | 141.1 C |
| 800 | trickle | 44.2 C | 203.5 C |
| 800 | stagnation | 50.2 C | 242.0 C |
| 1000 | trickle | 50.3 C | 242.7 C |
| 1000 | stagnation | 57.3 C | 284.9 C |
| 1200 | trickle | 56.4 C | 279.5 C |
| 1200 | stagnation | 64.3 C | 323.7 C |

Across the whole envelope - up to **1200 W/m2 at stagnation** - the glazing peaks at
**64.3 C**, below its own 72 C switching threshold. It never switches, anywhere.

The reason is the transparent insulation. The TIM is doing exactly its job, decoupling the
glazing from the absorber: at 1200 W/m2 stagnation the absorber reaches **324 C** while the
glass sits 259 K below it. A layer that senses glass temperature is blind to the condition it
exists to protect against.

## Result 2 — on the absorber it is well targeted

| operating point | glazing-mounted | absorber-mounted |
|---|---|---|
| design | dTp_max +0.0 K, d_eta +0.00 % | dTp_max **+0.0 K**, d_eta +0.00 % |
| high irradiance | dTp_max +0.0 K, d_eta +0.00 % | dTp_max **+0.0 K**, d_eta +0.00 % |
| trickle | dTp_max +0.0 K, d_eta +0.00 % | dTp_max **-112.8 K**, d_eta -52.51 % |
| stagnation | dTp_max +0.0 K, d_eta +0.00 % | dTp_max **-127.9 K**, d_eta -49.57 % |

At the design point and at 1000 W/m2 with design flow, **both placements do nothing at all** -
exactly 0.000 K and 0.000 %. The absorber peaks at 70.3 C there, just under the 72 C threshold.
So an absorber-coupled layer costs nothing during normal collection.

At trickle flow it removes **112.8 K** of peak plate temperature, and at stagnation **127.9 K**.

The efficiency figures for those two cases (-52.5 % and -49.6 %) should not be read as a loss
worth weighing: at trickle flow efficiency is already 0.175 and at stagnation it is 0.002.
Halving a number that small is not a cost, it is the point.

## Verdict for the filing

The mechanism works, and the placement decides everything. A thermotropic layer in the glazing
stack, following glass temperature, is inert across the entire operating envelope of this
collector. The same layer coupled to the absorber gives passive overheating protection worth
**128 K** at stagnation for **zero** cost in normal collection.

This is a steady-state result. How fast the layer switches, whether it cycles, and how it
behaves during the transient into stagnation are not modelled and are listed as outstanding.

