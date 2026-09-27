# Data dictionary — GRAIL_CFD_dataset_FINAL_rev4.2.csv

**What the rows are:** 300 outputs of the GRAIL-CHT reduced-order conjugate model (2-D plate + 1-D channel flow). Its Nusselt closure and pressure-drop calibration come from grid-studied 3-D conjugate CFD (OpenFOAM). The rows are **not** 300 independent 3-D CFD simulations. No experimental validation is claimed.

> **Important — `Nu_closure_input`:** this column is a **fixed model input**, not a computed per-case CFD output. The value 4.48 was derived once from the 3-D conjugate CFD and applied to every case, so it is identical in all 300 rows by design.

| # | Column | Unit | Category | Definition / source |
|---|---|---|---|---|
| 1 | `case_id` | - | METADATA | Case identifier. ALT_n = alternating, PAR_n = parallel. ALT_n and PAR_n are independent LHS samples and are NOT matched pairs |
| 2 | `geometry_version` | - | METADATA | Geometry build used (converging CAD, Gate A verified) |
| 3 | `solver` | - | METADATA | GRAIL-CHT reduced-order conjugate model (not a 3-D CFD solver) |
| 4 | `arrangement` | - | MODEL INPUT (sampled) | Flow arrangement: alternating (counter-current) or parallel |
| 5 | `f_interdig` | - | MODEL INPUT (sampled) | 1 = alternating, 0 = parallel |
| 6 | `G_T_W_m2` | W/m² | MODEL INPUT (sampled) | Incident solar irradiance on the aperture |
| 7 | `T_in_K` | K | MODEL INPUT (sampled) | Water inlet temperature |
| 8 | `T_amb_K` | K | MODEL INPUT (sampled) | Ambient air temperature |
| 9 | `v_wind_m_s` | m/s | MODEL INPUT (sampled) | Wind speed |
| 10 | `mdot_total_kg_s` | kg/s | MODEL INPUT (sampled) | Total water mass flow |
| 11 | `mdot_channel_kg_s` | kg/s | DERIVED (computed from other columns) | mdot_total / 12 |
| 12 | `bridge_mm` | mm | MODEL INPUT (sampled) | Bridge (metal land) width between channels |
| 13 | `g_ratio` | - | MODEL INPUT (sampled) | Grading ratio G = Dh_out / Dh_in |
| 14 | `lambda_G` | - | MODEL INPUT (sampled) | Grading exponent of the hydraulic-diameter profile |
| 15 | `Dh_in_mm` | mm | DERIVED (computed from other columns) | Inlet hydraulic diameter (same for all cases) |
| 16 | `Dh_out_mm` | mm | DERIVED (computed from other columns) | Dh_in × g_ratio |
| 17 | `A_in_mm2` | mm² | DERIVED (computed from other columns) | Inlet cross-section area (same for all cases) |
| 18 | `A_out_mm2` | mm² | DERIVED (computed from other columns) | A_in × (Dh_out/Dh_in)² |
| 19 | `Re_in` | - | DERIVED (computed from other columns) | mdot_channel·Dh_in/(A_in·mu) — non-circular definition (Rev 4.1) |
| 20 | `Re_out` | - | DERIVED (computed from other columns) | mdot_channel·Dh_out/(A_out·mu) |
| 21 | `mu_Pa_s` | Pa·s | DERIVED (computed from other columns) | Water viscosity, Vogel correlation at ½(T_in+T_out); evaluated with the nx220 T_out (≤0.17 % difference) |
| 22 | `dp_channel_Pa` | Pa | MODEL OUTPUT (solved) | Channel pressure drop: calibrated laminar integral (calibration factor from 3-D CFD); a model result, not a per-case 3-D CFD result |
| 23 | `W_pump_W` | W | DERIVED (computed from other columns) | dp_channel × mdot_total / 997 |
| 24 | `q_abs_W_m2` | W/m² | DERIVED (computed from other columns) | Absorbed flux = G_T × 0.833 × 0.82 × 0.95 (optical factor 0.6489) |
| 25 | `T_sky_K` | K | DERIVED (computed from other columns) | 0.0552 × T_amb^1.5 |
| 26 | `h_wind_W_m2K` | W/m²K | DERIVED (computed from other columns) | 5.7 + 3.8 × v_wind |
| 27 | `T_out_K` | K | MODEL OUTPUT (solved) | Mixed-mean outlet temperature |
| 28 | `dT_fluid_K` | K | DERIVED (computed from other columns) | T_out − T_in |
| 29 | `Qu_W` | W | DERIVED (computed from other columns) | Useful heat = mdot_total × 4180 × dT_fluid |
| 30 | `eta` | - | DERIVED (computed from other columns) | Thermal efficiency = Qu / (G_T × 0.528 m²), on INCIDENT irradiance |
| 31 | `T_plate_mean_K` | K | MODEL OUTPUT (solved) | Area-mean plate temperature |
| 32 | `T_plate_max_K` | K | MODEL OUTPUT (solved) | Maximum plate temperature |
| 33 | `T_plate_min_K` | K | MODEL OUTPUT (solved) | Minimum plate temperature |
| 34 | `plate_spread_K` | K | DERIVED (computed from other columns) | T_plate_max − T_plate_min |
| 35 | `plate_std_K` | K | MODEL OUTPUT (solved) | Standard deviation of plate temperature (uniformity metric) |
| 36 | `P90_K` | K | MODEL OUTPUT (solved) | 90th-percentile plate temperature |
| 37 | `P95_K` | K | MODEL OUTPUT (solved) | 95th-percentile plate temperature |
| 38 | `P99_K` | K | MODEL OUTPUT (solved) | 99th-percentile plate temperature |
| 39 | `R4_K4` | K⁴ | MODEL OUTPUT (solved) | Plate mean of T⁴ (radiative functional) |
| 40 | `Tmean_pow4_K4` | K⁴ | DERIVED (computed from other columns) | (T_plate_mean)⁴ — NOTE: fourth power of the mean, not mean of T⁴ |
| 41 | `T_R4_K` | K | DERIVED (computed from other columns) | R4^(1/4), effective radiative plate temperature |
| 42 | `Q_solar_W` | W | DERIVED (computed from other columns) | ABSORBED solar power = q_abs × 0.528 (not incident) |
| 43 | `Q_rad_W` | W | MODEL OUTPUT (solved) | Net radiative heat flow plate→glazing (signed; negative = heat gain) |
| 44 | `Q_conv_W` | W | MODEL OUTPUT (solved) | Net convective/conductive heat flow plate→glazing (signed) |
| 45 | `Q_rear_W` | W | MODEL OUTPUT (solved) | Net rear heat flow plate→ambient (signed; negative when plate below ambient) |
| 46 | `U_L_W_m2K` | W/m²K | DERIVED (computed from other columns) | (Q_solar − Qu)/(0.528 (T_plate_mean − T_amb)); undefined/unreliable when |T_plate_mean − T_amb| < 5 K |
| 47 | `T_glass_mean_K` | K | MODEL OUTPUT (solved) | Mean glazing temperature |
| 48 | `lateral_bridge_W` | W | MODEL OUTPUT (solved) | Heat conducted laterally through the bridges (≈0 in parallel flow by symmetry) |
| 49 | `energy_error_pct` | % | SOLVER RECORD | Solver energy-balance diagnostic (nx220 run) |
| 50 | `outer_iters` | - | SOLVER RECORD | Outer iterations (max of the two plate grids) |
| 51 | `residual` | - | SOLVER RECORD | Final outer-iteration residual (nx220 run) |
| 52 | `converged` | - | SOLVER RECORD | Convergence flag (tolerance 1e-6) |
| 53 | `Nu_closure_input` | - | FIXED MODEL INPUT (closure / constant) | **MODEL INPUT, NOT A PER-CASE CFD OUTPUT.** Fixed Nusselt closure applied to every case; derived once from grid-studied 3-D conjugate OpenFOAM CFD (4.48, GCI 2.1 %). Constant across all 300 cases by design (developed Nu was flow-independent in 3-D: 4.60 at 1.0, 2.49 and 4.5 g/s) |
| 54 | `Nu_closure_basis` | - | METADATA | Provenance of Nu_closure_input: conjugate 3-D benchmark, H1-type thermal condition |
| 55 | `dataset_rev` | - | METADATA | Integer revision field; file is Rev 4.2 (see filename and change log) |
| 56 | `k_model` | - | METADATA | Water thermal conductivity model k(T) |
| 57 | `outer_cap` | - | METADATA | Outer-iteration cap (3000) |
| 58 | `plate_nx` | - | METADATA | Plate-grid treatment: Richardson 2·f(220) − f(110) |
| 59 | `plate_ny` | - | METADATA | Plate grid cells across width (120) |
