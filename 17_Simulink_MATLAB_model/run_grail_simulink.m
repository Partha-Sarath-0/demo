% RUN_GRAIL_SIMULINK  Build the GRAIL Simulink model and simulate one year for 4 cases.
% MATLAB + Simulink. Run from this folder:  run_grail_simulink
% Inputs : xcos_inputs.csv (hourly G_eff, T_amb, T_mains, draw - the same file the Xcos model uses)
%          efficiency_correlations.json (Stage 6)
% Outputs: GRAIL_system.slx (the block diagram; open it with open_system('GRAIL_system'))
%          simulink_results.csv, and a comparison with xcos_results.csv if that file is present.
clear; clc;
here = fileparts(mfilename('fullpath'));
D = readmatrix(fullfile(here, 'xcos_inputs.csv'));         % hour, G_eff, T_amb, T_mains, draw
t = [D(:, 1); D(end, 1) + 1] * 3600;                        % add t = 8760 h: last hour is held,
D = [D; D(end, :)];                                         % not extrapolated
Vg = [t, D(:, 2)]; Va = [t, D(:, 3)]; Vm = [t, D(:, 4)]; Vd = [t, D(:, 5)];
assignin('base', 'Vg', Vg); assignin('base', 'Va', Va);
assignin('base', 'Vm', Vm); assignin('base', 'Vd', Vd);
Tc0 = D(1, 3); Tt0 = 298.15;                                % as in the Xcos and Octave models

cases = {'alternating', 2; 'parallel', 2; 'alternating', 4; 'parallel', 4};
fid = fopen(fullfile(here, 'simulink_results.csv'), 'w');
fprintf(fid, ['arrangement,n_modules,Q_coll_kWh,Q_loss_kWh,Q_draw_kWh,Q_solar_kWh,Q_load_kWh,', ...
              'pump_h,solar_fraction,Tt_end_K,Tc_max_K,closure_kWh,run_s\n']);
R = struct([]);
for k = 1:size(cases, 1)
    p = grail_sim_params(cases{k, 1}, cases{k, 2});
    mdl = build_grail_simulink(p, 'GRAIL_system', Tc0, Tt0);
    tic;
    out = sim(mdl, 'ReturnWorkspaceOutputs', 'on');
    rs = toc;
    E = out.get('E');  T = out.get('T');                    % E: rows every 3600 s, T: every 60 s
    Ef = E(end, :);                                         % totals at t = 8760 h (J, J, J, J, J, s)
    Tt_end = T(end, 2);
    closure = (Ef(1) - Ef(2) - Ef(3) - p.M * p.cp * (Tt_end - Tt0)) / 3.6e6;
    r.arr = cases{k, 1}; r.n = cases{k, 2};
    r.v = [Ef(1:5) / 3.6e6, Ef(6) / 3600, Ef(4) / Ef(5), Tt_end, max(T(:, 1)), closure, rs];
    R = [R, r]; %#ok<AGROW>
    fprintf(fid, '%s,%d,%.4f,%.4f,%.4f,%.4f,%.4f,%.2f,%.6f,%.4f,%.3f,%.3e,%.0f\n', r.arr, r.n, r.v);
    fprintf('%-11s %d modules: solar %.1f kWh, load %.1f kWh, SF %.2f %%, max Tc %.1f K, closure %.1e kWh (%.0f s)\n', ...
            r.arr, r.n, r.v(4), r.v(5), 100 * r.v(7), r.v(9), r.v(10), rs);
end
fclose(fid);
save_system('GRAIL_system');   % the saved .slx holds the parameters of the last case (parallel, 4)

% ---- comparison with the Scilab Xcos model (same equations, same inputs) -------------------
xf = fullfile(here, 'xcos_results.csv');
if exist(xf, 'file')
    X = readtable(xf);
    ok = true;
    fprintf('\nSimulink vs Xcos (PASS if solar heat within 0.25 %% and max Tc within 1.5 K)\n');
    for k = 1:numel(R)
        j = strcmp(X.arrangement, R(k).arr) & X.n_modules == R(k).n;
        dq = 100 * (R(k).v(4) / X.Q_solar_kWh(j) - 1);
        dt = R(k).v(9) - X.Tc_max_K(j);
        pass = abs(dq) <= 0.25 && abs(dt) <= 1.5;  ok = ok && pass;
        if pass, verdict = 'PASS'; else, verdict = 'FAIL'; end
        fprintf('%-11s %d: solar %+.3f %%, SF %+.3f points, max Tc %+.2f K  %s\n', R(k).arr, R(k).n, ...
                dq, 100 * (R(k).v(7) - X.solar_fraction(j)), dt, verdict);
    end
    if ok, disp('OVERALL PASS'); else, disp('OVERALL CHECK - see the lines above'); end
end
