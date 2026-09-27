# Generator scripts (the Python files the JSON files were made with)

These are **byte-identical copies** of the scripts in the project working tree, kept here so every
writer is in one place. They are for reading and tracing. Most of them need the CFD / OpenFOAM
results, the CAD kernel, or the original Linux folder layout (`/home/claude/grail_cfd/...`), so they
do not run on a Mac as they are. The Stage 3/6/7 ones can be re-run through `15_Run_in_VSCode`.

`writer` = its json.dump writes one or more of the delivered JSON files. `support` = a local module
that a writer imports.

| role | script (working-tree path) | MD5 | identical copy already in the package | JSON files it writes |
|---|---|---|---|---|
| writer | `02_geometry/build_strips.py` | `d0f8765cbcd9a43f156af24f12be74aa` | `03_CAD/geometry_scripts/build_strips.py` | strip_build.json |
| writer | `02_geometry/gate1_channels.py` | `837eb90f3d164ca1fa645fcdd6883600` | `03_CAD/geometry_scripts/gate1_channels.py` | gate1_channels.json |
| writer | `02_geometry/gate1_final.py` | `6e691ddfc70b6f6e0d2ff2faa0746bfb` | `03_CAD/geometry_scripts/gate1_final.py` | gate1_profile.json |
| writer | `02_geometry/gate1_grading2.py` | `d3b3c725414022c3148567e46ef1901c` | `03_CAD/geometry_scripts/gate1_grading2.py` | gate1_grading.json |
| writer | `02_geometry/step_audit.py` | `b046b48fcbda1eeb529b54d8baaa94ff` | `03_CAD/geometry_scripts/step_audit.py` | step_solids.json |
| writer | `02_geometry/tessellate.py` | `3784840b0e81249c8cbe5398a5756a2d` | `03_CAD/geometry_scripts/tessellate.py` | tessellate_report.json |
| writer | `05_validation/analyse.py` | `162e47c4fcdd3bdd73b5312eaf6da793` | no, only here | uncertainty_summary.json, uncertainty_summary_rev1.json |
| writer | `05_validation/campaign_grid_correction.py` | `a2f3e3c6ea7f823310c6bfc746a4e40c` | no, only here | grid_correction.json |
| writer | `05_validation/closeout.py` | `2c92c738404737ef55b880703aa88726` | no, only here | closeout.json |
| writer | `05_validation/gci_3d.py` | `503f8ef41155e83b32a3578a4aa23903` | no, only here | gci_3d.json |
| writer | `05_validation/gci_plate.py` | `0a3e19bfe51e380146aa81393164bd91` | no, only here | gci_plate.json |
| writer | `05_validation/htc_level.py` | `79a06b90000b83ac098c574fea9b4025` | no, only here | htc_L1.json, htc_L2.json, htc_L3.json |
| writer | `05_validation/hwb_validation.py` | `098d1c132319c8ff09282e40ec3cb0f8` | no, only here | hwb_validation.json |
| writer | `05_validation/mc_uncertainty.py` | `e4dd3f2bd5062307544fb19c71b5ef0b` | no, only here | mc_summary.json |
| writer | `05_validation/nu_corrected.py` | `da782b4578b6fba202ea943e91e9dd68` | no, only here | nu_corrected.json |
| writer | `05_validation/rev2_analysis.py` | `fa5bbe68d5e9be9df84b405f16004349` | no, only here | rev2_analysis.json |
| writer | `05_validation/section_conduction.py` | `bd0173e2d751df88ad0139937e9f32fa` | no, only here | section_conduction.json |
| writer | `06_domain_equiv/domain_fields.py` | `3c6f203a9bfc97a02f94763ba9558239` | no, only here | domain_fields.json |
| writer | `06_domain_equiv/domain_study.py` | `6120bea1ae8566faa418c84e972006c4` | no, only here | domain_study.json |
| writer | `19_rev41/audit_rev41.py` | `2f130af2cea0197f2e9e6c3dc10e8eb1` | `09_Records_MD/audit_rev41.py` | rev41_comparison.json |
| writer | `tools/auto_stop.py` | `95465e86618c3f037c7ba755dd54bb9c` | `10_Code/model_and_cfd/auto_stop.py` | bench_alt_nu48_nr4_nx120.json, bench_alt_nu96_nr8_nx120.json, bench_alt_nx240.json, bench_co_nu48_nr4_nx120.json, bench_co_nu96_nr8_nx120.json, bench_co_nx120_m1p0.json, bench_co_nx120_m4p5.json, bench_co_nx240.json |
| writer | `tools/campaign2.py` | `acf16f3ad113125051212e46acbbf920` | `10_Code/model_and_cfd/campaign2.py` | rev1_vs_rev2.json |
| writer | `tools/campaign3.py` | `915374abc6a82360906b6166fb14d6e7` | `10_Code/model_and_cfd/campaign3.py` | rev2_vs_rev3.json |
| writer | `tools/grail_bench.py` | `2123d67c5ba2ac9002429d28c00d9aaf` | `10_Code/model_and_cfd/grail_bench.py` | rom_const_nu.json, rom_const_nu_nx60flow.json |
| writer | `tools/make_solver_video.py` | `b1b88b511315c110d4ac3c2b7ba166cd` | `10_Code/model_and_cfd/make_solver_video.py` | solver_co_current.json, solver_counter_current.json |
| writer | `tools/nu_extract.py` | `a09dfe1967e38474b5c8553fc87047f8` | `10_Code/model_and_cfd/nu_extract.py` | nu_alt_nx60.json, nu_co_nu48_nr4_nx120.json, nu_co_nu96_nr8_nx120.json, nu_co_nx120.json, nu_co_nx120_m1p0.json, nu_co_nx120_m4p5.json, nu_co_nx240.json, nu_co_nx60.json |
| writer | `tools/rev4_compare.py` | `8b03fa15822d51bb6334d767d0833b71` | `10_Code/model_and_cfd/rev4_compare.py` | rev3_vs_rev4.json |
| writer | `tools/stage3_ann.py` | `27e30d4971f1745ed60246a5bfbf99a2` | `12_Stages_3-5-6-7/code/stage3_ann.py` | stage3_report.json |
| writer | `tools/stage6_fit.py` | `f73995a9aab7f3c20298d97d97d8cb5f` | `12_Stages_3-5-6-7/code/stage6_fit.py` | efficiency_correlations.json |
| writer | `tools/stage7_annual.py` | `0475f2ca2b9d37e27c328aab5d6026df` | `12_Stages_3-5-6-7/code/stage7_annual.py` | stage7_results.json |
| support | `tools/grail_cht.py` | `d12faa81d5a4ffbb4f593d3a4e8f75d8` | `10_Code/model_and_cfd/grail_cht.py` | - |
| support | `tools/grail_ext.py` | `62b093a2c7a1030a1d0a7c51781f4da9` | `10_Code/model_and_cfd/grail_ext.py` | - |
| support | `tools/campaign.py` | `1f6a0f2115a92f913b70f7cae2bdb44a` | `10_Code/model_and_cfd/campaign.py` | - |
| support | `tools/figstyle.py` | `c5f7d2722914e039124d28aed1d31638` | `10_Code/model_and_cfd/figstyle.py` | - |
| support | `tools/cht_post.py` | `c1ce3708e79c5aa298b84e40526ae40d` | `10_Code/model_and_cfd/cht_post.py` | - |
| support | `tools/stage7_weather.py` | `382be343128da71814cb42b7073c6314` | `12_Stages_3-5-6-7/code/stage7_weather.py` | - |
| support | `03_mesh/cht_solid2.py` | `dfb7468ec966f0c1734e25a255154ef2` | no, only here | - |

Not a writer of any delivered file: `02_geometry/gate1_grading.py` (it wrote an earlier gate1_grading.json that `gate1_grading2.py` replaced), so it is not copied here; it is in `03_CAD/geometry_scripts/`.
