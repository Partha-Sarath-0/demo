# GRAIL Collector: SDHW system block-diagram model (Scilab Xcos)

**This is a Scilab Xcos model, not MATLAB Simulink.** Xcos is the free block-diagram
simulator that comes with Scilab. It uses the same kind of blocks: integrators, expressions,
hysteresis, mux, from/to workspace, and a variable-step ODE solver. No MATLAB/Simulink
licence was available, so no `.slx` file exists. Tested with Scilab 2024.0.0.

## Files

| File | Purpose |
|---|---|
| `GRAIL_system.zcos` | The block diagram. Open it with `xcos("GRAIL_system.zcos")`. |
| `GRAIL_system_diagram.png` | Screenshot of the diagram in the Xcos editor. |
| `grail_xcos_build.sce` | Builds the diagram from a script (every block and link is listed there). |
| `run_grail_xcos.sce` | Builds and saves the .zcos, then runs the 8760-h year for alternating/parallel × 2/4 modules. Writes `xcos_results.csv`. |
| `quick.sce` | 1-day smoke test. |
| `save_only.sce`, `reimport.sce`, `shot.sce` | Save the diagram, re-import the saved .zcos and re-simulate it, and take the GUI screenshot. |
| `xcos_inputs.csv` | Hourly inputs: hour, G_eff (W/m², after IAM), T_amb (K), T_mains (K), draw (kg/s). Exported from the Octave model by `../13_Octave_system_model/export_xcos_inputs.m`. The PVGIS TMY file itself is unchanged. |
| `efficiency_correlations.json` | Stage 6 ISO 9806 coefficients (η0, a1, a2) read by the run script. |
| `xcos_results.csv` | Annual results. |
| `compare_xcos.py`, `xcos_verification.csv` | Verification against the Octave continuous-draw reference and the Stage 7 baseline. |

## How to run

```
scilab -f run_grail_xcos.sce          # GUI, or headless: xvfb-run -a scilab -nw -nb -f run_grail_xcos.sce
python3 compare_xcos.py
```

To run it interactively: open `GRAIL_system.zcos`, load the four workspace inputs `Vg`, `Va`,
`Vm`, `Vd` (see `quick.sce`, lines 3–6), set the context values (Simulation → Set Context),
and start the run. Each case takes 7–10 s for a full year.

## Model (SI units, kelvin throughout)

* **Collector node:** C dTc/dt = A[η0 G_eff − a1(Tc−Ta) − a2(Tc−Ta)²] − g2(Tc−Tt)·pump.
  * C = 33.5 kJ/m²K × A (PCM sensible heat only).
  * g2 = 2·ṁ·cp, with ṁ = n_modules × 0.00275 kg/s. This is the same collector–tank coupling as the Stage 7 / Octave model (grail_sdhw.m, line 18). The run script sets it for each case.
* **Tank (100 kg, UA 1.5 W/K, fully mixed):** M cp dTt/dt = g2(Tc−Tt)·pump − UA(Tt−Ta) − ṁ_t cp(Tt−T_mains).
  * The tank supplies ṁ_t = ṁ_d·min(1, (Tset−T_mains)/(Tt−T_mains)).
  * An electric top-up raises the delivered water to Tset = 318.15 K.
* **Pump:** HYSTHERESIS block on Tc−Tt (on at > 7 K, off at < 2 K), disabled while Tt > Tmax = 358.15 K.
* **Heat rates:** the six rates (collector→tank, tank loss, draw from tank, solar delivered,
  load, pump on) go through MUX → INTEGRAL_m → To-workspace `E`, sampled hourly.
  Tc and Tt are logged every 60 s to `T`.
* **Solver:** LSodar, reltol and abstol 1e-6, max step 60 s.
* **Inputs:** FROMWS_c blocks, zero-order hold: each hourly value is held constant for the whole hour.
* **Diagram wiring:** GOTO/FROM tags carry the signals that fan out (G_eff, T_amb, T_mains,
  m_draw, Tc, Tt, pump).

**One difference from the Stage 7 baseline.** In the Xcos model the hot-water draw is a
*continuous* flow (each hour's draw is spread evenly over that hour). The Python/Octave Stage 7 model
takes each hourly draw as a pulse at the start of the hour. Because of this, the Xcos solar
fraction is 1.5–1.6 SF points lower for 2 modules and 0.4 points lower for 4 modules. This
is a difference between the two draw models, not an error. The Octave continuous-draw
variant (`grail_sdhw_cont.m`) solves the same equations as Xcos and is the like-for-like
check.

## Results (Berhampur TMY, 100 L/day at 45 °C)

| Arrangement | Modules | Solar (kWh/yr) | Load (kWh/yr) | SF (%) | Max Tc (K) | Tank closure (kWh) |
|---|---|---|---|---|---|---|
| alternating | 2 | 626.0 | 768.9 | 81.42 | 348.0 | 4e-11 |
| parallel | 2 | 648.4 | 768.9 | 84.34 | 352.0 | 6e-12 |
| alternating | 4 | 749.7 | 768.9 | 97.51 | 429.8 | 2e-11 |
| parallel | 4 | 754.1 | 768.9 | 98.08 | 443.8 | −6e-11 |

The 4-module stagnation temperatures (> 420 K) carry the same **DESIGN_REVIEW_REQUIRED**
flag as in Stage 7.

## Verification (`xcos_verification.csv`)

**Against the Octave continuous-draw model** (dt 10 s): all four cases PASS.

* Solar heat differs by −0.04 % to −0.003 %.
* SF differs by at most 0.03 points.
* Max Tc differs by ≤ 1.1 K. The larger difference is in the 4-module stagnation peaks,
  where the Octave value itself moves 1–2 K between dt 60 s and dt 10 s.
* As the Octave step shrinks (60 → 10 s), its result moves toward the Xcos result.

**Tank first law:** the closure is ≤ 1e-10 kWh in every case.

**Re-import check:** importing the saved `.zcos` and simulating it again gives the same
result (parallel, 2 modules: 648.4 kWh).

This is model-to-model verification only. **No experimental validation has been done.**

## Known cosmetic issues

Long EXPRESSION formulas are drawn wider than their blocks in the Xcos editor, so some
labels overlap. The equations in the blocks are unaffected; double-click a block to read its
full expression.
