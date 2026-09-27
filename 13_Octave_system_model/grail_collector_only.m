function q = grail_collector_only(W, P, c, T_in)
% GRAIL_COLLECTOR_ONLY  Quasi-steady hourly useful heat (W/m2) at a fixed inlet temperature T_in (K).
% Mean fluid temperature solved from T_in by fixed-point iteration; only positive gains counted.
mdot_m2 = P.mdot_mod / P.A_mod;
Tm = T_in * ones(size(W.T_amb));
for it = 1:50
    dT = Tm - W.T_amb;
    q = c(1) * W.G_eff - c(2) * dT - c(3) * dT .^ 2;
    Tm = T_in + max(q, 0) / (2 * mdot_m2 * P.cp);
end
dT = Tm - W.T_amb;
q = c(1) * W.G_eff - c(2) * dT - c(3) * dT .^ 2;
q(q < 0) = 0;
end
