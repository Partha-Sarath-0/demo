%% GRAIL_SIMULINK_COMPLETE  GRAIL solar water-heating system as a Simulink model - one file.
%
% HOW TO RUN (MATLAB or MATLAB Online, with Simulink):
%   1. Put this file and xcos_inputs.csv in the SAME folder (e.g. MATLAB Drive/GRAIL_Simulink).
%   2. In the Command Window:   cd GRAIL_Simulink
%                               GRAIL_simulink_complete
%   3. Look at the diagram:     open_system('GRAIL_system')
%
% What it does: builds the block diagram GRAIL_system.slx with add_block/add_line, simulates one
% year (Berhampur TMY) for alternating/parallel x 2/4 modules, writes simulink_results.csv and
% compares with the Scilab Xcos results (PASS if solar heat within 0.25 % and max Tc within 1.5 K).
%
% Model (SI units, kelvin):
%   collector  C dTc/dt   = A[eta0 G - a1 (Tc-Ta) - a2 (Tc-Ta)^2] - g2 (Tc-Tt) pump
%   tank       M cp dTt/dt = g2 (Tc-Tt) pump - UA (Tt-Ta) - m_t cp (Tt-Tmains)
%   valve      m_t = m_draw min(1, (Tset-Tmains)/(Tt-Tmains)); electric top-up to Tset
%   pump       relay on Tc-Tt: on at 7 K, off at 2 K; off while Tt > Tmax
% C = 33.5 kJ/m2K x A (PCM sensible only), g2 = 2 mdot cp, mdot = 0.00275 kg/s per module,
% tank 100 kg, UA 1.5 W/K, Tset 318.15 K, Tmax 358.15 K. eta0, a1, a2 = Stage 6 (GRAIL-CHT fit).
% Hourly inputs are held constant within each hour. Hot-water draw is a continuous flow during
% each draw hour (as in the Xcos model).

clear; clc;
here = fileparts(mfilename('fullpath'));
if isempty(here) || ~isfile(fullfile(here, 'xcos_inputs.csv')), here = pwd; end
if ~isfile(fullfile(here, 'xcos_inputs.csv'))
    error(['xcos_inputs.csv not found in %s. Put it in the same folder as this file, cd to ', ...
           'that folder, and run GRAIL_simulink_complete from the Command Window.'], here);
end

% ---- hourly inputs: hour, G_eff (W/m2), T_amb (K), T_mains (K), draw (kg/s) ------------------
D = readmatrix(fullfile(here, 'xcos_inputs.csv'));
t = [D(:, 1); D(end, 1) + 1] * 3600;             % add t = 8760 h so the last hour is held
D = [D; D(end, :)];
assignin('base', 'Vg', [t, D(:, 2)]); assignin('base', 'Va', [t, D(:, 3)]);
assignin('base', 'Vm', [t, D(:, 4)]); assignin('base', 'Vd', [t, D(:, 5)]);
Tc0 = D(1, 3); Tt0 = 298.15;                      % same initial values as Xcos / Octave

% ---- Xcos results (14_Xcos_block_diagram_model/xcos_results.csv) for the comparison ----------
%        arrangement    n  Q_solar_kWh  solar_fraction  Tc_max_K
XCOS = {'alternating', 2, 626.0240,  0.814231, 347.962;
        'parallel',    2, 648.4200,  0.843361, 352.030;
        'alternating', 4, 749.7092,  0.975099, 429.849;
        'parallel',    4, 754.0794,  0.980785, 443.822};

fid = fopen(fullfile(here, 'simulink_results.csv'), 'w');
fprintf(fid, ['arrangement,n_modules,Q_coll_kWh,Q_loss_kWh,Q_draw_kWh,Q_solar_kWh,Q_load_kWh,', ...
              'pump_h,solar_fraction,Tt_end_K,Tc_max_K,closure_kWh,run_s\n']);
allok = true;
for k = 1:size(XCOS, 1)
    p = grail_params(XCOS{k, 1}, XCOS{k, 2});
    mdl = build_model(p, 'GRAIL_system', Tc0, Tt0, here);
    tic; out = sim(mdl, 'ReturnWorkspaceOutputs', 'on'); rs = toc;
    E = out.get('E'); T = out.get('T');          % E: every 3600 s, T = [Tc Tt] every 60 s
    Ef = E(end, :);                              % yearly totals: 5 energies (J) + pump time (s)
    Tt_end = T(end, 2);
    closure = (Ef(1) - Ef(2) - Ef(3) - p.M * p.cp * (Tt_end - Tt0)) / 3.6e6;   % tank first law
    v = [Ef(1:5) / 3.6e6, Ef(6) / 3600, Ef(4) / Ef(5), Tt_end, max(T(:, 1)), closure, rs];
    fprintf(fid, '%s,%d,%.4f,%.4f,%.4f,%.4f,%.4f,%.2f,%.6f,%.4f,%.3f,%.3e,%.0f\n', XCOS{k, 1}, XCOS{k, 2}, v);
    dq = 100 * (v(4) / XCOS{k, 3} - 1);  dT = v(9) - XCOS{k, 5};
    ok = abs(dq) <= 0.25 && abs(dT) <= 1.5;  allok = allok && ok;
    if ok, verdict = 'PASS'; else, verdict = 'FAIL'; end
    fprintf(['%-11s %d modules: solar %.1f kWh, SF %.2f %%, max Tc %.1f K, closure %.1e kWh (%.0f s)', ...
             ' | vs Xcos: solar %+.3f %%, max Tc %+.2f K  %s\n'], XCOS{k, 1}, XCOS{k, 2}, v(4), ...
            100 * v(7), v(9), closure, rs, dq, dT, verdict);
end
fclose(fid);
if allok, disp('OVERALL PASS'); else, disp('OVERALL CHECK - see the lines above'); end
disp('Results: simulink_results.csv   Diagram: open_system(''GRAIL_system'')');


%% ============================== local functions ==============================================

function p = grail_params(arrangement, n_modules)
% Stage 6 coefficients (efficiency_correlations.json, full precision) and system data.
switch arrangement
    case 'alternating', p.e0 = 0.5965906020740813; p.a1 = 2.003882844904737; p.a2 = 0.00037944758755233723;
    case 'parallel',    p.e0 = 0.6367728001004268; p.a1 = 2.1040764409992594; p.a2 = 0.0;
    otherwise, error('arrangement must be ''alternating'' or ''parallel''');
end
p.cp   = 4180;                              % J/kgK
p.A    = n_modules * 0.528;                 % m2 aperture
p.C    = 33500 * p.A;                       % J/K collector node capacity
p.g2   = 2 * (n_modules * 0.00275) * p.cp;  % W/K
p.M    = 100;                               % kg tank
p.UA   = 1.5;                               % W/K
p.Tset = 318.15;                            % K
p.Tmax = 358.15;                            % K
end

function X = expressions(p)
% Fcn-block equations. Only operators and abs() are used (all accepted by the Fcn block);
% min(a,b) = (a+b-|a-b|)/2 and max(a,b) = (a+b+|a-b|)/2, fully bracketed.
n  = @(v) sprintf('%.17g', v);
mn = @(a, b) ['(((' a ')+(' b ')-abs((' a ')-(' b ')))/2)'];
mx = @(a, b) ['(((' a ')+(' b ')+abs((' a ')-(' b ')))/2)'];
frac = @(Tt, Tmn) mn('1', ['(' n(p.Tset) '-' Tmn ')/' mx([Tt '-' Tmn], '1e-9')]);
X.dT      = 'u(1)-u(2)';                                                     % [Tc; Tt]
X.pump    = ['u(1)*(u(2)<=' n(p.Tmax) ')'];                                  % [demand; Tt]
X.dTc = ['(' n(p.A) '*(' n(p.e0) '*u(1)-' n(p.a1) '*(u(3)-u(2))-' n(p.a2) ...
         '*(u(3)-u(2))*(u(3)-u(2)))-' n(p.g2) '*(u(3)-u(4))*u(5))/' n(p.C)];  % [G; Ta; Tc; Tt; pump]
X.dTt = ['(' n(p.g2) '*(u(1)-u(2))*u(3)-' n(p.UA) '*(u(2)-u(4))-u(6)*' frac('u(2)', 'u(5)') ...
         '*' n(p.cp) '*(u(2)-u(5)))/' n(p.M * p.cp)];                        % [Tc; Tt; pump; Ta; Tm; md]
X.Q_coll  = [n(p.g2) '*(u(1)-u(2))*u(3)'];                                   % [Tc; Tt; pump]
X.Q_loss  = [n(p.UA) '*(u(1)-u(2))'];                                        % [Tt; Ta]
X.Q_draw  = ['u(3)*' frac('u(1)', 'u(2)') '*' n(p.cp) '*(u(1)-u(2))'];       % [Tt; Tm; md]
X.Q_solar = mn(['u(3)*' frac('u(1)', 'u(2)') '*' n(p.cp) '*' mx('u(1)-u(2)', '0')], ...
               ['u(3)*' n(p.cp) '*(' n(p.Tset) '-u(2))']);                    % [Tt; Tm; md]
X.Q_load  = ['u(2)*' n(p.cp) '*(' n(p.Tset) '-u(1))'];                       % [Tm; md]
X.pump_on = 'u(1)';                                                          % pump
end

function mdl = build_model(p, mdl, Tc0, Tt0, folder)
% Build GRAIL_system with add_block / add_line and save it as GRAIL_system.slx in folder.
X = expressions(p);
num = @(v) sprintf('%.17g', v);
at  = @(x, y, w, h) [x, y, x + w, y + h];            % block position [left top right bottom]
if bdIsLoaded(mdl), close_system(mdl, 0); end
new_system(mdl);
load_system('simulink');
L.fcn  = libpath('Fcn', 'Fcn');
L.int  = libpath('Integrator', 'Integrator');
L.rel  = libpath('Relay', 'Relay');
L.mux  = libpath('Mux', 'Mux');
L.from = libpath('FromWorkspace', 'From Workspace');
L.to   = libpath('ToWorkspace', 'To Workspace');
B = @(name) [mdl '/' name];
ln = @(src, dst) add_line(mdl, src, dst, 'autorouting', 'on');
mux = @(name, k, pos) add_block(L.mux, B(name), 'Position', pos, 'Inputs', num2str(k), 'DisplayOption', 'bar');
fcn = @(name, e, pos) add_block(L.fcn, B(name), 'Position', pos, 'Expr', e);

% inputs: [time value] matrices Vg, Va, Vm, Vd in the base workspace, held within each hour
add_block(L.from, B('G_eff (W per m2)'), 'Position', at(20,  60, 110, 36), 'VariableName', 'Vg', 'Interpolate', 'off');
add_block(L.from, B('T_amb (K)'),        'Position', at(20, 160, 110, 36), 'VariableName', 'Va', 'Interpolate', 'off');
add_block(L.from, B('T_mains (K)'),      'Position', at(20, 260, 110, 36), 'VariableName', 'Vm', 'Interpolate', 'off');
add_block(L.from, B('Draw (kg per s)'),  'Position', at(20, 360, 110, 36), 'VariableName', 'Vd', 'Interpolate', 'off');

% collector and tank states
mux('Mux dTc', 5, at(230, 40, 8, 130));
fcn('dTc/dt collector', X.dTc, at(290, 85, 200, 40));
add_block(L.int, B('Tc collector (K)'), 'Position', at(540, 85, 60, 40), 'InitialCondition', num(Tc0), 'LimitOutput', 'off');
mux('Mux dTt', 6, at(230, 230, 8, 160));
fcn('dTt/dt tank', X.dTt, at(290, 290, 200, 40));
add_block(L.int, B('Tt tank (K)'), 'Position', at(540, 290, 60, 40), 'InitialCondition', num(Tt0), 'LimitOutput', 'off');

% pump control
mux('Mux pump dT', 2, at(660, 470, 8, 50));
fcn('Tc - Tt', X.dT, at(700, 475, 80, 40));
add_block(L.rel, B('Pump hysteresis 7 K on, 2 K off'), 'Position', at(820, 475, 70, 40), ...
    'OnSwitchValue', '7', 'OffSwitchValue', '2', 'OnOutputValue', '1', 'OffOutputValue', '0');
mux('Mux pump enable', 2, at(930, 470, 8, 50));
fcn('Pump (off above Tmax)', X.pump, at(970, 475, 120, 40));

% heat rates -> yearly energies
mux('Mux Q_coll', 3, at(1150,  40, 8, 60));  fcn('Q collector to tank (W)', X.Q_coll,  at(1190,  50, 170, 40));
mux('Mux Q_loss', 2, at(1150, 130, 8, 50));  fcn('Q tank loss (W)',         X.Q_loss,  at(1190, 135, 170, 40));
mux('Mux Q_draw', 3, at(1150, 210, 8, 60));  fcn('Q drawn from tank (W)',   X.Q_draw,  at(1190, 220, 170, 40));
mux('Mux Q_solar', 3, at(1150, 300, 8, 60)); fcn('Q solar delivered (W)',   X.Q_solar, at(1190, 310, 170, 40));
mux('Mux Q_load', 2, at(1150, 390, 8, 50));  fcn('Q hot-water load (W)',    X.Q_load,  at(1190, 395, 170, 40));
fcn('Pump running (1 or 0)', X.pump_on, at(1190, 470, 170, 40));
mux('Mux energies', 6, at(1420, 40, 8, 470));
add_block(L.int, B('Energies (J, s)'), 'Position', at(1470, 255, 70, 40), 'InitialCondition', 'zeros(6,1)', 'LimitOutput', 'off');
add_block(L.to, B('To Workspace E'), 'Position', at(1590, 255, 90, 40), 'VariableName', 'E', ...
    'SaveFormat', 'Array', 'SampleTime', '3600', 'MaxDataPoints', 'inf');
mux('Mux temperatures', 2, at(1420, 560, 8, 50));
add_block(L.to, B('To Workspace T'), 'Position', at(1590, 565, 90, 40), 'VariableName', 'T', ...
    'SaveFormat', 'Array', 'SampleTime', '60', 'MaxDataPoints', 'inf');

% wiring
G = 'G_eff (W per m2)/1'; Ta = 'T_amb (K)/1'; Tm = 'T_mains (K)/1'; Md = 'Draw (kg per s)/1';
Tc = 'Tc collector (K)/1'; Tt = 'Tt tank (K)/1'; Pu = 'Pump (off above Tmax)/1';
ln(G, 'Mux dTc/1'); ln(Ta, 'Mux dTc/2'); ln(Tc, 'Mux dTc/3'); ln(Tt, 'Mux dTc/4'); ln(Pu, 'Mux dTc/5');
ln('Mux dTc/1', 'dTc/dt collector/1'); ln('dTc/dt collector/1', 'Tc collector (K)/1');
ln(Tc, 'Mux dTt/1'); ln(Tt, 'Mux dTt/2'); ln(Pu, 'Mux dTt/3'); ln(Ta, 'Mux dTt/4'); ln(Tm, 'Mux dTt/5'); ln(Md, 'Mux dTt/6');
ln('Mux dTt/1', 'dTt/dt tank/1'); ln('dTt/dt tank/1', 'Tt tank (K)/1');
ln(Tc, 'Mux pump dT/1'); ln(Tt, 'Mux pump dT/2'); ln('Mux pump dT/1', 'Tc - Tt/1');
ln('Tc - Tt/1', 'Pump hysteresis 7 K on, 2 K off/1');
ln('Pump hysteresis 7 K on, 2 K off/1', 'Mux pump enable/1'); ln(Tt, 'Mux pump enable/2');
ln('Mux pump enable/1', 'Pump (off above Tmax)/1');
ln(Tc, 'Mux Q_coll/1'); ln(Tt, 'Mux Q_coll/2'); ln(Pu, 'Mux Q_coll/3'); ln('Mux Q_coll/1', 'Q collector to tank (W)/1');
ln(Tt, 'Mux Q_loss/1'); ln(Ta, 'Mux Q_loss/2'); ln('Mux Q_loss/1', 'Q tank loss (W)/1');
ln(Tt, 'Mux Q_draw/1'); ln(Tm, 'Mux Q_draw/2'); ln(Md, 'Mux Q_draw/3'); ln('Mux Q_draw/1', 'Q drawn from tank (W)/1');
ln(Tt, 'Mux Q_solar/1'); ln(Tm, 'Mux Q_solar/2'); ln(Md, 'Mux Q_solar/3'); ln('Mux Q_solar/1', 'Q solar delivered (W)/1');
ln(Tm, 'Mux Q_load/1'); ln(Md, 'Mux Q_load/2'); ln('Mux Q_load/1', 'Q hot-water load (W)/1');
ln(Pu, 'Pump running (1 or 0)/1');
rates = {'Q collector to tank (W)', 'Q tank loss (W)', 'Q drawn from tank (W)', ...
         'Q solar delivered (W)', 'Q hot-water load (W)', 'Pump running (1 or 0)'};
for k = 1:6, ln([rates{k} '/1'], sprintf('Mux energies/%d', k)); end
ln('Mux energies/1', 'Energies (J, s)/1'); ln('Energies (J, s)/1', 'To Workspace E/1');
ln(Tc, 'Mux temperatures/1'); ln(Tt, 'Mux temperatures/2'); ln('Mux temperatures/1', 'To Workspace T/1');

% solver
set_param(mdl, 'StopTime', num(8760 * 3600), 'Solver', 'ode15s', 'RelTol', '1e-6', ...
          'AbsTol', '1e-6', 'MaxStep', '60');
save_system(mdl, fullfile(folder, [mdl '.slx']));
end

function lib = libpath(blockType, name)
% Library path of a standard Simulink block, found by BlockType and name.
hits = find_system('simulink', 'LookUnderMasks', 'all', 'FollowLinks', 'on', ...
                   'BlockType', blockType, 'Name', name);
if isempty(hits)
    hits = find_system('simulink', 'LookUnderMasks', 'all', 'FollowLinks', 'on', 'BlockType', blockType);
    if isempty(hits), error('No block of type %s in the Simulink library.', blockType); end
    warning('Block "%s" not found by name; using %s', name, hits{1});
end
lib = hits{1};
end
