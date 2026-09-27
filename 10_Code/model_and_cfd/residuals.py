"""Extract the real SIMPLE residual history from the OpenFOAM logs.

Nothing here is synthesised: every value is the `Initial residual` OpenFOAM printed for that
outer iteration. The momentum equations use smoothSolver, pressure uses GAMG (two correctors
per outer iteration - the last one is taken, which is what SIMPLE converges on), and the
continuity error is the `sum local` figure from the same iteration.
"""
import re, json, os
import numpy as np

CASE = "/home/claude/grail_cfd/04_baseline/ch05_flow"
RE_TIME = re.compile(r"^Time = (\S+)")
RE_SOL = re.compile(r"Solving for (\w+), Initial residual = (\S+),")
RE_CONT = re.compile(r"continuity errors : sum local = (\S+), global = (\S+),")


def parse(path, fields=("Ux", "Uy", "Uz", "p")):
    it, rec, cur = [], {f: [] for f in fields}, None
    cont = []
    seen = set()
    for line in open(path, errors="replace"):
        m = RE_TIME.match(line)
        if m:
            t = float(m.group(1))
            if t in seen:                       # controlDict re-read repeats the last step
                cur = None
                continue
            seen.add(t)
            it.append(t); cur = {}
            for f in fields:
                rec[f].append(np.nan)
            cont.append(np.nan)
            continue
        if cur is None:
            continue
        m = RE_SOL.search(line)
        if m and m.group(1) in rec:
            rec[m.group(1)][-1] = float(m.group(2))     # last corrector wins for p
            continue
        m = RE_CONT.search(line)
        if m:
            cont[-1] = abs(float(m.group(1)))
    out = {"iter": np.array(it)}
    for f in fields:
        out[f] = np.array(rec[f], float)
    out["continuity"] = np.array(cont, float)
    return out


if __name__ == "__main__":
    flow = parse(os.path.join(CASE, "log.par"))
    print("flow: %d SIMPLE iterations, %g -> %g" % (len(flow["iter"]), flow["iter"][0], flow["iter"][-1]))
    for k in ("Ux", "Uy", "Uz", "p", "continuity"):
        v = flow[k][np.isfinite(flow[k])]
        print("  %-11s first %.4e   last %.4e   min %.4e" % (k, v[0], v[-1], v.min()))

    th = None
    for nm in ("log.T2", "log.T"):
        p = os.path.join(CASE, nm)
        if os.path.exists(p):
            d = parse(p, fields=("T",))
            if np.isfinite(d["T"]).sum() > 5:
                th = d
                print("thermal (%s): %d iterations, T %.4e -> %.4e"
                      % (nm, len(d["iter"]), d["T"][0], d["T"][np.isfinite(d["T"])][-1]))
                break

    out = {"flow": {k: v.tolist() for k, v in flow.items()}}
    if th is not None:
        out["thermal"] = {k: v.tolist() for k, v in th.items()}
    json.dump(out, open("/home/claude/grail_cfd/09_post/residuals.json", "w"))
    print("wrote 09_post/residuals.json")
