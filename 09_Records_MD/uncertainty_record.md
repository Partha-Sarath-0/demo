> **NOTE (Rev 4.1, final):** Any ALT_n-vs-PAR_n "pair" statistic in this file is WITHDRAWN. The cases are independent samples. Use the group-wise results in 08_Tables/final/T3 and T4 and in the CFD Report Rev 4.1, Part V.

# GRAIL CFD — Uncertainty and sensitivity assessment

> **SUPERSEDED (Rev 4, 22 Sep 2026).** Sections 1 onwards are the Rev 2 assessment, kept unchanged.
> The current budget is the "Rev 4 update" section at the end of this file.


Framework: ASME V&V 20-2009. Three contributions are quantified separately and combined in
quadrature: discretisation (Roache grid convergence index), input uncertainty (paired Monte
Carlo over material properties and boundary conditions), and iterative convergence. Round-off
is not carried — the solver is float64 and the independent energy balance closes to 1e-7 %.

This assessment did not exist before. `05_validation/` and `06_domain_equiv/` were empty; the
only prior refinement study was on the geometry sampling (CR-09), not on any solver grid.

## 1. Headline result

| quantity | value, finest grid | expanded uncertainty, k = 2 | verdict |
|---|---|---|---|
| efficiency difference | -5.55 % | ± 0.64 pp | distinguishable from zero |
| loss-coefficient difference | -7.77 % | ± 1.71 pp | distinguishable from zero |
| plate-spread difference (RMS) | -11.52 % | ± 8.59 pp | distinguishable from zero |
| plate-spread difference (peak-to-peak) | +7.10 % | ± 13.15 pp | **NOT distinguishable from zero** |

The efficiency deficit and the loss-coefficient benefit are firm. The RMS uniformity benefit
survives but with a wide band. **The peak-to-peak uniformity claim does not survive** — its
95 % interval spans zero and its sign is not even stable between the campaign average
(−3.06 %) and the design point (+7.10 %). It should not be claimed.

## 2. Discretisation — the conjugate plate grid

Four levels, refinement ratio 1.41 in cell count per direction, both arrangements on every level.

| grid | cells | h (mm) | co η | alt η | co std (K) | alt std (K) | Δstd (%) |
|---|---|---|---|---|---|---|---|
| 110 × 120 **(campaign grid)** | 13200 | 6.3246 | 0.596553 | 0.564249 | 6.7240 | 5.7964 | -13.795 |
| 156 × 170 | 26520 | 4.4620 | 0.596641 | 0.563951 | 6.7368 | 5.8887 | -12.590 |
| 220 × 240 | 52800 | 3.1623 | 0.596697 | 0.563771 | 6.7370 | 5.9277 | -12.013 |
| 311 × 339 | 105429 | 2.2379 | 0.596735 | 0.563627 | 6.7407 | 5.9643 | -11.517 |

Observed orders and GCI on the difference, from the two independent triplets:

| quantity | p (fine triplet) | p (coarse triplet) | GCI | in the asymptotic range? |
|---|---|---|---|---|
| ΔTp_std | 0.446 | 2.087 | 32.34 % | **no** |
| Δ efficiency | 0.766 | 1.385 | 2.24 % | **no** |
| Δ loss coefficient | 0.905 | 1.347 | 1.40 % | yes |
| Δ peak-to-peak spread | 1.208 | 0.429 | 98.40 % | **no** |

Only ΔU_L is cleanly in the asymptotic range. Δη is borderline — its two triplets give 0.77 and
1.39 — but its GCI is 2.2 %, so the practical conclusion is unaffected. ΔTp_std is the problem: the
two triplets
give observed orders of 0.45 and 2.09 and Richardson extrapolations of −8.54 % and −11.46 %.
The larger GCI of the two is carried, and the disagreement is reported rather than resolved by
choosing the flattering triplet.

Co-current quantities are essentially grid-independent (GCI 0.003 – 0.19 %); all of the grid
sensitivity sits on the alternating side, where the lateral gradient across each bridge is what
the grid has to resolve.

### Lateral bridge conduction — a correction to an earlier statement

This study previously reported 170.84 W against **0.0000 W**. The co-current figure is exactly
zero *by symmetry*, not merely small: with every channel flowing the same way the plate field is
periodic in y and the temperature gradient at the bridge midline vanishes. The campaign reads
6.5e-11 to 9.1e-11 W, which is round-off. The grid study reads 0.000, 8.892, 0.000 and 3.345 W
across the four levels — those nonzero values are a **sampling artifact**, arising when the
midline does not coincide with a cell face, not physics. Alternating reads 67 – 303 W across the
campaign and 218 – 224 W at the design point. The contrast is real; the denominator is zero, so
it should be quoted as an absolute figure, never as a ratio.

## 3. Input uncertainty — paired Monte Carlo

200 samples, all accepted, on the campaign grid. Every draw is run through **both** arrangements
with identical inputs. That pairing is not a convenience: the claim is a difference, and a
difference between two runs sharing one property draw and one grid has most of its systematic
error cancelled.

| quantity | paired sd | sd if the draws were not paired | factor |
|---|---|---|---|
| Δ efficiency | 0.304 pp | 3.959 pp | 13.0× |
| ΔTp_std | 3.092 pp | 6.857 pp | 2.2× |
| Δ loss coefficient | 0.848 pp | 4.682 pp | 5.5× |
| Δ peak-to-peak spread | 3.464 pp | 6.696 pp | 1.9× |

Treating the two arrangements as independent would inflate the efficiency-difference band by
13× and would have made a firm result look indistinguishable from noise.

### Input distributions

Every entry is an **ENGINEERING_ASSUMPTION**. The roadmap's material table gives handbook values
for the material class with no tolerances, and its own verification item V6 requires confirmation
against supplier datasheets before final runs. These standard uncertainties are assumed, stated
here rather than buried, and the sensitivity ranking below shows which of them matter.

| input | nominal | standard uncertainty | basis |
|---|---|---|---|
| `k_al` | 229 | 2.0 % (rel) | AA1050 handbook value; temper/purity spread |
| `nu_cfd` | 3.428 | 5.0 % (rel) | extracted from this study's own 3-D CFD |
| `alpha_abs` | 0.95 | 0.01 (abs) | TiNOX datasheet tolerance |
| `eps_abs` | 0.04 | 0.01 (abs) | TiNOX datasheet tolerance |
| `tau_glz_sys` | 0.833 | 0.01 (abs) | two-pane system, roadmap correction C11 |
| `tau_tim` | 0.82 | 0.02 (abs) | homogenised PC honeycomb |
| `k_tim` | 0.075 | 5.0 % (rel) | handbook, perpendicular direction |
| `k_vip` | 0.006 | 13.0 % (rel) | fumed-silica VIP, 20 % service derate over 25 y |
| `h_wind_fac` | 1 | 15.0 % (rel) | scatter of the linear wind-convection correlation |
| `h_rear` | 3 | 0.5 (abs) | still-air external coefficient |
| `mdot_total` | 0.0025 | 2.0 % (rel) | pump and flowmeter class |
| `G_T` | 800 | 2.0 % (rel) | class-A pyranometer |
| `T_amb` | 298.15 | 0.5 (abs) | ambient measurement |

## 4. Sensitivity

| output | dominant inputs (share of variance) | linear-model R² |
|---|---|---|
| efficiency | `tau_tim` 68 %, `tau_glz_sys` 19 %, `alpha_abs` 12 % | 0.9998 |
| uniformity difference | `nu_cfd` 91 %, `mdot_total` 9 % | 0.9991 |

Two things follow. Efficiency is an **optical** result — 99 % of its variance is the transmittance
chain and absorptance, not anything thermal. And the uniformity difference is almost entirely
controlled by `nu_cfd`, the single constant Nusselt number carried from the 3-D CFD into the
plate solver. That is the one input worth improving, and its assumed ±5 % covers discretisation
but **not** the modelling assumption that one constant Nu represents a graded, developing
channel. That assumption is the largest unquantified term in this assessment.

## 5. Restating the campaign

The full 291-case campaign ran on the coarsest grid tested. Ten campaign operating points,
stratified by mass flow, were re-run at three levels to measure the correction directly.

| case | ṁ (g/s) | Δstd @110×120 | @156×170 | @220×240 | shift (pp) |
|---|---|---|---|---|---|
| PAR_065 | 1.23 | +5.584 % | +6.756 % | +7.754 % | +2.17 |
| PAR_117 | 1.41 | +3.905 % | +5.163 % | +6.012 % | +2.11 |
| PAR_091 | 1.94 | -3.757 % | -2.691 % | -1.831 % | +1.93 |
| PAR_120 | 2.14 | -5.324 % | -4.304 % | -3.594 % | +1.73 |
| PAR_079 | 2.50 | -14.316 % | -12.951 % | -12.431 % | +1.88 |
| PAR_112 | 2.94 | -20.469 % | -19.528 % | -19.092 % | +1.38 |
| PAR_018 | 3.33 | -26.222 % | -25.670 % | -25.227 % | +0.99 |
| PAR_005 | 3.57 | -30.048 % | -29.547 % | -29.156 % | +0.89 |
| PAR_010 | 3.92 | -35.065 % | -34.409 % | -34.058 % | +1.01 |
| PAR_020 | 4.21 | -38.318 % | -38.183 % | -37.816 % | +0.50 |

The correction is **additive, not multiplicative**. Expressed as a ratio it ranges from 0.49 to
1.54 and is meaningless, because Δstd changes sign across the range. The clean description is a
linear map, which fits to R² = 0.99990:

```
  Δstd(220×240)  =  1.0349 × Δstd(110×120)  +  2.0314
```

| | campaign grid, as published | restated on 220×240 |
|---|---|---|
| campaign-average Δ plate spread | **-20.09 %** | **-18.76 %** |

### The threshold — the most consequential finding

The uniformity benefit is **conditional on mass flow**, and below a threshold the alternating
arrangement is *worse* than co-current:

- at 1.23 g/s the plate spread is **+7.75 %% higher** than co-current
- at 1.41 g/s, **+6.01 %% higher**
- the sign changes at **ṁ ≈ 1.815 g/s** (0.0018 kg/s), about 73 % of the design flow
- above it the benefit grows monotonically, reaching **−37.8 %%** at 4.21 g/s

Refinement moves the threshold *upward*, so the coarse grid understates how much flow is needed
before the mechanism pays. Any claim of homogenisation has to carry this condition.

## 6. Iterative convergence

| solver | measure | value |
|---|---|---|
| conjugate plate | outer-loop tolerance | 1e-8 |
| conjugate plate | energy balance (independent check) | < 1e-6 % |
| simpleFoam baseline | Ux initial residual | 5.3461e-11 |
| simpleFoam baseline | p initial residual | 1.5287e-08 |
| simpleFoam baseline | continuity | 2.4805e-10 |

Three orders of magnitude below the other two contributions; not carried into the combined band.

## 7. What this assessment does not cover

- The 3-D hydraulic grid convergence study (34k / 106k / 356k cells) was still running when this
  record was written; it sets the discretisation part of `nu_cfd`, the dominant input. Reported
  separately.
- The constant-Nusselt modelling assumption itself, which the sensitivity analysis identifies as
  the largest term and which a grid study cannot bound.
- The temperature-dependent-viscosity case flagged in the material database (note 4). Viscosity
  does not enter the thermal result while Nu is held constant, so it affects pressure drop and
  pumping power only — but that is an assumption, not a proof, and it is untested.
- Domain equivalence (CR-03), still open.
- Model-form uncertainty against experiment: no independent validation data has been used. The
  η₀ and F_R·U_L agreement quoted elsewhere is agreement with the roadmap's own design targets,
  which is self-consistency, not validation.


## 8. Post-hoc revision — the dominant input is more uncertain than assumed

The sensitivity analysis put 91 % of the uniformity difference's variance on `nu_cfd`, the single
constant Nusselt number carried from the 3-D CFD into the plate solver. The Monte Carlo assumed
±5 % for it. The 3-D grid study shows that assumption is **not conservative**.

Applying the original extraction method (`09_post/extract_htc.py`, developed region ξ > 0.15)
unchanged to two grids:

| grid | cells | Nu, developed region |
|---|---|---|
| L1 | 34,304 | 3.7397 |
| L2 | 105,600 | **3.4282** — this is the 3.428 the solver uses |

A 9.09 % change across a refinement ratio of 1.4547. Converted to a discretisation uncertainty on
the finer grid:

| assumed order | u(`nu_cfd`) |
|---|---|
| p = 1 | 20.0 % |
| p = 2 | 8.1 % |
| p = 3 | 4.4 % |

The order is not yet observed — that needs the third level, which was still solving when this was
written. Rescaling the Monte Carlo band for the corrected input uncertainty, using the measured
variance share and the near-perfect linearity (SRC 1.007, R² 0.999):

| quantity | value | k = 2 band if p = 2 | k = 2 band if p = 1 |
|---|---|---|---|
| ΔTp_std | -11.52 % | ± 11.46 pp (excludes zero) | ± 24.39 pp (**includes zero**) |
| Δ efficiency | -5.55 % | ± 0.80 pp (excludes zero) | ± 1.61 pp (excludes zero) |

**This is the decisive result of the assessment.** The efficiency deficit survives either way —
−5.55 % ± 0.80 pp at best, ± 1.61 pp at worst, comfortably clear of zero. The uniformity benefit
does not: at second order it barely clears zero (−11.52 % ± 11.46 pp), and at first order it does
not clear zero at all.

Until the third grid level establishes the observed order, the honest statement is that the
uniformity benefit is **not yet demonstrated to be distinguishable from zero at the design point**.
It is clearly real at high mass flow, where the effect reaches −38 % and dwarfs this band.

A further term is still unquantified and is larger than either: the modelling assumption that one
constant Nusselt number represents a graded, developing channel at all. Nu varies from 3.29 to
3.65 over the developed region and reaches 29.8 at the inlet; collapsing that to a single constant
is a model-form choice no grid study can bound.


## 9. Resolved — the 3-D grid study, and what it changed

The fine 3-D grid finished after 360 SIMPLE iterations to the case's own residual controls
(`SIMPLE solution converged`, not an endTime stop). Three levels at refinement ratio ~1.5:

| quantity | 34,304 cells | 105,600 | 356,400 | observed order p | GCI |
|---|---|---|---|---|---|
| pressure drop (Pa) | 35.872 | 35.592 | 35.468 | 2.278 | 0.290 % |
| temperature rise (K) | 25.859 | 25.964 | 25.975 | 6.311 | 0.004 % |
| meshed volume (mm3) | 18500 | 18579 | 18617 | 2.159 | 0.179 % |
| peak / bulk velocity | 1.8274 | 2.0617 | 1.9274 | 1.442 | 10.972 % |
| Nu, developed region | 4.1272 | 3.9129 | 3.7519 | 0.937 | 11.610 % |

**Pressure drop, temperature rise and meshed volume are converged** at second order with GCIs
of 0.29 %, 0.004 % and 0.18 %. The hydraulic side of the baseline is sound.

**The Nusselt number is not.** Applying the original extraction method
(`09_post/extract_htc.py`, developed region xi > 0.15) unchanged to all three grids:

| grid | cells | Nu |
|---|---|---|
| L1 | 34,304 | 3.7397 |
| L2 | 105,600 | 3.4282 |
| L3 | 356,400 | 3.2236 |
| Richardson extrapolation | — | **2.9238** |

Observed order **p = 1.283** — first order, not second. GCI **11.63 %**, so
u(`nu_cfd`) = **9.30 %**, not the 5 % the Monte Carlo assumed. Both extraction methods agree
on this independently (mine gives p = 0.937, GCI 11.61 %).

### This is a bias, not just an uncertainty

Every conjugate result in this study was run with `nu_cfd` = 3.4282, the medium-grid value.
The grid-converged value is **2.9238** — the solver has been running **+17.25 %** high on the
one input that controls 91 % of the uniformity difference.

Rather than extrapolate the linear sensitivity model nearly three standard deviations outside
its sampled range, the corrected value was **run**. Same grid, same properties, only `nu_cfd`
changes:

| quantity | as run (Nu 3.4282) | grid-corrected (Nu 2.9238) | shift |
|---|---|---|---|
| Δ plate spread (RMS) | -12.010 % | **-21.093 %** | -9.083 pp |
| Δ efficiency | -5.518 % | **-4.937 %** | +0.581 pp |
| Δ loss coefficient | -7.739 % | **-7.068 %** | +0.671 pp |
| Δ peak-to-peak spread | +6.561 % | **-3.637 %** | -10.198 pp |

The predicted shift from the sensitivity model was -9.15 pp on Δ plate spread; the measured
shift is -9.08 pp. The linear model held.

## 10. Final result

Uncertainty is recombined using the **measured** local sensitivity dQ/d(Nu) from the two runs
above, rather than the Monte Carlo's rescaled coefficient, plus the contribution of all other
inputs, plus the plate-grid discretisation term.

| quantity | value | u_input | u_numerical | expanded, k = 2 | verdict |
|---|---|---|---|---|---|
| Δ plate spread (RMS) | **-21.09 %** | 4.983 pp | 2.979 pp | **± 11.61 pp** | **distinguishable from zero** |
| Δ efficiency | **-4.94 %** | 0.393 pp | 0.099 pp | **± 0.81 pp** | **distinguishable from zero** |
| Δ loss coefficient | **-7.07 %** | 0.442 pp | 0.087 pp | **± 0.90 pp** | **distinguishable from zero** |
| Δ peak-to-peak spread | **-3.64 %** | 5.595 pp | 5.590 pp | **± 15.82 pp** | NOT distinguishable |

### What this overturns

Section 8 of this record, written before the fine grid finished, said the uniformity benefit
was 'not yet demonstrated to be distinguishable from zero at the design point'. **That is now
superseded.** With the Nusselt bias corrected the benefit is **-21.09 % ± 11.61 pp** and clears
zero comfortably. The earlier statement was correct given what was then known and wrong given
what is known now; it is left in place above rather than edited, so the reasoning is traceable.

The efficiency deficit also shrinks, from -5.52 % to **-4.94 % ± 0.81 pp**. It remains firm
and it remains a deficit.

The **peak-to-peak** spread stays undemonstrable: -3.64 % ± 15.82 pp, spanning zero. It should
not be claimed under any grid or any Nusselt value.

### What still has to be done

The whole 291-case campaign and every figure derived from it were computed at `nu_cfd` = 3.4282
and therefore carry the same bias. The direction and size are now known (Δ plate spread shifts
about -9 pp, Δ efficiency about +0.6 pp), but the dataset itself has **not** been recomputed.
Doing so is the single largest outstanding item and it would move the campaign-average
uniformity figure substantially further negative.

Nu is still falling at 356,400 cells. The extrapolated 2.9238 carries an 11.6 % GCI and a fourth
level would be needed to tighten it. And the model-form question is untouched: one constant
Nusselt number is being asked to represent a graded, developing channel whose local Nu runs
3.09 to 3.43 in the developed region and reaches 29.8 at the inlet.


---

## 11. Closed out — the campaign recomputed, and the three remaining checks

Everything in sections 1 to 10 was computed at `nu_cfd` = 3.4282. This section supersedes the
"what still has to be done" list at the end of section 10. Nothing above is edited; it is
left as written so the reasoning stays traceable.

### 11.1 The campaign was recomputed (CR-13)

Same seed, same Latin Hypercube, same bounds, same gates, same grid, only `nu_cfd` changed
from 3.4282 to the Richardson-extrapolated **2.9238**. Rev 1 is kept on disk. Full analysis in
`05_validation/rev2_analysis.json`, figure R1.

Paired, case by case — the clean measurement of what the correction did:

| quantity | co-current | alternating |
|---|---|---|
| plate spread, RMS | −0.036 K | **−0.473 K** |
| plate peak-to-peak | −0.194 K | **−1.822 K** |
| efficiency | −0.0009 | +0.0022 |
| mean plate temperature | +0.288 K | −0.722 K |

The correction moves the alternating cases and barely touches the co-current ones, which is
what a bias on the wall-to-fluid coupling should do.

### 11.2 Rev 1's campaign average was censored (CR-14)

Rev 1 lost 9 rows to the convergence gate and Rev 2 loses none. The 9 were **all
alternating**, and all of them were the lowest-flow cases in the sample: 1.10 g/s mean against
a 2.75 g/s campaign mean, none above 1.19 g/s, mean plate spread 10.97 K against 4.69 K for
alternating overall. Rev 1 therefore averaged a sample with its own hardest cases removed.

| Δ plate spread, alternating minus co-current | value |
|---|---|
| Rev 1, the 291 rows both revisions share | −20.09 % |
| Rev 2, the same 291 rows | −27.60 % |
| **Rev 2, all 300 rows — the figure to quote** | **−20.83 ± 12.09 % (k = 2)** |

Two corrections of opposite sign and similar size, which nearly cancel. The uncensored number
is the one to use, because it is the only average taken over the sample that was drawn.

### 11.3 The mass-flow threshold is withdrawn (CR-15)

Every one of the 8 mass-flow bins from 1.23 to 4.27 g/s favours alternating in Rev 2. In
Rev 1 the lowest bin read +7.75 %. Both causes are in 11.1 and 11.2: the biased Nusselt
number, and the fact that the censored rows were precisely the low-flow ones that set the
threshold. **There is no minimum operating flow claim to make.** The bin-to-bin scatter is
sampling noise — the two arrangements are independent Latin Hypercube draws — so only the
sign, consistent across all 8 bins, is robust.

### 11.4 Nu(ξ) instead of a constant — the largest model-form term (CR-16)

Closeout check A ran the same solver at 220 × 240 three ways: with a constant Nu, with the
measured L3 profile, and with that profile rescaled to the constant's developed-region mean,
which separates the cost of the profile's *shape* from the cost of its *level*.

| Nu model | Δ plate spread | Δ efficiency |
|---|---|---|
| constant, 2.9238 | −21.09 % | −4.94 % |
| measured profile, rescaled to the same mean | **−6.85 %** | −5.51 % |
| measured profile, as measured | −2.14 % | −5.88 % |

Collapsing Nu(ξ) to one number is worth **+14.24 percentage points** on the uniformity
difference — larger than every numerical and input uncertainty in this assessment combined.
It costs only −0.57 pp on efficiency.

This does not change the sign of the uniformity result, and it does not change the efficiency
result at all. It does mean the uniformity benefit must be quoted as **model-form limited**:
the campaign carries a constant Nu, and a campaign carrying Nu(ξ) has not been run.

### 11.5 PCM time step (closeout check B)

Charge scenario, design point, 2 h, at dt = 20, 10 and 5 s:

| refinement | mean plate temperature | stored energy |
|---|---|---|
| 20 → 10 s | +0.068 K | +1.55 % |
| 10 → 5 s | +0.033 K | +0.76 % |

Both ratios are close to one half, which is first-order convergence in dt as backward Euler
requires. Richardson extrapolation puts dt = 5 s within 0.033 K and 0.76 % of converged.
**The PCM time step is adequate**; no PCM result changes.

### 11.6 The efficiency-curve estimator (closeout check C)

Six inlet temperatures from 288 to 338 K, fitted as the ISO 9806 / ASHRAE 93 straight line:

| arrangement | η₀ | F_R·U_L | R² |
|---|---|---|---|
| co-current | **0.60010** | **1.9227 W/m²K** | 0.999932 |
| alternating | 0.57053 | 1.8500 W/m²K | 0.999939 |

The roadmap's targets are η₀ = 0.60 and F_R·U_L = 2.00. The co-current fit lands on **0.60010
and 1.92**, which settles the earlier 15 % spread between the two F_R·U_L estimators: the
curve-slope value is the one to quote, and the Hottel-Whillier-Bliss point-wise product
(2.2993) is a different quantity, evaluated at a single operating point.

This is self-consistency with the roadmap, not experimental validation, and it is still
labelled as such.

### 11.7 The metal is verified; the 3-D conjugate run is not (CR-17)

`chtMultiRegionSimpleFoam` would not converge and **no conjugate result is reported anywhere**
(`cht_attempt_record.md`). The question it was meant to close was answered instead by a 2-D
finite-element conduction solution in the as-built roll-bond cross-section
(`section_conduction_record.md`): the plate solver's absorber temperature is right to 0.44 K,
its lumped-thickness assumption to 0.06 K, and the alternating bridge magnitude it predicts
is confirmed to 13 % by an independent discretisation.

### 11.8 What is still open

- **Nu(ξ) in the campaign.** Section 11.4 bounds the effect but does not remove it. This is
  now the largest single item.
- **A fourth 3-D grid level** to tighten the 11.6 % GCI on Nu. Estimated at 20+ hours on the
  two cores available; declared infeasible here, not done.
- **A converged 3-D conjugate run.** The mesh is built and verified; the solver is not.
- **No experimental validation.** Unchanged.
- **DESIGN_REVIEW_REQUIRED**: whether τ_glz_sys = 0.833 already includes the thermotropic
  layer. This cannot be resolved from the roadmap and needs a human decision.


---

## Rev 4 update (current)

Basis: Dataset Rev 4 (Nu 4.48, plate 110/220 + Richardson) and the 3-D conjugate benchmark.

| quantity (design flow) | 3-D best estimate | discretisation | model form (ROM) | Nu band 4.46–4.65 |
|---|---|---|---|---|
| Δη (alt vs co) | −18.9 % | ± 0.1 pp | 0.5 pp | ≈ 0.1 pp |
| Δ plate std | ≈ −6.6 % | ± 1.0 pp (bound; non-asymptotic) | 2.0 pp | ≈ 1.1 pp |

Across the design space (Rev 4 Richardson, 150 pairs): Δη median −7.2 % (lower η in 69 % of pairs);
Δ plate std median −0.7 % (lower in 51 %), strongly flow-dependent (+80 % below 2.2 g/s, −34 % above
3.3 g/s). The Rev 2 headline values (−5.55 % η; −11.52 % RMS spread) are superseded.
Not quantified: glazing/radiation loss model (not 3-D tested). Experimental validation: none (V5
reference rejected, `17_validation/V5_assessment_record.md`).
