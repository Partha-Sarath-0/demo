# GRAIL CFD — Domain equivalence. CR-03 closed.

## The question

CR-03 recorded an argument, not a measurement: that a plain symmetry plane is invalid under
alternating flow, because neighbours across a bridge run in opposite directions, so the field
is glide-symmetric rather than mirror-symmetric, and an adiabatic plane on a bridge midline
would corrupt exactly the lateral conduction the mechanism depends on. This measures it.

## Method

Five domains, identical cell size (dx = 5.0 mm, dy = 2.0 mm) so no grid effect enters the
comparison. Each strip carries its own share of the flow, so per-channel mass flow is identical
across domains and efficiency is divided by the area it was generated over. Co-current is run
as a control: every domain must reproduce the full plate there, because all channels are alike.

Strips are compared against the full plate's **interior** channels, not its edges, since a
strip is meant to stand for an interior slice.

## Result — alternating

| domain | efficiency | Δη vs full plate | Δ plate spread | bridge conduction per midline |
|---|---|---|---|---|
| full 12-channel (reference) | 0.563771 | — | — | **20.234 W** |
| 3ch-adiabatic | 0.571728 | +1.411 % | +12.238 % | 22.206 W (+9.75 %) |
| 3ch-periodic | 0.571728 | +1.411 % | +12.238 % | 22.206 W (+9.75 %) |
| 2ch-adiabatic | 0.566709 | +0.521 % | -7.408 % | 33.729 W (+66.70 %) |
| 2ch-periodic | 0.562036 | -0.308 % | +2.513 % | 19.412 W (-4.06 %) |

## Result — co-current control

Every reduced domain reproduces the full plate **exactly**: Δη = 0.000 %, Δ plate spread =
0.000 %, for all four. That is the expected answer and it confirms the comparison itself is
sound — any deviation seen under alternating flow is physics, not an artefact of the setup.
Bridge conduction is 0.000 W on the full plate and on both 2-channel domains, and 1.050 W on
the 3-channel ones, which is the same cell-alignment sampling artefact documented in the
uncertainty record, not a physical flux.

## Verdict

**CR-03 was correct, and the effect is large.**

1. **An adiabatic symmetry plane is not admissible.** The 2-channel adiabatic domain inflates
   lateral bridge conduction by **+66.70 %** (33.729 W against 20.234 W) and understates the
   plate spread by 7.41 %. It gets the mechanism badly wrong in both directions at once.

2. **Three channels cannot work at all, under either boundary condition.** The 3-channel
   adiabatic and periodic results are *identical to every digit* — η 0.571728, spread 6.5391,
   bridge 22.206 W. That is not a coincidence: the glide period is TWO channels, so an odd
   channel count cannot carry it and the periodic wrap pairs two channels flowing the same
   way, adding nothing. Both 3-channel domains sit +12.24 % high on plate spread.

3. **The 2-channel PERIODIC domain is valid.** Δη **-0.308 %**, Δ plate spread **+2.513 %**,
   bridge conduction **-4.06 %**. Two channels is exactly one glide period, and periodicity is
   the boundary condition that carries it.

## What this changes

Nothing in the reported results, because the campaign, the mechanism study and every figure
were run on the **full 12-channel plate**, which needs no symmetry assumption. The finding is
forward-looking: any future reduced-domain work — a 3-D conjugate run, a mesh-refinement study
on a strip, an optimisation loop — must use the 2-channel periodic domain. The 3-channel strip
built earlier in this project (`02_geometry/strip_3ch.step`) is **not** a valid alternating
domain and must not be used as one. It remains valid for co-current work.

CR-03 moves from *open* to *closed, confirmed*.

