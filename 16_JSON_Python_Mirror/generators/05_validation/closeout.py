"""
GRAIL — the three remaining verification items.

A. Nu(xi) instead of a constant       bounds the largest unquantified term in the assessment
B. PCM time-step sensitivity          the one numerical check the PCM study did not carry
C. efficiency-curve fit               settles the 15 % spread between the two F_R U_L estimators

Writes 05_validation/closeout.json
"""
import sys, os, json, time
import numpy as np

sys.path.insert(0, "/home/claude/grail_cfd/tools")
from grail_cht import Geometry, Materials, Operating, GrailCHT
from grail_ext import make_geom, make_op, GrailPCM

OUT = "/home/claude/grail_cfd/05_validation"
NX, NY = 220, 240
NU_CONST = 2.9238
res = {}
t0 = time.time()


# ============================================================ A. Nu(xi) vs a constant
def nu_profile_from(path, scale_to=None):
    """Local Nu(xi) from a 3-D solution, as an interpolator. Optionally rescaled so its
    flow-path mean over the developed region matches a target, which isolates the SHAPE
    of the profile from its level."""
    d = json.load(open(path))
    xi = np.array([r["xi"] for r in d])
    nu = np.array([r["Nu"] for r in d])
    ok = np.isfinite(nu)
    xi, nu = xi[ok], nu[ok]
    if scale_to is not None:
        dev = xi > 0.15
        nu = nu * (scale_to / nu[dev].mean())

    def f(q):
        return np.interp(np.clip(q, 0.0, 1.0), xi, nu)
    return f, xi, nu


print("A. Nu(xi) against a constant Nu", flush=True)
prof_raw, xi_p, nu_p = nu_profile_from(OUT + "/htc_L3.json")
prof_scaled, _, nu_s = nu_profile_from(OUT + "/htc_L3.json", scale_to=NU_CONST)
A = {"nu_constant": NU_CONST,
     "profile_source": "htc_L3.json, 356,400-cell grid",
     "nu_profile_min": float(nu_p.min()), "nu_profile_max": float(nu_p.max()),
     "nu_profile_developed_mean": float(nu_p[xi_p > 0.15].mean()),
     "cases": {}}
for tag, nu in (("constant", NU_CONST), ("profile_as_measured", prof_raw),
                ("profile_rescaled_same_mean", prof_scaled)):
    rec = {}
    for name, f in (("co", 0), ("alt", 1)):
        s = GrailCHT(Geometry(), Materials(), Operating(f_interdig=f), nx=NX, ny=NY, nu_cfd=nu)
        r = s.solve(max_outer=2500, tol=1e-8)
        rec[name] = {k: r[k] for k in ("eta", "Tp_mean", "Tp_std", "U_L", "T_out")}
    for q in ("eta", "Tp_std", "U_L"):
        rec["d_%s_pct" % q] = 100 * (rec["alt"][q] - rec["co"][q]) / rec["co"][q]
    A["cases"][tag] = rec
    print("   %-28s d_eta %+7.3f %%   d_Tp_std %+8.3f %%   (%.0f s)"
          % (tag, rec["d_eta_pct"], rec["d_Tp_std_pct"], time.time() - t0), flush=True)
c, p_, ps = A["cases"]["constant"], A["cases"]["profile_as_measured"], \
    A["cases"]["profile_rescaled_same_mean"]
A["model_form_effect"] = {
    "d_Tp_std_shift_from_shape_only_pp": ps["d_Tp_std_pct"] - c["d_Tp_std_pct"],
    "d_Tp_std_shift_total_pp": p_["d_Tp_std_pct"] - c["d_Tp_std_pct"],
    "d_eta_shift_from_shape_only_pp": ps["d_eta_pct"] - c["d_eta_pct"],
    "d_eta_shift_total_pp": p_["d_eta_pct"] - c["d_eta_pct"],
    "note": "'shape only' rescales the profile to the same developed-region mean as the "
            "constant, so it isolates the cost of collapsing Nu(xi) to one number from the "
            "cost of getting that number's level wrong"}
res["A_nu_profile"] = A

# ============================================================ B. PCM time step
print("\nB. PCM time-step sensitivity, charge scenario", flush=True)
B = {"scenario": "charge, design point, 2 h", "levels": {}}
for dt in (20.0, 10.0, 5.0):
    s = GrailPCM(make_geom(12), Materials(),
                 make_op(12, G_T=800.0, mdot_full=0.0025, f_interdig=1),
                 nx=110, ny=120, pcm_on=True, T_pcm0=300.0)
    fr, tt = s.run(t_end=2 * 3600.0, dt=dt, save_every=int(600 / dt), T0=300.0)
    B["levels"]["dt_%g" % dt] = {
        "dt": dt, "Tp_mean_final_K": float(fr[-1].mean()),
        "Tp_max_final_K": float(fr[-1].max()),
        "pcm_T_final_K": float(s.T_pcm.mean()),
        "liquid_fraction_final": float(s.liquid_fraction(s.T_pcm).mean()),
        "stored_MJ_m2": float(s.stored_energy_J_m2().mean() / 1e6)}
    print("   dt = %5.1f s   Tp mean %.4f K   f_liq %.5f   stored %.5f MJ/m2   (%.0f s)"
          % (dt, B["levels"]["dt_%g" % dt]["Tp_mean_final_K"],
             B["levels"]["dt_%g" % dt]["liquid_fraction_final"],
             B["levels"]["dt_%g" % dt]["stored_MJ_m2"], time.time() - t0), flush=True)
a, b, c2 = (B["levels"]["dt_20"], B["levels"]["dt_10"], B["levels"]["dt_5"])
B["convergence"] = {
    "Tp_mean_20_to_10_K": b["Tp_mean_final_K"] - a["Tp_mean_final_K"],
    "Tp_mean_10_to_5_K": c2["Tp_mean_final_K"] - b["Tp_mean_final_K"],
    "stored_20_to_10_pct": 100 * (b["stored_MJ_m2"] - a["stored_MJ_m2"]) / b["stored_MJ_m2"],
    "stored_10_to_5_pct": 100 * (c2["stored_MJ_m2"] - b["stored_MJ_m2"]) / c2["stored_MJ_m2"]}
res["B_pcm_timestep"] = B

# ============================================================ C. efficiency curve
print("\nC. efficiency-curve fit", flush=True)
G_T = 800.0
T_amb = 298.15
pts = []
for T_in in (288.0, 298.0, 308.0, 318.0, 328.0, 338.0):
    row = {"T_in": T_in, "x": (T_in - T_amb) / G_T}
    for name, f in (("co", 0), ("alt", 1)):
        s = GrailCHT(Geometry(), Materials(),
                     Operating(G_T=G_T, T_in=T_in, T_amb=T_amb, f_interdig=f),
                     nx=NX, ny=NY, nu_cfd=NU_CONST)
        r = s.solve(max_outer=2500, tol=1e-8)
        row[name] = {"eta": r["eta"], "U_L": r["U_L"], "Tp_mean": r["Tp_mean"]}
    pts.append(row)
    print("   T_in %.1f K   x = %.5f   eta co %.5f  alt %.5f   (%.0f s)"
          % (T_in, row["x"], row["co"]["eta"], row["alt"]["eta"], time.time() - t0), flush=True)
Cc = {"G_T": G_T, "T_amb": T_amb, "nu_cfd": NU_CONST, "points": pts, "fits": {}}
x = np.array([p["x"] for p in pts])
for name in ("co", "alt"):
    y = np.array([p[name]["eta"] for p in pts])
    a1, a0 = np.polyfit(x, y, 1)
    q = np.polyfit(x, y, 2)
    pred = a0 + a1 * x
    r2 = 1 - ((y - pred) ** 2).sum() / ((y - y.mean()) ** 2).sum()
    Cc["fits"][name] = {"eta0": float(a0), "FR_UL": float(-a1), "R2_linear": float(r2),
                        "quadratic": [float(v) for v in q],
                        "a2_second_order": float(q[0])}
    print("   %-4s  eta0 = %.5f   F_R U_L = %.4f W/m2K   R2 = %.6f"
          % (name, a0, -a1, r2))
Cc["comparison"] = {
    "roadmap_eta0_target": 0.60, "roadmap_FR_UL_target": 2.00,
    "hwb_pointwise_FR_UL": 2.2993,
    "note": "the curve-slope F_R U_L is the ISO 9806 / ASHRAE 93 estimator and is the one "
            "that should be quoted; the Hottel-Whillier-Bliss point-wise product uses U_L at "
            "a single operating point and is not the same quantity"}
res["C_efficiency_curve"] = Cc

json.dump(res, open(os.path.join(OUT, "closeout.json"), "w"), indent=1)
print("\nwrote closeout.json  (%.0f s)" % (time.time() - t0))
