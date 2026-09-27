% RUN_CONT_REFERENCE  Octave reference for the Xcos model: same system with the continuous draw
% formulation (grail_sdhw_cont.m), at 60 s and 10 s steps to show step-size convergence.
P = grail_params(); W = grail_weather(P);
arr = {'alternating', 'parallel'};
fid = fopen('octave_cont_reference.csv', 'w');
fprintf(fid, 'arrangement,n_modules,dt_s,Q_coll_kWh,Q_loss_kWh,Q_draw_kWh,Q_solar_kWh,Q_load_kWh,pump_h,solar_fraction,Tc_max_K,closure_kWh\n');
for n = [2 4]
  for a = 1:2
    for dt = [60 10]
      Pn = P; Pn.n_mod = n;
      [S, cl] = grail_sdhw_cont(W, Pn, P.corr.(arr{a}), dt);
      k = @(x) sum(x) / 3.6e6;
      fprintf(fid, '%s,%d,%d,%.4f,%.4f,%.4f,%.4f,%.4f,%.2f,%.6f,%.3f,%.3e\n', arr{a}, n, dt, k(S.Q_coll), k(S.Q_loss), k(S.Q_draw), ...
              k(S.Q_solar), k(S.Q_load), sum(S.pump_s) / 3600, k(S.Q_solar) / k(S.Q_load), max(S.Tc_max), cl);
      fprintf('%s %d mod dt %d: SF %.4f solar %.2f max Tc %.2f closure %.1e\n', arr{a}, n, dt, k(S.Q_solar) / k(S.Q_load), k(S.Q_solar), max(S.Tc_max), cl);
    end
  end
end
fclose(fid);
