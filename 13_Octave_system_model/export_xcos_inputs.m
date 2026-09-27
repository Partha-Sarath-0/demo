% EXPORT_XCOS_INPUTS  Writes the hourly inputs of the Xcos model (xcos_inputs.csv):
% hour, G_eff (W/m2), T_amb (K), T_mains (K), draw flow (kg/s). Same weather processing as
% run_grail_annual.m, so all three implementations see identical inputs.
P = grail_params(); W = grail_weather(P);
nh = numel(W.T_amb); mains = zeros(nh, 1);
for i = 1:nh, mains(i) = mean(W.T_amb(max(1, i - 23):i)); end
md = P.draw_kg_day * P.prof(W.hour_ist + 1)' / 3600;
M = [(0:nh-1)', W.G_eff, W.T_amb, mains, md];
fid = fopen('xcos_inputs.csv', 'w'); fprintf(fid, 'hour,G_eff_W_m2,T_amb_K,T_mains_K,draw_kg_s\n');
fprintf(fid, '%d,%.6f,%.6f,%.6f,%.9f\n', M'); fclose(fid);
fprintf('wrote xcos_inputs.csv (%d rows), draw %.3f kg/day\n', nh, sum(md) * 3600 / 365);
