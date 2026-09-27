# GRAIL CFD — solver-progress videos  (corrected converging geometry)

Two MP4s, 1408 x 792 at 20 fps, 320 frames = 16 s:

| file | arrangement |
|---|---|
| `GRAIL_CFD_solver_counter_current.mp4` | alternating counter-current, f_interdig = 1 |
| `GRAIL_CFD_solver_co_current.mp4` | co-current, f_interdig = 0 |

They replace the superseded video of the same layout, which was made on the withdrawn
diverging build (CR-01). Nothing in it was reusable: its velocity panel showed the section
GROWING with x and its tracers therefore DECELERATED downstream — the opposite of this
collector's behaviour.

## Panel 1 — velocity field, x-z projection

Genuine intermediate states, not a static field with a ticking counter. The verified baseline
case was re-run in `04_baseline/ch05_anim` with `writeInterval 10`, giving 52 snapshots across
the run, and the frames step through them in order.

The re-run is **bit-identical to the baseline**: 518 SIMPLE iterations in both, and the initial
residual of Ux, Uz, p and the continuity error agree at every iteration to
max |Δlog10| = 0. The final snapshot (iteration 518) is the baseline's own converged write, the
one every reported 3-D result came from.

| | |
|---|---|
| Mesh | 105,600 hexahedra, baseline channel at y = −60 mm |
| Cells drawn | 14,000, fixed random sample (seed 20260916) |
| \|U\| range | 0.67 → 51.86 mm/s; colour scale capped at the 99.7th percentile, 47.86 mm/s |
| Section | z_max 3.96 → 2.11 mm and y-span 8.14 → 4.29 mm between inlet and outlet (cell centres) |

The section shrinking left-to-right and the colour warming toward the outlet are the same fact:
mass conservation on a converging duct.

## Panel 2 — solver convergence

Parsed from the OpenFOAM log by `09_post/residuals.py`; every point is an `Initial residual`
OpenFOAM printed. Curves are Ux, Uz, p and the time-step continuity error (`sum local`); for p,
which has two correctors per outer iteration, the last corrector is taken because that is what
SIMPLE converges on. Dashed lines are the case's own `residualControl` values.

Final: Ux 5.3461e-11, Uz 1.0398e-06, p 1.5287e-08, continuity 2.4805e-10 after 518 iterations.

Uz is worth watching: it starts at exactly zero (the initial field is uniform axial) and becomes
finite as the solution develops, because a converging duct forces a wall-normal component. On a
straight duct it would stay at zero.

## Panel 3 — conjugate plate with tracers

Background: the converged plate field from the verified conjugate solver at 220 x 240.

| | alternating | co-current |
|---|---|---|
| efficiency | 0.56377 | 0.59670 |
| mean plate T | 328.00 K | 315.04 K |
| plate T std | 5.928 K | 6.737 K |
| energy balance error | 5.39e-05 % | -1.37e-05 % |

Tracers move at the true local bulk velocity u(x) = ṁ / (ρ A(x)), integrated with four sub-steps
per frame. They are massless markers of the bulk speed, not particle paths: no slip, dispersion
or secondary flow is implied.

Because the section converges, they **accelerate**: 7.448 mm/s at ξ = 0 to
25.547 mm/s at ξ = 1, a factor 3.4302 — which is exactly 1/G² with
G = 0.539935, as it must be for a fixed mass flow through an area that scales with the square of
the section. One transit takes 90.17 s; the clock runs to 100 s, so the video covers a
little more than one full pass.

Panel 3 keeps its own clock. It is tracer time in seconds, not SIMPLE iterations — the solver
panels above are a steady-state iteration count and the two are deliberately labelled apart.

## What these videos do not claim

The velocity panel is the **fluid-region** solution on one channel. The plate panel is the
plate-resolved conjugate solver. Neither is a 3-D conjugate OpenFOAM run over the meshed solid
region; that remains outstanding, along with the PCM transient, thermotropic switching and
view-factor radiation.
