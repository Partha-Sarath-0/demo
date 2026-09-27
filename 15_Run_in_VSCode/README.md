# Running and viewing the GRAIL package in VS Code

## 1. One-time setup (Mac)

1. **Open the right folder.** In VS Code choose **File → Open Folder…** and pick
   `GRAIL_Collector_Complete_Final` itself, not the parent `Solar Minor Project` folder.
   The task list only appears when this folder is the workspace root.
2. **Install the task list (once).** Open the VS Code terminal (⌃`) and run:
   ```
   python3 15_Run_in_VSCode/run.py install-vscode
   ```
   This copies `15_Run_in_VSCode/vscode_config/*.json` into the package's `.vscode/` folder,
   which is where VS Code looks for tasks. If you already had your own files there, it keeps
   them with the suffix `.before_grail`.
3. **Install the recommended extensions.** VS Code offers them automatically (from
   `.vscode/extensions.json`):
   * *Python* (ms-python.python). Needed.
   * *Rainbow CSV* (mechatroner.rainbow-csv). Optional; colours CSV columns.
4. **Choose a Python 3.10+ interpreter.** Press ⌘⇧P, run **Python: Select Interpreter**, and
   pick one. To make a clean environment, use **Python: Create Environment → Venv**.
5. **Install the Python packages.** In the VS Code terminal (⌃`), run:
   ```
   pip install -r 15_Run_in_VSCode/requirements.txt
   ```
   To use the exact versions the results were made with, install `requirements-tested.txt` instead.
6. **Install the optional programs:**
   * **GNU Octave** for the Octave tasks: `brew install octave`
   * **Scilab 2024.x** for the Xcos tasks: download it from scilab.org and drag it to Applications.

   The launcher finds both automatically. If it can't, set `GRAIL_OCTAVE` or `GRAIL_SCILAB` to
   the full path of the program.
7. **Check the setup.** Press ⌘⇧P → **Tasks: Run Task** → **0. Check setup**. It lists what is
   installed and what is missing.

## 2. How to run things

Press ⌘⇧P → **Tasks: Run Task**, then pick a task. ⌘⇧B runs the default task, Stage 7 annual.

Everything goes through one launcher, `15_Run_in_VSCode/run.py`. You can also run it from the
terminal:
```
python3 15_Run_in_VSCode/run.py            # lists all commands
python3 15_Run_in_VSCode/run.py stage7-annual
```

Times below are from the test machine; a Mac will be similar or faster.

| Task | What it re-runs | Time | Needs |
|---|---|---|---|
| **Stage 7: weather check** | POA irradiance for the Berhampur TMY by model and tilt | ~5 s | Python |
| **Stage 7: annual SDHW + economics + sizing** | 8760-h collector + tank simulation, solar fraction, LCOH, payback, sizing for 1–4 modules | ~20 s | Python |
| **Stage 6: efficiency fit** | ISO 9806 η0, a1, a2 from the virtual test matrix | ~1 s | Python |
| **Stage 5: NSGA-II optimisation** | Pareto fronts on the ANN surrogate | ~20 s | Python |
| **Stage 3: ANN surrogate + SHAP** | 10-seed ANN ensemble, GPR, 5-fold CV, SHAP, on `06_Datasets/GRAIL_CFD_dataset_FINAL_rev4.2.csv` | ~5 min | Python |
| **Stage 5: verify optimum in GRAIL-CHT** | 8 optimum points recomputed with the CHT solver | ~8–15 min | Python |
| **Stage 6: virtual test matrix** | 25 GRAIL-CHT points behind the efficiency fit | ~40–60 min | Python |
| **Figures F15–F19** | Redraws the Stage 3–7 figures from the results in `work/` | ~10 s | Python |
| **Octave: annual model** | MATLAB-compatible version of the system model | ~2 min | Octave |
| **Octave: compare with Python** | PASS/FAIL check against the Python Stage 7 results | ~1 s | Octave |
| **Octave: continuous-draw reference** | Reference solution used to verify Xcos | ~20–40 min | Octave |
| **Xcos: run full year** | Builds the block diagram, saves it and simulates the 4 cases | ~40 s | Scilab |
| **Xcos: compare** | PASS/CHECK against the Octave reference | ~1 s | Python |
| **Xcos: open block diagram** | Opens `GRAIL_system.zcos` in the Xcos editor so you can see the blocks | — | Scilab |
| **Compare re-run results with delivered results** | Writes `work/compare_report.md` | ~1 s | Python |
| **Reset work folder** | Deletes `work/` and starts again from the delivered results | ~2 s | Python |

**Suggested order:**

1. Check setup.
2. Stage 7 annual.
3. Figures.
4. Octave annual, then Octave compare.
5. Xcos run, then Xcos compare.
6. Compare re-run results with delivered results.

The slow Stage 3 / 5 / 6 CHT tasks are optional. Their delivered results are already in the
package.

## 3. Rules the launcher follows (so nothing is changed blindly)

* **The original scripts are never edited.** The Stage 3–7 scripts in `12_Stages_3-5-6-7/code`
  contain the absolute paths of the machine they were written on (`/home/claude/grail_cfd/...`),
  so they cannot run on the Mac as they are. The launcher makes copies in
  `portable_code/` with only those path strings replaced.
* **Every changed line is listed.** `portable_code/PATH_CHANGES.md` records each replaced line
  with the md5 of its source file. There are 31 lines, and every one is a path.
* **Re-runs never touch the delivered results.** Re-runs read and write only in `work/`. It
  starts as a copy of the delivered results in 12_/13_/14_ and uses the original folder names
  (20_annual, 21_surrogate, 22_system, 23_optimisation, 24_figures_stage3to7, 25_octave,
  26_xcos). The delivered results themselves are never overwritten.
* **Stages feed each other inside `work/`.** For example, re-running Stage 6 fit changes the
  correlations that Stage 7 and the figures then use.
* **Differences are reported, not hidden.** **Compare** checks every result file in `work/`
  against the delivered file and lists every numeric difference above 1e-6. Nothing is
  filtered or deleted.
* **Test result:** on the test machine these all reproduced the delivered results byte for byte:
  * Stage 7, Stage 6 fit, Stage 5 NSGA-II and the Stage 5 GRAIL-CHT verification;
  * the Stage 3 ANN/GPR test metrics and parity tables;
  * the Octave model and the Xcos model (apart from the run-time column).
* **Two expected differences in `stage3_report.json`:**
  * The recorded dataset path is different, because it is the path on the machine that ran it.
  * The SHAP mean-|SHAP| importances differ by up to about 3 %, mostly for the smallest
    importances. The SHAP KernelExplainer samples at random, so this is normal. The feature
    ranking is unchanged.
* **Expect small differences on another machine.** With other library versions (especially
  scikit-learn for Stage 3) numbers may differ in the last digits. If Stage 5 cannot load
  `ann_surrogate.pkl` because your scikit-learn version is different, run Stage 3 first; it
  writes a new surrogate into `work/21_surrogate`.

**Do not press ▶ on the files in `12_Stages_3-5-6-7/code`.** They will stop with "file not
found" because of the old paths. After any task has run once, you *can* open a file in
`15_Run_in_VSCode/portable_code/` and press ▶. Those copies have the correct paths.

**If you move or rename the package folder,** just run any task again. The copies are
regenerated with the new paths each time.

## 4. What can NOT be re-run in VS Code on a Mac

* **The full CFD dataset campaign** (`10_Code/model_and_cfd/campaign*.py`, 300 cases, several
  hours) and the OpenFOAM 3-D benchmarks. These need OpenFOAM and the original Linux working
  tree. Their results are delivered in `06_Datasets` and `07_Results_JSON` and can only be
  viewed.
* **CAD scripts** (`03_CAD/geometry_scripts`). These need the CAD kernel they were written for.
  Open the `.step` files in Fusion instead.
* **Videos.** Open the `.mp4` files in `05_Videos` directly.

## 5. Files you open and read (JSON and Markdown are not "run")

`.md` and `.json` files are documents and data, not programs.

* **Markdown:** open the file and press **⌘⇧V** for the formatted preview (or ⌘K V for a side-by-side view).
* **JSON:** VS Code shows it with folding. Right-click → **Format Document** makes it
  readable.
* **Images:** `.png` files open inside VS Code.
* **Word, PDF and video:** open `.docx`, `.pdf` and `.mp4` files from Finder.

**Start with these:**

| File | What it tells you |
|---|---|
| `00_README.md` | Package map. It still describes the Rev 4.1 CFD phase only; the Stage 3–7, Octave and Xcos folders (12–15) are described in their own READMEs |
| `02_Reports/Thesis_Abstract_FINAL.md` | Thesis abstract |
| `12_Stages_3-5-6-7/report/GRAIL_Stages_3-5-6-7_Report.docx` | Stages 3, 5, 6, 7 + Octave + Xcos report (open in Word) |
| `12_Stages_3-5-6-7/surrogate/stage3_report.json` | ANN/GPR accuracy per output, best architectures, SHAP importances |
| `12_Stages_3-5-6-7/system_model/efficiency_correlations.json` | η0, a1, a2 for alternating and parallel, fit errors, hold-out errors |
| `12_Stages_3-5-6-7/annual/stage7_results.json` | Annual yield, solar fraction, economics, all assumptions |
| `12_Stages_3-5-6-7/annual/sizing_sweep.csv` | 1–4 modules: solar fraction, LCOH, payback, stagnation temperature |
| `12_Stages_3-5-6-7/optimisation/verification_vs_GRAIL-CHT.csv` | Surrogate optimum vs CHT solver |
| `13_Octave_system_model/README.md` | Octave model and its PASS check |
| `14_Xcos_block_diagram_model/README.md` | Xcos block diagram, results, verification |
| `09_Records_MD/correction_register.md` | Every correction made during the project |
| `07_Results_JSON/validation_and_uncertainty/final_uncertainty.json` | Final uncertainty budget |
| `06_Datasets/archive/GRAIL_CFD_dataset_FINAL_rev4.2_DATA_DICTIONARY.md` | Meaning and unit of every dataset column |

**After re-running**, look in `15_Run_in_VSCode/work/` for the new results:

* `work/compare_report.md`: re-run vs delivered.
* `work/logs/`: the console output of every run.
* `work/24_figures_stage3to7/`: redrawn figures.
