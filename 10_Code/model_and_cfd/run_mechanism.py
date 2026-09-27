import sys, time, json
import numpy as np
sys.path.insert(0, '/home/claude/grail_cfd/tools')
from grail_cht import Geometry, Materials, Operating, GrailCHT

OUT = '/home/claude/grail_cfd/07_mechanism'
res = {}
for f, name in ((0, 'parallel'), (1, 'alternating')):
    t0 = time.time()
    g = Geometry(); m = Materials(); op = Operating(f_interdig=f)
    s = GrailCHT(g, m, op, nx=110, ny=240)
    r = s.solve(max_outer=600, tol=1e-6)
    res[name] = r
    np.save('%s/Tp_%s.npy' % (OUT, name), s.Tp)
    np.save('%s/Tf_%s.npy' % (OUT, name), s.Tf)
    print("%-12s outer %3d resid %.1e conv %s  energy err %+.4f%%  (%.1fs)"
          % (name, r['outer'], r['residual'], r['converged'], r['energy_error_pct'],
             time.time() - t0), flush=True)

json.dump(res, open('%s/mechanism.json' % OUT, 'w'), indent=1)
p, a = res['parallel'], res['alternating']
print()
print("MECHANISM STUDY  -  matched mdot, G_T, geometry, materials, ambient, wind")
print("%-24s %14s %14s %14s" % ("quantity", "parallel", "alternating", "change"))


def row(k, label, fmt="%.4f"):
    dv = a[k] - p[k]
    ch = ("%+.3f %%" % (100 * dv / p[k])) if p[k] else "%+.4f" % dv
    print("%-24s %14s %14s %14s" % (label, fmt % p[k], fmt % a[k], ch))


for k, l, fm in (('Tp_max', 'T_p,max (K)', '%.4f'), ('Tp_min', 'T_p,min (K)', '%.4f'),
                 ('Tp_mean', 'T_p,mean (K)', '%.4f'), ('dTp', 'dT_p (K)', '%.4f'),
                 ('Tp_std', 'T_p std (K)', '%.4f'), ('P95', 'P95 (K)', '%.4f'),
                 ('P99', 'P99 (K)', '%.4f'), ('R4', 'R4 = mean(T^4)', '%.6e'),
                 ('Q_rad', 'Q_rad (W)', '%.4f'), ('Q_conv', 'Q_conv (W)', '%.4f'),
                 ('Q_rear', 'Q_rear (W)', '%.4f'), ('Q_u', 'Q_u (W)', '%.4f'),
                 ('eta', 'efficiency', '%.5f'), ('T_out', 'T_out (K)', '%.4f'),
                 ('U_L', 'U_L (W/m2K)', '%.4f')):
    row(k, l, fm)
print()
print("energy balance: parallel %+.4f %%   alternating %+.4f %%"
      % (p['energy_error_pct'], a['energy_error_pct']))
print("per-channel outlet T (K):")
print("  parallel    ", " ".join("%.2f" % t for t in p['T_out_per_channel']))
print("  alternating ", " ".join("%.2f" % t for t in a['T_out_per_channel']))
