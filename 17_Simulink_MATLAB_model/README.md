# GRAIL SDHW system: MATLAB / Simulink model (code)

These MATLAB scripts **build the Simulink block diagram themselves** (`new_system`,
`add_block`, `add_line`), save it as `GRAIL_system.slx`, and simulate one year for 4 cases. It is
the same system as the Scilab Xcos model (`14_Xcos_block_diagram_model`) and the Octave model
(`13_Octave_system_model`).

> **Not yet run in MATLAB.** No MATLAB/Simulink licence was available to me, so the Simulink calls
> have not been executed.
>
> The **equations** have been tested. `test_expressions_octave.m` evaluates the exact strings that
> go into the Fcn blocks, and they reproduce the Xcos results; see "Verification" below.
>
> Run `run_grail_simulink` once in MATLAB. It prints PASS/FAIL against the Xcos results. If an
> `add_block`/`set_param` call errors on your MATLAB release, the error message names the block
> and parameter.

## Files

| File | What it does |
|---|---|
| `run_grail_simulink.m` | **Start here.** Loads the inputs, builds the model, simulates alternating/parallel × 2/4 modules, and writes `simulink_results.csv`. It then compares with `xcos_results.csv` (PASS if solar heat is within 0.25 % and max Tc within 1.5 K). |
| `build_grail_simulink.m` | Builds the block diagram and saves `GRAIL_system.slx`. Every block and every line is listed here. |
| `grail_sim_expressions.m` | The equations of every Fcn block, in one place. |
| `grail_sim_params.m` | Collector, tank and Stage 6 coefficients (reads `efficiency_correlations.json`). |
| `test_expressions_octave.m` | Checks the Fcn-block equations in GNU Octave or MATLAB, without Simulink. |
| `xcos_inputs.csv` | Hourly G_eff, T_amb, T_mains and draw. This is the same file the Xcos model uses, built from the unchanged Berhampur TMY. |
| `xcos_results.csv` | Xcos results used for the PASS/FAIL comparison. |
| `efficiency_correlations.json` | Stage 6 η0, a1, a2. |

**Needs:** MATLAB R2019a or newer (for `readmatrix`/`readtable`; `jsondecode` needs R2016b) and
Simulink. No other toolbox is used.

## How to run

```matlab
cd <this folder>
run_grail_simulink              % builds GRAIL_system.slx, runs 4 cases, compares with Xcos
open_system('GRAIL_system')     % look at the block diagram
```

To build one case only:

```matlab
p = grail_sim_params('parallel', 2);
build_grail_simulink(p);
```

To simulate that case, first put `Vg`, `Va`, `Vm` and `Vd` in the workspace; see the first lines of
`run_grail_simulink.m`.

## The block diagram

| Group | Blocks |
|---|---|
| Inputs | 4 × **From Workspace** (`Vg`, `Va`, `Vm`, `Vd` = `[time_s, value]`), *Interpolate off*: each hourly value is held for the whole hour, as in Xcos |
| States | **Integrator** `Tc collector (K)` and **Integrator** `Tt tank (K)`, each fed by a **Mux** → **Fcn** (the energy balance) |
| Pump | **Fcn** `Tc - Tt` → **Relay** (on at 7 K, off at 2 K, outputs 1/0) → **Fcn** `demand × (Tt ≤ 358.15 K)` |
| Heat rates | 6 × **Fcn**: collector→tank, tank loss, drawn from tank, solar delivered, hot-water load, pump running |
| Energies | **Mux**(6) → **Integrator**(6 states) → **To Workspace** `E`, every 3600 s |
| Log | **Mux**(Tc, Tt) → **To Workspace** `T`, every 60 s |
| Solver | ode15s, RelTol 1e-6, AbsTol 1e-6, MaxStep 60 s, stop time 8760 h |

**Equations** (SI units, kelvin; C = 33.5 kJ/m²K × A; g2 = 2·ṁ·cp):

* **Collector:** C dTc/dt = A[η0·G − a1(Tc−Ta) − a2(Tc−Ta)²] − g2(Tc−Tt)·pump
* **Tank:** M·cp·dTt/dt = g2(Tc−Tt)·pump − UA(Tt−Ta) − ṁ_t·cp(Tt−T_mains)
* **Mixing valve:** ṁ_t = ṁ_draw·min(1, (Tset−T_mains)/(Tt−T_mains))

**How the Fcn blocks are written:**

* They use only operators and `abs()`, so `min` and `max` are written as
  (a+b∓|a−b|)/2.
* The parameter values are written into the expressions as numbers. The `.slx` therefore does not
  depend on workspace variables, apart from the four input signals.
* Library blocks are found by BlockType and name, so the script does not depend on the library
  path names of a particular MATLAB release.

## Verification

The Fcn equations were checked in GNU Octave with `test_expressions_octave.m`: fixed 10 s step,
the same hourly inputs and the same relay rule. The results were compared with the Scilab Xcos
model (`expression_test_vs_xcos.csv`); all four cases PASS:

| Case | Solar heat: test vs Xcos (kWh/yr) | Difference | Solar fraction | Max Tc difference | Tank balance |
|---|---|---|---|---|---|
| alternating, 2 modules | 626.31 vs 626.02 | +0.045 % | 81.46 vs 81.42 % | +0.01 K | 1e-10 kWh |
| parallel, 2 modules | 648.57 vs 648.42 | +0.023 % | 84.36 vs 84.34 % | 0.00 K | 2e-10 kWh |
| alternating, 4 modules | 749.75 vs 749.71 | +0.006 % | 97.52 vs 97.51 % | +1.07 K | 5e-10 kWh |
| parallel, 4 modules | 754.13 vs 754.08 | +0.007 % | 98.09 vs 98.08 % | +0.38 K | 5e-10 kWh |

The small differences come from the fixed 10 s step against Xcos's variable-step solver; the
largest is at the 4-module stagnation peaks.

The test also caught one bug during development. The first version wrote `a/max(b,c)` without
enough brackets, so it was evaluated as `(a/(b+c+|b−c|))/2`. It was fixed before this check, so
the strings in `grail_sim_expressions.m` are the corrected ones.

Two further checks happen when you run `run_grail_simulink.m` in MATLAB:

* **Energy balance:** the tank first law is closed for every case (`closure_kWh`).
* **Xcos comparison:** results are compared with the Xcos results and marked PASS/FAIL.

The draw is spread evenly over each draw hour, as in Xcos. For the same reason as Xcos, the
Stage 7 solar fractions (hourly-pulse draw) are 1.5–1.6 points higher at 2 modules; the Stage 7
figures remain the reported baseline.

This is model-to-model verification; **no experimental validation is claimed.**
