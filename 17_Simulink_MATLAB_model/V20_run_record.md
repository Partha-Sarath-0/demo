# Simulink V20 run record (MATLAB Online, run by the user, 25 Sep 2026)

Script: `GRAIL_simulink_complete_FINAL_v20.m` (8760 h data embedded). Solver ode45, RelTol/AbsTol 1e-6, MaxStep 60 s.

| Case | Solar heat (kWh) | Solar fraction | Max Tc (K) | Tank end (K) | Energy closure (kWh) | vs Xcos solar | vs Xcos max Tc | Verdict |
|---|---|---|---|---|---|---|---|---|
| Alternating, 2 modules | 626.2796 | 81.4531 % | 347.963 | 311.435 | 4.9e-12 | +0.0408 % | +0.0009 K | PASS |
| Parallel, 2 modules | 648.5528 | 84.3499 % | 352.021 | 312.899 | -3.1e-11 | +0.0205 % | -0.0089 K | PASS |
| Alternating, 4 modules | 749.7898 | 97.5176 % | 430.787 | 334.159 | -6.0e-11 | +0.0108 % | +0.9375 K | PASS |
| Parallel, 4 modules | 754.1304 | 98.0834 % | 444.211 | 338.204 | -1.5e-10 | +0.0068 % | +0.3892 K | PASS |

**OVERALL PASS** (limits: solar heat within 0.25 %, max Tc within 1.5 K).

Notes:
- Tank energy balance closes to machine precision in all four cases.
- The larger max-Tc differences in the 4-module cases (0.4-0.9 K) are at stagnation (> 420 K), where the
  pump is off and the peak depends on solver step placement; annual energy agrees within 0.011 %.
- Model-to-model check (Simulink vs Xcos vs Octave). Not an experimental validation.

## V21 (same numerics, cleaner layout)

`GRAIL_simulink_complete_FINAL_v21.m` was run by the user in MATLAB Online on 25 Sep 2026: **OVERALL PASS** (reported by the user).
The printed diagram (`GRAIL_system_v21`, parallel, 2 modules) is the thesis figure.
