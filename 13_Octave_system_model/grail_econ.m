function E = grail_econ(saved_kWh, pump_kWh, Q_solar_kWh, P, capex, tariff)
% GRAIL_ECON  Annual saving, simple and discounted payback, NPV and levelised cost of solar heat.
net = (saved_kWh - pump_kWh) * tariff - P.om * capex;
r = P.disc; n = P.life;
crf = r * (1 + r) ^ n / ((1 + r) ^ n - 1);
E.net_saving_Rs = net;
E.simple_payback_yr = capex / net;
E.discounted_payback_yr = NaN;
for y = 1:40
    if net * (1 - (1 + r) ^ -y) / r >= capex, E.discounted_payback_yr = y; break; end
end
E.NPV_Rs = net * (1 - (1 + r) ^ -n) / r - capex;
E.LCOH_Rs_kWh = (capex * crf + P.om * capex + pump_kWh * tariff) / Q_solar_kWh;
end
