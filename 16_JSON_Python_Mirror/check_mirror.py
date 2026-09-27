#!/usr/bin/env python3
"""Prove that the Python mirror is a 100 % mirror of the JSON files.

    python3 16_JSON_Python_Mirror/check_mirror.py              # check, write MIRROR_CHECK.md
    python3 16_JSON_Python_Mirror/check_mirror.py --export DIR # also write the rebuilt JSONs to DIR

For every .py in mirror/:
  1. to_json_text() is compared with the JSON file byte for byte;
  2. the JSON file's MD5 is compared with the MD5 recorded when the mirror was built
     (so a JSON that was edited later is caught, not silently "matched");
  3. DATA is compared with json.load(JSON file) value by value (NaN counted equal to NaN).
And in the other direction: every .json in the package (outside 15_, 16_ and .vscode) must have
a mirror. PASS only if all of this holds. Nothing is edited. Standard library only.
"""
import os, sys, json, math, hashlib, runpy

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
MIRROR = os.path.join(HERE, "mirror")
SKIP = ("15_Run_in_VSCode", "16_JSON_Python_Mirror", ".vscode", "_to_delete")


def same(a, b):
    if isinstance(a, float) and isinstance(b, float) and math.isnan(a) and math.isnan(b):
        return True
    if type(a) is not type(b):
        return False
    if isinstance(a, dict):
        return list(a) == list(b) and all(same(a[k], b[k]) for k in a)
    if isinstance(a, list):
        return len(a) == len(b) and all(same(x, y) for x, y in zip(a, b))
    return a == b


def main():
    export = sys.argv[sys.argv.index("--export") + 1] if "--export" in sys.argv else None
    rows, ok_all, mirrored = [], True, set()
    for dp, _, fs in sorted(os.walk(MIRROR)):
        for f in sorted(fs):
            if not f.endswith(".py"):
                continue
            ns = runpy.run_path(os.path.join(dp, f))
            rel = ns["SOURCE_JSON"]
            mirrored.add(rel)
            src = os.path.join(ROOT, rel)
            if not os.path.exists(src):
                rows.append((rel, "MISSING JSON", "", "", "")); ok_all = False; continue
            raw = open(src, "rb").read()
            text = ns["to_json_text"]().encode("utf-8")
            b = text == raw
            m = hashlib.md5(raw).hexdigest() == ns["SOURCE_MD5"]
            d = same(ns["DATA"], json.loads(raw.decode("utf-8")))
            ok = b and m and d
            ok_all &= ok
            rows.append((rel, "PASS" if ok else "FAIL", "yes" if b else "NO", "yes" if m else "NO", "yes" if d else "NO"))
            if export:
                out = os.path.join(export, rel)
                os.makedirs(os.path.dirname(out), exist_ok=True)
                open(out, "wb").write(text)
    missing = []
    for dp, dns, fs in os.walk(ROOT):
        dns[:] = [x for x in dns if x not in SKIP]
        for f in fs:
            if f.endswith(".json"):
                rel = os.path.relpath(os.path.join(dp, f), ROOT).replace(os.sep, "/")
                if rel not in mirrored:
                    missing.append(rel)
    ok_all &= not missing
    npass = sum(r[1] == "PASS" for r in rows)
    lines = ["# JSON <-> Python mirror check\n",
             "\n**%s** - %d of %d mirror files reproduce their JSON byte for byte; %d JSON files without a mirror.\n"
             % ("PASS" if ok_all else "FAIL", npass, len(rows), len(missing)),
             "\n| JSON file | result | bytes identical | MD5 as built | data identical |\n|---|---|---|---|---|\n"]
    lines += ["| %s | %s | %s | %s | %s |\n" % r for r in rows]
    if missing:
        lines.append("\n## JSON files with no mirror (run build_mirror.py after adding them to provenance.csv)\n\n")
        lines += ["- %s\n" % x for x in missing]
    txt = "".join(lines)
    open(os.path.join(HERE, "MIRROR_CHECK.md"), "w", encoding="utf-8").write(txt)
    print(txt)
    sys.exit(0 if ok_all else 1)


if __name__ == "__main__":
    main()
