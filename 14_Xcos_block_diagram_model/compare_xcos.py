"""Compare the Scilab Xcos block-diagram results with (a) the Octave continuous-draw
reference (same equations, fixed-step Euler, dt 10 s) and (b) the Python/Octave
hourly-pulse baseline of Stage 7. Numbers are read from the result files; nothing is edited."""
import csv
import os
rd = lambda p: list(csv.DictReader(open(p)))
HERE = os.path.dirname(os.path.abspath(__file__))
def find(*cands):
    # working tree layout first, then the delivered package layout
    for c in cands:
        p = os.path.join(HERE, c)
        if os.path.exists(p):
            return p
    raise FileNotFoundError(' / '.join(cands))
OCT = find('../25_octave/octave_cont_reference.csv', '../13_Octave_system_model/octave_cont_reference.csv')
BASE = find('../20_annual/sizing_sweep.csv', '../12_Stages_3-5-6-7/annual/sizing_sweep.csv')
XR = os.path.join(HERE, 'xcos_results.csv')
X = {(r['arrangement'], r['n_modules']): r for r in rd(XR)}
O = {(r['arrangement'], r['n_modules']): r for r in rd(OCT) if r['dt_s'] == '10'}
B = {(r['arrangement'], r['n_modules']): r for r in rd(BASE)}
out = ['arrangement,n_modules,xcos_SF,octave_cont_SF,diff_SF_pts,xcos_Qsolar_kWh,octave_cont_Qsolar_kWh,diff_Qsolar_pct,'
       'xcos_Tcmax_K,octave_cont_Tcmax_K,diff_Tcmax_K,pulse_baseline_SF,xcos_minus_pulse_SF_pts,verdict']
ok = True
for k in X:
    x, o, b = X[k], O[k], B[k]
    dsf = 100 * (float(x['solar_fraction']) - float(o['solar_fraction']))
    dq = 100 * (float(x['Q_solar_kWh']) / float(o['Q_solar_kWh']) - 1)
    dt = float(x['Tc_max_K']) - float(o['Tc_max_K'])
    dp = 100 * (float(x['solar_fraction']) - float(b['solar_fraction']))
    v = 'PASS' if abs(dq) <= 0.25 and abs(dt) <= 1.5 else 'CHECK'
    ok &= v == 'PASS'
    out.append(f"{k[0]},{k[1]},{float(x['solar_fraction']):.5f},{float(o['solar_fraction']):.5f},{dsf:+.3f},"
               f"{float(x['Q_solar_kWh']):.2f},{float(o['Q_solar_kWh']):.2f},{dq:+.3f},{float(x['Tc_max_K']):.2f},"
               f"{float(o['Tc_max_K']):.2f},{dt:+.2f},{float(b['solar_fraction']):.5f},{dp:+.2f},{v}")
open(os.path.join(HERE, 'xcos_verification.csv'), 'w').write('\n'.join(out) + '\n')
print('\n'.join(out)); print('OVERALL', 'PASS' if ok else 'CHECK')
