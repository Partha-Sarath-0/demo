"""
Stop a running frozen-flow CHT case once it has converged, by an explicit criterion:

  between the two most recent snapshots (250 iterations apart):
    |d eta| / eta, |d Tp_mean| / Tp_mean, |d Tp_std| / Tp_std   all < 1e-5
  and |energy balance| < 0.05 %  (the independent balance from cht_post)

When met, endTime in the case's controlDict is set to the current snapshot time; the solver
re-reads controlDict every iteration, sees endTime already passed, writes and ends normally
("End"), and the queue lane moves on. Every decision is appended to auto_stop.log with the numbers
that justified it. Runs as a background loop over the given cases.
"""
import os, re, sys, time, json
sys.path.insert(0, os.path.dirname(__file__))
import cht_post as P

PAR = {"q_abs": 519.1256, "U_top": 4.191176, "h_rear": 3.0, "T_amb": 298.15, "T_in": 300.0, "G_T": 800.0}
TOL, BAL = 1e-5, 0.05
LOG = "/home/claude/grail_cfd/06_cht/auto_stop.log"


def outlets(case):
    return ("outlet_a", "inlet_b") if "/bench_co_" in case or os.path.basename(case).startswith("bench_co_") \
        else ("outlet_a", "outlet_b")


def snaps(case):
    return sorted([d for d in os.listdir(case) if re.fullmatch(r"\d+", d) and d != "0"], key=int)


def check(case, seen):
    s = snaps(case)
    if len(s) < 2 or os.path.exists(os.path.join(case, "CHT_DONE")):
        return
    key = s[-1]
    if seen.get(case) == key:
        return
    seen[case] = key
    a = P.analyse(case, s[-2], PAR, outlets=outlets(case))
    b = P.analyse(case, s[-1], PAR, outlets=outlets(case))
    rel = {k: abs(b[k] - a[k]) / abs(a[k]) for k in ("eta", "Tp_mean", "Tp_std")}
    ok = all(v < TOL for v in rel.values()) and abs(b["balance_pct"]) < BAL
    line = "%s %s %s->%s rel %s bal %.4f%% -> %s" % (
        time.strftime("%H:%M:%S"), os.path.basename(case), s[-2], s[-1],
        json.dumps({k: "%.1e" % v for k, v in rel.items()}), b["balance_pct"], "CONVERGED" if ok else "running")
    open(LOG, "a").write(line + "\n")
    if ok:
        cd = os.path.join(case, "system/controlDict")
        t = open(cd).read()
        t = re.sub(r"(\n\s*endTime\s+)[^;]+;", r"\g<1>%s;" % s[-1], t, count=1)
        open(cd, "w").write(t)
        json.dump({"converged_at": s[-1], "final": b, "previous": a, "rel_change": rel},
                  open(os.path.join(case, "convergence.json"), "w"), indent=1)


if __name__ == "__main__":
    cases = sys.argv[1:]
    seen = {}
    while True:
        for c in cases:
            if os.path.isdir(c):
                try:
                    check(c, seen)
                except Exception as e:
                    open(LOG, "a").write("%s %s error %r\n" % (time.strftime("%H:%M:%S"), c, e))
        if all(os.path.exists(os.path.join(c, "CHT_DONE")) for c in cases):
            break
        time.sleep(120)
