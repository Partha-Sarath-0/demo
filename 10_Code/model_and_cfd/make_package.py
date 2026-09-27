"""
GRAIL — assemble the deliverable package.

The working tree is 3 GB, almost all of it OpenFOAM field data that nobody outside the run
needs. This collects what a reader actually uses - every figure, every video, every dataset,
every result JSON, every record, and all the code that produced them - into one zip with a
folder per kind of thing, and writes an INDEX that says what each file is.

Nothing is deleted from the working tree.
"""
import os, sys, json, shutil, zipfile, csv, datetime, hashlib

SRC = "/home/claude/grail_cfd"
STAGE = "/tmp/claude-0/package/GRAIL_Collector_CFD_Study"
OUTZIP = "/mnt/user-data/outputs/GRAIL_Collector_CFD_Study.zip"

# ------------------------------------------------------------------ figure grouping
FIG_GROUPS = {
    "01_geometry_and_sections": ["C1_geometry", "C2_sections", "C3_pressure_drop",
                                 "C4_reynolds", "C5_buoyancy"],
    "02_mesh": ["M1_section_inlet", "M2_section_outlet", "M3_root_fillet", "M4_swept_mesh",
                "M5_multichannel", "M6_assembly_surface_mesh", "M7_cfd_mesh_in_assembly",
                "M8_cutaway", "M9_inlet_end", "M10_full_plate_mesh"],
    "03_baseline_3d_cfd": ["C6_3d_hydraulics", "C7_3d_thermal", "C8_3d_velocity",
                           "C9_3d_temperature"],
    "04_campaign_results": ["C10_efficiency", "C11_hottel_whillier", "C12_temperature_rise",
                            "C13_wind", "C17_correlation", "C18_grading", "C19_bridge",
                            "C20_distributions", "C22_quality"],
    "05_the_mechanism": ["C14_mechanism_fields", "C15_distribution", "C16_bridge_conduction",
                         "C21_mechanism_campaign", "F8_mechanism_fields",
                         "F9_temperature_distribution", "F10_bridge_conduction"],
    "06_verification_and_uncertainty": ["U1_grid_convergence", "U2_input_uncertainty",
                                        "U3_sensitivity", "U4_campaign_correction",
                                        "G1_3d_grid_convergence", "D1_domain_equivalence",
                                        "D2_domain_fields", "V1_hwb_validation",
                                        "V2_section_conduction", "R1_rev1_vs_rev2"],
    "07_patent_filings": ["P1_pcm_transient", "P2_thermotropic", "P3_pcm_state",
                          "P4_thermotropic_effect"],
}

FIG_CAPTIONS = {
    "C1_geometry": "Channel geometry along the flow axis. The section CONVERGES, G = 0.539935.",
    "C2_sections": "Channel cross-section at inlet, mid-span and outlet, on the CAD surface.",
    "C3_pressure_drop": "Channel pressure drop and its departure from the circular-duct reference.",
    "C4_reynolds": "Reynolds number RISES along the converging channel.",
    "C5_buoyancy": "Buoyancy screening: buoyant head against friction at the design point.",
    "M1_section_inlet": "CFD mesh, channel cross-section at the inlet.",
    "M2_section_outlet": "CFD mesh, channel cross-section at the outlet.",
    "M3_root_fillet": "Root-fillet detail, r = 0.5 mm tangent blend.",
    "M4_swept_mesh": "Structured hexahedral mesh swept along one channel.",
    "M5_multichannel": "Four adjacent channels at the inlet, showing the conductive bridge.",
    "M6_assembly_surface_mesh": "Complete collector assembly, surface mesh, 128 of 129 solids.",
    "M7_cfd_mesh_in_assembly": "The CFD mesh in position inside the assembly.",
    "M8_cutaway": "Cut-away through the CFD mesh.",
    "M9_inlet_end": "CFD mesh at the inlet end of the absorber.",
    "M10_full_plate_mesh": "Full 12-channel absorber, complete CFD mesh.",
    "C6_3d_hydraulics": "3-D OpenFOAM channel: area, velocity and pressure along the flow.",
    "C7_3d_thermal": "3-D OpenFOAM channel: fluid temperature against the energy balance.",
    "C8_3d_velocity": "3-D velocity magnitude, sections along the channel.",
    "C9_3d_temperature": "3-D fluid temperature, sections along the channel.",
    "S5_3d_temperature": "EXCLUDED - the volume render degenerated (x compressed 83:1) and "
                         "shows almost nothing. C9 carries the same data correctly.",
    "S6_3d_velocity": "EXCLUDED - same render failure as S5. C8 carries the same data.",
    "S1_hydraulics": "byte-identical earlier copy of C6_3d_hydraulics.",
    "S2_thermal": "byte-identical earlier copy of C7_3d_thermal.",
    "S3_velocity_sections": "byte-identical earlier copy of C8_3d_velocity.",
    "S4_temperature_sections": "byte-identical earlier copy of C9_3d_temperature.",
    "C10_efficiency": "Efficiency against irradiance and reduced temperature, Rev 2.",
    "C11_hottel_whillier": "Hottel-Whillier curve fitted to the Rev 2 dataset.",
    "C12_temperature_rise": "Temperature rise and plate overheat versus irradiance.",
    "C13_wind": "Sensitivity to wind speed.",
    "C17_correlation": "Input/output correlation across the Rev 2 dataset.",
    "C18_grading": "Grading sensitivity: endpoint ratio G and exponent lambda_G.",
    "C19_bridge": "Bridge-width sensitivity across 20 - 37 mm.",
    "C20_distributions": "Distributions of efficiency, plate temperature and spread.",
    "C22_quality": "Dataset quality control: energy conservation, convergence, Reynolds.",
    "C14_mechanism_fields": "Absorber temperature field, parallel against alternating.",
    "C15_distribution": "Absorber temperature distribution - the flattening, and what it is worth.",
    "C16_bridge_conduction": "Heat crossing each bridge midline - the mechanism, measured.",
    "C21_mechanism_campaign": "The mechanism across the campaign.",
    "F8_mechanism_fields": "Mechanism fields at matched mass flow (same as C14).",
    "F9_temperature_distribution": "Temperature distribution, matched flow and matched mean.",
    "F10_bridge_conduction": "Bridge conduction per midline (same as C16).",
    "U1_grid_convergence": "Grid convergence of the claim quantities, with GCI bands.",
    "U2_input_uncertainty": "Propagated input uncertainty, paired Monte Carlo, 200 samples.",
    "U3_sensitivity": "Which inputs the results actually depend on. nu_cfd carries 91 %.",
    "U4_campaign_correction": "Campaign-grid correction. NOTE: the 1.81 g/s threshold is WITHDRAWN.",
    "G1_3d_grid_convergence": "3-D grid convergence and the Nusselt correction to 2.9238.",
    "D1_domain_equivalence": "Domain equivalence, CR-03: only 2-channel periodic is valid.",
    "D2_domain_fields": "The same alternating solution on three domains.",
    "V1_hwb_validation": "Validation against Hottel-Whillier-Bliss. Co-current agrees to +0.22 %.",
    "V2_section_conduction": "3-D conduction in the metal: the fin treatment verified to 0.44 K.",
    "R1_rev1_vs_rev2": "The campaign at the old and the corrected Nusselt number.",
    "P1_pcm_transient": "Graded PCM tray: charge, cloud and stagnation.",
    "P2_thermotropic": "Thermotropic switching: the glazing never reaches its switching band.",
    "P3_pcm_state": "PCM state: liquid fraction and stored energy.",
    "P4_thermotropic_effect": "Thermotropic layer effect if mounted on the absorber.",
}

RESULT_JSON = {
    "campaign": [("10_dataset/rev1_vs_rev2.json",
                  "Rev 1 against Rev 2, written by the recompute itself")],
    "verification": [
        ("05_validation/rev2_analysis.json", "Rev 1 vs Rev 2, paired and campaign-average, with the censoring analysis"),
        ("05_validation/uncertainty_summary.json", "combined uncertainty, Rev 2"),
        ("05_validation/uncertainty_summary_rev1.json", "the same, as it stood at Rev 1"),
        ("05_validation/final_uncertainty.json", "final k = 2 statement"),
        ("05_validation/closeout.json", "Nu(xi) model form, PCM time step, efficiency curve"),
        ("05_validation/section_conduction.json", "3-D conduction in the metal"),
        ("05_validation/gci_3d.json", "three-level 3-D grid convergence"),
        ("05_validation/gci_3d_twolevel.json", "the two-level result it superseded"),
        ("05_validation/gci_plate.json", "conjugate plate grid, four levels"),
        ("05_validation/nu_gci.json", "GCI on the Nusselt number"),
        ("05_validation/nu_corrected.json", "the Nusselt bias, measured"),
        ("05_validation/nu_cfd_revision.json", "the revision itself"),
        ("05_validation/grid_correction.json", "campaign-grid correction, 10 operating points"),
        ("05_validation/mc_summary.json", "paired Monte Carlo summary"),
        ("05_validation/hwb_validation.json", "Hottel-Whillier-Bliss check"),
        ("05_validation/htc_L1.json", "local Nu, coarse 3-D grid"),
        ("05_validation/htc_L2.json", "local Nu, medium 3-D grid"),
        ("05_validation/htc_L3.json", "local Nu, fine 3-D grid"),
    ],
    "geometry_and_mesh": [
        ("02_geometry/gate1_channels.json", "Gate 1: every channel measured"),
        ("02_geometry/gate1_grading.json", "Gate 1: the grading law"),
        ("02_geometry/gate1_profile.json", "Gate 1: section profile along the flow"),
        ("02_geometry/step_solids.json", "what the STEP file contains"),
        ("02_geometry/tessellate_report.json", "tessellation report"),
        ("02_geometry/strip_build.json", "the reduced-domain strip build"),
        ("02_geometry/asm/groupA.json", "assembly tessellation, group A"),
        ("02_geometry/asm/groupA_fallback.json", "assembly tessellation, the 4 deferred barrels"),
        ("02_geometry/asm/groupB.json", "assembly tessellation, group B"),
        ("03_mesh/plate/plate12.json", "full 12-channel plate mesh"),
        ("03_mesh/cht/cht2ch.json", "two-region conjugate mesh (built, never solved)"),
    ],
    "mechanism_and_filings": [
        ("06_domain_equiv/domain_study.json", "CR-03 domain equivalence"),
        ("06_domain_equiv/domain_fields.json", "the fields behind figure D2"),
        ("07_mechanism/mechanism.json", "the mechanism study"),
        ("07_mechanism/mechanism_raw.json", "its raw output"),
        ("07_mechanism/pcm_study.json", "filing 2, graded PCM"),
        ("07_mechanism/thermotropic_study.json", "filing 3, thermotropic glazing"),
    ],
    "baseline_3d": [
        ("04_baseline/ch05_flow/qoi.json", "the baseline 3-D channel, quantities of interest"),
        ("05_validation/gci3d/L1/qoi.json", "3-D grid level 1"),
        ("05_validation/gci3d/L3/qoi.json", "3-D grid level 3"),
        ("09_post/htc.json", "heat-transfer coefficient extraction"),
        ("09_post/residuals.json", "solver residual history"),
        ("12_figures/axial_profiles.json", "axial profiles used by the figures"),
    ],
}

CODE = [
    ("tools", "the solver, the campaign, the figure suite and the packaging"),
    ("02_geometry", "geometry audit and tessellation"),
    ("03_mesh", "mesh generation"),
    ("05_validation", "every verification and uncertainty script"),
    ("06_cht", "the conjugate case builder (built, never solved)"),
    ("06_domain_equiv", "CR-03 domain study"),
    ("07_mechanism", "the mechanism study and the two filings"),
    ("09_post", "post-processing"),
]
CODE_EXT = {".py", ".sh"}


def copy(src, dst):
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    shutil.copy2(src, dst)


def main():
    if os.path.exists(STAGE):
        shutil.rmtree(STAGE)
    os.makedirs(STAGE)
    idx = []
    manifest = []

    # ---------------------------------------------------------- 00 start here
    copy(SRC + "/README.md", STAGE + "/00_START_HERE/README.md")

    # ---------------------------------------------------------- 01 figures
    placed = set()
    for grp, names in FIG_GROUPS.items():
        for n in names:
            s = SRC + "/12_figures/%s.png" % n
            if os.path.exists(s):
                copy(s, STAGE + "/01_figures/%s/%s.png" % (grp, n))
                placed.add(n)
                idx.append(("01_figures/%s/%s.png" % (grp, n), FIG_CAPTIONS.get(n, "")))
    BROKEN = {"S5_3d_temperature", "S6_3d_velocity"}
    for f in sorted(os.listdir(SRC + "/12_figures")):
        if f[:-4] in BROKEN:
            continue
        if f.endswith(".png") and f[:-4] not in placed:
            copy(SRC + "/12_figures/" + f, STAGE + "/01_figures/08_duplicate_names/" + f)
            idx.append(("01_figures/08_duplicate_names/" + f, FIG_CAPTIONS.get(f[:-4], "")))
    r1 = SRC + "/12_figures/rev1_nu3.4282"
    if os.path.isdir(r1):
        for f in sorted(os.listdir(r1)):
            copy(r1 + "/" + f, STAGE + "/01_figures/09_superseded_rev1/" + f)
        idx.append(("01_figures/09_superseded_rev1/",
                    "the figure set as it stood at Nu = 3.4282, kept, superseded by CR-13"))

    # ---------------------------------------------------------- 02 videos
    vd = SRC + "/12_figures/video"
    if os.path.isdir(vd):
        for f in sorted(os.listdir(vd)):
            if f.endswith((".mp4", ".gif")):
                copy(vd + "/" + f, STAGE + "/02_videos/" + f)
                idx.append(("02_videos/" + f, "solver animation"))

    # ---------------------------------------------------------- 03 datasets
    for s, note in (("10_dataset/GRAIL_CFD_dataset_rev2.csv",
                     "THE dataset. 300 cases at the corrected Nu = 2.9238."),
                    ("10_dataset/GRAIL_CFD_dataset_corrected.csv",
                     "Rev 1, 291 cases at Nu = 3.4282. Superseded, kept."),
                    ("11_failures/failures_rev2.csv", "Rev 2 rejections: none."),
                    ("11_failures/failures.csv",
                     "Rev 1 rejections: 9 rows, all alternating, all low flow. See CR-14."),
                    ("05_validation/mc_samples.csv", "the 200 paired Monte Carlo draws")):
        if os.path.exists(SRC + "/" + s):
            copy(SRC + "/" + s, STAGE + "/03_datasets/" + os.path.basename(s))
            idx.append(("03_datasets/" + os.path.basename(s), note))

    # ---------------------------------------------------------- 04 results
    for grp, items in RESULT_JSON.items():
        for rel, note in items:
            if os.path.exists(SRC + "/" + rel):
                dst = "04_results/%s/%s" % (grp, os.path.basename(rel))
                copy(SRC + "/" + rel, STAGE + "/" + dst)
                idx.append((dst, note))

    # ---------------------------------------------------------- 05 records
    for f in sorted(os.listdir(SRC + "/14_provenance")):
        if f.endswith(".md"):
            copy(SRC + "/14_provenance/" + f, STAGE + "/05_records/" + f)
            idx.append(("05_records/" + f, ""))
    for f in sorted(os.listdir(SRC + "/13_tables")):
        copy(SRC + "/13_tables/" + f, STAGE + "/06_tables/" + f)
        idx.append(("06_tables/" + f, ""))

    # ---------------------------------------------------------- 07 code
    for d, note in CODE:
        base = SRC + "/" + d
        if not os.path.isdir(base):
            continue
        for root, _, files in os.walk(base):
            if "__pycache__" in root or "/processor" in root:
                continue
            for f in files:
                if os.path.splitext(f)[1] in CODE_EXT:
                    rel = os.path.relpath(os.path.join(root, f), SRC)
                    copy(os.path.join(root, f), STAGE + "/07_code/" + rel)
        idx.append(("07_code/" + d + "/", note))

    # ---------------------------------------------------------- 08 cad
    for f in sorted(os.listdir(SRC + "/01_cad")):
        if f.lower().endswith((".step", ".stp")):
            copy(SRC + "/01_cad/" + f, STAGE + "/08_cad/" + f)
            h = hashlib.md5(open(SRC + "/01_cad/" + f, "rb").read()).hexdigest()
            idx.append(("08_cad/" + f, "the source geometry, md5 " + h))

    # ---------------------------------------------------------- index
    write_index(STAGE, idx)

    # ---------------------------------------------------------- zip
    os.makedirs(os.path.dirname(OUTZIP), exist_ok=True)
    if os.path.exists(OUTZIP):
        os.remove(OUTZIP)
    n = 0
    with zipfile.ZipFile(OUTZIP, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as z:
        for root, _, files in os.walk(STAGE):
            for f in sorted(files):
                p = os.path.join(root, f)
                z.write(p, os.path.relpath(p, os.path.dirname(STAGE)))
                n += 1
    print("packaged %d files -> %s  (%.1f MB)" % (n, OUTZIP, os.path.getsize(OUTZIP) / 1e6))
    return OUTZIP


def write_index(stage, idx):
    from collections import OrderedDict
    groups = OrderedDict()
    for path, note in idx:
        top = path.split("/")[0]
        groups.setdefault(top, []).append((path, note))
    L = []
    L.append("# GRAIL Collector — CFD study: what is in this package\n")
    L.append("Generated %s. Every number here was computed in this project.\n"
             % datetime.date.today().isoformat())
    L.append("**Read `00_START_HERE/README.md` first.** It carries the headline results and, "
             "just as importantly, the three things a reader of an earlier draft has to know: "
             "the mass-flow threshold is withdrawn, the uniformity benefit is model-form "
             "limited, and two of the four campaign differences are not distinguishable from "
             "zero.\n")
    L.append("## Folders\n")
    L.append("| folder | what is in it |")
    L.append("|---|---|")
    for k, desc in (("00_START_HERE", "the README: headline results, how to reproduce, what is not claimed"),
                    ("01_figures", "every figure, grouped by what it shows; Rev 1's figures kept under 09_superseded_rev1"),
                    ("02_videos", "solver animations"),
                    ("03_datasets", "the CFD campaign as CSV, both revisions, plus the rejection lists"),
                    ("04_results", "every result as JSON, grouped"),
                    ("05_records", "the provenance records, including the correction register CR-01 to CR-17"),
                    ("06_tables", "result tables in markdown"),
                    ("07_code", "every script that produced any of it"),
                    ("08_cad", "the source STEP geometry")):
        if k in groups or k == "00_START_HERE":
            L.append("| `%s` | %s |" % (k, desc))
    L.append("")
    L.append("## Where to start, by question\n")
    L.append("| if you want to know | open |")
    L.append("|---|---|")
    for q, f in (("what the study found",
                  "`00_START_HERE/README.md`"),
                 ("whether the alternating arrangement is worth it",
                  "`01_figures/04_campaign_results/` and `05_records/uncertainty_record.md` §11"),
                 ("how the mechanism works",
                  "`01_figures/05_the_mechanism/` and `01_figures/06_verification_and_uncertainty/V2_section_conduction.png`"),
                 ("how much to trust it",
                  "`05_records/uncertainty_record.md` and `05_records/correction_register.md`"),
                 ("what changed from an earlier draft",
                  "`05_records/correction_register.md`, entries CR-13 to CR-17"),
                 ("what did not work",
                  "`05_records/cht_attempt_record.md`"),
                 ("the raw numbers",
                  "`03_datasets/GRAIL_CFD_dataset_rev2.csv`")):
        L.append("| %s | %s |" % (q, f))
    L.append("")
    L.append("## Every file\n")
    for top, items in groups.items():
        L.append("### %s\n" % top)
        L.append("| file | what it is |")
        L.append("|---|---|")
        for path, note in items:
            L.append("| `%s` | %s |" % (path[len(top) + 1:] or "(folder)", note))
        L.append("")
    open(stage + "/INDEX.md", "w").write("\n".join(L) + "\n")


if __name__ == "__main__":
    main()
