function [S, closure_kWh] = grail_sdhw_cont(W, P, c, dt)
% GRAIL_SDHW_CONT  Same system as grail_sdhw.m, but the hot-water draw is a continuous flow
% during each draw hour (the formulation used in the Xcos block diagram). Used to verify Xcos.
A = P.n_mod * P.A_mod; C = P.C_eff * A; mdot = P.mdot_mod * P.n_mod;
M = P.tank_kg; UA = P.tank_UA; cp = P.cp; nsub = round(3600 / dt); g2 = 2 * mdot * cp;
Ta_h = W.T_amb; G_h = W.G_eff; nh = numel(Ta_h); mains = zeros(nh, 1);
for i = 1:nh, mains(i) = mean(Ta_h(max(1, i - 23):i)); end
Tc = Ta_h(1); Tt = 298.15; pump = false; E0 = M * cp * Tt;
f = {'Q_coll', 'Q_load', 'Q_aux', 'Q_solar', 'Q_loss', 'pump_s', 'Tc_max', 'Q_draw'};
for k = 1:numel(f), S.(f{k}) = zeros(nh, 1); end
for i = 1:nh
    Ta = Ta_h(i); G = G_h(i); Tmn = mains(i); tcmax = Tc;
    md = P.draw_kg_day * P.prof(W.hour_ist(i) + 1) / 3600;
    for s = 1:nsub
        if pump && (Tc - Tt < P.dT_off || Tt > P.T_tank_max), pump = false;
        elseif ~pump && (Tc - Tt > P.dT_on) && (Tt <= P.T_tank_max), pump = true; end
        dT = Tc - Ta; gain = A * (c(1) * G - c(2) * dT - c(3) * dT * dT);
        if pump
            Tc = (C * Tc + dt * (gain + g2 * Tt)) / (C + dt * g2); qf = g2 * (Tc - Tt); S.pump_s(i) = S.pump_s(i) + dt;
        else
            Tc = Tc + dt * gain / C; qf = 0;
        end
        ql = UA * (Tt - Ta);
        mt = md * min(1, (P.T_set - Tmn) / max(Tt - Tmn, 1e-9));
        qd = mt * cp * (Tt - Tmn);
        qs = min(mt * cp * max(Tt - Tmn, 0), md * cp * (P.T_set - Tmn));
        qL = md * cp * (P.T_set - Tmn);
        Tt = Tt + dt * (qf - ql - qd) / (M * cp);
        S.Q_coll(i) = S.Q_coll(i) + qf * dt; S.Q_loss(i) = S.Q_loss(i) + ql * dt; S.Q_draw(i) = S.Q_draw(i) + qd * dt;
        S.Q_solar(i) = S.Q_solar(i) + qs * dt; S.Q_load(i) = S.Q_load(i) + qL * dt;
        if Tc > tcmax, tcmax = Tc; end
    end
    S.Q_aux(i) = S.Q_load(i) - S.Q_solar(i); S.Tc_max(i) = tcmax;
end
closure_kWh = (sum(S.Q_coll) - sum(S.Q_loss) - sum(S.Q_draw) - (M * cp * Tt - E0)) / 3.6e6;
end
