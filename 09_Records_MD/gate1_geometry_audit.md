# Gate 1 — Geometry audit (STEP as received)

Source: `Grail_Collector 2.step`, 6,384,030 bytes, md5 `e3ca020c159abf017138feabe8811e05`,
exported from Fusion by the user, ST-DEVELOPER v20.2 / Autodesk Translation Framework v15.15.0.0,
schema AUTOMOTIVE_DESIGN (AP214).

## High-level CAD sanity check
| Quantity | Brief states | Measured in this STEP | Verdict |
|---|---|---|---|
| Solids | ~129 | **129** | PASS |
| Closed shells | 129 | **129** | PASS |
| Faces | ~1297 | **1291** | PASS (differs by 6; the file post-dates the manifold regrouping) |
| Bounding box | ~1270 × 636 × 148.018 mm | **1270.000 × 636.000 × 148.000** | PASS |
| Cylindrical surfaces | — | 263 | — |
| B-spline surfaces | — | 96 (the lofted channels) | — |

## What the STEP does and does not contain
Present: all 12 channel fluid voids, both absorber sheets, frame, glazing, TIM, PCM tray,
insulation, backsheet, seals, sensing, mounting.

Absent — **43 CAD bodies did not translate**, and they share one property: they were hidden in the
Fusion browser. Fusion's STEP export skips hidden bodies.
- `STRIP_SOLID_3CH`, `STRIP2_SOLID_2CH` and their 5 fluid bodies (the CFD strip domains)
- `CFD_ABSORBER_SOLID_MASTER`, both `CFD_FLUID_CIRCUIT_*`
- 4 `MANIFOLD_FLUID_*`, 2 `SEALED_AIR_GAP_*`, `SELECTIVE_COATING_TiNOX`, 14 fastener heads

This is not a loss. The strips were themselves cut from the absorber, and that cut is reproduced
here as an OCC boolean against the same box — exactly the operation Fusion performed — and verified
against the CAD invariants rather than trusted.

One malformed solid: `SELECTIVE_COATING` translates with **volume −111.8 mm³** (negative, inverted
orientation) against a CAD volume of 171.050 mm³. It is a 0.3 µm layer, far below any sane cell
size. It is excluded from the geometry and represented as a **surface radiative property**
(alpha 0.95 / eps 0.04) on the absorber, which is the correct CFD treatment regardless.

## Channel verification — all 12 channels
Pitch 40.000 mm exactly, centres at y = −220 … +220, every channel x ∈ [−550, +550].

**Alternation confirmed from geometry alone**, not from any parameter: the large end face
(28.065 mm²) lies at x = −550 for CH01, 03, 05, 07, 09, 11 and at x = +550 for CH02, 04, 06, 08,
10, 12. Odd and even channels genuinely oppose.

Mirror symmetry about y = 0 is exact: channel pairs (±220), (±180), (±140), (±100), (±60), (±20)
return identical volumes to 3 decimal places.

## Hydraulic profile along the flow direction
Measured on CH05 and CH06 at normalised flow coordinate xi from each channel's **own local inlet**,
so counter-flowing channels are compared correctly. Area at the ends from the solid's own planar end
faces; interior areas from a 0.02 mm slab volume; perimeters from a plane section.

| xi | A (mm²) | P (mm) | Dh (mm) | Dh/Dh_in | law, lambda_G = 1 | deviation |
|---|---|---|---|---|---|---|
| 0.00 | 28.0652 | 21.5865 | 5.20051 | 1.000000 | 1.000000 | — |
| 0.10 | 25.5427 | 20.5539 | 4.97088 | 0.955845 | 0.954034 | +0.190 % |
| 0.25 | 21.9080 | 19.0047 | 4.61106 | 0.886657 | 0.885085 | +0.178 % |
| 0.50 | 16.4824 | 16.4253 | 4.01391 | 0.771830 | 0.770169 | +0.216 % |
| 0.75 | 11.8311 | 13.8520 | 3.41644 | 0.656945 | 0.655254 | +0.258 % |
| 0.90 | 9.4306 | 12.3116 | 3.06397 | 0.589168 | 0.586305 | +0.488 % |
| 1.00 | 7.8630 | 11.2884 | 2.78624 | 0.535763 | 0.540339 | −0.847 % |

CH06 reproduces every station to better than 0.1 % — the two counter-flowing channels are exact
mirrors, as required.

### Findings
1. **The channel genuinely converges** and follows the baseline law Dh(x) = Dh_in[1 − (1 − G)(x/L)^lambda]
   with **lambda_G = 1.0** to within +0.49 % across xi = 0.10–0.90. The linear-in-Dh baseline is
   confirmed against as-built geometry, not merely assumed.
2. **Inlet** Dh = 5.20051 mm against the CAD parameter 5.199685 mm — **+0.016 %**, inside tolerance.
3. **Outlet** Dh = 2.78624 mm against the CAD parameter 2.809592 mm — **−0.84 %, outside the 0.1 %
   tolerance**. The as-translated grading ratio is **0.535763**, not 0.540339.

   Cause: the channel is a B-spline loft (96 B_SPLINE_SURFACE entities) and STEP translation shifts
   the small end, where relative error is largest. The inlet is unaffected.

   This is recorded as **CR-08**. It is not corrected by adjusting geometry — the STEP is what will
   be meshed, so 0.5357 is the physically true value of the object being simulated. Every reported
   result carries the as-meshed value; the CAD parameter 0.5403 is never quoted as a CFD input.
   Effect on outlet Reynolds number and outlet velocity: +0.85 % and +1.7 % respectively relative to
   figures computed from the CAD parameter.
