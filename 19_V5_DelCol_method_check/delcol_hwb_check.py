"""V5 method check: Hottel-Whillier-Bliss (Duffie & Beckman) model applied to the roll-bond collectors
tested by Del Col et al., Energy 58 (2013) 258-269 (EN 12975-2 steady state, Table 3).

Stated by Del Col (used as given): aperture 1.81 m2, 28 channels, channel ID 3.7 mm, Al roll-bond absorber
1.5 mm, black coating a=0.96 e=0.96 / semi-selective a=0.87 e=0.35, flow 0.02 kg/s per m2 aperture,
G tested 800-1000 W/m2 (curves given at 1000), T_amb 8-12 C, wind 1.4 m/s, tilt 45/60 deg, single glass cover.
NOT stated -> ENGINEERING_ASSUMPTION with a range, sampled in a Monte Carlo (uniform):
  glass solar transmittance tau 0.89-0.92 (low-iron single glazing), glass IR emittance 0.84-0.90,
  absorber width 0.85-1.00 m (sets channel pitch), Al conductivity 160-220 W/mK,
  back insulation 40-60 mm, k 0.035-0.045 W/mK, edge loss 0.1-0.4 W/m2K (per aperture area),
  channel Nu 3.66-5.0 (laminar, Re ~ 700, fully developed to developing), bonded footprint D = 3.7-6 mm,
  wind heat-transfer coefficient h_w = 2.8 + 3.0 V (Watmuff, as in Duffie & Beckman) with V 1.0-2.0 m/s,
  tilt 45-60 deg, T_amb 8-12 C.
Top loss: Klein's empirical correlation (Duffie & Beckman eq. 6.4.9). (tau alpha) = 1.01 tau alpha.
Efficiency on the mean-fluid-temperature basis used by EN 12975 and by Del Col's Eq. (3):
  eta = F' [ (tau alpha) - U_L (Tm - Ta)/G ],  U_L evaluated at the mean plate temperature (iterated).
eta0, a1, a2 are then fitted (least squares) over Tm* = 0 ... 0.08 m2K/W at G = 1000 W/m2 and compared with the
measured steady-state coefficients and their 95 % uncertainties. Nothing is tuned to the measurements.
"""
import json, numpy as np

SIG = 5.670374419e-8
MEAS = {"black": dict(alpha=0.96, eps=0.96, eta0=(0.7995, 0.0108), a1=(4.6911, 0.7879), a2=(0.0288, 0.0121)),
        "semi_selective": dict(alpha=0.87, eps=0.35, eta0=(0.7409, 0.0110), a1=(4.5477, 0.6865), a2=(0.0131, 0.0100))}
A_AP, NCH, DCH, DELTA, FLOW_PER_M2 = 1.81, 28, 3.7e-3, 1.5e-3, 0.02
G = 1000.0


def U_top(Tp, Ta, eps_p, eps_g, hw, beta, N=1):
    C = 520 * (1 - 0.000051 * beta ** 2)
    f = (1 + 0.089 * hw - 0.1166 * hw * eps_p) * (1 + 0.07866 * N)
    e = 0.430 * (1 - 100 / Tp)
    conv = 1.0 / (N / ((C / Tp) * ((Tp - Ta) / (N + f)) ** e) + 1 / hw)
    rad = SIG * (Tp + Ta) * (Tp ** 2 + Ta ** 2) / (1 / (eps_p + 0.00591 * N * hw) + (2 * N + f - 1 + 0.133 * eps_p) / eps_g - N)
    return conv + rad


def curve(p, alpha, eps):
    W = p["width"] / NCH
    D = min(p["D"], W * 0.9)
    k_w = 0.64
    h_fi = p["Nu"] * k_w / DCH
    ta = 1.01 * p["tau"] * alpha
    xs = np.linspace(0.0, 0.08, 17)
    etas = []
    for x in xs:
        Ta = p["Ta"]; Tm = Ta + x * G
        Tp = Tm + 5.0
        for _ in range(60):
            UL = U_top(Tp, Ta, eps, p["eps_g"], p["hw"], p["beta"]) + p["k_ins"] / p["L_ins"] + p["U_edge"]
            m = np.sqrt(UL / (p["k_al"] * DELTA))
            F = np.tanh(m * (W - D) / 2) / (m * (W - D) / 2)
            Fp = (1 / UL) / (W * (1 / (UL * (D + (W - D) * F)) + 1 / (h_fi * np.pi * DCH)))
            q = Fp * (ta * G - UL * (Tm - Ta))
            Tp_new = Tm + q * (1 - Fp) / (Fp * UL)
            if abs(Tp_new - Tp) < 1e-6:
                break
            Tp = 0.5 * (Tp + Tp_new)
        etas.append(q / G)
    X = np.column_stack([np.ones_like(xs), -xs, -G * xs ** 2])
    e0, a1, a2 = np.linalg.lstsq(X, np.array(etas), rcond=None)[0]
    return e0, a1, a2, Fp


def sample(rng):
    return dict(tau=rng.uniform(0.89, 0.92), eps_g=rng.uniform(0.84, 0.90), width=rng.uniform(0.85, 1.00),
                k_al=rng.uniform(160, 220), L_ins=rng.uniform(0.04, 0.06), k_ins=rng.uniform(0.035, 0.045),
                U_edge=rng.uniform(0.1, 0.4), Nu=rng.uniform(3.66, 5.0), D=rng.uniform(3.7e-3, 6e-3),
                hw=2.8 + 3.0 * rng.uniform(1.0, 2.0), beta=rng.uniform(45, 60), Ta=273.15 + rng.uniform(8, 12))


if __name__ == "__main__":
    rng = np.random.default_rng(20130258)
    nominal = dict(tau=0.905, eps_g=0.87, width=0.925, k_al=190, L_ins=0.05, k_ins=0.04, U_edge=0.25, Nu=4.36,
                   D=4.5e-3, hw=2.8 + 3.0 * 1.4, beta=52.5, Ta=283.15)
    out = {"source": "Del Col et al., Energy 58 (2013) 258-269, Table 3 (steady state)", "cases": {}}
    for name, mcase in MEAS.items():
        e0n, a1n, a2n, Fpn = curve(nominal, mcase["alpha"], mcase["eps"])
        mc = np.array([curve(sample(rng), mcase["alpha"], mcase["eps"])[:3] for _ in range(2000)])
        lo, hi = np.percentile(mc, 2.5, axis=0), np.percentile(mc, 97.5, axis=0)
        rec = {"nominal": dict(eta0=e0n, a1=a1n, a2=a2n, F_prime=Fpn),
               "mc_95": {k: [float(lo[i]), float(hi[i])] for i, k in enumerate(("eta0", "a1", "a2"))},
               "measured": {k: mcase[k] for k in ("eta0", "a1", "a2")}}
        verdict = {}
        for i, k in enumerate(("eta0", "a1", "a2")):
            v, u = mcase[k]
            # overlap of model band with measured +/- U95
            verdict[k] = bool(hi[i] >= v - u and lo[i] <= v + u)
        rec["overlap_with_measured_U95"] = verdict
        out["cases"][name] = rec
        print("%-15s model eta0 %.4f [%.4f-%.4f] vs %.4f+-%.4f | a1 %.3f [%.3f-%.3f] vs %.3f+-%.3f | a2 %.4f [%.4f-%.4f] vs %.4f+-%.4f | %s"
              % (name, e0n, lo[0], hi[0], *mcase["eta0"], a1n, lo[1], hi[1], *mcase["a1"], a2n, lo[2], hi[2], *mcase["a2"], verdict))
    json.dump(out, open("/home/claude/grail_cfd/30_delcol/delcol_hwb_check.json", "w"), indent=1, default=float)
