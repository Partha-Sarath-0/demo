# GRAIL CFD — Validation against the Hottel-Whillier-Bliss model

## Why this and not a published experiment

Matching someone else's measurement on a different collector validates the combination of
their geometry, their instrument and my model, and cannot separate them. Hottel-Whillier-Bliss
is the standard closed-form flat-plate model (Duffie & Beckman), it is the accepted reference
for a bonded-fin absorber, and it shares **none** of this solver's discretisation. Agreement
with it tests the fin and flow solution directly.

Everything quoted elsewhere as 'validation' against the roadmap's eta0 = 0.60 and
F_R U_L = 2.00 is agreement with the project's own design intent. That is self-consistency.
This is the independent check.

## Method

```
  fin efficiency        F   = tanh(m (W-D)/2) / (m (W-D)/2),   m = sqrt(U_L / (k delta))
  collector eff. factor F'  = (1/U_L) / ( W [ 1/(U_L (D + (W-D) F)) + 1/(h_fi P) ] )
  heat removal factor   F_R = (mdot cp/(Ac U_L)) [1 - exp(-Ac U_L F'/(mdot cp))]
  efficiency            eta = F_R (tau alpha) - F_R U_L (T_in - T_amb)/G_T
```
The channel is graded, so W-D, D_h, P and h_fi all vary along the flow. F and F' are evaluated
at 400 stations and averaged over the flow path; averaging the geometry first would bias F,
which is nonlinear in D.

**U_L is not fitted.** It is taken from the solver's own loss balance, so the comparison tests
the fin and flow solution rather than the loss model, which both share.

## Result

| arrangement | solver eta | HWB eta | deviation | U_L used |
|---|---|---|---|---|
| co-current | 0.596697 | 0.597995 | **+0.218 %** | 2.4731 W/m2K |
| alternating | 0.563771 | 0.601730 | +6.733 % | 2.2817 W/m2K |

**Co-current agrees to +0.218 %.** For a model with no shared discretisation and no fitted
parameter, that is a strong result and it validates the conjugate solver's fin and flow
treatment on this geometry.

**Alternating differs by +6.733 %, and that is expected and informative.** Hottel-Whillier-Bliss
assumes every tube is alike and every fin is symmetric about its own channel. It has no way to
represent neighbours flowing in opposite directions. The 6.7 % gap is therefore a measure of
how far the alternating arrangement departs from the classical model - it is the part of the
physics the standard model cannot see. HWB **over**-predicts, because it cannot represent the
mean-temperature rise that costs the alternating arrangement its efficiency.

## Analytical chain, co-current

| quantity | value |
|---|---|
| fin efficiency F, inlet | 0.9996 |
| fin efficiency F, outlet | 0.9994 |
| collector efficiency factor F' | 0.9883 |
| heat removal factor F_R | 0.9297 |
| (tau alpha) | 0.6489 |
| eta0 = F_R (tau alpha) | 0.6033 |

The fin efficiency is **0.9995** - essentially unity. That is the physically important reading:
with 2 mm of aluminium at 229 W/mK spanning a 31.3 mm bridge against a loss coefficient near
2.5 W/m2K, the fin parameter m(W-D)/2 is tiny and the bond land is very nearly isothermal.
**This is why the absorber conducts laterally so readily, and it is the physical basis of the
alternating mechanism.**

## A discrepancy to flag, not to bury

F_R U_L from this chain is **2.2993 W/m2K**, against the roadmap target of 2.00 and against the
1.9986 reported earlier in this project - **+15.0 %** apart. The two are different estimators:
the earlier figure is the slope of an efficiency curve fitted across inlet temperatures, while
this is the point-wise product using U_L from the design-point loss balance. They need not
agree, and a 15 % spread between them means neither should be quoted as 'the' loss coefficient
without saying which estimator produced it. Resolving this needs a proper efficiency-curve fit
across several inlet temperatures, which is listed as outstanding.

