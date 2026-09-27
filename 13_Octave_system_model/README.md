# GRAIL Collector — system model in GNU Octave (roadmap Section 11, Stages 6–7)

Runs in **GNU Octave 7 or later** and **MATLAB R2016b or later**, with no toolboxes. Tested here with GNU Octave 8.4.0.
Simulink was not used: no MATLAB/Simulink licence was available. This model covers the same physics as a Simulink block
diagram would, written as plain equations and integrated in time.

## How to run
```
cd 13_Octave_system_model
octave --no-gui run_grail_annual.m      % or open run_grail_annual.m in MATLAB and press Run
octave --no-gui compare_with_python.m   % checks every result against the Python model
```
One full run (collector-only yields + 8 annual system simulations at a 60 s step) takes about 90 s.

## Files
| File | What it does |
|---|---|
| grail_params.m | All inputs; the efficiency correlations are read from efficiency_correlations.json (from the GRAIL-CHT virtual test) |
| grail_weather.m | Reads the PVGIS TMY file unchanged; NOAA solar position; Hay-Davies plane-of-array irradiance; incidence-angle modifier |
| grail_collector_only.m | Hourly useful heat at a fixed inlet temperature |
| grail_sdhw.m | Dynamic model: collector thermal node + mixed 100 L tank + pump control + mixing valve + electric top-up; tank first-law check |
| grail_econ.m | Saving, payback, NPV, levelised cost of heat |
| run_grail_annual.m | Main script; writes octave_results.csv, octave_collector_only.csv, octave_monthly.csv (and octave_annual.png where graphics work) |
| compare_with_python.m, pass_str.m | Independent check against the Python results (found in ../20_annual or ../12_Stages_3-5-6-7/annual) |

## Check result (GNU Octave 8.4.0)
| Quantity | Largest difference vs Python | Tolerance |
|---|---|---|
| Solar fraction | 0.000004 | 0.001 |
| Solar heat delivered | 0.003 kWh/yr | 0.5 kWh |
| Payback | 0.0004 yr | 0.01 yr |
| Cost of heat | 0.00004 Rs/kWh | 0.005 Rs/kWh |
| NPV | Rs 0.14 | Rs 5 |
| Collector-only yield | 0.004 kWh/m²/yr | 0.5 kWh/m²/yr |
| Peak collector temperature | 0.17 K | 0.5 K (first set to 0.1 K, which it failed; see below) |

The two codes use different solar-position algorithms: NOAA here, NREL SPA (pvlib) in Python. Hourly plane-of-array irradiance
therefore differs by up to 0.17 W/m², which is 0.01 kWh/m² over the year. A single-hour stagnation peak picks that up as a 0.17 K
difference. The tank energy balance closes to about 1e-12 kWh in every run.

## Figure
In this headless container, Octave's font renderer could not draw figures, so the script skips the figure and prints a message.
On a normal desktop Octave or MATLAB installation it writes octave_annual.png.
