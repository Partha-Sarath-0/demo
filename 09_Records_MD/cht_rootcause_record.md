# GRAIL — Root cause of the chtMultiRegionSimpleFoam divergence, and the repair

Supersedes the diagnosis in `cht_attempt_record.md`, whose record of what was built and tried
remains correct but whose explanation of WHY was incomplete and, in two places, wrong.

## Corrections to the earlier record

| earlier statement | what the evidence shows |
|---|---|
| "simpleFoam on the **identical** fluid region runs stably" | The simpleFoam case (`fluidonly`) is a **different mesh**: 69,120 cells (NX 60) against the CHT fluid region's 230,400 (NX 200). It is identical to `trial2`'s fluid region, not `trial3`'s. |
| "simpleFoam … runs stably" (from 9 iterations) | The 9 logged iterations showed the continuity error **rising** 0.0037 → 0.0078, which is not evidence of stability. Run to 180 iterations it does converge: continuity 6.5e-9, mass imbalance ~1e-9, dp stationary to 1.3e-6. The conclusion was right; the evidence offered for it was not. |
| "the mesh is not the cause" | Correct, but only now proven — see test 5 below. |

## Controlled experiments

Each test changes one thing. Continuity errors are `sum local` after iterations 1, 2, 3.

| # | test | result | verdict |
|---|---|---|---|
| 1 | `buoyantSimpleFoam` on the CHT **fluid region alone** — no solid, no interface, fixed wall T | 0.0038145324 → 7449.3404 → 8.5569699e+08, **identical to every digit** to the CHT run | conjugate coupling, solid mesh and interface **cleared** |
| 2 | absolute pressure reference 1e5 Pa → 0 | 0.0038151107 → 7449.2846 → 8.554e+08 | precision **rejected** |
| 3 | wall p_rgh fixedFluxPressure → zeroGradient | identical to 10 digits | **rejected**: at a no-slip wall the predicted wall flux is zero, so the two conditions are mathematically the same |
| 4 | locate the blow-up after iteration 1 | worst cells have aspect ratio 19, non-orthogonality 22 °, skewness 0.04; **221,628 of 230,400** cells exceed 1 m/s | bad cells **rejected**: the failure is global |
| 5 | `buoyantSimpleFoam` on the **validated single-channel baseline mesh** (105,600 cells), on which simpleFoam converged for 360 iterations in the GCI study | 0.0027 → 8252 → divergence; same signature | the new CHT mesh **cleared**: the formulation fails on this mesh FAMILY |
| — | earlier record: relaxation, upwind, non-orthogonal correctors, SIMPLEC, inlet BC, axial refinement | no effect | rejected |

Mesh quality does not discriminate either. The validated L3 mesh that simpleFoam converged on
has non-orthogonality 85.76 ° and aspect ratio 905, worse on paper than the CHT fluid mesh
(85.23 °, 882).

## The mechanism the data proves

After iteration 1 of the buoyant solver:

| | simpleFoam (69,120-cell mesh) | buoyantSimpleFoam (230,400-cell mesh) |
|---|---|---|
| max \|Ux\| | 0.098 m/s | 0.0195 m/s |
| max \|Uy\|, \|Uz\| | 0.004, 0.009 m/s | **628, 588 m/s** |
| continuity, sum local | 0.028 | **0.0038** |

(These two columns are on different meshes and are indicative only; the discriminating evidence
is tests 1 and 5, each of which is on a single mesh.)

1. After iteration 1 the buoyant solver's **continuity error is small** — the corrected FACE
   FLUXES satisfy continuity.
2. Yet the **CELL velocities are wrong by ~10^5**, and only in the cross-section plane; the
   axial component is sane.
3. Correct face fluxes with wrong cell velocities locates the fault in the operation that builds
   cell velocity from face fluxes. On cells micrometres thick radially and 5.5 – 18 mm long
   axially, that reconstruction is ill-conditioned in the transverse directions.
4. Iteration 2's momentum equation is driven by those cell velocities, and continuity explodes.

simpleFoam corrects cell velocity with a cell-centred pressure gradient instead, and converges on
the same meshes. The v1912 source could not be retrieved to quote the exact line (the official
repository refuses automated access), so the reconstruction is stated as CONSISTENT WITH the
evidence. Steps 1, 2 and 4 are measured.

## The repair: one-way (frozen-flow) coupling — exact for this benchmark

The benchmark fluid has constant rho, mu, k and cp (`rhoConst`, `const` transport). Momentum and
continuity then contain no temperature, so the steady velocity field is independent of the
energy solution. Solving the flow with simpleFoam and then the conjugate energy on that frozen
flow is **the same steady solution** as a fully coupled solve. It never calls the failing step.

It is NOT valid with temperature-dependent properties, and is documented as such in
`tools/cht_frozen.py`.

Verified before use, not assumed:

| check | result |
|---|---|
| `frozenFlow` present in the installed v1912 binary | yes (string search of `/usr/bin/chtMultiRegionSimpleFoam`) |
| frozenFlow honoured | 0 pressure solves, 0 momentum solves; energy solved in fluid and solid |
| supplied mass flux used, not rebuilt from U | written vs supplied phi: max diff 5e-14 against max 3.3e-6 (1.5e-8 relative, write precision), unchanged across iterations |
| flow mesh = CHT fluid mesh | points, faces, owner, neighbour identical (`fluidonly` = `trial2` fluid) |

## A second error found in the old case: solar input over-applied by 12.2 %

The `solid_top` patch follows the domed upper sheet. Its area on the 2-channel strip is
**0.098723 m²**; the plan area is **0.088000 m²**. The old case applied q″ = 519.13 W/m² per
unit of CURVED area — 51.25 W instead of 45.68 W. Sunlight is intercepted per unit plan area and
the TIM and glazing sit parallel to the plate, so each face now carries h = U_top · n_z.
Σ n_z dA = **0.088000 m² exactly**, asserted equal to the flat bottom area in the builder.

## A third: the 3-D mass flow is 0.30 % below nominal

At NU = 64 the meshed inlet area is 27.9726 mm² against the CAD's 28.0569 mm² (polygonal
approximation of the curved section). The fixed-velocity inlet therefore carries
2.077072e-4 kg/s, not 2.083333e-4. The reduced-order side of the benchmark is run at the 3-D
case's ACTUAL flow, so the two models solve the same problem.

## An operator error during this work, recorded

A cleanup command built around a command substitution returned empty and deleted the entire
converged alternating flow case (`diag_sf`). No other case, dataset or record was affected. The
flow was re-run from its unchanged boundary conditions. Deletes are now explicit and guarded.

## A capability error during the grid study, recorded

The benchmark queue passed `-fields '(T)'` to `mapFields` to seed the NX 240 conjugate cases with
the NX 120 temperature field. **v1912 `mapFields` has no `-fields` option** ("Invalid option:
-fields"). Only `-sourceRegion`, `-targetRegion`, `-sourceTime`, `-consistent` and `-mapMethod`
had been verified; the rest was assumed, which breaks this project's own rule against using an
unverified OpenFOAM option. It failed safely: nothing was written, the case files were checked
intact (solid_top h list 26,880 = NX 240), and both cases start from a uniform 300 K. The only cost
is iteration count — a steady solution does not depend on its initial guess. Mapping without
`-fields` was deliberately NOT used as a fix, because it would also map U and phi and overwrite the
installed frozen flow.

## Sandbox restart, 03:1x – 03:28 (recorded)
All solvers were killed by a sandbox restart. Lanes were restarted from latestTime (restart-safe
markers). `flow_co_nu48_nr4_nx120` had reached End at 400 before the restart (dp stationary to
1e-6 Pa, mass 2.07707e-4 kg/s both channels) and was accepted. Its CHT case had been built with the
queue's failing `-fields` map, i.e. a cold 300 K start; it was stopped at iteration 0 and seeded
with the NX120/NU64 co-current T via a throw-away copy (T only; U, phi untouched; cold T kept as
`T.coldstart_backup`), exactly as done for NX240. The initial guess does not affect the steady
answer.
