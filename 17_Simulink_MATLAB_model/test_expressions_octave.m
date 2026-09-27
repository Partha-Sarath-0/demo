function r = test_expressions_octave(arrangement, n_modules, dt, n_hours)
% TEST_EXPRESSIONS_OCTAVE  Check the Simulink Fcn-block equations without Simulink.
%   r = test_expressions_octave('parallel', 2)          % GNU Octave or MATLAB
% Evaluates the EXACT expression strings of grail_sim_expressions.m (the strings that
% build_grail_simulink.m writes into the Fcn blocks) with a fixed-step integration, using the
% same hourly inputs (held for each hour), the same Relay rule (on when Tc-Tt >= 7 K, off when
% <= 2 K) and the same initial values. Result is compared with xcos_results.csv.
% This tests the equations; it does not test the Simulink API calls (that needs MATLAB).
if nargin < 3 || isempty(dt), dt = 10; end
here = fileparts(mfilename('fullpath'));
D = dlmread(fullfile(here, 'xcos_inputs.csv'), ',', 1, 0);
if nargin < 4 || isempty(n_hours), n_hours = size(D, 1); end
p = grail_sim_params(arrangement, n_modules);
X = grail_sim_expressions(p);
f = structfun(@(e) str2func(['@(u) ' e]), X, 'UniformOutput', false);
Tc = D(1, 3); Tt = 298.15; Tt0 = Tt; demand = 0; Q = zeros(1, 6); Tcmax = Tc;
ns = round(3600 / dt);
for h = 1:n_hours
    G = D(h, 2); Ta = D(h, 3); Tm = D(h, 4); md = D(h, 5);
    for s = 1:ns
        d = f.dT([Tc; Tt]);
        if demand == 0 && d >= 7, demand = 1; elseif demand == 1 && d <= 2, demand = 0; end
        pu = f.pump([demand; Tt]);
        q = [f.Q_coll([Tc; Tt; pu]), f.Q_loss([Tt; Ta]), f.Q_draw([Tt; Tm; md]), ...
             f.Q_solar([Tt; Tm; md]), f.Q_load([Tm; md]), f.pump_on(pu)];
        dTc = f.dTc([G; Ta; Tc; Tt; pu]);
        dTt = f.dTt([Tc; Tt; pu; Ta; Tm; md]);
        Q = Q + q * dt; Tc = Tc + dt * dTc; Tt = Tt + dt * dTt;
        if Tc > Tcmax, Tcmax = Tc; end
    end
end
closure = (Q(1) - Q(2) - Q(3) - p.M * p.cp * (Tt - Tt0)) / 3.6e6;
r = struct('arrangement', arrangement, 'n_modules', n_modules, 'Q_solar_kWh', Q(4) / 3.6e6, ...
           'Q_load_kWh', Q(5) / 3.6e6, 'solar_fraction', Q(4) / Q(5), 'Tc_max_K', Tcmax, ...
           'closure_kWh', closure, 'Tt_end_K', Tt);
fprintf('%s,%d,%.4f,%.4f,%.6f,%.3f,%.3e,%d\n', arrangement, n_modules, r.Q_solar_kWh, r.Q_load_kWh, ...
        r.solar_fraction, r.Tc_max_K, closure, dt);
end
