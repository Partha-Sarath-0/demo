"""Load any GRAIL JSON through its Python mirror.

    from grail_json import load, names
    d = load("12_Stages_3-5-6-7/annual/stage7_results")   # same data as the .json file
    names()                                               # every mirrored JSON

(Run Python from inside 16_JSON_Python_Mirror, or add that folder to sys.path.)
"""
import os, runpy

HERE = os.path.dirname(os.path.abspath(__file__))
MIRROR = os.path.join(HERE, "mirror")


def names():
    out = []
    for dp, _, fs in os.walk(MIRROR):
        for f in fs:
            if f.endswith(".py"):
                out.append(os.path.relpath(os.path.join(dp, f), MIRROR)[:-3].replace(os.sep, "/"))
    return sorted(out)


def load(name):
    """name: package-relative JSON path without .json (a trailing .json is also accepted)."""
    if name.endswith(".json"):
        name = name[:-5]
    return runpy.run_path(os.path.join(MIRROR, name + ".py"))["DATA"]


if __name__ == "__main__":
    for n in names():
        print(n)
