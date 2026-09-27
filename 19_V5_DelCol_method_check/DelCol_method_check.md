# V5 method check: Hottel-Whillier-Bliss model vs Del Col et al. (2013) roll-bond collectors

**Script:** `delcol_hwb_check.py`. **Results:** `delcol_hwb_check.json`.

**Model:**
- Duffie & Beckman fin model (F, F′), with Klein's top-loss correlation.
- Efficiency on the mean-fluid-temperature basis, as in EN 12975.
- Every input Del Col states was used as given.
- The 11 inputs Del Col does not state (glass τ and ε, collector width, Al conductivity,
  insulation, edge loss, channel Nu, bond footprint, wind coefficient, tilt, ambient) were
  sampled over typical ranges: 2,000 Monte Carlo runs, 95 % band.
- **Nothing was tuned to the measurements.**

| Collector | Coefficient | Model (nominal) | Model 95 % band | Measured ± U95 | Overlap? |
|---|---|---|---|---|---|
| Roll-bond, black | η0 | 0.862 | 0.848–0.876 | 0.800 ± 0.011 | **No** (+0.06) |
| | a1 (W/m²K) | 5.37 | 5.05–5.77 | 4.69 ± 0.79 | Yes |
| | a2 (W/m²K²) | 0.019 | 0.017–0.020 | 0.029 ± 0.012 | Yes |
| Roll-bond, semi-selective | η0 | 0.785 | 0.773–0.798 | 0.741 ± 0.011 | **No** (+0.045) |
| | a1 | 4.26 | 3.99–4.60 | 4.55 ± 0.69 | Yes |
| | a2 | 0.012 | 0.011–0.013 | 0.013 ± 0.010 | Yes |

## Result: PARTIAL

- **Heat loss: reproduced.** a1 and a2 fall within the test uncertainty for both collectors. The
  method correctly captures the loss behaviour of a real roll-bond collector.
- **Optical efficiency: over-predicted.** η0 is 0.045–0.06 above the measured value, which is
  6–8 %, outside the test uncertainty. The fin/flow part is not the cause (F′ ≈ 0.98, and
  channel-side changes hardly move η0).
- **Likely causes.** The gap comes from optical items the ideal model leaves out:
  - absorber area smaller than aperture (frame and edge shading);
  - glass soiling or ageing;
  - absorptance below the nominal value;
  - reflection or dust losses.
  
  None of these are stated in the paper. They were deliberately **not** tuned in.

## Consequence for GRAIL

- **GRAIL's optical efficiency is an input, not a prediction.** GRAIL's η0 comes from an
  assumed optical factor (0.649) and is therefore a design input.
- **The check suggests the ideal-model optical path can be optimistic by about 6–8 %.** A
  similar margin should be stated as an uncertainty on GRAIL's η0, and so on its annual yield.
- **The heat-loss side (a1) is supported by this check.** This is the side on which GRAIL's
  advantage rests.

This is a method check on a different collector, **not** an experimental validation of GRAIL.
**V5 remains OPEN.**
