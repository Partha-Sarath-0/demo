# GRAIL Collector — CFD study. Reproducibility guide

Everything here was computed in this project. No number is carried from a textbook, a
correlation or another author's paper unless it is labelled as such.

## Headline results

All numbers below are from the **Rev 2** campaign, recomputed at the grid-extrapolated
Nusselt number `nu_cfd` = 2.9238 (`10_dataset/GRAIL_CFD_dataset_rev2.csv`, 300 cases, none
rejected). Rev 1 is kept on disk and is superseded, not deleted.

| quantity | value | expanded uncertainty, k = 2 |
|---|---|---|
| efficiency, alternating vs co-current | **−4.33 %** | ± 2.34 pp |
| plate temperature spread, RMS | **−20.83 %** | ± 12.09 pp |
| plate spread, peak-to-peak | −11.57 % | ± 12.06 pp (spans zero — do not claim) |
| loss coefficient | −0.90 % | ± 22.93 pp (spans zero — do not claim) |
| efficiency curve, co-current | η₀ = **0.60010**, F_R·U_L = **1.923 W/m²K** | R² = 0.99993 |

The alternating arrangement **costs about 4 % of efficiency** and **buys about 21 % better
plate temperature uniformity**, at every mass flow sampled from 1.2 to 4.3 g/s.

### Three things a reader of an earlier draft must know

1. **There is no mass-flow threshold.** The earlier claim that alternating is *worse* below
   1.81 g/s is **withdrawn** (CR-15). It came from a biased Nusselt number and from 9 censored
   low-flow cases.
2. **The uniformity benefit is model-form limited.** Carrying the measured Nu(ξ) instead of a
   constant, at the same mean, moves it from −21.1 % to −6.9 % — 14 percentage points, larger
   than every other uncertainty combined (CR-16). The efficiency result is unaffected.
3. **The peak-to-peak spread and the loss coefficient are not distinguishable from zero**
   across the campaign and should not be claimed.

## Environment

```
OpenFOAM v1912 (ESI), package 1912.200626-2build3   gmsh 4.15.2   Open MPI 4.1.6
Python 3.11, numpy / scipy / matplotlib / pyvista 0.48.4
2 cores, 7 GB RAM
```
Geometry: `01_cad/Grail_Collector_2.step`, md5 `e3ca020c159abf017138feabe8811e05`

## Run order

Each step depends only on the ones above it.

```
# 1. geometry and mesh
python3 02_geometry/step_audit.py            # Gate 1: 129 solids, envelope, face counts
python3 02_geometry/gate1_final.py           # 12/12 geometry checks
python3 03_mesh/ogrid.py 48 8 200 ch05.msh   # the baseline channel mesh
python3 03_mesh/plate_mesh.py 48 8 200 plate12 12   # all 12 channels + roll-bond solid

# 2. 3-D baseline, OpenFOAM
./05_validation/run_gci_3d.sh L1 2           # 34,304 cells
#   the medium level IS 04_baseline/ch05_flow, already run
./05_validation/run_gci_3d.sh L3 2           # 356,400 cells
python3 05_validation/extract_3d.py <case> <label>
python3 05_validation/htc_level.py <case> <out.json>   # Nu, original method
python3 05_validation/gci_3d.py              # three-level GCI

# 3. uncertainty
python3 05_validation/gci_plate.py           # conjugate grid, 4 levels
python3 05_validation/mc_uncertainty.py 200 2  # paired Monte Carlo
python3 05_validation/campaign_grid_correction.py
python3 05_validation/nu_corrected.py        # the Nusselt bias, measured
python3 05_validation/analyse.py             # combine

# 4. validation and the three filings
python3 05_validation/hwb_validation.py      # analytical Hottel-Whillier-Bliss
python3 06_domain_equiv/domain_study.py      # CR-03
python3 06_domain_equiv/domain_fields.py     # fields for the figure
python3 07_mechanism/pcm_study.py            # filing 2
python3 07_mechanism/thermotropic_study.py   # filing 3

# 5. figures
python3 tools/figs_geometry.py tools/figs_campaign.py tools/figs_sensitivity.py
python3 tools/figs_mesh.py tools/figs_assembly.py
python3 tools/figs_uncertainty.py tools/figs_filings.py tools/fig_g1.py
python3 tools/make_solver_video.py alt ; python3 tools/make_solver_video.py co
```

## Solver extension points

`tools/grail_cht.py` and `tools/transient.py` carry five hooks that default to no-ops, so
adding physics never touches the solved equations. Verified: co-current 110x120 gives
eta 0.596553 and Tp_std 6.72400 before and after the hooks were added, bit-identical.

| hook | purpose | used by |
|---|---|---|
| `_q_absorbed(Tg)` | absorbed flux may depend on glazing temperature | `GrailThermo` |
| `_extra_couplings(kt_y, idx)` | extra matrix entries, e.g. periodic lateral BC | `GrailDomain` |
| `_rear_init(dt)` | set up a rear-path state | `GrailPCM` |
| `_rear_coupling(Tp, dt)` | implicit rear coupling | `GrailPCM` |
| `_rear_update(Tp_new, dt)` | advance the rear state | `GrailPCM` |

## Figures

| set | what | count |
|---|---|---|
| C1 - C22 | geometry, hydraulics, campaign, mechanism, sensitivity, QC | 22 |
| M1 - M10 | mesh: channel sections through to the complete assembly | 10 |
| U1 - U4 | uncertainty: grid, inputs, sensitivity, campaign correction | 4 |
| G1 | 3-D grid convergence and the Nusselt correction | 1 |
| D1 - D2 | domain equivalence, CR-03 | 2 |
| P1 - P4 | PCM and thermotropic filings | 4 |
| V1 | validation against Hottel-Whillier-Bliss | 1 |

## Provenance records

| file | covers |
|---|---|
| `correction_register.md` | every correction, CR-01 to CR-17, with what to discard |
| `gate1_geometry_audit.md` | what the STEP contains and what it does not |
| `geometry_route_decision.md` | why NURBS evaluation, not gmsh tessellation |
| `gate2_mesh_strategy.md` | O-grid versus snappyHexMesh |
| `material_database.md` | roadmap 5.3 quoted verbatim, with the simplifications named |
| `assembly_mesh_record.md` | how M6 - M10 were built and what they assert |
| `video_record.md` | the solver videos |
| `uncertainty_record.md` | the full V&V assessment, including what it overturned |
| `domain_equivalence_record.md` | CR-03 closed |
| `pcm_record.md` | filing 2 |
| `thermotropic_record.md` | filing 3 |
| `hwb_validation_record.md` | the independent analytical check |
| `section_conduction_record.md` | 3-D conduction in the metal: the fin treatment verified |
| `cht_attempt_record.md` | the conjugate run that did not converge, in full |

## What this study does NOT claim

1. **No experimental validation.** The check is against the analytical Hottel-Whillier-Bliss
   model, which agrees to +0.218 % on co-current, and against the roadmap's own η₀ and F_R·U_L
   targets, which the Rev 2 efficiency curve reproduces to 0.60010 and 1.923. Both are
   self-consistency, not validation against measurement.
2. **No converged 3-D conjugate CFD run.** `chtMultiRegionSimpleFoam` diverged and no
   conjugate result is reported anywhere (CR-17, `cht_attempt_record.md`). The question it was
   meant to close — does the plate solver's fin treatment of the metal hold — was answered
   instead by a 2-D finite-element conduction solution in the as-built roll-bond section
   (`section_conduction_record.md`), which verifies it to 0.44 K.
3. **The uniformity benefit carries a constant Nusselt number.** See CR-16 and section 11.4 of
   the uncertainty record. This is the largest open item.
4. **No view-factor radiation.** At ε = 0.04 radiation is under 1 % of absorbed power, so the
   linearised treatment is adequate; this is a judgement, not a demonstration.
5. **PCM stagnation protection is model-only.** The tray reaches 200 °C in the model; RT55
   would have decomposed. No degradation physics is included.
6. **Thermotropic switching is steady-state.** Switching rate, cycling and the transient into
   stagnation are not modelled.
7. **No ANN, surrogate, optimisation or annual-performance modelling.** Out of scope by
   instruction, and nothing here should be read as implying it.

## Open items

- **Nu(ξ) in the campaign** — bounded at 14.2 pp (CR-16) but not removed. The largest item.
- a fourth 3-D grid level to tighten the 11.6 % GCI on Nu — estimated 20+ h on two cores,
  declared infeasible here
- a converged 3-D conjugate run — the mesh is built and verified, the solver is not
- experimental validation
- **DESIGN_REVIEW_REQUIRED**: whether τ_glz_sys = 0.833 already includes the thermotropic
  layer. This cannot be resolved from the roadmap and needs a human decision.

## Figure style

Every figure is drawn through `tools/figstyle.py`, which fixes one specific failure of the
first generation: the text that carried the result was the first thing to get crowded out.
Nothing is below 10 pt; `constrained_layout` is allowed to move text apart; annotations sit in
a box in whichever corner the data is not; two series use one validated colour pair and more
than two, if ordered, use a single-hue ramp with a colourbar rather than a cycled colour list.

The pair `#2472b8` / `#c0522d` passes every check of the palette validator on a light surface:
lightness band, chroma floor, CVD separation (ΔE 20.5 protan, 28.5 tritan), normal-vision
separation (ΔE 27.4) and contrast. The previous pair failed the chroma floor — the blue read
as grey.

### How the figures are checked

`tools/textcheck.py` renders every figure through the real scripts with `savefig`
intercepted, asks the renderer for the bounding box of every piece of text on the canvas, and
reports three defects:

| check | what it catches |
|---|---|
| OVERLAP | two texts whose boxes intersect — a label printed through another label |
| ON DATA | a legend or annotation parked on top of markers, lines or bars |
| TINY | any text below 8.5 pt |

It has to know what is and is not a real defect, so it ignores tick labels the locator made
for positions outside the view (never drawn), treats a twin axis as one axis rather than two
(its duplicate ticks are not a collision), and does not count an `axhspan` band as an
obstruction, because a label on its own band is intentional. The current state of the suite is
**0 OVERLAP, 0 ON DATA, 0 TINY across all 55 figures.**

Two fixes in `figstyle.py` run automatically on every figure at save time, so this stays true
for figures added later:

- **`autoplace_legends`** puts each legend in the corner of its axes with least under it.
  matplotlib's own `loc="best"` scores only `Line2D` vertices — it is blind to scatter
  offsets and to bar patches, which is why legends kept landing on the campaign scatter plots.
  This scores lines, scatter, bars *and* existing annotations, analytically from one render.
- **`plain_log_ticks`** writes plain numbers on a log axis spanning less than a decade.
  matplotlib labels such an axis `6 x 10^0`, `4 x 10^0`, which is unreadable on an axis that
  simply runs from 2 to 7 mm.

### Symbols and units on the figures

Dataset column names and solver variable names used to leak straight onto the axes: a plot
labelled `mdot_total_kg_s` or `T_amb_K` shows the reader a database schema, not physics.
`figstyle.mathify` maps every one of them to how the thesis writes it — **ṁ** with an overdot,
**T** with a subscript, **η**, **τ**, **α**, **ε**, **λ**, **Δp**, **Nu** — and rewrites units
as `W/m²`, `mm²`, `K m²/W`, `K⁴`. It runs on every figure at save time alongside the placement
pass, so it also covers figures added later.

Two details that had to be right for it to work:

- It splits each label on existing `$...$` spans and substitutes only outside them, so a
  label that already contains maths cannot be corrupted.
- Tick labels are rewritten by **reading what the axis is currently showing** and freezing the
  result, not by inspecting the formatter's type. `set_xticklabels` installs a `FuncFormatter`
  in current matplotlib, not the `FixedFormatter` an earlier version of this looked for, so a
  type check left the correlation heatmap's category labels untouched.
