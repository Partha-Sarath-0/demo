"""Verification of the conjugate solver by two limiting cases with known answers.

LIMIT A — plate conductivity -> infinity.
   The plate becomes isothermal, so lateral conduction can carry any amount of heat and
   the flow ARRANGEMENT cannot matter. Parallel and alternating must give identical
   results. Any difference is solver error.

LIMIT B — plate conductivity -> 0.
   No lateral conduction at all. Each channel is thermally isolated, and reversing half of
   them only relabels which end is the inlet. By symmetry the panel totals must again be
   identical.

The real conductivity sits between these, so the physical difference between arrangements
must vanish at both ends and peak somewhere in between. If it does not, the mechanism
result is an artefact.
"""
import sys, time
import numpy as np
sys.path.insert(0, '/home/claude/grail_cfd/tools')
import grail_cht as G
from grail_cht import Geometry, Materials, Operating, GrailCHT

print("k_al (W/mK)   topology        Q_u (W)      eta       T_p,mean    T_p,std       R4         err%")
rows = {}
for k in (1.0e-2, 1.0, 22.9, 229.0, 2290.0, 2.29e6):
    out = {}
    for f, name in ((0, 'parallel'), (1, 'alternating')):
        class M(Materials):
            k_al = k
        g = Geometry(); m = M(); op = Operating(f_interdig=f)
        s = GrailCHT(g, m, op, nx=110, ny=120)
        r = s.solve(max_outer=900, tol=1e-6)
        out[name] = r
        print("%11.4g   %-12s %10.4f  %9.6f  %9.4f  %8.4f  %.6e  %+.4f"
              % (k, name, r['Q_u'], r['eta'], r['Tp_mean'], r['Tp_std'], r['R4'],
                 r['energy_error_pct']), flush=True)
    d = 100 * (out['alternating']['Q_u'] - out['parallel']['Q_u']) / out['parallel']['Q_u']
    dR = 100 * (out['alternating']['R4'] - out['parallel']['R4']) / out['parallel']['R4']
    ds = 100 * (out['alternating']['Tp_std'] - out['parallel']['Tp_std']) / out['parallel']['Tp_std']
    print("              -> dQ_u %+.4f %%   dR4 %+.4f %%   d(std) %+.4f %%\n" % (d, dR, ds), flush=True)
    rows[k] = (d, dR, ds)

print("SUMMARY: difference between arrangements vs plate conductivity")
print("  k_al        dQ_u %      dR4 %      d(std) %")
for k, (d, dR, ds) in rows.items():
    print("  %9.4g  %+9.4f  %+9.4f  %+9.4f" % (k, d, dR, ds))
print()
print("Expected: both limits -> 0. AA1050 is 229 W/mK.")
