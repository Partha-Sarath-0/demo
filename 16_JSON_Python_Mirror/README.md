# 16 — JSON ↔ Python mirror

Every JSON file in the package (65) now has a Python file next to it in this folder. There are
two parts:

1. **`mirror/`: the same data as Python.** There is one `.py` file per JSON, at the same path,
   for example `07_Results_JSON/validation_and_uncertainty/gci_plate.json` →
   `mirror/07_Results_JSON/validation_and_uncertainty/gci_plate.py`. Each file contains:
   * `DATA`, the full content as an indented Python dict or list in the same key order;
   * a header saying what the file holds, which script made the JSON, the MD5/SHA-256 of the
     JSON, and an outline of its keys;
   * `to_json_text()`, which rebuilds the original JSON text **byte for byte**.
2. **`generators/`: the Python scripts the JSON files were made with.** See
   [GENERATORS.md](GENERATORS.md) and `provenance.csv`.

## Proof that it is a 100 % mirror

```
python3 16_JSON_Python_Mirror/check_mirror.py
```

For all 65 files, the check tests three things:

1. **Bytes:** `to_json_text()` must equal the JSON file byte for byte.
2. **MD5:** the JSON's MD5 must still equal the MD5 recorded when the mirror was built, so a JSON
   edited later is flagged.
3. **Data:** `DATA` must equal `json.load(file)` value by value.

It also checks the other direction: every `.json` in the package must have a mirror. The result
is written to `MIRROR_CHECK.md`, and the current result is **PASS, 65 of 65**.

To rebuild all 65 JSON files from Python only, run `python3 check_mirror.py --export some_folder`.

The build (`build_mirror.py`) writes a mirror file only after checking that it reproduces its
JSON exactly. If a file cannot be reproduced exactly, the build stops and names the file; it
never writes an approximate copy. The JSON files are only read, never changed. Everything uses the
Python standard library only.

## Using the data in Python / VS Code

```python
# run from inside 16_JSON_Python_Mirror
from grail_json import load, names
d = load("12_Stages_3-5-6-7/annual/stage7_results")
print(d["weather"]["POA_kWh_m2"])
```

You can also open any mirror file and press ▶: it prints the JSON text.

## How each JSON was made (`provenance.csv`)

| Evidence | Files | Meaning |
|---|---|---|
| CONFIRMED | 32 | The writer script's `json.dump` names this file |
| CONFIRMED + REPRODUCED | 4 | The same, and a re-run in `15_Run_in_VSCode` gave the identical bytes (Stage 7 results, Stage 6 correlations and their 2 copies) |
| CONFIRMED + REPRODUCED except SHAP | 1 | `stage3_report.json`: re-run accuracy numbers identical; the randomly sampled SHAP values differ by up to ~3 % with the same ranking |
| CONFIRMED_ARGUMENT | 12 | The writer writes to a file named on its command line (`nu_extract.py`, `htc_level.py`, `grail_bench.py`). The output structure matches, but the exact command line was not saved |
| EARLIER_VERSION | 1 | `rom_const_nu.json` has tags that the saved `grail_bench.py` no longer writes, so it came from an earlier state of that script |
| KEPT_COPY | 1 | `uncertainty_summary_rev1.json` is the Rev 1 output of `analyse.py`, kept for the record |
| NOT_RECORDED | 14 | No saved script writes this file. The numbers were collected by commands that were not kept as scripts |

The 14 NOT_RECORDED files are:

* `cht3d_axial_study.json` and `cht3d_nx120.json`
* `nu_developed_summary.json`
* six `rom_*.json` files: `rom_design_axial`, `rom_design_nu448`, `rom_envelope`, `rom_nu_h1`,
  `rom_nuxi_envelope` and `rom_nuxi_nx120`
* `rev4_regime_breakdown.json`
* `final_uncertainty.json`
* `gci_3d_twolevel.json`
* `nu_cfd_revision.json`
* `nu_gci.json`

They are marked as not recorded rather than given a made-up generator. Their Python mirror is
still exact, because the mirror copies the data rather than recomputing it.
