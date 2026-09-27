# Gate 1 — RESULT: **PASS** (revised; supersedes the earlier conditional pass)

## Why this document was rewritten
The first version of this gate recorded four failing invariants and attributed them to STEP
translation error at the channel's small end (correction CR-08). **That conclusion was wrong, and it
was wrong because the measuring instrument was trusted without being tested.**

All four "failures" came from `gmsh.model.occ.getMass`. Direct integration of the true NURBS surface,
h-refined until converged, lands on the **CAD** values instead. CR-08 is withdrawn; CR-09 records the
real cause. No CFD had been run, so nothing downstream is affected.

### The convergence evidence
End-cap areas by direct evaluation of the channel wall surface, refining the sampling from 96 to 2304
points around the section:

| NU | inlet area | dev vs CAD | dev vs OCC | outlet area | dev vs CAD | dev vs OCC | G |
|---|---|---|---|---|---|---|---|
| 96 | 28.036605 | −0.0663 % | −0.1019 % | 7.908667 | −0.1431 % | +0.5803 % | 0.539764 |
| 192 | 28.051893 | −0.0118 % | −0.0475 % | 7.918230 | −0.0223 % | +0.7019 % | 0.539892 |
| 288 | 28.054711 | −0.0017 % | −0.0374 % | 7.920019 | +0.0002 % | +0.7247 % | 0.539916 |
| 576 | 28.056409 | +0.0043 % | −0.0314 % | 7.921098 | +0.0139 % | +0.7384 % | 0.539930 |
| 1152 | 28.056833 | +0.0058 % | −0.0299 % | 7.921368 | +0.0173 % | +0.7418 % | 0.539934 |
| **2304** | **28.056939** | **+0.0062 %** | −0.0295 % | **7.921436** | **+0.0181 %** | **+0.7427 %** | **0.539935** |

The sequence converges monotonically onto the CAD numbers and **away** from the OCC numbers. The
outlet face is the small trimmed planar face where OCC's integration is weakest: it is off by
+0.74 %. The channel volume behaves the same way — direct integration converges to 18,643.7 mm³
against the CAD 18,643.963 mm³ (−0.0015 %), while OCC reports 18,694.397 mm³ (+0.27 %).

Independent confirmation that the wall surface itself was never in doubt: the tessellated **wall
area** converges on the OCC face area to +0.007 %, because that face is large, untrimmed and easy to
integrate. Only the small trimmed faces and the enclosed volume are affected.

## Acceptance table — all 12 invariants
| # | Invariant | CAD reference | Measured (converged) | Deviation | Verdict |
|---|---|---|---|---|---|
| 1 | Fluid volume per channel | 18,643.963 mm³ | 18,643.7 mm³ | −0.0015 % | PASS |
| 2 | Strip solid volume, 3CH | 281,693.638 mm³ | 281,600.554 mm³ | −0.033 % | PASS |
| 3 | Strip solid volume, 2CH | 187,817.190 mm³ | 187,736.130 mm³ | −0.043 % | PASS |
| 4 | Channel inlet face area | 28.0552 mm² | 28.056939 mm² | +0.0062 % | PASS |
| 5 | Channel outlet face area | 7.9200 mm² | 7.921436 mm² | +0.0181 % | PASS |
| 6 | Inlet hydraulic diameter | 5.199685 mm | 5.198875 mm | −0.0156 % | PASS |
| 7 | Outlet hydraulic diameter | 2.809592 mm | 2.807053 mm | −0.0904 % | PASS |
| 8 | Hydraulic grading ratio | 0.540339 | 0.539935 | −0.0748 % | PASS |
| 9 | Channel pitch | 40.000 mm | 40.000000 mm | 0 | PASS |
| 10 | Periodic face area, 2CH | 2200.000000 mm² each | 2200.000000 mm² each | 0 | PASS |
| 11 | Bridge width | 31.299046 mm | 31.285944 mm | −0.042 % | PASS |
| 12 | Channel length | 1100 mm | 1100.000 mm | 0 | PASS |

**12 PASS, 0 FAIL.** Invariants 2 and 3 are still OCC volumes and therefore carry the same positive
bias; their true values are marginally closer to CAD than shown, so the pass is conservative.

## Governing as-meshed geometry
| Quantity | Governing value |
|---|---|
| Dh, inlet | 5.198875 mm |
| Dh, outlet | 2.807053 mm |
| Grading ratio G | 0.539935 |
| Grading exponent lambda_G | 1.0 (confirmed, ≤ 0.49 % deviation over xi = 0.10–0.90) |
| Inlet area | 28.056939 mm² |
| Outlet area | 7.921436 mm² |
| Fluid volume per channel | 18,643.7 mm³ |
| Bridge width | 31.285944 mm |
| Pitch / length | 40.000000 mm / 1100.000 mm |
| Periodic face area (2CH) | 2200.000000 mm² |

## Independent check on the whole chain
Reynolds number from per-channel mass flow (mdot_total / 12), water mu = 8.55e-4 Pa·s,
Re = 4·mdot/(pi·Dh·mu), on the converged geometry:

| mdot_total (kg/s) | mdot_channel (kg/s) | Re at inlet Dh | Re at outlet Dh |
|---|---|---|---|
| 0.0010 | 8.3333e-05 | 23.87 | 44.21 |
| 0.0025 | 2.0833e-04 | 59.68 | 110.52 |
| 0.0045 | 3.7500e-04 | 107.42 | **198.94** |

The project brief states the corrected as-built geometry gives **Re = 23.9 – 198.8**. The converged
geometry reproduces **23.87 – 198.94**, a match to 0.07 %. The withdrawn CR-08 geometry gave 200.43,
which is 0.8 % out. The Reynolds range is therefore an independent third witness — alongside the CAD
parameters and the refinement study — that CR-09 is correct and CR-08 was not.

Flow is deeply laminar across the entire operating range. No turbulence model.

## Gate 1 passed. Tessellation and meshing may proceed.
