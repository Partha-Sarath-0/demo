# GRAIL CFD — Material property database
**Source: Roadmap Rev I, Section 5.3 "Material properties for COMSOL", quoted verbatim.**
Provenance class per the roadmap's own tier system: handbook values for the material class, not a
specific product datasheet. Roadmap verification item V6 requires confirmation against supplier
datasheets before final runs. No value below was invented; blanks are recorded as blanks.

| Material | rho (kg/m³) | cp (J/kg·K) | k (W/m·K) | Other | CFD role |
|---|---|---|---|---|---|
| Water at 300 K | 997 | 4180 | 0.610 | mu = 8.55e-4 Pa·s | fluid region |
| Aluminium AA1050 | 2705 | 900 | 229 | — | absorber sheets, solid region |
| Aluminium 6063-T6 | 2700 | 900 | 201 | — | frame |
| Low-iron solar glass | 2500 | 750 | 1.05 | tau 0.91, eps 0.88 | glazing, radiation surfaces |
| PC honeycomb, homogenised | 85 | 1200 | 0.075 perp / 0.16 para | tau 0.82 | TIM |
| Silica aerogel, granular | 120 | 1000 | 0.020 | tau 0.62 | — |
| TiNOX coating | — | — | boundary condition | **alpha 0.95, eps 0.04** | absorber surface property |
| RT55 + 10 % EG, **solid** | 880 | 2000 | 2.80 | **L = 170 kJ/kg** | PCM |
| RT55 + 10 % EG, **liquid** | 770 | 2200 | 2.40 | **T_m = 51–57 °C** | PCM |
| Graphite interface | 1100 | 710 | 300 para / 5 perp | — | thin resistance layer |
| VIP fumed silica | 190 | 850 | 0.006 | derate 20 % / 25 y | rear insulation |
| Aerogel blanket | 150 | 1000 | 0.015 | — | edge insulation |
| EPDM gasket | 1150 | 2000 | 0.25 | — | seals |

## Notes carried into the CFD setup
1. **PCM transition interval is 6 K** (51 → 57 °C), matching the brief. Apparent-heat-capacity form
   c_p,eff = c_p + L·(df_l/dT). Solid and liquid properties differ in all three of rho, cp and k, so
   the two branches are kept distinct rather than averaged.
2. **TiNOX carries no bulk properties by design** — the roadmap itself specifies it as a boundary
   condition. This independently confirms the Gate 1 decision to drop the malformed 0.3 um coating
   solid and represent it as a surface radiative property.
3. **Two anisotropic entries**: PC honeycomb (0.075 perp / 0.16 para) and graphite (300 para /
   5 perp). OpenFOAM v1912 solid thermo is isotropic per region. Through-thickness conduction is the
   governing direction for both, so the perpendicular value is used and the in-plane value is
   recorded as a documented simplification — not silently averaged.
4. **Water is treated with constant properties at 300 K** for the baseline. mu varies strongly with
   temperature (8.55e-4 at 300 K falling to ~4.7e-4 at 333 K), so a temperature-dependent-viscosity
   sensitivity case is required before the constant-property assumption is accepted. Flagged.
5. **VIP derate 20 % over 25 years** is a service-life note, not a CFD input. Baseline uses 0.006.

## Optical chain (Roadmap, corrections C9/C11)
q"_solar = G_T · tau_glz_sys · tau_TIM · alpha_abs · (1 − f_shade)
with tau_glz_sys = **0.833** (two panes, correction C11 — NOT the single-pane 0.91),
tau_TIM = 0.82, alpha_abs = 0.95.
At G_T = 800 W/m²: q" = 800 × 0.833 × 0.82 × 0.95 = **519.1 W/m²**.

## External boundary relations (project-defined)
| Relation | Form |
|---|---|
| Sky temperature | T_sky = 0.0552 · T_amb^1.5   (T_amb in K) |
| Wind convection | h_wind = 5.7 + 3.8 · v_wind   (W/m²K, v in m/s) |
| Rear external, still air | h_rear = 3 W/m²K |
| Surface radiation | q_rad = eps · sigma · (T_s^4 − T_sur^4), **kelvin only** |
