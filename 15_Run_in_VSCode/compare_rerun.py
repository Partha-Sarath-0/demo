#!/usr/bin/env python3
"""Compare the results in work/ with the delivered results they were seeded from.

For every result file (.csv / .json / .txt) listed in work/seed_manifest.json:
  SAME       byte-identical to the delivered file (either not re-run, or re-run bit for bit)
  NUMERIC    same table/JSON structure; the largest numeric differences are listed
  CHANGED    structure differs (different rows/columns/keys) - look at it yourself
Nothing is edited, deleted or filtered. Small differences are expected after a re-run on another
computer (different library versions / BLAS / random-number streams); they are reported, not hidden.
Writes work/compare_report.md.
"""
import os, json, csv, hashlib, math

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
WORK = os.path.join(HERE, "work")
REL_FLAG = 1e-6
TIMING_COLUMNS = {"run_s"}          # wall-clock time, not a result: reported as timing only


def md5(p):
    return hashlib.md5(open(p, "rb").read()).hexdigest()


def num(x):
    try:
        v = float(x)
        return v if math.isfinite(v) else None
    except (TypeError, ValueError):
        return None


def flat_json(o, pre=""):
    if isinstance(o, dict):
        for k, v in o.items():
            yield from flat_json(v, f"{pre}.{k}" if pre else str(k))
    elif isinstance(o, list):
        for i, v in enumerate(o):
            yield from flat_json(v, f"{pre}[{i}]")
    else:
        yield pre, o


def diff_pairs(pairs):
    out = []
    for key, a, b in pairs:
        x, y = num(a), num(b)
        if x is None or y is None:
            if str(a) != str(b):
                out.append((key, a, b, float("inf")))
            continue
        d = abs(y - x)
        rel = d / max(abs(x), 1e-12)
        if d > 0:
            out.append((key, x, y, rel))
    return sorted(out, key=lambda t: -t[3])


def compare_csv(a, b):
    A, B = list(csv.reader(open(a))), list(csv.reader(open(b)))
    if not A or not B or A[0] != B[0] or len(A) != len(B):
        return "CHANGED", "header or row count differs (%d vs %d rows)" % (len(A), len(B)), []
    h = A[0]
    pairs = [(f"row {i} {h[j] if j < len(h) else j}", A[i][j], B[i][j])
             for i in range(1, len(A)) for j in range(min(len(A[i]), len(B[i])))
             if not (j < len(h) and h[j] in TIMING_COLUMNS)]
    return "NUMERIC", "", diff_pairs(pairs)


def compare_json(a, b):
    A, B = dict(flat_json(json.load(open(a)))), dict(flat_json(json.load(open(b))))
    if set(A) != set(B):
        return "CHANGED", "keys differ: %d only delivered, %d only re-run" % (len(set(A) - set(B)), len(set(B) - set(A))), []
    return "NUMERIC", "", diff_pairs([(k, A[k], B[k]) for k in A])


def main():
    man_p = os.path.join(WORK, "seed_manifest.json")
    if not os.path.exists(man_p):
        raise SystemExit("work/ not set up yet - run any task first (or: python3 run.py setup)")
    man = json.load(open(man_p))
    rep = ["# Re-run vs delivered results\n", "Flag threshold: relative difference > %g\n\n" % REL_FLAG,
           "| file | status | largest relative difference | where |\n|---|---|---|---|\n"]
    detail = []
    n_same = n_diff = 0
    for rel, m in sorted(man.items()):
        if not rel.endswith((".csv", ".json", ".txt")):
            continue
        w, d = os.path.join(WORK, rel), os.path.join(ROOT, m["source"])
        if not (os.path.exists(w) and os.path.exists(d)):
            continue
        if md5(w) == md5(d):
            n_same += 1
            continue
        if rel.endswith(".csv"):
            st, note, dd = compare_csv(d, w)
        elif rel.endswith(".json"):
            st, note, dd = compare_json(d, w)
        else:
            st, note, dd = "CHANGED", "text differs", []
        n_diff += 1
        big = [t for t in dd if t[3] > REL_FLAG]
        top = dd[0] if dd else None
        if top:
            where = f"{top[0]}: {top[1]} -> {top[2]}"
        else:
            where = note or "only the run-time column (%s) differs" % ", ".join(sorted(TIMING_COLUMNS))
        where = where.replace("|", "/")
        rep.append("| %s | %s%s | %s | %s |\n" % (rel, st, " (%d values above threshold)" % len(big) if st == "NUMERIC" else "",
                                                "%.3g" % top[3] if top else "-", where))
        if big:
            detail.append("\n## %s\n\n| value | delivered | re-run | relative |\n|---|---|---|---|\n" % rel)
            for k, x, y, r in big[:15]:
                detail.append("| %s | %s | %s | %.3g |\n" % (k, x, y, r))
    rep.append("\n%d result files byte-identical to the delivered ones (not re-run, or reproduced exactly).\n" % n_same)
    rep.append("%d result files differ (listed above).\n" % n_diff)
    txt = "".join(rep + detail)
    open(os.path.join(WORK, "compare_report.md"), "w").write(txt)
    print(txt)
    print("written:", os.path.join(WORK, "compare_report.md"))


if __name__ == "__main__":
    main()
