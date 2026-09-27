"""
GRAIL CFD production campaign — CORRECTED converging geometry.

Replaces the superseded 480-row dataset, which was computed on the obsolete DIVERGING
channel (Dh 5.2 -> 8.3 mm, G = 1.596, r_fillet 1.0 mm) and is barred from use by
corrections CR-01 and CR-05.

Latin Hypercube over the documented GRAIL operating variables, fixed seed, both flow
topologies. Every row carries geometry provenance and its own convergence and energy
balance so nothing can be quoted without its quality flags.
"""
import sys, os, csv, json, time, math
import numpy as np
from scipy.stats import qmc
sys.path.insert(0, '/home/claude/grail_cfd/tools')
from grail_cht import Geometry, Materials, Operating, GrailCHT

SEED = 20260915
N_PER_TOPOLOGY = 150
NX, NY = 110, 120
NU_CFD = 3.428          # module-level so a re-run can override it; default is the as-run value
OUT = '/home/claude/grail_cfd/10_dataset/GRAIL_CFD_dataset_corrected.csv'
FAIL = '/home/claude/grail_cfd/11_failures/failures.csv'
os.makedirs(os.path.dirname(OUT), exist_ok=True)
os.makedirs(os.path.dirname(FAIL), exist_ok=True)

# pressure-drop closure calibrated against the resolved 3-D OpenFOAM solution:
# CFD 35.31 Pa vs 33.31 Pa from the laminar integral at the design point
DP_CAL = 35.31 / 33.31
XI = np.linspace(0, 1, 60)

BOUNDS = {                       # documented GRAIL design / operating variables only
    'G_T':        (400.0, 1000.0),
    'T_in':       (288.0, 333.0),
    'T_amb':      (283.0, 313.0),
    'v_wind':     (0.0, 5.0),
    'mdot_total': (0.0010, 0.0045),
    'bridge_mm':  (20.0, 37.0),   # hard geometric limit: bridge = pitch - w_ch < 40 mm
    'g_ratio':    (0.35, 1.00),   # capped at 1.00 by Filing 1 dependent claim 1
    'lam_G':      (0.5, 2.0),
}
KEYS = list(BOUNDS)


def dp_channel(geo, mdot_ch, T_mean):
    """Laminar integral along the converging channel, calibrated to the 3-D CFD."""
    mu = 2.414e-5 * 10 ** (247.8 / (T_mean - 140.0))       # water, Vogel
    rho = 997.0
    s = geo.dh(XI) / geo.DH_IN
    A = geo.A_IN * s ** 2
    Dh = geo.DH_IN * s
    u = mdot_ch / (rho * A)
    return float(np.trapezoid(32 * mu * u / Dh ** 2, XI * geo.L)) * DP_CAL, mu


def lateral_bridge(s):
    kt = s.m.k_al * s.t_y
    d = np.zeros_like(s.Tp); d[:, :-1] = (s.Tp[:, 1:] - s.Tp[:, :-1]) / s.dy
    kf = np.zeros_like(s.Tp); kf[:, :-1] = 2 * kt[:, :-1] * kt[:, 1:] / (kt[:, :-1] + kt[:, 1:])
    q = kf * d
    mids = 0.5 * (s.ch_y[:-1] + s.ch_y[1:])
    return float(sum(np.abs(q[:, int(np.argmin(np.abs(s.yc - ym)))]).sum() * s.dx for ym in mids))


def run_case(cid, p, topo):
    geo = Geometry(g_ratio=p['g_ratio'], lam_g=p['lam_G'], bridge=p['bridge_mm'] / 1000.0)
    mat = Materials()
    op = Operating(G_T=p['G_T'], T_in=p['T_in'], T_amb=p['T_amb'],
                   v_wind=p['v_wind'], mdot_total=p['mdot_total'], f_interdig=topo)
    s = GrailCHT(geo, mat, op, nx=NX, ny=NY, nu_cfd=NU_CFD)
    r = s.solve(max_outer=900, tol=1e-6)
    Tp = s.Tp.ravel()
    Tmean_f = 0.5 * (op.T_in + r['T_out'])
    dp, mu = dp_channel(geo, op.mdot_ch, Tmean_f)
    rho = 997.0
    Re_in = 4 * op.mdot_ch / (math.pi * geo.DH_IN * mu)
    Re_out = 4 * op.mdot_ch / (math.pi * geo.dh(1.0) * mu)
    row = dict(
        case_id=cid, geometry_version='GateA_converged_v1', solver='GRAIL-CHT-1.0',
        arrangement='alternating' if topo else 'parallel', f_interdig=topo,
        G_T_W_m2=p['G_T'], T_in_K=p['T_in'], T_amb_K=p['T_amb'], v_wind_m_s=p['v_wind'],
        mdot_total_kg_s=p['mdot_total'], mdot_channel_kg_s=op.mdot_ch,
        bridge_mm=p['bridge_mm'], g_ratio=p['g_ratio'], lambda_G=p['lam_G'],
        Dh_in_mm=geo.DH_IN * 1000, Dh_out_mm=geo.dh(1.0) * 1000,
        A_in_mm2=geo.A_IN * 1e6, A_out_mm2=geo.area(1.0) * 1e6,
        Re_in=Re_in, Re_out=Re_out, mu_Pa_s=mu,
        dp_channel_Pa=dp, W_pump_W=dp * op.mdot_total / rho,
        q_abs_W_m2=op.G_T * mat.tau_glz_sys * mat.tau_tim * mat.alpha_abs,
        T_sky_K=op.T_sky, h_wind_W_m2K=op.h_wind,
        T_out_K=r['T_out'], dT_fluid_K=r['dT'], Qu_W=r['Q_u'], eta=r['eta'],
        T_plate_mean_K=r['Tp_mean'], T_plate_max_K=r['Tp_max'], T_plate_min_K=r['Tp_min'],
        plate_spread_K=r['dTp'], plate_std_K=r['Tp_std'],
        P90_K=r['P90'], P95_K=r['P95'], P99_K=r['P99'],
        R4_K4=r['R4'], mean_T_pow4_K4=r['mean_T_pow4'], T_R4_K=r['R4'] ** 0.25,
        Q_solar_W=r['Q_solar'], Q_rad_W=r['Q_rad'], Q_conv_W=r['Q_conv'], Q_rear_W=r['Q_rear'],
        U_L_W_m2K=r['U_L'], T_glass_mean_K=r['T_glass_mean'],
        lateral_bridge_W=lateral_bridge(s),
        energy_error_pct=r['energy_error_pct'], outer_iters=r['outer'],
        residual=r['residual'], converged=r['converged'],
    )
    return row


def main():
    sampler = qmc.LatinHypercube(d=len(KEYS), seed=SEED)
    fields = None
    n_ok = n_bad = 0
    t0 = time.time()
    fo = open(OUT, 'w', newline='')
    ff = open(FAIL, 'w', newline='')
    fw = csv.writer(ff); fw.writerow(['case_id', 'topology', 'reason', 'params'])
    writer = None
    for topo in (0, 1):
        sample = sampler.random(n=N_PER_TOPOLOGY)
        for i in range(N_PER_TOPOLOGY):
            p = {k: BOUNDS[k][0] + sample[i, j] * (BOUNDS[k][1] - BOUNDS[k][0])
                 for j, k in enumerate(KEYS)}
            cid = "%s_%03d" % ('ALT' if topo else 'PAR', i)
            # ---- PRE-RUN VALIDATION GATE: reject impossible geometry before solving.
            # bridge = pitch - w_ch, so on a 40 mm pitch the bridge can never reach the
            # roadmap's stated 60 mm. Beyond ~37 mm the channel falls below the 3 mm
            # roll-bond minimum feature size of Section 9.1.
            w_ch = Geometry.PITCH * 1000.0 - p['bridge_mm']
            if w_ch < 3.0:
                n_bad += 1
                fw.writerow([cid, topo,
                             'invalid_geometry:w_ch=%.2f_mm_below_3mm_rollbond_minimum' % w_ch,
                             json.dumps(p)])
                ff.flush()
                continue
            try:
                row = run_case(cid, p, topo)
            except Exception as e:
                n_bad += 1
                fw.writerow([cid, topo, 'solver_exception:' + str(e)[:120], json.dumps(p)])
                ff.flush()
                continue
            # quality gates
            bad = []
            if not row['converged']:
                bad.append('not_converged')
            if abs(row['energy_error_pct']) > 0.5:
                bad.append('energy_balance_%.3f%%' % row['energy_error_pct'])
            if row['T_plate_max_K'] > 500 or row['T_plate_min_K'] < 250:
                bad.append('nonphysical_temperature')
            if bad:
                n_bad += 1
                fw.writerow([cid, topo, ';'.join(bad), json.dumps(p)])
                ff.flush()
                continue
            if writer is None:
                fields = list(row)
                writer = csv.DictWriter(fo, fieldnames=fields)
                writer.writeheader()
            writer.writerow(row); fo.flush()
            n_ok += 1
            if n_ok % 10 == 0:
                print("  %3d ok / %3d rejected   %.0f s elapsed" % (n_ok, n_bad, time.time() - t0),
                      flush=True)
    fo.close(); ff.close()
    print("CAMPAIGN DONE: %d accepted, %d rejected, %.1f min" % (n_ok, n_bad, (time.time() - t0) / 60))


if __name__ == '__main__':
    main()
