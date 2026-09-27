"""Does the alternating arrangement ever win?

The mechanism targets radiative loss. On this collector TiNOX (eps = 0.04) has already
removed almost all of it, so there is nothing left to save. This sweeps absorber emittance
from the selective coating up to a plain black paint to find the crossover, if one exists.

Both arrangements are run at matched mass flow AND at matched mean plate temperature, so
the flattening is separated from the mean shift.
"""
import sys
import numpy as np
sys.path.insert(0, '/home/claude/grail_cfd/tools')
from grail_cht import Geometry, Materials, Operating, GrailCHT

NX, NY = 110, 120


def run(f, eps, T_in=300.0):
    class M(Materials):
        eps_abs = eps
    s = GrailCHT(Geometry(), M(), Operating(f_interdig=f, T_in=T_in), nx=NX, ny=NY)
    return s, s.solve(max_outer=900, tol=1e-6)


print("MATCHED MASS FLOW")
print(" eps_abs   eta_co    eta_alt   d_eta%%   Qrad_co   Qrad_alt   Tp_co    Tp_alt   std_co  std_alt")
res = {}
for eps in (0.04, 0.10, 0.20, 0.35, 0.50, 0.70, 0.90):
    _, rc = run(0, eps)
    _, ra = run(1, eps)
    res[eps] = (rc, ra)
    print("  %.2f    %.5f  %.5f  %+6.2f   %7.3f  %8.3f  %7.2f %8.2f  %6.3f %7.3f"
          % (eps, rc['eta'], ra['eta'], 100 * (ra['eta'] - rc['eta']) / rc['eta'],
             rc['Q_rad'], ra['Q_rad'], rc['Tp_mean'], ra['Tp_mean'],
             rc['Tp_std'], ra['Tp_std']), flush=True)

print()
print("MATCHED MEAN PLATE TEMPERATURE  (isolates the flattening from the mean shift)")
print(" eps_abs   R4_co         R4_alt        dR4%%      Qrad_co   Qrad_alt   dQrad%%   d_eta%%")
for eps in (0.04, 0.20, 0.50, 0.90):
    rc = res[eps][0]
    target = rc['Tp_mean']
    Tg = 300.0 - (res[eps][1]['Tp_mean'] - target)
    for _ in range(7):
        _, ra = run(1, eps, Tg)
        err = ra['Tp_mean'] - target
        if abs(err) < 0.01:
            break
        Tg -= err
    print("  %.2f   %.6e  %.6e  %+7.4f  %7.4f  %8.4f  %+7.3f  %+7.4f"
          % (eps, rc['R4'], ra['R4'], 100 * (ra['R4'] - rc['R4']) / rc['R4'],
             rc['Q_rad'], ra['Q_rad'], 100 * (ra['Q_rad'] - rc['Q_rad']) / rc['Q_rad'],
             100 * (ra['eta'] - rc['eta']) / rc['eta']), flush=True)

print()
print("radiative loss as a share of absorbed power:")
for eps in sorted(res):
    rc = res[eps][0]
    print("  eps %.2f :  Q_rad %7.3f W  of  Q_solar %7.3f W  =  %5.2f %%"
          % (eps, rc['Q_rad'], rc['Q_solar'], 100 * rc['Q_rad'] / rc['Q_solar']))
