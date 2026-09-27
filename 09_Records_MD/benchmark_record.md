# GRAIL — Level-3 benchmark: 3-D conjugate CFD against the reduced-order model

This is the first converged 3-D conjugate heat-transfer solution in the project, and the first
test of the reduced-order model (GRAIL-CHT) against one. Root cause of the earlier divergence and
the repair: `14_provenance/cht_rootcause_record.md`.

## Problem definition — identical in both models

| item | value | status |
|---|---|---|
| domain | 2-channel periodic strip, 1100 × 80 mm, translational cyclic in y (CR-03 validated) | — |
| geometry | the CAD plate: taper ALTERNATES channel to channel | as built |
| fluid | water, rho 997, cp 4180, k 0.610, mu 8.55e-4 — constant | ENGINEERING_ASSUMPTION (enables exact one-way coupling) |
| solid | AA1050, k 229 | roadmap |
| inlet | 300 K, uniform velocity profile | — |
| mass flow per channel | 2.077072e-4 kg/s (the 3-D case's meshed inlet area gives −0.30 % vs nominal; GRAIL-CHT run at the same flow) | measured |
| top | q″ − U_top (T − T_amb) per unit PLAN area, q″ = 519.1256 W/m², U_top = 4.191176 W/m²K | benchmark ENGINEERING_ASSUMPTION |
| rear | h_rear (T − T_amb), 3.0 W/m²K | benchmark ENGINEERING_ASSUMPTION |
| T_amb | 298.15 K | — |

The loss model is linear and simpler than the campaign's (no glazing radiation, no PCM/VIP path).
That is deliberate: the benchmark tests the COUPLING physics — the Nusselt closure, the lumped
plate, lateral conduction — which do not depend on the loss model.

Arrangements, both on the same CAD geometry:
- **alternating**: the real GRAIL plate, neighbours flowing in opposite directions
- **co-current (CAD taper)**: same plate and metal, both channels flowing −x, so one converges
  and one diverges. This holds the metal distribution fixed and isolates flow direction.

GRAIL-CHT also run co-current with CO-taper (the campaign's definition): efficiency identical to
5 digits (0.50993), std within 0.07 %. The taper pattern has no thermal effect under a constant
Nu, because h·P = Nu·k·P/D_h and P/D_h = P²/4A is invariant along a self-similar section.

## Verification of the 3-D solutions (NX 60 level)

| check | co-current | alternating |
|---|---|---|
| flow: mass per channel | 2.07707161e-4 kg/s | 2.07707161e-4 kg/s |
| flow: mass imbalance | ~1e-9 | ~1e-9 |
| flow: dp per channel | 37.929 Pa (converging) / 66.78 Pa (diverging, see note) | 37.929 Pa both |
| energy: frozenFlow honoured | 0 p, 0 U solves | 0 p, 0 U solves |
| energy balance, independent, from raw fields | **0.005 %** | **0.035 %** |
| iteration convergence of every reported quantity | 2000 → 4000: ≤ 2e-6 | 6000 → 8000: ≤ 3e-7 |
| absorbed power, per plan area | 45.683 W = q″ × 0.088000 m² | 45.683 W |

Note on the diverging channel's dp: 36.1 Pa of its 66.8 Pa sits in the single 18 mm inlet cell,
where a uniform inlet profile meets a micrometre wall layer. Over the rest of the channel the two
channels lose 30.6 and 33.4 Pa — nearly the same, as the physics requires. It is a coarse-grid
inlet artefact, and why NX 60 cannot be the final level.

## Result at NX 60 — the constant-Nu closure is the model-form error

| | 3-D conjugate | GRAIL-CHT, Nu 4.6 | GRAIL-CHT, Nu 4.088 | GRAIL-CHT, Nu 2.9238 (campaign) |
|---|---|---|---|---|
| η alternating | 0.42212 | 0.42249 | 0.42754 | 0.44059 |
| η co-current | 0.51484 | 0.51565 | 0.51439 | 0.50993 |
| **Δη** | **−18.01 %** | **−18.07 %** | −16.89 % | −13.60 % |
| std alternating (K) | 5.2543 | 5.2286 | 4.8801 | 3.9035 |
| std co-current (K) | 5.7713 | 5.7398 | 5.7001 | 5.5612 |
| **Δ std** | **−8.96 %** | **−8.91 %** | −14.39 % | −29.81 % |
| Δ mean plate T | +10.29 K | +10.36 K | +9.66 K | +7.71 K |

With the conjugate Nu the reduced-order model reproduces the 3-D solution to 0.2 % on efficiency,
0.5 % on plate std, and **0.1 pp on the arrangement difference**. Its STRUCTURE is validated;
its Nu INPUT was wrong.

## Why the campaign's Nu was wrong

The campaign closure (2.9238) is the Richardson extrapolation of the single-channel fluid-only 3-D
study, which imposed a heat flux UNIFORM AROUND THE PERIMETER as well as along the axis: the H2
condition, by definition. In the real absorber, 1 mm of aluminium at 229 W/m·K makes the wall
nearly isothermal around the perimeter: the H1 condition. For non-circular ducts H1 exceeds H2
because a uniform peripheral flux creates corner hot spots.

Measured conjugate Nu (co-current, NX 60): 4.6 flat along the channel, both channels.
Reference, verified: fully developed laminar Nu for a semicircular duct under constant axial
gradient with peripherally uniform wall temperature (H1) = **4.088184**
(Erdoğan & Imrak, Mathematical and Computational Applications, 2005), and independently **4.089** in the Shah & London / Kakaç et al. table reproduced in Hesselgreaves, *Compact Heat Exchangers* (2001), Table 5.1.
The H2 value for a semicircular duct is RECALLED as ≈ 2.92 (Shah & London 1978) and is NOT yet
verified from the source; no conclusion here depends on it.

## The mechanism behind the efficiency penalty — measured

Heat budget per channel, alternating, NX 60 (the decomposition is an identity by construction;
the independent check is the global balance above):

| | co-current | alternating |
|---|---|---|
| heat absorbed by the fluid | 18.12 W | **24.80 W** |
| heat handed BACK to the plate | 0 | **9.94 W (40.1 %)** |
| channel length over which the fluid loses heat | 0 % | **41 %** |
| peak bulk temperature | 320.8 K (at outlet) | **328.6 K (mid-channel)** |
| outlet bulk temperature | 320.87 K | **317.11 K** |

Two counter-flowing channels on a highly conductive plate are a counter-flow heat exchanger
through the metal. Each channel's hot downstream fluid heats the plate, and that heat conducts
into the neighbour's cold inlet. Heat that should leave with the outlet is recirculated upstream.
This one mechanism accounts for the higher mean plate temperature, the lower outlet temperature,
the efficiency penalty, and the large lateral bridge conduction.

Local Nu in the alternating channel passes through a 0/0 singularity (Nu ≈ 47 at ξ ≈ 0.61) where
q′ and T_w − T_b change sign together. It is not physical: the definition of Nu breaks down
there. h itself stays near 4 – 5 on both sides, which is why one correct constant still
reproduces the 3-D result.

## Status

NX 60 is coarse (18 mm axial cells). Grid study NX 60 / 120 / 240 at constant ratio 2 is running;
nothing above is final until it closes.

---

## Update — NX 120, and grid convergence on BOTH sides

### 3-D conjugate, NX 120 (NU 64), converged
Co-current identical to 7 digits over iterations 4000 / 4400 / 4600. Alternating drifting
geometrically (ratio ~0.7 per 200 iterations); extrapolated remaining change ~5e-5 on eta and
~9e-4 K on std (~0.01 %), recorded as iteration uncertainty. A residual period-2 flip of 1.4e-4 K
amplitude in the solid minimum is negligible.

A limit cycle was found and removed during this run: fluid-energy relaxation 1.0 with the
nonlinear `limitedLinear` scheme produced a period-2 oscillation (fluid minimum flipping 300.000 /
299.334 K, below the inlet temperature). Damping the fluid energy to 0.8 removed it; the steady
answer does not depend on relaxation. The NX 60 cases were checked iteration by iteration and
showed no oscillation, so they were not aliased by the even-numbered snapshot comparison.

| Δ (alternating − co-current) | 3-D NX 60 | 3-D NX 120 |
|---|---|---|
| efficiency | −18.01 % | −18.96 % |
| plate std | −8.96 % | **−4.88 %** |
| plate spread (max − min) | −2.52 % | **+3.40 %** |
| mean plate T | +10.29 K | +10.87 K |

Conjugate Nu, developed region (15 – 85 % of length), co-current: 4.602 / 4.584 (NX 60) →
4.614 / 4.591 (NX 120). Axially converged to +0.2 %. The cross-section refinement is what can
move Nu; that study (NU 48 / 64 / 96) is queued.

### GRAIL-CHT's own plate grid — also not converged axially
Nu = 4.6, CAD taper, benchmark conditions:

| plate grid | Δ std | Δ eta |
|---|---|---|
| 110 × 40 | −10.51 % | −17.72 % |
| 220 × 80 | −8.91 % | −18.07 % |
| 440 × 80 | −8.12 % | −18.23 % |
| 440 × 160 | −8.11 % | −18.23 % |

Lateral resolution has no effect; axial resolution does, at observed order p = 1.01 — exactly the
formal order of the reduced-order model's implicit first-order axial fluid march. Richardson
extrapolation gives Δ std ≈ −7.3 %. **The production campaign ran at 110 axial cells**, where the
axial error alone overstates the uniformity benefit by about 3 pp.

### GRAIL-CHT with the 3-D conjugate Nu(ξ) profile
Profile from NX 120 co-current (first slab 5.02, developed 4.60, last 4.74), applied along each
channel's own flow direction: Δ std −8.22 %, Δ eta −18.11 % (220 × 80). Barely different from
the constant — the co-current conjugate profile is nearly flat, so the NX 120 difference between
the models is NOT an entrance-profile effect.

### What must be compared
Both models carry axial discretisation error. The fair comparison is extrapolated against
extrapolated. NX 240 (queued) fixes the 3-D observed order.

---

## Update — NX 240 closes the 3-D axial study; both models extrapolated

### 3-D conjugate, NU 64, axial ratio 2 (all converged by the auto_stop criterion except NX 60/120, judged earlier)
| | NX 60 | NX 120 | NX 240 |
|---|---|---|---|
| η co / alt | 0.51484 / 0.42212 | 0.51597 / 0.41817 | 0.51594 / 0.41840 |
| std co / alt (K) | 5.7713 / 5.2543 | 5.7907 / 5.5083 | 5.7842 / 5.4737 |
| **Δη** | −18.01 % | −18.95 % | **−18.91 %** |
| **Δ std** | −8.96 % | −4.88 % | **−5.37 %** |
| Δ spread | −2.52 % | +3.40 % | +3.07 % |
| Δ mean T | +10.29 K | +10.87 K | +10.82 K |
| balance co / alt | 0.005 / 0.035 % | — | 0.006 / 0.049 % |

Δη is converged (NX 120 → 240: 0.04 pp). Δ std converges OSCILLATORILY (−8.96 → −4.88 → −5.37),
so Richardson extrapolation is not applicable. Reported as −5.4 %, with the NX 120/240 change
(0.5 pp) as the discretisation estimate and, conservatively, half the three-level range (2.0 pp)
as the bound. The NX 60 agreement with the ROM (−8.96 vs −8.91 %) was therefore a coincidence of
two coarse grids and is withdrawn as evidence.

The alternating NX 240 balance (0.049 %) sits just inside the 0.05 % auto_stop limit; its trend
was geometric toward ≈0.05 %. It is well inside the campaign's 0.5 % gate.

### GRAIL-CHT, Nu 4.6, design point, axial 220 / 440 / 880 (p = 1, extrapolated)
| | co | alt | Δ |
|---|---|---|---|
| η, extrapolated | 0.51598 | 0.42101 | −18.40 % |
| std, extrapolated (K) | 5.7506 | 5.3289 | −7.33 % |
| mean T (K) | 312.94 | 323.50 | +10.56 K |

### Residual model-form difference (both sides grid-converged)
| | 3-D NX 240 | ROM extrapolated | ROM error |
|---|---|---|---|
| co η / std | 0.51594 / 5.7842 | 0.51598 / 5.7506 | +0.01 % / −0.6 % |
| alt η / std | 0.41840 / 5.4737 | 0.42101 / 5.3289 | +0.6 % / −2.6 % |
| Δη | −18.91 % | −18.40 % | 0.5 pp |
| Δ std | −5.37 % | −7.33 % | **2.0 pp (ROM overstates the uniformity benefit)** |

Co-current is reproduced to within the grid uncertainty. The alternating arrangement keeps a
2 pp model-form error on Δ std: a constant Nu cannot represent the alternating channel, whose
local Nu is undefined where q′ changes sign (the 0/0 point above). This is carried into the
uncertainty budget. It is NOT tuned away.

## Nu envelope, co-current, NU 64 / NX 120
| flow per channel | 3-D η / std / mean | ROM (Nu 4.6, 440) η / std / mean | 3-D Nu, developed |
|---|---|---|---|
| 8.333e-5 kg/s (1.0 g/s total) | 0.39957 / 10.673 / 325.875 | 0.39974 / 10.667 / 325.869 | 4.60 / 4.59 |
| 2.077e-4 kg/s (design) | 0.51597 / 5.7907 / 312.937 | 0.51582 / 5.7452 / 312.956 | 4.61 / 4.59 |

Nu is flow-independent over the range, as fully developed laminar flow requires.
4.5 g/s: pending.

## Cross-section study of the conjugate Nu (co-current, NX 120, design flow)
Developed region (15–85 % of length), mean of the two channels:

| level | fluid cells | Nu ch-a / ch-b | mean | 3-D η | 3-D std (K) |
|---|---|---|---|---|---|
| NU 48 / NR 4 | 80,640 | 4.658 / 4.633 | 4.6455 | 0.516051 | 5.7921 |
| NU 64 / NR 5 | 138,240 | 4.614 / 4.590 | 4.6022 | 0.515968 | 5.7907 |
| NU 96 / NR 8 | 322,560 | 4.567 / 4.545 | 4.5557 | 0.515865 | 5.7888 |

Grid measure h ∝ (cross-section cells)^-1/2 (axial fixed): r21 = 1.528, r32 = 1.309. Celik
iteration: observed order p = 1.12, **extrapolated Nu = 4.48**, GCI_fine = 2.1 %.
Plate-level outputs are already cross-section converged (η changes 1e-4, std 0.03 %); only the
extracted Nu moves. Nu is also axially converged (NX 60/120/240: 4.592 / 4.602 / 4.602) and
flow-independent (1.0 g/s: 4.599).

DECISION (recorded, not tuned): Rev 4 uses **Nu = 4.48**, the grid-extrapolated conjugate value,
uncertainty band 4.46 – 4.65 (NU 96 value ± GCI). Chosen before any Rev 4 row was seen.

## Rev 4 plate-grid decision
The ROM is first-order axially with p = 1.01 already from 110 cells (110/220/440 differences
1.60 / 0.79 pp). A full campaign at 880 cells would take ~27 CPU-h. Rev 4 is therefore run at
plate NX 110 AND 220, and every row carries the Richardson value 2·f(220) − f(110) as well as
both raw values. Nothing is replaced: all three are published.

## Nu envelope — completed (co-current, NU 64 / NX 120)
| total flow | 3-D η / std (K) | ROM Nu 4.6 const, 440 | ROM with 3-D Nu(ξ), 440 | 3-D Nu entry / developed |
|---|---|---|---|---|
| 1.0 g/s | 0.39957 / 10.673 | 0.39974 / 10.667 | 0.39971 / 10.666 | 4.30–4.45 / 4.60 |
| design 2.49 g/s | 0.51597 / 5.7907 | 0.51582 / 5.7452 | 0.51583 / 5.7612 | 5.0 / 4.60 |
| 4.5 g/s | 0.55855 / 3.5376 | 0.5582 / 3.464 | 0.55835 / 3.5046 | 6.1–6.35 / 4.60 |

The developed Nu is flow-independent. The thermal-entry region grows with flow; at the top of the
envelope a constant Nu understates the co-current plate std by 2.1 %, the entry profile halves
that to 0.9 %. η is within 0.1 % everywhere. Carried into the uncertainty budget as a
flow-dependent closure error (≤ 2.1 % on std, ≤ 0.1 % on η), NOT corrected in Rev 4 (the
campaign closure stays a single constant, as in Rev 1–3, so revisions stay comparable).

Also: alternating NU 48 converged: η 0.417861, std 5.5263 (NU 64: 0.418167, 5.5083).

## Cross-section study of the ARRANGEMENT difference (3-D, NX 120; alt NU 96 converged at 6500)
| level | η alt / co | std alt / co (K) | Δη | Δ std | Δ spread | Δ mean |
|---|---|---|---|---|---|---|
| NU 48 / NR 4 | 0.41786 / 0.51605 | 5.5263 / 5.7921 | −19.03 % | −4.59 % | +3.42 % | +10.90 K |
| NU 64 / NR 5 | 0.41817 / 0.51597 | 5.5083 / 5.7907 | −18.95 % | −4.88 % | +3.40 % | +10.87 K |
| NU 96 / NR 8 | 0.41849 / 0.51586 | 5.4810 / 5.7888 | −18.88 % | −5.32 % | +3.20 % | +10.81 K |

Δη converges (p = 1.7, extrapolated −18.8 %). Δ std changes monotonically but NOT in the
asymptotic range (Celik p = 0.11; the extrapolation is meaningless and is not used). Its
movement tracks the extracted Nu (4.646 → 4.602 → 4.556): the ROM's sensitivity is
dΔstd/dNu ≈ 10.6 pp per unit Nu (Nu 4.6 → 4.48 moves the ROM from −7.33 to −8.60 %).

**3-D best estimate of Δ std at design flow**: NU 96 / NX 120 value −5.32 %, plus the axial
correction measured at NU 64 (NX 120 → 240: −0.49 pp), plus the cross-section Nu extrapolation
(4.556 → 4.48, ≈ −0.8 pp by the sensitivity above) = **≈ −6.6 %, uncertainty ±1.0 pp**
(the sum of the two correction magnitudes, treated as a bound, not a standard deviation).
Δη = −18.9 ± 0.1 %. Δ spread = +3.1 ± 0.3 % (the alternating plate's max–min is LARGER).

**ROM (Rev 4 closure Nu 4.48, axially extrapolated)**: Δη −18.13 %, Δ std −8.60 %.
Like-for-like model-form gap (both at the NU 64 Nu ≈ 4.60, both axially converged): Δ std
−7.33 % vs −5.37 % → **the ROM overstates the alternating uniformity benefit by ≈ 2.0 pp and
understates the efficiency penalty by ≈ 0.5 pp**. These are applied as model-form uncertainty on
every Rev 4 arrangement comparison. They are not subtracted from the rows.
