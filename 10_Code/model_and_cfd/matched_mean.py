"""Matched-mean-absorber-temperature comparison, and direct bridge heat-flow measurement.

At equal mass flow the two arrangements settle at different mean plate temperatures, so a
raw R4 comparison mixes two effects: the flattening, and a shift of the mean. Radiation is
so strongly nonlinear that the mean shift swamps everything. This isolates the flattening
by tuning inlet temperature until the two cases share a mean plate temperature.

Also integrates the lateral (y-direction) conductive heat flow through the bridge planes,
which is the mechanism itself rather than an inference from contours.
"""
import sys
import numpy as np
sys.path.insert(0, '/home/claude/grail_cfd/tools')
from grail_cht import Geometry, Materials, Operating, GrailCHT

NX, NY = 110, 120      # grid-converged: Q_u 238.338 vs 238.314 W at ny=240


def run(f, T_in):
    g = Geometry(); m = Materials(); op = Operating(f_interdig=f, T_in=T_in)
    s = GrailCHT(g, m, op, nx=NX, ny=NY)
    r = s.solve(max_outer=900, tol=1e-6)
    return s, r


def lateral_flux(s):
    """Integrate |k t dT/dy| across every bridge midline, and the axial equivalent."""
    m = s.m
    Tp = s.Tp
    kt_y = m.k_al * s.t_y
    dTdy = np.zeros_like(Tp)
    dTdy[:, :-1] = (Tp[:, 1:] - Tp[:, :-1]) / s.dy
    ktf = np.zeros_like(Tp)
    ktf[:, :-1] = 2 * kt_y[:, :-1] * kt_y[:, 1:] / (kt_y[:, :-1] + kt_y[:, 1:])
    qy = ktf * dTdy                              # W/m of x, per face
    # bridge midlines sit halfway between channel centres
    mids = 0.5 * (s.ch_y[:-1] + s.ch_y[1:])
    tot = 0.0
    per = []
    for ym in mids:
        j = int(np.argmin(np.abs(s.yc - ym)))
        q = np.abs(qy[:, j]).sum() * s.dx        # W across this plane
        per.append(q); tot += q
    # axial for comparison
    kt_x = m.k_al * s.t_x
    dTdx = np.zeros_like(Tp)
    dTdx[:-1, :] = (Tp[1:, :] - Tp[:-1, :]) / s.dx
    ktfx = np.zeros_like(Tp)
    ktfx[:-1, :] = 2 * kt_x[:-1, :] * kt_x[1:, :] / (kt_x[:-1, :] + kt_x[1:, :])
    qx = ktfx * dTdx
    i = NX // 2
    ax = np.abs(qx[i, :]).sum() * s.dy
    return tot, per, ax


print("STEP 1 — baseline, equal inlet temperature 300 K")
sp_, rp = run(0, 300.0)
sa_, ra = run(1, 300.0)
print("  parallel     T_p,mean %.4f K   R4 %.6e   Q_u %.4f W" % (rp['Tp_mean'], rp['R4'], rp['Q_u']))
print("  alternating  T_p,mean %.4f K   R4 %.6e   Q_u %.4f W" % (ra['Tp_mean'], ra['R4'], ra['Q_u']))
target = rp['Tp_mean']

print("\nSTEP 2 — tune the alternating case to the SAME mean plate temperature")
# secant iteration on T_in; dT_p,mean/dT_in is close to 1 so this converges in a few steps
Tg = 300.0 - (ra['Tp_mean'] - target)
for it in range(8):
    s_, r_ = run(1, Tg)
    err = r_['Tp_mean'] - target
    print("    iter %d  T_in %.4f -> T_p,mean %.4f  (err %+.4f K)" % (it, Tg, r_['Tp_mean'], err), flush=True)
    if abs(err) < 0.01:
        break
    Tg -= err
mid = Tg
print("  matched at T_in = %.4f K -> T_p,mean %.4f K (target %.4f)"
      % (mid, r_['Tp_mean'], target))

print("\nMATCHED-MEAN COMPARISON  (the fair test of the flattening claim)")
print("%-26s %14s %14s %14s" % ("quantity", "parallel", "alternating", "change"))
for k, lbl, fm in (('Tp_mean', 'T_p,mean (K)', '%.4f'), ('Tp_std', 'T_p std (K)', '%.4f'),
                   ('dTp', 'dT_p (K)', '%.4f'), ('P99', 'P99 (K)', '%.4f'),
                   ('R4', 'R4 = mean(T^4)', '%.6e'), ('Q_rad', 'Q_rad (W)', '%.5f'),
                   ('Q_conv', 'Q_conv (W)', '%.4f'), ('Q_u', 'Q_u (W)', '%.4f'),
                   ('eta', 'efficiency', '%.5f')):
    dv = r_[k] - rp[k]
    print("%-26s %14s %14s %13s" % (lbl, fm % rp[k], fm % r_[k],
                                    ("%+.4f %%" % (100 * dv / rp[k])) if rp[k] else "-"))
print("\n  R4 / mean(T)^4  :  parallel %.6f   alternating %.6f"
      % (rp['R4'] / rp['Tp_mean'] ** 4, r_['R4'] / r_['Tp_mean'] ** 4))
print("  (this ratio isolates the nonuniformity contribution to radiation)")

print("\nSTEP 3 — lateral bridge conduction, measured directly")
for nm, s in (("parallel", sp_), ("alternating", sa_)):
    tot, per, ax = lateral_flux(s)
    print("  %-12s lateral through 11 bridge planes %8.4f W | axial at mid-span %8.4f W | ratio %.4f"
          % (nm, tot, ax, tot / ax if ax else np.nan))
    print("               per bridge (W): " + " ".join("%.3f" % q for q in per))
