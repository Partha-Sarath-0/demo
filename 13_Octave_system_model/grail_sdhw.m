function [S, closure_kWh] = grail_sdhw(W, P, c)
% GRAIL_SDHW  Dynamic solar domestic hot-water system: GRAIL collector (one thermal node, ISO 9806
% quasi-dynamic form) + fully mixed tank + differential pump control + mixing valve + electric
% top-up. Explicit tank, implicit collector-fluid coupling, step P.dt (60 s), weather held within
% each hour. c = [eta0 a1 a2].
%   C_eff A dTc/dt = A [eta0 G_eff - a1 (Tc-Ta) - a2 (Tc-Ta)^2] - 2 mdot cp (Tc - Tt) * pump
%   M cp dTt/dt    = 2 mdot cp (Tc - Tt) * pump - UA (Tt - Ta)          (+ hourly draw)
A = P.n_mod * P.A_mod; C = P.C_eff * A; mdot = P.mdot_mod * P.n_mod;
M = P.tank_kg; UA = P.tank_UA; cp = P.cp; dt = P.dt; nsub = round(3600 / dt);
Ta_h = W.T_amb; G_h = W.G_eff; nh = numel(Ta_h);
mains = zeros(nh, 1);
for i = 1:nh
    mains(i) = mean(Ta_h(max(1, i - 23):i));               % trailing 24-h mean
end
Tc = Ta_h(1); Tt = 298.15; pump = false; E0 = M * cp * Tt;
f = {'Q_coll', 'Q_load', 'Q_aux', 'Q_solar', 'Q_loss', 'pump_s', 'Tt', 'Tc_max', 'Q_draw'};
for k = 1:numel(f), S.(f{k}) = zeros(nh, 1); end
g2 = 2 * mdot * cp;
for i = 1:nh
    Ta = Ta_h(i); G = G_h(i); tcmax = Tc;
    qc = 0; qlo = 0; ps = 0;
    for s = 1:nsub
        if pump && (Tc - Tt < P.dT_off || Tt > P.T_tank_max)
            pump = false;
        elseif ~pump && (Tc - Tt > P.dT_on) && (Tt <= P.T_tank_max)
            pump = true;
        end
        dT = Tc - Ta;
        gain = A * (c(1) * G - c(2) * dT - c(3) * dT * dT);
        if pump
            Tc = (C * Tc + dt * (gain + g2 * Tt)) / (C + dt * g2);
            qf = g2 * (Tc - Tt); ps = ps + dt;
        else
            Tc = Tc + dt * gain / C; qf = 0;
        end
        ql = UA * (Tt - Ta);
        Tt = Tt + dt * (qf - ql) / (M * cp);
        qc = qc + qf * dt; qlo = qlo + ql * dt;
        if Tc > tcmax, tcmax = Tc; end
    end
    S.Q_coll(i) = qc; S.Q_loss(i) = qlo; S.pump_s(i) = ps;
    m_load = P.draw_kg_day * P.prof(W.hour_ist(i) + 1);
    Tmn = mains(i);
    if m_load > 0
        Ql = m_load * cp * (P.T_set - Tmn);
        if Tt >= P.T_set
            m_t = m_load * (P.T_set - Tmn) / (Tt - Tmn);
        else
            m_t = m_load;
        end
        if Tt > Tmn, sol = min(m_t * cp * (Tt - Tmn), Ql); else, sol = 0; end
        S.Q_draw(i) = m_t * cp * (Tt - Tmn);
        Tt = (Tt * (M - m_t) + Tmn * m_t) / M;
        S.Q_load(i) = Ql; S.Q_solar(i) = sol; S.Q_aux(i) = Ql - sol;
    end
    S.Tt(i) = Tt; S.Tc_max(i) = tcmax;
end
% first law for the tank: dE = Q_coll - Q_loss - Q_draw
closure_kWh = (sum(S.Q_coll) - sum(S.Q_loss) - sum(S.Q_draw) - (M * cp * Tt - E0)) / 3.6e6;
end
