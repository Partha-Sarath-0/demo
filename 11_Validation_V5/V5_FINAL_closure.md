# V5 final record: validation against published experimental work

**Status: COMPLETE (closed by the user on 25 Sep 2026).**
**Verdict: PARTIAL PASS at method and component level. This is not an experimental validation of the GRAIL collector itself.**

## 1. What V5 asked

The roadmap asks for baseline validation within 8 %. No prototype of GRAIL exists. The project therefore
validates the **modelling method** against published measurements on similar collectors.

## 2. Screening rules (applied to every paper)

A paper is usable as a reference only if it passes all three tests:

- **(a)** its measured data are given in tables;
- **(b)** the data pass an independent energy check;
- **(c)** it states the inputs needed to rerun it.

## 3. All papers screened (16)

| # | Paper | Measured data? | Tables | Energy check | Inputs | Use |
|---|---|---|---|---|---|---|
| 1 | Gunjo et al. 2017 | CFD vs test | – | **Fails** (its CFD exceeds solar input) | – | Rejected |
| 2 | Bharathiraja et al. 2024 (nano-PCM FPC) | Yes, outdoor | Yes | Pass | Partly (flow/wind inconsistent, transient) | Comparison only |
| 3 | Vahidinia & Khorasanizadeh 2024 (minichannel) | No (model) | – | Pass on quoted points | No | Pointer to Mansour |
| 4 | Zareie et al. 2024 (roll-bond PVT) | Yes, simulator | No (plot) | Not checkable | Partly | Rejected (error on absolute K) |
| 5 | Parthiban et al. 2025 (honeycomb TIM) | No (model) | System only | n/a | Yes | Comparison; TIM τ = 0.89 |
| 6 | Ding et al. 2025 (varying channel width) | Yes (heat sink) | Partly | n/a | Yes | Physics support only |
| 7 | Li et al. 2024 (tapered manifold) | No | n/a | n/a | n/a | Method support only |
| 8 | Alawi et al. 2024 (ML for FPC) | No (literature data) | n/a | n/a | n/a | ANN comparison |
| 9 | **Del Col et al. 2013 (roll-bond, EN 12975)** | **Yes** | **Yes, with U95** | **Pass** | Mostly | **Reference – method check** |
| 10 | Mansour 2013 (minichannel) | Yes | No (plots) | Model table passes | Model only | Model benchmark only |
| 11 | Zheng et al. 2024 (honeycomb + aerogel TIM) | Yes | No (plot) | ~11 % uncertainty | Yes | Comparison (calibrated fit) |
| 12 | Sakib et al. 2026 (KAN/MLP + NSGA-II) | No | n/a | n/a | n/a | Method comparison |
| 13 | **Beikircher et al. 2015 (TIM front + VIP rear)** | **Yes** | **Yes** | **Pass** | Partly | **Reference – component check** |
| 14 | Kessentini et al. (CTTC, TIM collector) | Yes | Fitted line only | Plausible | Partly | Comparison (measured TIM curve) |
| 15 | Robles et al. 2014 (Al minichannel) | Yes, year-round | No (plots) | Not checkable | No | Background only |
| 16 | Oyinlola & Shire 2018 (micro-channel plate) | Yes, lab rig | No (plots) | n/a | Rig only | Background only |

(16 rows: Gunjo 2017 plus the 15 papers supplied in three rounds.)

## 4. Checks carried out

### 4.1 Method check – Del Col 2013 (folder 19)

Same Hottel-Whillier-Bliss fin model and Klein top-loss correlation, no tuning; the 11 unstated inputs
sampled by Monte Carlo (2,000 runs).

| Coefficient | Black roll-bond | Semi-selective roll-bond | Within test U95? |
|---|---|---|---|
| η0 (model / measured) | 0.862 / 0.800 (+7.8 %) | 0.785 / 0.741 (+6.0 %) | No |
| a1 (W/m²K) | 5.37 / 4.69 ± 0.79 | 4.26 / 4.55 ± 0.69 | **Yes** |
| a2 (W/m²K²) | 0.019 / 0.029 ± 0.012 | 0.012 / 0.013 ± 0.010 | **Yes** |

Efficiency curve, model vs measured (G = 1000 W/m²):

| Tm* (m²K/W) | 0 | 0.01 | 0.02 | 0.03 | 0.04 | 0.06 | 0.08 |
|---|---|---|---|---|---|---|---|
| Black, deviation | +7.9 % | +7.6 % | +7.7 % | +8.2 % | +9.2 % | +14.3 % | +31 % |
| Semi-selective, deviation | +6.0 % | +6.8 % | +7.9 % | +9.1 % | +10.8 % | +15.7 % | +26 % |

Absolute deviation is at most 0.076 efficiency points over the whole range. The relative error grows at
high Tm* only because the measured efficiency itself becomes small; the cause is the constant optical
offset (η0), not the heat-loss model.

### 4.2 Component check – Beikircher 2015 (folder 21)

| Component | GRAIL model | Measured | Result |
|---|---|---|---|
| Front (glass + TIM) U | 1.95–2.06 W/m²K | 1.95–2.2 W/m²K (honeycomb covers) | **Pass** |
| Rear VIP conductivity | 0.006 W/m·K (catalogue) | 0.010–0.018 W/m·K (in a hot collector) | **Optimistic** → a1 2.1 → 2.3–2.5 W/m²K |

## 5. Result against the V5 criterion (< 8 %)

| Item | Result |
|---|---|
| Heat-loss coefficients a1, a2 | **Pass** – inside the measured 95 % uncertainty for both tested collectors |
| Optical efficiency η0 | **Pass (< 8 %)** – +6.0 % and +7.8 %, but outside the test uncertainty |
| Efficiency curve, Tm* ≤ 0.02 m²K/W | **Pass (< 8 %)** |
| Efficiency curve, Tm* > 0.03 m²K/W | **Fail in relative terms** (≤ 0.076 points absolute) |
| TIM front loss | **Pass** |
| VIP rear loss | Model optimistic; carried as an uncertainty (a1 up to 2.5 W/m²K) |

## 6. What may be written in the thesis and paper

> "The modelling method was checked against published experimental data. Applied without tuning to
> tested roll-bond collectors (Del Col et al. 2013), it reproduces the measured heat-loss coefficients
> within test uncertainty and the optical efficiency within 8 %. The modelled cover heat loss lies
> within the range measured for honeycomb transparent insulation (Beikircher et al. 2015). No
> prototype of the present collector was tested."

**Not allowed:** "experimentally validated", "validated against experiment" for GRAIL itself.

## 7. Uncertainties carried into GRAIL results

- η0: up to about −7 % (optical losses not in the ideal model).
- a1: 2.1 to 2.5 W/m²K (VIP conductivity). DESIGN_REVIEW_REQUIRED: use a measured in-collector value.
- Annual yield and solar fraction inherit both.

Files: `11_Validation_V5/V5_screening_2024-2026_papers.md`, `19_V5_DelCol_method_check/`,
`21_V5_Beikircher_component_check/`.
