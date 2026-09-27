# Gate 2 — Meshing strategy: decision and evidence

## What was tried and rejected
**snappyHexMesh from STL.** Requires a surface tessellation. gmsh's 2-D mesher could not produce one
in any reasonable time: three attempts at progressively relaxed sizing (min 0.12 → 0.35 mm, curvature
on and off, algorithms 1 / 5 / 6) each ran **> 10 minutes without completing a single surface**, and
one aborted outright with `Impossible to mesh periodic surface`.

Diagnosis (see `02_geometry/diag.py`): the geometry is not the problem — the boolean completes in
**3.3 s** and the cut solid has only **16 faces**. The problem is that each channel wall is a
**single B-spline surface 1100 mm long**:

```
CH05 faces:
  face 1187  Plane            x[ 550.000  550.000]  area =     7.8630
  face 1188  Plane            x[-550.000 -550.000]  area =    28.0652
  face 1189  BSpline surface  x[-550.000  550.000]  area = 18069.7603
```

Its parametric domain is extremely stretched (1100 mm in one direction, ~21 mm of perimeter in the
other), which is pathological for Delaunay meshing in parameter space.

## What the probe found instead
The wall carries a **clean unit parameterisation**, u around the section perimeter and v along the
channel:

```
wall face 1189   param bounds u[0, 1]  v[0, 1]
  varying u  ->  dx = 0.000    dy = 8.4993   dz = 4.1021     (section perimeter, closed loop)
  varying v  ->  dx = 1100.000 dy = 2.0845   dz = 0.0963     (axial)
  200 x 400 = 80,000 surface points evaluated in 0.05 s
```

Direct evaluation is roughly **four orders of magnitude faster** than meshing the same surface, and
it lands exactly on the NURBS rather than on a tessellation of it.

## Route adopted: structured hex mesh by direct surface evaluation
1. Sample the wall on a structured (u, v) grid — u around the section, v along the flow.
2. Build an O-grid inside each section: wall ring → graded radial layers → square core. Gives genuine
   boundary-layer control through radial grading rather than snappy's `addLayers` heuristics.
3. Sweep along v to form hexahedra.
4. Solid region built as conforming H-grid blocks around the channels, sharing the wall nodes exactly.
5. Write `polyMesh` directly, then `splitMeshRegions -cellZones`, `createPatch` for the cyclics.

### Why this is the right choice here, not merely the workable one
| | snappyHexMesh | structured by evaluation |
|---|---|---|
| Geometry fidelity | snapping error on top of the 0.85 % already in CR-08 | exact on the NURBS |
| Cell type | hex-dominant with split/concave cells at the 0.5 mm fillet | pure hex |
| Boundary layers | `addLayers`, frequently fails to reach target in tight fillets | radial grading, deterministic |
| Cells for a given accuracy | high — refinement is octree, so resolving the fillet refines its neighbourhood too | low — resolution placed only where needed |
| Mesh independence study | rerun snappy per level, quality varies between levels | change N; levels are exactly self-similar |
| Campaign regeneration (bridge 20–60 mm, fillet 0.5–2.0 mm, G_ratio, lambda_G) | re-export CAD per point | change parameters |
| Cost on 2 cores | prohibitive | tractable |

The last two rows decide it. The campaign **requires** regenerable geometry, and a pure-hex mesh is
the only way a multi-region CHT campaign fits on two cores without coarsening below the resolution
this problem needs.

## Status
Gate 2 is NOT yet passed. The generator is the next artefact to build, and it must clear the same
kind of acceptance test as Gate 1: the meshed fluid volume must reproduce the OCC volume
(18,693.9 mm³ per channel), the wall area must reproduce 18,069.76 mm², and `checkMesh` must report
no negative-volume cells before any physics runs.
