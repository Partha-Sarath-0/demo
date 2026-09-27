# V5 screening of the seven papers supplied by the user (2024–2026)

These are the same three tests used for Gunjo et al. 2017. A paper can serve as the V5 experimental
reference only if it:

- **(a) tabulates** its measured data;
- **(b) passes an independent energy balance** (useful heat ≤ incident solar, with a plausible
  efficiency);
- **(c) states every boundary input** needed to rerun it: geometry, flow, inlet temperature, ambient
  temperature, irradiance and wind.

A match with a different collector type tests only the general method, not GRAIL itself.

**Decision: V5 stays OPEN.** None of the seven papers can validate the GRAIL collector. Two contain
data that pass the energy check and can be cited for comparison, and one points to the best
remaining candidate (Mansour 2013, see the end).

| # | Paper | Experiment? | (a) Tables | (b) Energy check | (c) Inputs | Verdict |
|---|---|---|---|---|---|---|
| 1 | Bharathiraja et al., *J. Energy Storage* 96 (2024) 112649: hybrid nano-PCM flat-plate collector | Yes, outdoor, Coimbatore (India), 100 L tank | **Yes**: Tables 5–6, hourly inlet/outlet, ambient, wind, irradiance | **Pass**: recomputed η = ṁcpΔT/(A·G) with ṁ 0.01 kg/s and A 2 m² gives a daily peak of 64.8 % (no PCM) and 73.0 % (PCM), matching the paper's 64.7 % and 71.7 %; never above 100 % | **Partly**: see issues below | Comparison only, at system level. Not a validation reference |
| 2 | Vahidinia & Khorasanizadeh, *Energy* 304 (2024) 132232: minichannel vs conventional flat-plate collector | No; numerical, validated against Yousefi et al. 2012 and Mansour 2013 | Inputs given in text | **Pass** for the quoted Yousefi points: η ≈ 0.68 (ṁ 0.0167 kg/s, G 964 W/m², ΔT 14.1 K, A 1.51 m²) and 0.61 (ṁ 0.0333 kg/s, G 975 W/m², ΔT 6.5 K) | No: riser count and pitch, glazing and U_L are not given | Leads to Mansour 2013 (see below) |
| 3 | Zareie et al., *Energy* 286 (2024) 129452: branch-inspired roll-bond PVT | Yes, indoor solar simulator, 275 × 195 mm panel | **No**: validation shown only as a plot (Fig. 6), 3 flow rates | Cannot be checked | Partly | **Reject.** "Max error 0.2 %" is computed on absolute kelvin (0.4 K / ~300 K), the same flaw found in Gunjo 2017. A PV module, not a thermal collector |
| 4 | Parthiban et al., *Appl. Therm. Eng.* 258 (2025) 124715: honeycomb TIM collector | No. The TIM model was checked only against a natural-convection cavity benchmark (up to 13.5 % deviation); the TRNSYS system model was checked against Ayompe & Duffy (their Table 4) | Table 4 (system level, not TIM) | n/a | Yes, for the model | Comparison only. It over-predicts outlet temperature by 7–20 % (RMSE 5.68 °C). Useful TIM property: τ = 0.89 for 20 mm polycarbonate honeycomb |
| 5 | Ding et al., *Int. J. Therm. Sci.* 208 (2025) 109394: varying micro-channel width | Yes, electronics-cooling test piece | Partly | n/a | Yes | Physics support for non-uniform channel widths improving uniformity. Not a collector |
| 6 | Li et al., *Appl. Therm. Eng.* 251 (2024) 123587: tapered manifold microchannel heat sink | No; numerical, validated against the Drummond et al. experiment (Table 3, < 1 K) | n/a | n/a | n/a | Method support (surrogate + NSGA-II + TOPSIS). Not a collector |
| 7 | Alawi et al., *Eng. Appl. AI* 133 (2024) 108158: machine-learning prediction of flat-plate collector efficiency | No; 504 points collected from the literature | n/a | n/a | n/a | Method comparison for Stage 3. Their best test R² is about 0.93; GRAIL's ANN reaches 0.9994–0.9998 on CFD data |

## Issues found in paper 1 (Bharathiraja 2024), recorded rather than corrected

- **Flow is described two ways.** The tables are titled "natural circulation solar water heater",
  but Section 2 says the flow was set to a constant 0.01 kg/s. The energy check above assumes the
  stated 0.01 kg/s.
- **Probable typo.** Table 5, 17:00 h, gives wind 24 m/s; every other hour is 1.8–3.8 m/s.
- **Low temperature resolution.** Temperatures are given as whole °C, so each hourly ΔT carries
  about ±1.4 K of uncertainty (compared with ΔT of 2–25 K).
- **Not steady-state.** The data are transient (the tank heats up during the day). The paper cites
  ASHRAE 93, but ASHRAE 93 efficiency points must be steady-state, so these points cannot give an
  η0/a1 curve comparable to GRAIL's Stage 6 fit.
- **Different collector.** 10 round tubes (16 mm), no TIM, PCM behind the absorber.

## Best remaining candidate for V5

**Khamis Mansour M., "Thermal analysis of novel minichannel-based solar flat-plate collector",
*Energy* 60 (2013) 333–343.** It is an analytical and experimental study of a minichannel
flat-plate collector (0.6 m² absorber), compared against a conventional collector. Paper 2 used it
for validation and reports an outlet-temperature difference of 0 % (minichannel) and 1.96 %
(conventional).

A minichannel absorber is the closest published analogue to a roll-bond channel plate. The full
text is needed to apply tests (a)–(c).

Until a paper passes all three tests, the thesis states: **verified simulation (3-D conjugate CFD,
grid convergence, Hottel-Whillier-Bliss check within 0.22 %); no experimental validation.**

---

# Round 2: four more papers (full texts supplied)

| # | Paper | (a) Tables | (b) Energy / plausibility | (c) Inputs | Verdict |
|---|---|---|---|---|---|
| 8 | **Del Col, Padovan, Bortolato, Dai Prè, Zambolin, *Energy* 58 (2013) 258–269**: roll-bond vs sheet-and-tube flat-plate collectors, EN 12975-2 | **Yes**: Tables 3–4 give η0, a1, a2 with 95 % uncertainties for two roll-bond and two standard collectors, from both steady-state and quasi-dynamic tests | **Pass**: η0 0.7995 (black roll-bond) is below τα ≈ 0.87 (α 0.96 × a typical glass τ ≈ 0.91), so F′ ≈ 0.92, which is plausible. The two test methods agree within their uncertainties | **Partly**: 28 channels, Ø 3.7 mm, aperture 1.81 m², 1.5 mm Al absorber, α/ε, flow 0.02 kg/s·m², G 800–1000 W/m², T_amb 8–12 °C and wind 1.4 m/s are given. **Not given:** glass transmittance and thickness, air gap, insulation thickness, collector length/width | **Best reference found.** The only paper with tabulated, uncertainty-rated test data on a real roll-bond collector. Can be used for comparison now; could support a method validation (see below) |
| 9 | Khamis Mansour, *Energy* 60 (2013) 333–343: minichannel flat-plate collector | **No**: the experiment (0.6 m² prototype, Beirut) is shown only in Figs. 8–9. Tables 1–2 are **model** results for a 2 m² design | Model table is self-consistent (Qu 1195 W / (900 × 2 m²) = 0.664, as stated) | Full inputs for the **model** case (Table 1); not for the experiment | Not a V5 reference. Measured-vs-model deviation is up to 10 % (efficiency) and 20.4 % (U_L), read from plots only. Table 1–2 could serve as a published model-to-model benchmark |
| 10 | Zheng, Febrer, Castro, Kizildag, Rigola, *Applied Energy* 355 (2024) 122221: honeycomb + silica-aerogel TIM collector | **No**: measured efficiency shown only in Fig. 14 | Stated efficiency uncertainty is about 11 % | **Yes**: full geometry and optics in Table 1 | Comparison only. The model was fitted to the test by adjusting aerogel porosity to 15 %, so the model-to-test agreement is a calibrated fit, not an independent validation |
| 11 | Sakib et al., *Energy Convers. Manage.: X* 31 (2026) 102073: CFD → KAN/MLP → NSGA-II | n/a (simulation + machine learning) | n/a | n/a | Method comparison for Stages 3 and 5 only |

## What paper 8 (Del Col 2013) allows

**1. Direct comparison (can be written now).** Steady-state coefficients at G = 1000 W/m², based on
mean fluid temperature, the same basis as GRAIL's Stage 6 fit:

| Collector | η0 | a1 (W/m²K) | a2 (W/m²K²) |
|---|---|---|---|
| Del Col roll-bond, black | 0.7995 ± 0.011 | 4.69 ± 0.79 | 0.029 ± 0.012 |
| Del Col roll-bond, semi-selective | 0.7409 ± 0.011 | 4.55 ± 0.69 | 0.013 ± 0.010 |
| GRAIL parallel (model) | 0.637 | 2.10 | 0 |
| GRAIL alternating (model) | 0.597 | 2.00 | 0.0004 |

- **Trade-off.** GRAIL loses about 0.10–0.20 in optical efficiency (the TIM + glass stack,
  optical factor 0.649) and gains a heat-loss coefficient less than half that of the tested
  roll-bond collectors.
- **Crossover.** The curves cross at Tm* ≈ 0.036–0.050 m²K/W. GRAIL is better above that, i.e.
  above about 36–50 K of mean-fluid-to-ambient difference at 1000 W/m².
- **Fit range caveat.** GRAIL's fit covers Tm − Ta up to 40 K, so the crossover lies at the edge of
  its fitted range. State this with the numbers.

**2. Method validation (possible, needs your approval).** Apply the same Hottel-Whillier-Bliss fin
model used in GRAIL's check to Del Col's black roll-bond collector and compare the predicted
η0 / a1 with the measured values and their uncertainties.

- The missing inputs (glass τ, gap, insulation) would be ENGINEERING_ASSUMPTIONs taken from typical
  values and stated openly, with a sensitivity band.
- If the prediction falls within the test uncertainty, the thesis can say: *"the modelling method
  reproduces the measured efficiency of a published roll-bond collector within its test
  uncertainty"*.
- This is a method validation, **not** an experimental validation of GRAIL itself.

**V5 status: still OPEN,** as instructed. Closing it (fully or as "method validated on a
published roll-bond collector") is the user's decision.

---

# Round 3: four more papers (full texts supplied)

| # | Paper | (a) Tables | (b) Plausibility | (c) Inputs | Verdict |
|---|---|---|---|---|---|
| 12 | **Beikircher, Möckl, Osgyan, Streib, *Sol. Energy Mater. Sol. Cells* 141 (2015) 398–406**: film/honeycomb TIM front + vacuum super insulation (VSI) rear, full-area Al absorber | **Yes**: Table 1, η0/a1/a2 (EN 12975-2) for the VSI prototype (0.89 / 3.28 / 0.014) and base collector SF100-03 (0.877 / 3.73 / 0.014). Honeycomb TIM front U = 2.2 W/m²K (30 mm), 1.95 (40 mm); VSI rear U 0.25–0.84 W/m²K | **Pass**: η0 0.89 < τα (AR glass τ 0.96 × α ≈ 0.95 = 0.91), F′ ≈ 0.97, as stated. Outdoor error 3 % | Partly: many coefficients are for "calculated for AR glass" variants; honeycomb prototype coefficients only in figures | **Comparison / component check.** Best source for GRAIL's rear VIP and TIM U-values. Measured VSI benefit ≈ 0.5 W/m²K in a1 |
| 13 | **Kessentini, Capdevila, Castro, Oliva (CTTC/UPC)**: flat-plate collector with honeycomb (slat) TIM + overheating channel (conference paper; journal version Appl. Energy 133 (2014) 206–223) | **Partly**: fitted efficiency equation given as text, η = 0.732 − 7.19 (Tav − Tamb)/G (ISO 9806-1, 16 points, R² 0.98); raw points only in Fig. 6 | Plausible; the authors note a poor selective coating (ε 0.5) | Partly: A 2.24 m², 4 mm glass, 4 mm TIM, α 0.95/ε 0.5, 0.042 kg/s; glass τ, gap, insulation thickness not given | **Comparison + possible method check** (second TIM collector). Their own model over-predicts by ≤ 3 %. High a1 (7.19) is due to ε 0.5, so it is not a like-for-like TIM benefit |
| 14 | **Robles, Duong, Martin, Guadarrama, Diaz, *Solar Energy* 110 (2014) 356–364**: aluminium minichannel vs copper flat-plate water heater, year-round | Geometry table only (Table 1: 11 tubes, Dh 1.42 mm, A 3.20 m², glass τ 0.909) | Cannot be checked: results are daily transient curves in figures | No steady-state inlet/flow table | **Not a V5 reference.** System-level, transient, figures only. Cite qualitatively (minichannel beats sheet-and-tube) |
| 15 | **Oyinlola & Shire, BSERT (2018/19)**: micro-channel absorber plates (Dh 0.44 and 0.8 mm) | Geometry and data-reduction tables only; measured h shown in figures, h uncertainty < 20 % | n/a (heated test rig, no sun) | Yes for the rig | **Not a V5 reference.** Supports the channel-level approach (3-wall H1 condition, h > 300 W/m²K has marginal effect on F′) |

**Round 3 result:** Beikircher 2015 is a second tabulated, test-standard reference (after Del Col 2013), for the insulation parts of GRAIL. Kessentini gives one measured TIM efficiency line. Robles and Oyinlola are background only.

**V5 status: still OPEN,** as instructed.

---

**Update 25 Sep 2026:** V5 closed by the user at method/component level. Final record: `V5_FINAL_closure.md`.
