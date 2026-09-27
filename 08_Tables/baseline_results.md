# GRAIL CFD — Stage 3 results: flow + energy verification, channel CH05

**Solver** OpenFOAM v1912 `simpleFoam` (laminar, SIMPLEC) then `scalarTransportFoam`
**Mesh** structured O-grid, 105,600 hexahedra (100 % hex), `checkMesh` = Mesh OK
**Domain** single channel CH05, x −550 … +550 mm, geometry from the verified CAD NURBS
**Operating point** mdot_total 0.0025 kg/s → mdot_channel 2.0833e-04 kg/s, T_in 300 K
**Wall flux** G_T 800 × tau_glz_sys 0.833 × tau_TIM 0.82 × alpha 0.95 = 519.13 W/m² absorbed
→ 22.8415 W per channel over the 40 × 1100 mm plate strip → **1264.07 W/m²** on the channel wall

## Convergence
| Level | Criterion | Achieved |
|---|---|---|
| Numerical | p, U residuals | p 2.3e-08, Ux 5.6e-08, Uy 1.9e-07, T 4.6e-05 |
| Physical — mass | sum(phi) in + out | **2.18e-16 m³/s (0.0000 %)** |
| Physical — energy | Q_u vs Q_imposed | 22.7962 W vs 22.8415 W → **−0.198 %** |

## Hydraulic results
| Quantity | CFD | Reference | Deviation |
|---|---|---|---|
| Pressure drop dP | **35.31 Pa** | 33.31 Pa (laminar, f·Re = 16) | +6.0 % |
| Pumping power | 7.3778e-06 W | — | — |
| Peak velocity | 52.86 mm/s | — | — |
| Outlet bulk velocity | 31.81 mm/s (section mean) | 26.38 mm/s (mdot/rho·A) | — |
| **Peak / bulk ratio** | **2.01** | 2.0, laminar duct | **+0.5 %** |

The +6 % on dP has the right sign: the reference uses the circular-duct f·Re = 16, while a
lenticular section with a 0.5 mm root fillet runs higher, and the flow accelerates 4.8× through
the convergence.

## Thermal results
| Quantity | Value |
|---|---|
| T_out, flux-weighted bulk | 326.1775 K (53.03 °C) |
| dT | **26.1775 K** vs analytic Q/(m·cp) = 26.230 K → **−0.200 %** |
| Wall-adjacent T | 300.21 min / 316.57 mean / 328.84 max K |
| Q_u | 22.7962 W |

## Section-by-section, at xi from the channel's OWN local inlet
| xi | x (mm) | A (mm²) | u_max (mm/s) | u_mean | p (Pa) | T_mean (°C) | T_max (°C) |
|---|---|---|---|---|---|---|---|
| 0.00 | −550 | 27.975 | 6.557 | 4.458 | 35.593 | 26.922 | 27.376 |
| 0.10 | −440 | 25.408 | 16.678 | 9.506 | 34.000 | 30.649 | 35.079 |
| 0.25 | −275 | 21.787 | 19.423 | 11.178 | 32.164 | 35.351 | 39.905 |
| 0.50 | 0 | 16.373 | 25.742 | 15.094 | 27.393 | 42.262 | 46.255 |
| 0.75 | +275 | 11.736 | 35.730 | 21.250 | 18.514 | 48.182 | 51.501 |
| 0.90 | +440 | 9.325 | 44.814 | 26.833 | 9.214 | 51.258 | 54.141 |
| 1.00 | +550 | 7.872 | 52.857 | 31.814 | 0.285 | 53.099 | 55.686 |

Two physical signatures worth noting, both correct:
1. **Entrance development.** At xi = 0 the peak is 6.56 mm/s against a mean of 4.46 — the imposed
   uniform inlet profile has not yet developed. By xi = 0.10 the peak/mean ratio has reached the
   laminar value and holds to the outlet.
2. **Concave temperature rise.** dT(xi) lies above the straight line Q·xi/(m·cp). The wall flux is
   uniform but the wetted perimeter falls from 21.59 to 11.29 mm, so more heat enters per unit
   length upstream. The curvature is a direct consequence of the convergence, not a numerical artefact.

## Two Reynolds definitions — both reported
The brief specifies Re = 4·mdot/(pi·Dh·mu), which is the **circular-duct** form. It equals the
physical duct Reynolds number rho·u·Dh/mu only when A = pi·Dh²/4, which this section does not satisfy.

| | A actual | pi·Dh²/4 | ratio |
|---|---|---|---|
| inlet | 28.057 mm² | 21.229 mm² | 1.322 |
| outlet | 7.921 mm² | 6.188 mm² | 1.280 |

| mdot_total | Re brief, inlet → outlet | Re physical, inlet → outlet |
|---|---|---|
| 0.0010 | 23.87 → 44.21 | 18.06 → 34.54 |
| 0.0025 | 59.67 → 110.53 | 45.15 → 86.34 |
| 0.0045 | 107.41 → 198.95 | 81.27 → 155.41 |

Deeply laminar under either definition, so no turbulence model — but any f·Re or Nu correlation
must state which one it uses or it is wrong by about 30 %.

## Scope of this stage
This is the **flow + energy verification** rung of the staged ladder: fluid-only, with the absorbed
solar flux imposed on the channel wall. It verifies geometry, mesh, hydraulics and energy transport
before conjugate physics is switched on.

It is **not** conjugate heat transfer. There is no solid region, therefore no bridge conduction, no
lateral transfer between neighbouring channels, and no alternating-flow mechanism. Nothing here
speaks to the central hypothesis yet.
