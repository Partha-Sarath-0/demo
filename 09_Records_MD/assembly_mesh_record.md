# GRAIL CFD — Assembly-level mesh record  (figures M6 – M10)

Built on `01_cad/Grail_Collector_2.step` (md5 e3ca020c159abf017138feabe8811e05), the corrected,
converging geometry. Supersedes the assembly renders made on the withdrawn diverging build
(CR-01, CR-05, CR-10).

## 1. Assembly surface mesh

| Route | Solids | Triangles | Area (mm²) |
|---|---|---|---|
| Group A — gmsh 2-D mesher, Plane + Cylinder faces only, 20 mm cap / 2 mm floor | 115 | 193,138 | 15,947,622.2 |
| Group B — direct NURBS evaluation: upper sheet (36 B-spline dome faces) + 12 fluid voids | 13 | 98,406 | 1,394,741.5 |
| Deferred — 4 manifold barrels, direct parametric evaluation (CR-11) | — | 8,000 | 52,875.2 |
| Port-hole correction, computed exactly from the CAD boundary curves | — | — | −813.1 |
| **Total** | **128** of 129 | **299,544** | **17,394,425.8**  = 17.3944 m² |

Envelope 1270.000 × 636.000 × 148.000 mm, exactly the Gate-1 bounding box.

Why two routes: gmsh cannot mesh the 1100 mm B-spline channel walls in reasonable time
(`14_provenance/gate2_mesh_strategy.md`), but it handles the 1111 planar and cylindrical faces of
the enclosure in 46 s. Direct evaluation of a face's own parameterisation lands exactly on the CAD
surface and was verified at Gate 1 to +0.007 % on wall area and −0.0015 % on enclosed volume.

Excluded: `SELECTIVE_COATING` (negative STEP volume, carried as a surface radiative property,
alpha 0.95 / eps 0.04 — CR-03). Note also that 43 bodies hidden in the Fusion browser never
entered the STEP at all; that accounting is in `gate1_geometry_audit.md` and is unchanged.

Tree note: the STEP shows `04_MANIFOLD` nested under `01_GLAZING`, a browser-tree nesting from a
cut/paste in Fusion. Positions, body count and volumes are unaffected (verified: 145 bodies before
and after, no volume change). The figures label it by its own component name, not its parent.

## 2. Full-plate CFD mesh  (`03_mesh/plate/plate12.npz`, built by `03_mesh/plate_mesh.py`)

Fluid: the same O-grid the 3-D OpenFOAM baseline used — NU = 48 perimeter, NR = 8 graded radial
layers (expansion 1.18, clustered at the wall), an 12 × 12 transfinite core, NX = 200 axial
stations over 1100 mm, on all 12 channels.

Solid: the roll-bond sheet pair, three conformal structured blocks per section —
S1 lower sheet slab (z ∈ [−1, 0] across the full 40 mm pitch), S2 upper-sheet shell (1 mm normal
offset of the non-bonded ring), S3 upper-sheet lands (z ∈ [0, 1], shell feet out to the pitch edge,
tracked per station because the feet move inboard as the channel converges).

| Quantity | Value | Check |
|---|---|---|
| Nodes | 2,100,852 | — |
| Fluid hexahedra | 1,267,200 | 105,600 per channel, = the baseline mesh |
| Solid hexahedra | 561,600 | 234 cells per section |
| Cell type | 100 % hexahedral | 0 pyramids, prisms, tets or polyhedra |
| Inverted cells | **0 fluid, 0 solid** | signed volume by centroid decomposition, every cell |
| Re-ordered cells | 633,600 fluid, 280,800 solid | index-grid handedness fix; **no node moved**, so no geometry changed |
| Smallest fluid cell | 7.035e-03 mm³ | positive |
| Meshed fluid volume | 222,948.13 mm³ | CAD 223,727.56 mm³ → **-0.348 %** (chordal; matches the single-channel −0.347 %) |
| Meshed solid volume | 1,142,631 mm³ | CAD sheet pair 1,126,582 mm³ → **+1.42 %** |
| — lower sheet (S1) | 528,000.0 mm³ | CAD `ABSORBER_LOWER_SHEET` 528,000.0 mm³ → **0.000 %** |
| — upper sheet (S2+S3) | 614,631.2 mm³ | CAD `ABSORBER_UPPER_SHEET` 598,581.6 mm³ → **+2.68 %** |

The CAD reference volume is the **h-refined** value 18,643.963 mm³ per channel, not
`gmsh.model.occ.getMass`, which over-integrates this enclosed volume by +0.27 % (CR-09).

### Interfaces
- **Fluid ↔ upper sheet (wetted wall): exactly conformal.** S2's layer 0 is not a copy of the fluid
  ring — it is the same node indices. Gap identically zero by construction.
- **Fluid floor ↔ lower sheet:** the slab's top row shares the floor nodes' y-positions at every
  station and sits at z = 0; the CAD floor surface lies 1.1 µm below z = 0. That residual is the
  CAD surface's own offset, not a meshing error, and is reported on Fig M8 rather than absorbed.

### ENGINEERING_ASSUMPTION — nominal sheet thickness
The solid region is built at a uniform 1.0 mm. The real roll-bond upper sheet thins over the dome:
marching outward along the wall normal (`02_geometry/measure_thickness.py`) gives 0.22 – 1.32 mm,
mean 1.08 – 1.23 mm by station. The uniform-offset model therefore lands +1.42 % on the CAD sheet
pair. This affects the solid region's thermal mass in a 3-D conjugate run; it does **not** affect
any result reported in this study, because the conjugate coupling was solved on the plate-resolved
solver with the sheet thicknesses taken from the CAD volumes directly.

## 3. What the figures assert, and what they do not

M6–M10 are pictures of the actual mesh: every triangle is evaluated on a CAD surface and every
hexahedron is a cell of `plate12.npz`. They do **not** assert that a 3-D conjugate OpenFOAM run has
been executed on this solid region. The 3-D OpenFOAM baseline reported in this study is the
fluid-region flow and thermal solution on one channel; the conjugate coupling is the plate-resolved
solver, verified against the k → 0 and k → ∞ limits. The solid region here is meshed, verified and
ready; that run is listed as outstanding work.
