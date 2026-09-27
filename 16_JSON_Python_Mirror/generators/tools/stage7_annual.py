"""Stage 6c + 7 - dynamic collector/tank system model and 8760-h annual simulation, Berhampur.

All temperatures in kelvin. SI units throughout (J, W, kg, s, m2); kWh only at reporting.

A. Collector-only annual yield at fixed inlet temperature (the standard 'kWh/m2/yr' figure):
   quasi-steady, hourly, eta(Tm) from the Stage 6 fit, Tm solved from T_in by fixed point,
   heat counted only when q_u > 0. Inlet cases: 313.15 K and 333.15 K.

B. Solar domestic hot water (SDHW) system, dynamic (60 s step, weather held within the hour):
   collector: single thermal node at Tm (ISO 9806 quasi-dynamic form, effective capacity C_eff)
       C_eff A dTm/dt = A [K(theta) eta0 G - a1 (Tm-Ta) - a2 (Tm-Ta)^2] - 2 mdot cp (Tm - T_tank)*pump
   tank: fully mixed, M = 100 kg, UA = 1.5 W/K to ambient
   control: pump on when Tm - T_tank > 7 K, off below 2 K; off when T_tank > 358.15 K (protection)
   load: 100 L/day delivered at 318.15 K (45 C) through a thermostatic mixing valve; draw profile
         40 % 06-08 h, 20 % 12-13 h, 40 % 18-20 h IST; mains = trailing 24-h mean ambient.
   auxiliary: electric top-up to 318.15 K at the draw.
C. Economics (Odisha, TPSODL LT-domestic tariff FY 2025-26, retained for FY 2026-27).

ENGINEERING_ASSUMPTIONS are listed in ASSUMPTIONS and written to the output JSON.
"""
import json, sys, numpy as np, pandas as pd
sys.path.insert(0, "/home/claude/grail_cfd/tools")
import stage7_weather as W

CP = 4180.0
A_MOD = 0.528
CORR = json.load(open("/home/claude/grail_cfd/22_system/efficiency_correlations.json"))
OUT = "/home/claude/grail_cfd/20_annual/"

ASSUMPTIONS = dict(
    tilt_deg=19.3, azimuth_deg=180, transposition="Hay-Davies, albedo 0.20",
    iam="Kb = 1 - b0 (1/cos(theta) - 1), b0 = 0.10, Kb = 0 beyond 80 deg; diffuse Kd = Kb(60 deg) = 0.90",
    n_modules=4, aperture_m2=4 * A_MOD, mdot_per_module_kg_s=0.00275,
    C_eff_J_m2K=33500.0,
    C_eff_basis="Al sheets 4.87 + channel water 7.46 + PCM sensible only 16.0 + 0.5x(glass 6.72 + TIM 0.36 + VIP 3.2) kJ/m2K; PCM latent heat NOT modelled (deferred)",
    tank_kg=100.0, tank_UA_W_K=1.5, T_set_K=318.15, daily_draw_kg=100.0,
    draw_profile="40% 06-08h, 20% 12-13h, 40% 18-20h IST", mains="trailing 24-h mean ambient",
    pump_on_dT_K=7.0, pump_off_dT_K=2.0, tank_max_K=358.15, pump_power_W=15.0,
    geyser_efficiency=0.95,
)
ECON = dict(
    tariff_Rs_kWh=4.70, tariff_basis="TPSODL LT domestic 51-200 kWh/month slab, 470 paise/kWh (FY 2025-26, retained FY 2026-27); electricity duty excluded (conservative)",
    tariff_high_Rs_kWh=5.70, capex_Rs=30000.0, capex_range_Rs=[22000.0, 45000.0],
    capex_basis="ENGINEERING_ASSUMPTION: market 100 LPD flat-plate system Rs 20,000-30,000 + installation Rs 3,000-10,000; GRAIL prototype cost unknown",
    om_frac_per_yr=0.01, life_yr=15, discount=0.08,
)


def iam(theta_deg, b0=0.10):
    th = np.radians(np.minimum(theta_deg, 89.9))
    k = 1.0 - b0 * (1.0 / np.cos(th) - 1.0)
    return np.where(theta_deg < 80.0, np.clip(k, 0, 1), 0.0)


def eff_irr(w):
    return iam(w.aoi_deg.values) * w.G_beam.values + 0.90 * w.G_diff.values


def q_useful(Tm, Ta, Geff, c):
    dT = Tm - Ta
    return c["eta0"] * Geff - c["a1_W_m2K"] * dT - c["a2_W_m2K2"] * dT ** 2


def collector_only(w, Geff, c, T_in, mdot_m2):
    """Quasi-steady hourly yield per m2 at fixed inlet; returns W/m2 array."""
    Ta = w.T_amb_K.values
    Tm = np.full(len(w), T_in)
    for _ in range(50):
        q = q_useful(Tm, Ta, Geff, c)
        Tm = T_in + np.maximum(q, 0) / (2 * mdot_m2 * CP)
    q = q_useful(Tm, Ta, Geff, c)
    return np.where(q > 0, q, 0.0), Tm


def sdhw(w, Geff, c, a=ASSUMPTIONS, dt=60.0):
    A = a["aperture_m2"]; C = a["C_eff_J_m2K"] * A
    mdot = a["mdot_per_module_kg_s"] * a["n_modules"]
    M, UA, Tset = a["tank_kg"], a["tank_UA_W_K"], a["T_set_K"]
    Ta_h, G_h, hr = w.T_amb_K.values, Geff, w.local_hour.values
    mains = pd.Series(Ta_h).rolling(24, min_periods=1).mean().values
    prof = np.zeros(24); prof[[6, 7]] = 0.20; prof[12] = 0.20; prof[[18, 19]] = 0.20
    n = int(3600 / dt)
    Tc, Tt, pump = Ta_h[0], 298.15, False
    rec = {k: np.zeros(len(w)) for k in ["Q_coll", "Q_load", "Q_aux", "Q_solar_del", "Q_tankloss", "pump_s", "Tt", "Tc_max", "stag_s", "Q_draw_tank"]}
    E0 = M * CP * Tt
    for i in range(len(w)):
        Ta, G = Ta_h[i], G_h[i]
        tcmax = Tc
        for _ in range(n):
            if pump and (Tc - Tt < a["pump_off_dT_K"] or Tt > a["tank_max_K"]):
                pump = False
            elif (not pump) and Tc - Tt > a["pump_on_dT_K"] and Tt <= a["tank_max_K"]:
                pump = True
            gain = A * q_useful(Tc, Ta, G, c)
            qf = 2 * mdot * CP * (Tc - Tt) if pump else 0.0
            # implicit-in-Tc update for the fluid coupling (stable at any dt)
            if pump:
                Tc_new = (C * Tc + dt * (gain + 2 * mdot * CP * Tt)) / (C + dt * 2 * mdot * CP)
                qf = 2 * mdot * CP * (Tc_new - Tt)
                Tc = Tc_new
                rec["pump_s"][i] += dt
            else:
                Tc = Tc + dt * gain / C
            ql = UA * (Tt - Ta)
            Tt += dt * (qf - ql) / (M * CP)
            rec["Q_coll"][i] += qf * dt; rec["Q_tankloss"][i] += ql * dt
            if Tt > a["tank_max_K"] and not pump and Tc - Tt > a["pump_on_dT_K"]:
                rec["stag_s"][i] += dt
            tcmax = max(tcmax, Tc)
        # draw for this hour (applied at end of hour, mass-weighted)
        m_load = a["daily_draw_kg"] * prof[hr[i]]
        Tmn = mains[i]
        if m_load > 0:
            Ql = m_load * CP * (Tset - Tmn)
            if Tt >= Tset:
                m_t = m_load * (Tset - Tmn) / (Tt - Tmn); aux = 0.0
            else:
                m_t = m_load; aux = m_load * CP * (Tset - Tt)
            sol = m_t * CP * (Tt - Tmn) if Tt > Tmn else 0.0
            sol = min(sol, Ql)
            aux = Ql - sol
            rec["Q_draw_tank"][i] = m_t * CP * (Tt - Tmn)
            Tt = (Tt * (M - m_t) + Tmn * m_t) / M
            rec["Q_load"][i], rec["Q_aux"][i], rec["Q_solar_del"][i] = Ql, aux, sol
        rec["Tt"][i], rec["Tc_max"][i] = Tt, tcmax
    # tank energy closure: dE_tank = Q_coll - Q_tankloss - (energy removed by draws)
    return pd.DataFrame(rec, index=w.index), M * CP * Tt - E0


def econ(E_saved_kWh, pump_kWh, e=ECON, capex=None, tariff=None):
    capex = e["capex_Rs"] if capex is None else capex
    tariff = e["tariff_Rs_kWh"] if tariff is None else tariff
    net = (E_saved_kWh - pump_kWh) * tariff - e["om_frac_per_yr"] * capex
    r, n = e["discount"], e["life_yr"]
    crf = r * (1 + r) ** n / ((1 + r) ** n - 1)
    pv = net * (1 - (1 + r) ** -n) / r
    disc_pb = next((y for y in range(1, 41) if net * (1 - (1 + r) ** -y) / r >= capex), None)
    return dict(annual_net_saving_Rs=net, simple_payback_yr=capex / net if net > 0 else None,
                discounted_payback_yr=disc_pb, NPV_Rs=pv - capex, CRF=crf)


if __name__ == "__main__":
    w = W.load()
    Geff = eff_irr(w)
    res = dict(assumptions=ASSUMPTIONS, economics_inputs=ECON, weather=dict(
        POA_kWh_m2=w.G_T.sum() / 1e3, POA_eff_after_IAM_kWh_m2=Geff.sum() / 1e3, GHI_kWh_m2=w.GHI.sum() / 1e3))
    monthly = {}
    for arr in ["alternating", "parallel"]:
        c = CORR[arr]
        r = dict()
        for Tin in (313.15, 333.15):
            q, Tm = collector_only(w, Geff, c, Tin, 0.00275 / A_MOD)
            r["collector_only_Tin_%d_K" % round(Tin)] = dict(kWh_m2_yr=q.sum() / 1e3,
                                                              annual_eff_on_POA=q.sum() / w.G_T.sum(),
                                                              operating_hours=int((q > 0).sum()))
            monthly[(arr, round(Tin))] = pd.Series(q, index=w.index).groupby(w.month.values).sum() / 1e3
        s, dE = sdhw(w, Geff, c)
        Qload = s.Q_load.sum() / 3.6e6; Qaux = s.Q_aux.sum() / 3.6e6; Qsol = s.Q_solar_del.sum() / 3.6e6
        Qcoll = s.Q_coll.sum() / 3.6e6; Qloss = s.Q_tankloss.sum() / 3.6e6
        pump_kWh = s.pump_s.sum() / 3600 * ASSUMPTIONS["pump_power_W"] / 1e3
        closure = (Qcoll - Qloss - s.Q_draw_tank.sum() / 3.6e6) - dE / 3.6e6   # tank first law
        saved = Qsol / ASSUMPTIONS["geyser_efficiency"]
        r["sdhw"] = dict(Q_load_kWh=Qload, Q_solar_delivered_kWh=Qsol, Q_aux_kWh=Qaux, solar_fraction=Qsol / Qload,
                         Q_collector_to_tank_kWh=Qcoll, Q_tank_loss_kWh=Qloss, system_yield_kWh_m2=Qsol / ASSUMPTIONS["aperture_m2"],
                         pump_hours=s.pump_s.sum() / 3600, pump_kWh=pump_kWh, hours_tank_at_limit=int((s.Tt > 358.0).sum()),
                         max_collector_node_K=float(s.Tc_max.max()), max_tank_K=float(s.Tt.max()),
                         energy_closure_kWh=float(closure), electricity_saved_kWh=saved,
                         monthly_solar_fraction={int(m): float(g.Q_solar_del.sum() / g.Q_load.sum()) for m, g in s.groupby(w.month.values)})
        r["economics_base"] = econ(saved, pump_kWh)
        r["economics_sensitivity"] = {
            "capex_low": econ(saved, pump_kWh, capex=ECON["capex_range_Rs"][0]),
            "capex_high": econ(saved, pump_kWh, capex=ECON["capex_range_Rs"][1]),
            "tariff_570": econ(saved, pump_kWh, tariff=ECON["tariff_high_Rs_kWh"])}
        crf = r["economics_base"]["CRF"]
        r["LCOH_Rs_per_kWh_th"] = (ECON["capex_Rs"] * crf + ECON["om_frac_per_yr"] * ECON["capex_Rs"] + pump_kWh * ECON["tariff_Rs_kWh"]) / Qsol
        res[arr] = r
        s.to_csv(OUT + "sdhw_hourly_%s.csv" % arr)
        print(arr, json.dumps({k: (round(v, 3) if isinstance(v, float) else v) for k, v in r["sdhw"].items() if k != "monthly_solar_fraction"}))
        print("   collector-only:", {k: round(v["kWh_m2_yr"], 1) for k, v in r.items() if k.startswith("collector_only")},
              " econ:", {k: (round(v, 2) if isinstance(v, float) else v) for k, v in r["economics_base"].items()}, " LCOH %.2f" % r["LCOH_Rs_per_kWh_th"])
    pd.DataFrame({"%s_Tin%d" % k: v for k, v in monthly.items()}).assign(
        POA_kWh_m2=w.groupby("month").G_T.sum().values / 1e3).to_csv(OUT + "monthly_collector_yield.csv")
    json.dump(res, open(OUT + "stage7_results.json", "w"), indent=1, default=float)


def sizing_sweep():
    """Collector-area sizing for the same 100 L/day load: 1-4 modules, both arrangements.
    Capex scaled as fixed balance-of-system + per-module cost, anchored to the base case
    (4 modules = Rs 30,000): Rs 12,000 fixed + Rs 4,500 per module (ENGINEERING_ASSUMPTION)."""
    w = W.load(); Geff = eff_irr(w); rows = []
    for arr in ["alternating", "parallel"]:
        for n in (1, 2, 3, 4):
            a = dict(ASSUMPTIONS, n_modules=n, aperture_m2=n * A_MOD)
            s, dE = sdhw(w, Geff, CORR[arr], a=a)
            Qsol, Qload = s.Q_solar_del.sum() / 3.6e6, s.Q_load.sum() / 3.6e6
            pump_kWh = s.pump_s.sum() / 3600 * a["pump_power_W"] / 1e3
            capex = 12000.0 + 4500.0 * n
            e = econ(Qsol / a["geyser_efficiency"], pump_kWh, capex=capex)
            lcoh = (capex * e["CRF"] + ECON["om_frac_per_yr"] * capex + pump_kWh * ECON["tariff_Rs_kWh"]) / Qsol
            rows.append(dict(arrangement=arr, n_modules=n, aperture_m2=n * A_MOD, solar_fraction=Qsol / Qload,
                             Q_solar_kWh=Qsol, yield_kWh_m2=Qsol / (n * A_MOD), tank_loss_kWh=s.Q_tankloss.sum() / 3.6e6,
                             hours_tank_limit=int((s.Tt > 358.0).sum()), max_collector_K=float(s.Tc_max.max()),
                             hours_collector_above_393K=int((s.Tc_max > 393.15).sum()),
                             capex_Rs=capex, net_saving_Rs=e["annual_net_saving_Rs"], simple_payback_yr=e["simple_payback_yr"],
                             discounted_payback_yr=e["discounted_payback_yr"], NPV_Rs=e["NPV_Rs"], LCOH_Rs_kWh=lcoh))
    df = pd.DataFrame(rows); df.to_csv(OUT + "sizing_sweep.csv", index=False)
    print(df.round(3).to_string())


if __name__ == "__main__" and len(sys.argv) > 1 and sys.argv[1] == "sweep":
    sizing_sweep()
