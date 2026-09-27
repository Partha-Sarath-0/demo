"""Stage 6b - collector efficiency correlations from the virtual test (ISO 9806 steady form).

  q_u / A = eta0 * G  -  a1 (Tm - Ta)  -  a2 (Tm - Ta)^2          [W/m2],  Tm = (T_in + T_out)/2
  eta = eta0 - a1 x - a2 G x^2,  x = (Tm - Ta)/G  (reduced temperature, K m2/W)

Fit set: the 8 (G, T_in) points at wind 3 m/s and T_amb 303.15 K, per arrangement.
Held-out validation (NOT used in the fit): wind 0.5 and 4.9 m/s, and T_amb 288.15 K.
Also reported: the inlet-temperature form (x_in = (T_in - Ta)/G), which is what the dataset uses.
Aperture 0.528 m2 and eta on INCIDENT irradiance, exactly as the dataset defines them.
"""
import json, numpy as np, pandas as pd

D = "/home/claude/grail_cfd/22_system/"
v = pd.read_csv(D + "virtual_test_matrix.csv")
assert v.converged.all()
v["Tm"] = 0.5 * (v.T_in + v.T_out_K)
v["dT"] = v.Tm - v.T_amb
v["x"] = v.dT / v.G_T
v["q"] = v.eta * v.G_T                 # useful heat per m2 aperture, W/m2
v["x_in"] = (v.T_in - v.T_amb) / v.G_T
fit_mask = (v.v_wind == 3.0) & (v.T_amb == 303.15)
out = {}
for arr, g in v.groupby("arrangement"):
    f = g[fit_mask[g.index]]
    A = np.column_stack([f.G_T, -f.dT, -f.dT ** 2])
    coef, *_ = np.linalg.lstsq(A, f.q, rcond=None)
    eta0, a1, a2 = coef
    unconstrained = dict(eta0=eta0, a1=a1, a2=a2)
    if a2 < 0:   # a negative quadratic loss is unphysical; refit with a2 = 0 and keep both on record
        coef2, *_ = np.linalg.lstsq(A[:, :2], f.q, rcond=None)
        eta0, a1, a2 = coef2[0], coef2[1], 0.0
    pred = lambda h: eta0 - a1 * h.x - a2 * h.G_T * h.x ** 2
    res_fit = (f.eta - pred(f)) * 100
    h = g[~fit_mask[g.index]]
    res_val = (h.eta - pred(h)) * 100
    # inlet-temperature form
    Ai = np.column_stack([f.G_T, -(f.T_in - f.T_amb), -(f.T_in - f.T_amb) ** 2])
    ci, *_ = np.linalg.lstsq(Ai, f.q, rcond=None)
    wind = g[(g.G_T == 900) & (g.T_in == 323.15) & (g.T_amb == 303.15)].sort_values("v_wind")
    out[arr] = dict(unconstrained_fit=unconstrained, a2_constraint='a2 >= 0 enforced' if unconstrained['a2'] < 0 else 'not active', eta0=eta0, a1_W_m2K=a1, a2_W_m2K2=a2,
                    fit_rms_pp=float(np.sqrt(np.mean(res_fit ** 2))), fit_max_pp=float(np.abs(res_fit).max()),
                    holdout=[dict(G=r.G_T, T_in=r.T_in, T_amb=r.T_amb, wind=r.v_wind, eta_cht=r.eta,
                                  eta_fit=float(pred(r)), err_pp=float((r.eta - pred(r)) * 100)) for _, r in h.iterrows()],
                    inlet_form=dict(eta0=ci[0], a1=ci[1], a2=ci[2]),
                    wind_sensitivity_eta=dict(zip(wind.v_wind.astype(str), wind.eta.round(5))),
                    Tm_minus_Ta_range_K=[float(f.dT.min()), float(f.dT.max())])
    print(arr, "eta0 %.4f a1 %.3f a2 %.5f  fit rms %.3f pp  holdout errs %s  wind %s" % (
        eta0, a1, a2, out[arr]["fit_rms_pp"], [round(x["err_pp"], 3) for x in out[arr]["holdout"]],
        out[arr]["wind_sensitivity_eta"]))
json.dump(out, open(D + "efficiency_correlations.json", "w"), indent=1, default=float)
v.to_csv(D + "virtual_test_matrix_with_x.csv", index=False)
