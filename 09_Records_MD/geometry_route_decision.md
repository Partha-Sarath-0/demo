# Geometry route — decision and evidence

## What was attempted first
Direct export of the two CFD strip domains from the live Fusion model:
- `ExportManager.createSTEPExportOptions(path, component)` → reported success, wrote a 3,400-byte file.
- `createSTLExportOptions(body | occurrence-proxy | occurrence)` → `execute()` returned **True** in all
  three variants and **wrote no file at all**.

## Evidence the STEP is empty
```
lines in file        : 109
ADVANCED_FACE count  : 0
MANIFOLD_SOLID_BREP  : 0
```
A valid export of STRIP_SOLID_3CH (21 faces) plus three fluid bodies would contain hundreds of
ADVANCED_FACE entities. The file contains a header and no geometry.

## Cause
Both strip domains are **BaseFeature (non-parametric) bodies**. In this environment Fusion's export
API does not serialise base-feature geometry through the scripted path; it reports success and emits
an empty container. This is a tooling limitation, not a defect in the CAD model — the bodies are
valid, watertight and were verified point-by-point at CAD v16.

## Route adopted
Parametric reconstruction of the CFD geometry directly in gmsh/OpenFOAM from the GRAIL parameter
register, **verified against the CAD-measured invariants** rather than trusted.

The brief permits this explicitly: *"Import or otherwise construct the corrected CAD geometry using a
robust OpenFOAM-compatible route."*

### Why this is the better route here, not merely the available one
The campaign requires geometry to be **regenerated** for bridge width (20–60 mm), root fillet
(0.5–2.0 mm), grading ratio and grading exponent sweeps. A static STEP snapshot cannot be swept; a
parametric generator can. A single exported solid would have forced either a manual re-export per
sweep point or an unacceptable simplification.

### Acceptance criteria — Gate 1 (geometry) must reproduce the CAD to these tolerances
| Invariant | CAD-measured value | Tolerance |
|---|---|---|
| Fluid volume per channel | 18,643.963 mm³ | ≤ 0.25 % |
| Strip solid volume, 3CH | 281,693.638 mm³ | ≤ 0.25 % |
| Strip solid volume, 2CH | 187,817.190 mm³ | ≤ 0.25 % |
| Channel inlet face area | 28.0552 mm² | ≤ 0.25 % |
| Channel outlet face area | 7.9200 mm² | ≤ 0.25 % |
| Inlet hydraulic diameter | 5.199685 mm | ≤ 0.1 % |
| Outlet hydraulic diameter | 2.809592 mm | ≤ 0.1 % |
| Hydraulic grading ratio | 0.540339 | ≤ 0.1 % |
| Channel pitch | 40.000 mm | exact |
| Periodic face area, 2CH | 2200.000000 mm² each | exact |
| Bridge width (as-built) | 31.299046 mm | ≤ 0.1 % |
| Channel length | 1100 mm (x −550…+550) | exact |

Geometry that misses any of these does not proceed to meshing.
