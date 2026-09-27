"""
GRAIL — validation of the conjugate solver against the analytical Hottel-Whillier-Bliss model.

This is the validation that matters most, and it is stronger than matching someone else's
experiment on a different collector: HWB is the standard closed-form flat-plate model
(Duffie & Beckman, Solar Engineering of Thermal Processes), it shares none of this solver's
discretisation, and for a bonded-fin absorber it is the accepted reference.

The chain is:
    fin efficiency        F  = tanh(m (W - D)/2) / (m (W - D)/2),   m = sqrt(U_L / (k delta))
    collector eff. factor F' = (1/U_L) / ( W [ 1/(U_L (D + (W-D) F)) + 1/(h_fi P) ] )
    heat removal factor   F_R = (mdot cp / (Ac U_L)) [1 - exp(-Ac U_L F' / (mdot cp))]
    efficiency            eta = F_R (tau alpha) - F_R U_L (T_in - T_amb) / G_T

The collector is graded, so W - D, D_h, P and h_fi all vary along the flow. F and F' are
evaluated locally at 400 stations and averaged over the flow path rather than taken at a
single nominal section - averaging the geometry first would bias F, which is nonlinear in D.

U_L is NOT fitted. It is taken from the solver's own loss balance, so the comparison tests
the fin/flow solution, not the loss model, which the Hottel-Whillier-Bliss form shares.

Writes 05_validation/hwb_validation.json
"""
import sys, os, json
import numpy as np

sys.path.insert(0, "/home/claude/grail_cfd/tools")
from grail_cht import Geometry, Materials, Operating, GrailCHT

OUT = "/home/claude/grail_cfd/05_validation"
NX, NY = 220, 240
NSTATION = 400


def hwb(g, m, op, U_L, nu_cfd=3.428):
    xi = np.linspace(0.0, 1.0, NSTATION)
    D = g.w_ch(xi)                       # bonded channel footprint, the "tube" width
    Dh = g.dh(xi)
    P = g.perim(xi)
    delta = g.T_LOWER + g.T_UPPER        # the fin is the bonded sheet pair
    W = g.PITCH

    mpar = np.sqrt(U_L / (m.k_al * delta))
    half = mpar * (W - D) / 2.0
    F_fin = np.tanh(half) / half

    h_fi = nu_cfd * m.k_w / Dh
    denom = W * (1.0 / (U_L * (D + (W - D) * F_fin)) + 1.0 / (h_fi * P))
    F_prime = (1.0 / U_L) / denom

    F_fin_avg = float(np.trapezoid(F_fin, xi)) if hasattr(np, "trapezoid") else float(np.trapz(F_fin, xi))
    F_prime_avg = float(np.trapezoid(F_prime, xi)) if hasattr(np, "trapezoid") else float(np.trapz(F_prime, xi))

    Ac = g.L * g.W
    mc = op.mdot_total * m.cp_w
    F_R = (mc / (Ac * U_L)) * (1.0 - np.exp(-Ac * U_L * F_prime_avg / mc))
    tau_alpha = m.tau_glz_sys * m.tau_tim * m.alpha_abs
    eta = F_R * tau_alpha - F_R * U_L * (op.T_in - op.T_amb) / op.G_T
    return dict(F_fin_inlet=float(F_fin[0]), F_fin_outlet=float(F_fin[-1]),
                F_fin_avg=F_fin_avg, F_prime_inlet=float(F_prime[0]),
                F_prime_outlet=float(F_prime[-1]), F_prime_avg=F_prime_avg,
                F_R=float(F_R), tau_alpha=float(tau_alpha), eta=float(eta),
                FR_UL=float(F_R * U_L), eta0=float(F_R * tau_alpha),
                m_per_m=float(mpar), delta_m=delta)


if __name__ == "__main__":
    g, m = Geometry(), Materials()
    res = {"model": "Hottel-Whillier-Bliss, Duffie & Beckman form", "n_stations": NSTATION,
           "grid": [NX, NY], "cases": {}}

    for tag, f in (("co_current", 0), ("alternating", 1)):
        op = Operating(f_interdig=f)
        s = GrailCHT(g, m, op, nx=NX, ny=NY)
        r = s.solve(max_outer=2000, tol=1e-8)
        a = hwb(g, m, op, r["U_L"])
        rec = {"solver": {k: r[k] for k in ("eta", "U_L", "T_out", "dT", "Tp_mean")},
               "hwb": a,
               "d_eta_pct": 100 * (a["eta"] - r["eta"]) / r["eta"]}
        res["cases"][tag] = rec
        print("%-12s  solver eta %.6f   HWB eta %.6f   deviation %+6.3f %%"
              % (tag, r["eta"], a["eta"], rec["d_eta_pct"]))
        print("              U_L %.4f W/m2K (from the solver, not fitted)   "
              "F_fin %.4f -> %.4f (avg %.4f)   F' avg %.4f   F_R %.4f"
              % (r["U_L"], a["F_fin_inlet"], a["F_fin_outlet"], a["F_fin_avg"],
                 a["F_prime_avg"], a["F_R"]))

    # the roadmap's own design targets, for completeness
    co = res["cases"]["co_current"]
    res["roadmap_targets"] = {
        "eta0_target": 0.60, "eta0_solver": co["solver"]["eta"],
        "FR_UL_target": 2.00, "FR_UL_hwb": co["hwb"]["FR_UL"],
        "note": "these are the roadmap's design intent, so agreement with them is "
                "self-consistency, not validation. The HWB comparison above is the "
                "independent check."}
    json.dump(res, open(os.path.join(OUT, "hwb_validation.json"), "w"), indent=1)
    print("\nroadmap eta0 target 0.60 vs solver %.4f ; F_R U_L target 2.00 vs HWB %.4f"
          % (co["solver"]["eta"], co["hwb"]["FR_UL"]))
    print("wrote hwb_validation.json")
