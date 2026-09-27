# GRAIL — 3-D conjugate (fluid + solid) run: what was built, and what did not work

This records an attempt that **did not produce a result**. It is here because the mesh and the
case are on disk and someone will otherwise assume they were used.

## What the run was for

The uncertainty assessment left one item that nothing else could close: the 2-D plate solver
represents the metal as a fin with a lumped through-thickness temperature and represents the
wall-to-fluid coupling by a single Nusselt number. A 3-D conjugate solution on the real
roll-bond cross-section would test both at once. CR-03 made it affordable by establishing
that a 2-channel periodic strip reproduces the full plate (Δη −0.31 %, Δ spread +2.51 %,
Δ bridge −4.06 %), so the domain is about 355k cells rather than the full plate's 1.83M.

## What was built and verified

**Geometry finding that changed the construction.** The channel section's widest point is not
at the sheet interface. Measured on channel y = −20 mm at the inlet station, the extreme-y
node sits at z = 0.447 mm and the wall reaches z = 0 only 0.54 mm further in: the signature of
the r = 0.5 mm fillet where the domed upper sheet blends into the flat lower one. An earlier
note in `03_mesh/cht_solid2.py` said the wall "meets z = 0 at the channel edges"; that was
wrong and is corrected in the file.

**Solid region.** `03_mesh/cht_solid2.py` builds the metal as two structured blocks on shared
y columns. Verified:

| check | result |
|---|---|
| inverted cells | **0** at NU = 64, 96, 192 |
| metal cross-section, length average | 83.29 mm² (NU 96) → 83.33 mm² (NU 192) |
| metal volume vs CAD sheet pair (93,881.8 mm³ per pitch, from the STEP solids) | **−2.2 % as meshed, −3.14 % as a converged continuum integral** |

The −3.14 % is the fillet shoulder at each channel corner, where a 1 mm sheet cannot be
offset across a 0.5 mm concave fillet without the offset surface crossing itself, so the CAD
fills the corner as solid metal and a constant-thickness shell model cannot represent it.
It is bounded, localised within ~1 mm of the corners, and **conservative** for the claim being
tested: less metal at the corner means less lateral conduction, which understates the
alternating-flow benefit rather than inflating it.

The abandoned alternative is also on disk. `03_mesh/cht_solid.py` maps the wall ring onto the
metal's outer outline by arc length; it folds its own cells (measured overlap 47 %, 38 % after
400 Laplace sweeps) because an 8 mm concave floor has to stretch onto a 40 mm flat bottom.
Documented, not used.

**Ring re-parameterisation.** Both regions are built from a corner-pinned ring
(`resample_rings`), because the node nearest the section's widest point drifts with x: at
NU = 96 it is index 44 at the first station and 43 at every other one, and at the changeover
the two candidates differ by 0.9 µm in y while differing by 0.155 mm in z. Splitting at a
per-station argmax gives branches of different lengths (43/55 at most stations, 44/54 at
three) which cannot form a structured block; splitting at one fixed index leaves the branch
doubling back by that 0.9 µm, which inverts one cell per station. Pinning the corner as a node
removes both. The resampling preserves each branch's **original node spacing** — an earlier
version imposed uniform arc length and took checkMesh's fluid skewness from 1.24 on the
validated mesh to 3.34.

**Mesh pipeline, end to end, verified:**

| stage | result |
|---|---|
| `gmshToFoam` | two cellZones, `fluid` and `solid` |
| node weld on the shared land | 427 welded at NX = 60 (= 7 z-levels × 61 stations, exactly as predicted) |
| `createPatch` | `sideA`/`sideB` created as a translational cyclic pair, separation 0.08 m |
| `splitMeshRegions -cellZonesOnly` | fluid 230,400 cells, solid 124,800 cells at NU 64 / NX 200 |
| coupled interface | **25,600 faces = NU × NX × 2, exactly the predicted count** |
| `checkMesh` fluid | max skewness **0.63** (validated baseline: 1.24), non-orthogonality 85.2°, aspect 882 (baseline 670) |
| `checkMesh` solid | max skewness 3.57, non-orthogonality 90.0°, aspect 4546 |

`-cellZones` is wrong here and `-cellZonesOnly` is required: the two channels' fluid volumes
are not connected to each other, so walking connectivity splits the fluid into two regions and
names one of them `domain1`.

Two setup errors were found and fixed during the build, both by reading the mesh rather than
assuming:
* the inlet patches were being assigned from the channel's y sign, which fed **both** channels
  at their narrow end. Adjacent channels converge in opposite directions, so the feed end
  differs between them; it is now read from the mesh (`meta["feed_ends"]`) and asserted to
  differ, since identical feed ends would be co-current, not alternating.
* the two channels' NURBS return x values that differ by ~1.4e-5 mm at the same station, and
  their station lists run in opposite directions. Stations are now snapped to a uniform ladder
  between each channel's own end points, without which the land nodes where the two solid
  blocks abut are not coincident and the weld finds nothing (14 of 427).

## What did not work

`chtMultiRegionSimpleFoam` **diverges on this case and no result was obtained.**

The failure is in the flow solve, not the energy solve, and it is present from the first
iteration:

| iteration | max &#124;U&#124; | p_rgh range | sum local continuity error |
|---|---|---|---|
| 1 | 155 m/s | 1,400 Pa | 0.0022 |
| 2 | 2.0e7 m/s | 35,000 Pa | 2,400 |
| 3 | — | — | 7.3e7 |

The expected mean velocity is 0.00745 m/s and the expected pressure drop is of order 0.03 Pa.

The mesh is not the cause. `simpleFoam` on the **identical** fluid region, same boundary
patches, runs stably: max &#124;U&#124; 0.098 m/s at iteration 1, 0.060 m/s at iteration 2, with
bounded continuity errors. The fluid region is therefore solvable; the compressible
segregated solver on it is not, at least not with any settings tried.

What was tried, and did not fix it:

| change | outcome |
|---|---|
| GAMG → PCG/DIC for p_rgh | pressure solve converges (13 iterations instead of diverging after 1000 GAMG sweeps), divergence unchanged |
| relaxation U 0.9 → 0.2, h 0.7 → 0.1, p_rgh 0.3 → 0.15 | divergence unchanged |
| `linearUpwind` → `upwind` on all convection terms | divergence unchanged |
| non-orthogonal correctors 1 → 3 | divergence unchanged |
| SIMPLEC (`consistent yes`, as in the validated baseline case) | worse: max &#124;U&#124; 1,037 m/s at iteration 1 |
| `fixedFluxPressure` → `zeroGradient` at the inlets | worse |
| axial refinement NX 60 → 200 (aspect ratio 1,876 → 882) | divergence unchanged |

Six dictionary errors were found and fixed along the way by reading what the solver reported,
not by guessing: `g` belongs at the case root and not per region; v1912 reads
`turbulenceProperties` and not `momentumTransport`; `heSolidThermo` requires `0/solid/p`;
`splitMeshRegions` needs a top-level `system/fvSchemes` and `system/fvSolution`; `createPatch`
will not change an existing patch's type, so the gmsh-side patches are named `side0`/`side1`
and the cyclic pair is created from them; and OpenFOAM's parser rejects a leading `+` on a
scalar.

## Status

The mesh and the case are reproducible — `03_mesh/cht_mesh.py`, `06_cht/make_case.py`,
`06_cht/build.sh` — and the mesh passes every geometric check above. **No conjugate result is
reported anywhere in this work**, and nothing in the thesis or the filings rests on one. The
open question the run was meant to close, whether the 2-D solver's fin and single-Nusselt
treatment holds when the metal is resolved in 3-D, remains open and is stated as such in the
uncertainty record.
