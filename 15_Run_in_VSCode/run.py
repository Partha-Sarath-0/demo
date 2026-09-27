#!/usr/bin/env python3
"""GRAIL Collector - one launcher for everything that can be re-run from VS Code.

    python3 15_Run_in_VSCode/run.py <command>        (or use Terminal > Run Task... in VS Code)

Commands: see COMMANDS below, or run with no argument.

What it does, and what it does NOT do
-------------------------------------
* The Stage 3-7 Python scripts in 12_Stages_3-5-6-7/code were written in the project working tree
  and contain absolute paths such as /home/claude/grail_cfd/20_annual. They are NOT edited.
  Instead, every run makes path-converted copies in 15_Run_in_VSCode/portable_code/. The only change
  is replacing those path strings (see PATH_MAP; the full list of replaced lines is written to
  portable_code/PATH_CHANGES.md). No other character of the code is changed.
* All re-runs read and write inside 15_Run_in_VSCode/work/, which rebuilds the original working-tree
  layout (20_annual, 21_surrogate, 22_system, 23_optimisation, 24_figures_stage3to7, 25_octave,
  26_xcos). The work folder is first seeded with copies of the delivered results. The delivered
  results in 12_, 13_ and 14_ are never overwritten.
* `compare` then checks the re-run results against the delivered ones.
"""
import os, sys, shutil, subprocess, hashlib, json, time, glob

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)                          # GRAIL_Collector_Complete_Final
PORT = os.path.join(HERE, "portable_code")
WORK = os.path.join(HERE, "work")
S = os.path.join(ROOT, "12_Stages_3-5-6-7")
OCT_PKG = os.path.join(ROOT, "13_Octave_system_model")
XC_PKG = os.path.join(ROOT, "14_Xcos_block_diagram_model")

PY_SOURCES = [os.path.join(S, "code", f) for f in (
    "stage3_ann.py", "stage5_nsga2.py", "stage5_verify.py", "cht_point.py", "stage6_testmatrix.py",
    "stage6_fit.py", "stage7_weather.py", "stage7_annual.py", "stage3to7_figures.py")] + \
    [os.path.join(ROOT, "10_Code", "model_and_cfd", f) for f in (
    "grail_cht.py", "campaign.py", "campaign3.py", "campaign4.py", "figstyle.py")]

# ordered: specific prefixes first, the generic working-tree root last
PATH_MAP = [
    ("/home/claude/grail_cfd/tools", PORT),
    ("/home/claude/grail_cfd/19_rev41", os.path.join(ROOT, "06_Datasets")),   # rev4.2 dataset, read only
    ("/home/claude/grail_cfd/", WORK + "/"),
]

# delivered result -> working-tree location (seeded once; re-runs overwrite only the work copy)
SEED = [
    (os.path.join(S, "annual"), "20_annual"),
    (os.path.join(S, "surrogate"), "21_surrogate"),
    (os.path.join(S, "system_model"), "22_system"),
    (os.path.join(S, "optimisation"), "23_optimisation"),
    (os.path.join(S, "figures"), "24_figures_stage3to7"),
    (OCT_PKG, "25_octave"),
    (XC_PKG, "26_xcos"),
]
CODE_EXT = (".m", ".sce", ".py", ".md")   # code: always refreshed from the package; data/results: seeded once


def md5(p):
    return hashlib.md5(open(p, "rb").read()).hexdigest()


def convert():
    """Write path-converted copies of the Python scripts. Refuses if a path would break a string."""
    for _, new in PATH_MAP:
        if '"' in new or "'" in new or "\\" in new:
            sys.exit("Folder path contains a quote or backslash; move the package to a plain path: " + new)
    os.makedirs(PORT, exist_ok=True)
    log = ["# Path changes made by run.py (generated, do not edit)\n",
           "Only these lines differ from the originals. Everything else is byte-identical.\n"]
    for src in PY_SOURCES:
        if not os.path.exists(src):
            sys.exit("missing source file: " + src)
        txt = open(src, encoding="utf-8").read()
        out = txt
        for old, new in PATH_MAP:
            out = out.replace(old, new)
        if "/home/claude/grail_cfd" in out:
            sys.exit("unconverted path left in " + src)
        dst = os.path.join(PORT, os.path.basename(src))
        if not os.path.exists(dst) or open(dst, encoding="utf-8").read() != out:
            open(dst, "w", encoding="utf-8").write(out)
        a, b = txt.splitlines(), out.splitlines()
        ch = [(i + 1, x, y) for i, (x, y) in enumerate(zip(a, b)) if x != y]
        log.append("\n## %s  (source md5 %s)\n" % (os.path.relpath(src, ROOT), md5(src)))
        for i, x, y in ch:
            log.append("- line %d\n  - was: `%s`\n  - now: `%s`\n" % (i, x.strip(), y.strip()))
    open(os.path.join(PORT, "PATH_CHANGES.md"), "w", encoding="utf-8").write("".join(log))


def seed():
    """Copy delivered results into work/ once (re-runs then overwrite only work/); refresh code files."""
    man_p = os.path.join(WORK, "seed_manifest.json")
    man = json.load(open(man_p)) if os.path.exists(man_p) else {}
    for src_dir, sub in SEED:
        if not os.path.isdir(src_dir):
            sys.exit("missing folder: " + src_dir)
        for dp, _, fs in os.walk(src_dir):
            for f in fs:
                if f.startswith("."):
                    continue
                s = os.path.join(dp, f)
                rel = os.path.join(sub, os.path.relpath(s, src_dir))
                d = os.path.join(WORK, rel)
                is_code = f.endswith(CODE_EXT)
                if os.path.exists(d) and not is_code:
                    continue
                if os.path.exists(d) and md5(d) == md5(s):
                    continue
                os.makedirs(os.path.dirname(d), exist_ok=True)
                shutil.copy2(s, d)
                man[rel] = dict(source=os.path.relpath(s, ROOT), md5=md5(s), copied=time.time())
    os.makedirs(WORK, exist_ok=True)
    json.dump(man, open(man_p, "w"), indent=1)


def prepare():
    convert()
    seed()


def py(script, *args, log=None):
    prepare()
    cmd = [sys.executable, os.path.join(PORT, script), *args]
    return run(cmd, cwd=WORK, log=log)


def run(cmd, cwd, log=None):
    print(">>", " ".join('"%s"' % c if " " in c else c for c in cmd), "\n   in", cwd, flush=True)
    t0 = time.time()
    if log:
        os.makedirs(os.path.dirname(log), exist_ok=True)
        with open(log, "w") as fh:
            p = subprocess.Popen(cmd, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
            for line in p.stdout:
                sys.stdout.write(line); fh.write(line)
            rc = p.wait()
    else:
        rc = subprocess.call(cmd, cwd=cwd)
    print("<< exit %d after %.0f s" % (rc, time.time() - t0))
    if rc:
        sys.exit(rc)


# ---------------------------------------------------------------- external programs
def _walk_for(roots, names):
    for r in roots:
        for app in sorted(glob.glob(r), reverse=True):
            for dp, _, fs in os.walk(app):
                for n in names:
                    if n in fs and os.access(os.path.join(dp, n), os.X_OK):
                        return os.path.join(dp, n)
    return None


def find_octave():
    e = os.environ.get("GRAIL_OCTAVE")
    if e:
        return e
    for n in ("octave-cli", "octave"):
        p = shutil.which(n)
        if p:
            return p
    for p in ("/opt/homebrew/bin/octave-cli", "/opt/homebrew/bin/octave", "/usr/local/bin/octave-cli",
              "/usr/local/bin/octave"):
        if os.path.exists(p):
            return p
    return _walk_for(["/Applications/Octave*.app"], ["octave-cli", "octave"])


def find_scilab():
    e = os.environ.get("GRAIL_SCILAB")
    if e:
        return e
    p = shutil.which("scilab")
    if p:
        return p
    return _walk_for(["/Applications/scilab*.app", "/Applications/Scilab*.app"], ["scilab"])


def octave(script):
    prepare()
    exe = find_octave()
    if not exe:
        sys.exit("GNU Octave not found. Install it (macOS: brew install octave) or set GRAIL_OCTAVE=/path/to/octave-cli")
    args = [exe, "--quiet", script] if exe.endswith("octave-cli") else [exe, "--no-gui", "--quiet", script]
    run(args, cwd=os.path.join(WORK, "25_octave"), log=os.path.join(WORK, "logs", "octave_" + script.replace(".m", ".log")))


def scilab_run(script):
    prepare()
    exe = find_scilab()
    if not exe:
        sys.exit("Scilab not found. Install it from scilab.org or set GRAIL_SCILAB=/path/to/scilab")
    run([exe, "-nw", "-nb", "-f", script], cwd=os.path.join(WORK, "26_xcos"),
        log=os.path.join(WORK, "logs", "xcos_" + script.replace(".sce", ".log")))


# ---------------------------------------------------------------- commands
def c_check():
    print("package root:", ROOT)
    print("python:", sys.executable, sys.version.split()[0])
    for m in ("numpy", "scipy", "pandas", "sklearn", "matplotlib", "shap", "pymoo", "pvlib"):
        try:
            mod = __import__(m)
            print("  %-10s %s" % (m, getattr(mod, "__version__", "ok")))
        except Exception as e:
            print("  %-10s MISSING (%s) -> pip install -r 15_Run_in_VSCode/requirements.txt" % (m, type(e).__name__))
    print("octave:", find_octave() or "not found (only needed for the Octave tasks)")
    print("scilab:", find_scilab() or "not found (only needed for the Xcos tasks)")


def c_octave_export():
    octave("export_xcos_inputs.m")
    s, d = os.path.join(WORK, "25_octave", "xcos_inputs.csv"), os.path.join(WORK, "26_xcos", "xcos_inputs.csv")
    shutil.copy2(s, d)
    print("copied", os.path.relpath(s, HERE), "->", os.path.relpath(d, HERE))


def c_xcos_open():
    prepare()
    exe = find_scilab()
    if not exe:
        sys.exit("Scilab not found. Install it from scilab.org or set GRAIL_SCILAB=/path/to/scilab")
    z = os.path.join(XC_PKG, "GRAIL_system.zcos")
    subprocess.Popen([exe, "-e", 'xcos("%s")' % z])
    print("opening", z, "in Xcos (read-only look; to simulate, use the task 'Xcos: run full year')")


def c_install_vscode():
    """Copy the task list, recommended extensions and settings into <package>/.vscode (one time)."""
    src, dst = os.path.join(HERE, "vscode_config"), os.path.join(ROOT, ".vscode")
    os.makedirs(dst, exist_ok=True)
    for f in ("tasks.json", "extensions.json", "settings.json"):
        d = os.path.join(dst, f)
        if os.path.exists(d) and md5(d) != md5(os.path.join(src, f)):
            shutil.copy2(d, d + ".before_grail")
            print("kept your old", f, "as", f + ".before_grail")
        shutil.copy2(os.path.join(src, f), d)
        print("installed", os.path.relpath(d, ROOT))
    print("Done. In VS Code: Cmd+Shift+P -> Tasks: Run Task")


def c_reset():
    if os.path.isdir(WORK):
        shutil.rmtree(WORK)
    prepare()
    print("work/ re-created from the delivered results")


COMMANDS = {
    "install-vscode":  ("One time: install the VS Code task list into .vscode/", c_install_vscode),
    "check":           ("Check Python packages, Octave and Scilab", c_check),
    "setup":           ("Make portable_code/ and seed work/ (done automatically by every command)", prepare),
    "reset":           ("Delete work/ and re-seed it from the delivered results", c_reset),
    "stage7-weather":  ("Stage 7 weather check: POA by model and tilt (~10 s)",
                        lambda: py("stage7_weather.py", log=os.path.join(WORK, "20_annual", "stage7_weather_check_rerun.txt"))),
    "stage7-annual":   ("Stage 7 annual SDHW + economics + 1-4 module sizing sweep (~2-5 min)",
                        lambda: py("stage7_annual.py", "sweep", log=os.path.join(WORK, "logs", "stage7_annual.log"))),
    "stage6-fit":      ("Stage 6 ISO 9806 fit of the virtual test matrix (~1 s)",
                        lambda: py("stage6_fit.py", log=os.path.join(WORK, "logs", "stage6_fit.log"))),
    "stage3-ann":      ("Stage 3 ANN ensemble + GPR + SHAP on the rev4.2 dataset (~5 min)",
                        lambda: py("stage3_ann.py", log=os.path.join(WORK, "logs", "stage3_ann.log"))),
    "stage5-nsga2":    ("Stage 5 NSGA-II on the ANN surrogate (~20 s)",
                        lambda: py("stage5_nsga2.py", log=os.path.join(WORK, "logs", "stage5_nsga2.log"))),
    "stage5-verify":   ("Stage 5 check of 8 optimum points in GRAIL-CHT (slow: ~8-15 min)",
                        lambda: py("stage5_verify.py", log=os.path.join(WORK, "logs", "stage5_verify.log"))),
    "stage6-testmatrix": ("Stage 6 virtual test matrix, 22+3 GRAIL-CHT points (slow: ~40-60 min)",
                        lambda: py("stage6_testmatrix.py", log=os.path.join(WORK, "logs", "stage6_testmatrix.log"))),
    "figures":         ("Figures F15-F19 from the results in work/ (~20 s)",
                        lambda: py("stage3to7_figures.py", log=os.path.join(WORK, "logs", "figures.log"))),
    "octave-annual":   ("Octave/MATLAB model: 8760 h, collector yield + sizing sweep (~1-2 min)",
                        lambda: octave("run_grail_annual.m")),
    "octave-compare":  ("Octave model vs Python Stage 7 results (PASS/FAIL)", lambda: octave("compare_with_python.m")),
    "octave-cont":     ("Octave continuous-draw reference for Xcos, dt 60 and 10 s (slow: ~20-40 min)",
                        lambda: octave("run_cont_reference.m")),
    "octave-export-xcos-inputs": ("Octave: write xcos_inputs.csv and copy it to work/26_xcos", c_octave_export),
    "xcos-run":        ("Scilab Xcos block diagram: build, save, simulate 4 cases (~1 min)",
                        lambda: scilab_run("run_grail_xcos.sce")),
    "xcos-compare":    ("Xcos vs Octave continuous-draw reference and Stage 7 baseline (PASS/CHECK)",
                        lambda: (prepare(), run([sys.executable, "compare_xcos.py"], cwd=os.path.join(WORK, "26_xcos")))),
    "xcos-open":       ("Open the delivered GRAIL_system.zcos diagram in the Xcos editor", c_xcos_open),
    "compare":         ("Compare every re-run result in work/ with the delivered results",
                        lambda: run([sys.executable, os.path.join(HERE, "compare_rerun.py")], cwd=HERE)),
}

if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] not in COMMANDS:
        print(__doc__)
        for k, (d, _) in COMMANDS.items():
            print("  %-26s %s" % (k, d))
        sys.exit(0 if len(sys.argv) < 2 else 2)
    COMMANDS[sys.argv[1]][1]()
