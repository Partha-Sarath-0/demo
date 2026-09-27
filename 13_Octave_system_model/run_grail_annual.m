% RUN_GRAIL_ANNUAL  GRAIL Collector - Stage 6/7 system model and 8760-h Berhampur simulation.
% GNU Octave / MATLAB. Run from this folder:   octave --no-gui run_grail_annual.m
% Outputs: octave_results.csv (sizing sweep), octave_collector_only.csv, octave_monthly.csv,
%          octave_annual.png
clear; clc;
P = grail_params();
tic; W = grail_weather(P);
fprintf('Weather: GHI %.1f  POA %.1f  POA after IAM %.1f kWh/m2/yr  (%.1f s)\n', ...
        sum(W.GHI) / 1e3, sum(W.G_T) / 1e3, sum(W.G_eff) / 1e3, toc);

arr = {'alternating', 'parallel'};
% ---- A. collector-only yield at fixed inlet ----
fid = fopen('octave_collector_only.csv', 'w');
fprintf(fid, 'arrangement,T_in_K,kWh_m2_yr,annual_eff_on_POA,operating_hours\n');
mon = zeros(12, 2);
for a = 1:2
    c = P.corr.(arr{a});
    for Tin = [313.15 333.15]
        q = grail_collector_only(W, P, c, Tin);
        fprintf(fid, '%s,%.2f,%.4f,%.6f,%d\n', arr{a}, Tin, sum(q) / 1e3, sum(q) / sum(W.G_T), sum(q > 0));
        fprintf('%-11s collector only, T_in %.2f K: %7.1f kWh/m2/yr\n', arr{a}, Tin, sum(q) / 1e3);
        if Tin == 313.15
            for m = 1:12, mon(m, a) = sum(q(W.month == m)) / 1e3; end
        end
    end
end
fclose(fid);

% ---- B. SDHW sizing sweep (1-4 modules) with economics ----
fid = fopen('octave_results.csv', 'w');
fprintf(fid, 'arrangement,n_modules,aperture_m2,solar_fraction,Q_solar_kWh,Q_load_kWh,tank_loss_kWh,max_collector_K,pump_kWh,closure_kWh,capex_Rs,net_saving_Rs,simple_payback_yr,discounted_payback_yr,NPV_Rs,LCOH_Rs_kWh\n');
sfm = zeros(12, 2);
for a = 1:2
    c = P.corr.(arr{a});
    for n = 1:4
        Pn = P; Pn.n_mod = n;
        tic; [S, cl] = grail_sdhw(W, Pn, c); t = toc;
        Qs = sum(S.Q_solar) / 3.6e6; Ql = sum(S.Q_load) / 3.6e6;
        pk = sum(S.pump_s) / 3600 * P.pump_W / 1e3;
        capex = P.capex_fixed + P.capex_per_mod * n;
        E = grail_econ(Qs / P.geyser_eff, pk, Qs, P, capex, P.tariff);
        fprintf(fid, '%s,%d,%.3f,%.6f,%.3f,%.3f,%.3f,%.2f,%.3f,%.2e,%.0f,%.2f,%.3f,%d,%.1f,%.4f\n', arr{a}, n, n * P.A_mod, ...
                Qs / Ql, Qs, Ql, sum(S.Q_loss) / 3.6e6, max(S.Tc_max), pk, cl, capex, E.net_saving_Rs, ...
                E.simple_payback_yr, E.discounted_payback_yr, E.NPV_Rs, E.LCOH_Rs_kWh);
        fprintf('%-11s %d modules: SF %5.1f %%  solar %6.1f kWh  LCOH %.2f Rs/kWh  payback %.1f yr  closure %.1e kWh  (%.0f s)\n', ...
                arr{a}, n, 100 * Qs / Ql, Qs, E.LCOH_Rs_kWh, E.simple_payback_yr, cl, t);
        if n == 2
            for m = 1:12, k = W.month == m; sfm(m, a) = sum(S.Q_solar(k)) / sum(S.Q_load(k)); end
        end
    end
end
fclose(fid);
M = [(1:12)', mon, sfm];
fid = fopen('octave_monthly.csv', 'w');
fprintf(fid, 'month,alt_yield_Tin313_kWh_m2,par_yield_Tin313_kWh_m2,alt_SF_2mod,par_SF_2mod\n');
fprintf(fid, '%d,%.4f,%.4f,%.5f,%.5f\n', M');
fclose(fid);

% ---- figure (needs a working graphics toolkit; skipped with a message on headless systems) ----
try
    if exist('OCTAVE_VERSION', 'builtin') && ~any(strcmp(available_graphics_toolkits(), 'qt'))
        warning('off', 'all'); graphics_toolkit('gnuplot');   % headless Octave: fall back to gnuplot
    end
    h = figure('visible', 'off', 'position', [0 0 1100 420]);
    subplot(1, 2, 1); bar(1:12, mon(:, [2 1]));
    xlabel('month'); ylabel('useful heat (kWh/m^2)'); title('Collector yield, inlet 40 C (Octave model)');
    legend('parallel', 'alternating', 'location', 'northeast'); grid on;
    subplot(1, 2, 2); plot(1:12, 100 * sfm(:, 2), '-o', 1:12, 100 * sfm(:, 1), '-s');
    xlabel('month'); ylabel('solar fraction (%)'); title('2 modules, 100 L/day at 45 C');
    legend('parallel', 'alternating', 'location', 'southwest'); grid on;
    print(h, 'octave_annual.png', '-dpng', '-r110');
catch err
    fprintf('figure skipped: %s\n', err.message);
end
fprintf('done\n');
