# GRAIL — 3-D conduction in the metal: does the plate solver's fin treatment hold?

This closes, by a different route, the question the conjugate OpenFOAM run was meant to answer
and did not (`cht_attempt_record.md`).

## The question

The 2-D plate solver makes three assumptions about the absorber metal, and nothing in the
study so far tested any of them directly:

1. the metal is at **one temperature through its thickness** at each (x, y)
2. lateral conduction into the bond land follows the **Hottel-Whillier-Bliss straight-fin
   formula** on a flat fin of thickness t_lower + t_upper
3. the absorber's effective temperature is the **fin-average**

## The method

A full 2-D finite-element conduction solution in the **as-built roll-bond cross-section**,
over one glide period — two pitches, cyclic in y, because a glide period is two channels
(CR-03) — at five stations along the plate, for both arrangements.

The geometry is the real section: the channel wall taken straight off the CAD NURBS, the
lower sheet flat at 1 mm, and the upper sheet as the 1 mm outward offset of the dome merged
into the flat land by taking the **upper envelope** of the two. The envelope is what makes
this tractable where the structured conjugate mesh was not: a 1 mm sheet cannot be offset
across the 0.5 mm concave corner fillet without the offset surface crossing itself, and the
envelope resolves that crossing the way the metal itself does, by filling the corner.

Every boundary condition is taken from the plate solver's own converged design-point
solution, so the two are comparable term by term:

| boundary | condition |
|---|---|
| top | q" − U_top (T − T_amb), both **per unit aperture**, scaled by the surface's dy/ds, because the glazing and TIM above are flat |
| bottom | −h_rear (T − T_amb), flat, unscaled |
| channel wall | −h_f (T − T_f) per unit **wetted** area, h_f = Nu·k_w/D_h(ξ), Nu = 2.9238 (grid-extrapolated) |
| sides | cyclic, period 80 mm |

`05_validation/section_conduction.py`; results in `section_conduction.json`, figure S1.

## Correctness checks before any result is read off it

| check | result |
|---|---|
| **energy balance** at every station | top + bottom + both channels = **exactly 0.000 W/mm** |
| metal area, length mean over 26 stations | 166.72 mm² against the CAD's 170.69 mm² for two pitches, **−2.33 %** |
| grid: area-mean temperature | 333.011591 → 333.011592 → 333.011628 K over three mesh sizes |

The −2.33 % is the same corner-fillet deficit the structured mesh showed (−2.2 %), from the
same cause, and it is conservative in the same direction: less metal at the corner means less
lateral conduction, which understates the alternating-flow benefit.

**One limitation stated plainly.** The through-thickness difference is *not* grid-converged.
The two coarser meshes give 0.0420 K and the finest gives 0.0540 K — a 29 % change — because
the boundary polygon, not the size field, sets the element count until the finest level, so
this is really a two-level check. The quantity is resolved to about 30 %, and the conclusion
below survives that because even the largest value is three orders of magnitude below the
driving temperature difference.

## What it found

### 1. The metal is isothermal through its thickness

Top surface minus channel wall, across all ten cases: **0.021 to 0.057 K**, on a plate that
runs 22 to 35 K above ambient. The lumped-thickness assumption is good to about 0.2 % of the
driving temperature difference. **Assumption 1 holds.**

### 2. The plate solver's absorber temperature is right to half a kelvin

Area-weighted mean of this solution minus the plate solver's Tp at the same station:

| ξ along channel a | co-current | alternating |
|---|---|---|
| 0.10 | −0.284 K | −0.435 K |
| 0.30 | −0.336 K | +0.127 K |
| 0.50 | −0.257 K | +0.210 K |
| 0.70 | −0.169 K | +0.127 K |
| 0.90 | −0.165 K | −0.435 K |

Worst case 0.44 K out of a 22–35 K rise, about 1.5 %. **Assumptions 2 and 3 hold**, which is
also consistent with the Hottel-Whillier-Bliss check's fin efficiency of 0.9995.

### 3. The co-current lateral bridge is zero — confirmed by an independent solver

Under co-current flow the two neighbouring channels are at the **same** temperature at every
station (ΔT_f = 0.000 K), and the heat crossing the bridge midline reads −0.00012 to
+0.00013 W/mm, which is round-off. This is CR-12 confirmed from a completely separate
discretisation: co-current bridge conduction is **exactly zero by symmetry**, not merely
small, and must never be quoted as the denominator of a ratio.

### 4. The mechanism, measured directly

Under alternating flow the neighbours differ, antisymmetrically about mid-plate as glide
symmetry requires, and the bridge carries heat in proportion:

| ξ along channel a | T_f(a) − T_f(b) | heat across the bridge midline |
|---|---|---|
| 0.10 | −15.21 K | −0.0244 W/mm |
| 0.30 | −7.23 K | −0.0117 W/mm |
| 0.50 | −0.08 K | −0.00014 W/mm |
| 0.70 | +7.23 K | +0.0116 W/mm |
| 0.90 | +15.21 K | +0.0240 W/mm |

Two things worth stating.

**The magnitude agrees independently with the campaign.** The length-average of the
alternating bridge flux is 0.0144 W/mm; over 1100 mm and 11 midlines that is **174 W for the
plate**, against the Rev 2 campaign's 154 W and Rev 1's 171 W. Three separate models,
same number to about 13 %.

**The metal does the smoothing, and by a factor of about 7.5.** At ξ = 0.10 the two fluid
streams differ by 15.2 K; the metal between them varies by only **2.01 K** peak to peak. That
is the alternating-flow mechanism, resolved in the real cross-section rather than inferred.

## Verdict

The plate solver's treatment of the metal is verified. Its absorber temperature is right to
half a kelvin, its lumped-thickness assumption is right to 0.06 K, and its lateral bridge
magnitude is confirmed by an independent discretisation to within 13 %.

The model-form question that remains open is **not** about the metal. It is about the fluid:
collapsing Nu(ξ) to one constant is worth 14 percentage points on the uniformity difference
(CR-16), and nothing here touches that.
