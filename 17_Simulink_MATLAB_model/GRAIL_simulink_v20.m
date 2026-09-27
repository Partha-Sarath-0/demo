%% GRAIL_SIMULINK_V20  GRAIL solar water-heating system as a clean, colour-coded Simulink model.
%
% Same equations and numbers as GRAIL_simulink_complete.m (verified PASS vs Xcos). Only the
% diagram layout changed: 6 coloured sections, Goto/From tags instead of crossing wires, and the
% equations printed next to each block. Q_load = m_draw cp (Tset - Tmains)  (mains, not ambient).
%
% HOW TO RUN (MATLAB or MATLAB Online, with Simulink):
%   1. Put this file and xcos_inputs.csv in the SAME folder (e.g. MATLAB Drive/GRAIL_Simulink).
%   2. In the Command Window:   cd GRAIL_Simulink
%                               GRAIL_simulink_v20
%   3. The diagram opens at the end (parallel, 2 modules = the chosen design).
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
           'that folder, and run GRAIL_simulink_v20 from the Command Window.'], here);
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
disp('Results: simulink_results.csv');
p = grail_params('parallel', 2);                 % leave the chosen design open on screen
build_model(p, 'GRAIL_system', Tc0, Tt0, here);
open_system('GRAIL_system');


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
% Build GRAIL_system (6 colour-coded sections, Goto/From signal tags) and save it as .slx.
X   = expressions(p);
num = @(v) sprintf('%.17g', v);
at  = @(x, y, w, h) [x, y, x + w, y + h];
if bdIsLoaded(mdl), close_system(mdl, 0); end
new_system(mdl);
load_system('simulink');
L.fcn  = libpath('Fcn', 'Fcn');             L.int  = libpath('Integrator', 'Integrator');
L.rel  = libpath('Relay', 'Relay');         L.mux  = libpath('Mux', 'Mux');
L.from = libpath('FromWorkspace', 'From Workspace');
L.to   = libpath('ToWorkspace', 'To Workspace');
L.gto  = libpath('Goto', 'Goto');           L.gfr  = libpath('From', 'From');
B = @(name) [mdl '/' name];

% ---- colours: one per section; every signal tag takes the colour of the section that makes it
C.inp  = '[0.80 0.90 1.00]';   % 1 inputs        light blue
C.col  = '[1.00 0.85 0.60]';   % 2 collector     orange
C.tank = '[0.78 0.94 0.78]';   % 3 tank          green
C.pump = '[0.90 0.82 1.00]';   % 4 pump          lilac
C.rate = '[1.00 0.97 0.72]';   % 5 heat rates    pale yellow
C.out  = '[0.88 0.88 0.88]';   % 6 outputs       grey
tagC = struct('G', C.inp, 'Ta', C.inp, 'Tm', C.inp, 'Md', C.inp, 'Tc', C.col, 'Tt', C.tank, 'P', C.pump);

S = struct('mdl', mdl, 'L', L, 'tagC', tagC);

% ---- section backgrounds (drawn first so they sit behind the blocks) --------------------------
sec_area(S, '1  INPUTS (hourly)',          at(  20,  80, 300, 400), C.inp);
sec_area(S, '2  COLLECTOR',                at( 360,  80, 640, 230), C.col);
sec_area(S, '3  STORAGE TANK',             at( 360, 340, 640, 260), C.tank);
sec_area(S, '4  PUMP CONTROL',             at(  20, 640, 980, 170), C.pump);
sec_area(S, '5  HEAT RATES (W)',           at(1040,  80, 560, 730), C.rate);
sec_area(S, '6  YEARLY TOTALS & OUTPUTS',  at(1640,  80, 360, 730), C.out);
note(S, sprintf('GRAIL SOLAR WATER HEATER  |  %g m2 (%d modules)  |  eta0 %.4f  a1 %.3f  a2 %.4f', ...
     p.A, round(p.A / 0.528), p.e0, p.a1, p.a2), 20, 20, 16, true);
note(S, 'Colour = section. Tag colour = section that produces the signal. Layout only: numbers are unchanged.', 20, 50, 10, false);

% ---- 1 INPUTS ----------------------------------------------------------------------------------
ins = {'G_eff (W per m2)', 'Vg', 'G'; 'T_amb (K)', 'Va', 'Ta'; 'T_mains (K)', 'Vm', 'Tm'; 'Draw (kg per s)', 'Vd', 'Md'};
for i = 1:4
    y = 120 + 90 * (i - 1);
    blk(S, L.from, ins{i, 1}, at(40, y, 150, 40), C.inp, 'VariableName', ins{i, 2}, 'Interpolate', 'off');
    gto(S, ins{i, 3}, at(230, y + 10, 60, 20));
    ln(S, [ins{i, 1} '/1'], ['Goto ' ins{i, 3} '/1']);
end

% ---- 2 COLLECTOR: C dTc/dt = A[eta0 G - a1(Tc-Ta) - a2(Tc-Ta)^2] - g2(Tc-Tt)P -----------------
row(S, 'dTc', {'G', 'Ta', 'Tc', 'Tt', 'P'}, 'dTc_dt collector', X.dTc, 380, 110, C.col);
blk(S, L.int, 'Tc collector (K)', at(720, 165, 70, 40), C.col, 'InitialCondition', num(Tc0));
ln(S, 'dTc_dt collector/1', 'Tc collector (K)/1');
gto(S, 'Tc', at(830, 175, 60, 20)); ln(S, 'Tc collector (K)/1', 'Goto Tc/1');
note(S, sprintf('C dTc/dt = A[eta0 G - a1(Tc-Ta) - a2(Tc-Ta)^2] - g2(Tc-Tt)P\nA = %g m2   C = %g J/K   g2 = %g W/K', ...
     p.A, p.C, p.g2), 380, 270, 10, false);

% ---- 3 TANK: M cp dTt/dt = g2(Tc-Tt)P - UA(Tt-Ta) - m_t cp (Tt-Tmains) -------------------------
row(S, 'dTt', {'Tc', 'Tt', 'P', 'Ta', 'Tm', 'Md'}, 'dTt_dt tank', X.dTt, 380, 360, C.tank);
blk(S, L.int, 'Tt tank (K)', at(720, 430, 70, 40), C.tank, 'InitialCondition', num(Tt0));
ln(S, 'dTt_dt tank/1', 'Tt tank (K)/1');
gto(S, 'Tt', at(830, 440, 60, 20)); ln(S, 'Tt tank (K)/1', 'Goto Tt/1');
note(S, sprintf(['M cp dTt/dt = g2(Tc-Tt)P - UA(Tt-Ta) - m_t cp(Tt-Tmains)\n', ...
     'm_t = m_draw min(1, (Tset-Tmains)/(Tt-Tmains))   M = %g kg   UA = %g W/K   Tset = %g K'], ...
     p.M, p.UA, p.Tset), 380, 560, 10, false);

% ---- 4 PUMP: relay on Tc-Tt (on 7 K, off 2 K); forced off while Tt > Tmax ----------------------
row(S, 'dT', {'Tc', 'Tt'}, 'Tc - Tt', X.dT, 40, 680, C.pump);
blk(S, L.rel, 'Relay 7 K on, 2 K off', at(400, 680, 90, 40), C.pump, ...
    'OnSwitchValue', '7', 'OffSwitchValue', '2', 'OnOutputValue', '1', 'OffOutputValue', '0');
ln(S, 'Tc - Tt/1', 'Relay 7 K on, 2 K off/1');
blk(S, L.mux, 'Mux pump', at(530, 680, 6, 60), '[0 0 0]', 'Inputs', '2', 'DisplayOption', 'bar', 'ShowName', 'off');
ln(S, 'Relay 7 K on, 2 K off/1', 'Mux pump/1');
gfr(S, 'pump in Tt', 'Tt', at(460, 740, 40, 20)); ln(S, 'pump in Tt/1', 'Mux pump/2');
blk(S, L.fcn, 'Pump (off if Tt > Tmax)', at(570, 690, 170, 40), C.pump, 'Expr', X.pump);
ln(S, 'Mux pump/1', 'Pump (off if Tt > Tmax)/1');
gto(S, 'P', at(780, 700, 60, 20)); ln(S, 'Pump (off if Tt > Tmax)/1', 'Goto P/1');
note(S, sprintf('P = 1 when Tc - Tt rises above 7 K, 0 when it falls below 2 K;  P = 0 while Tt > Tmax = %g K', p.Tmax), ...
     40, 780, 10, false);

% ---- 5 HEAT RATES -> 6 YEARLY TOTALS -----------------------------------------------------------
R = {'Qc', {'Tc', 'Tt', 'P'},  'Q_coll = g2(Tc-Tt)P',            X.Q_coll;
     'Ql', {'Tt', 'Ta'},       'Q_loss = UA(Tt-Ta)',             X.Q_loss;
     'Qd', {'Tt', 'Tm', 'Md'}, 'Q_draw = m_t cp(Tt-Tmains)',     X.Q_draw;
     'Qs', {'Tt', 'Tm', 'Md'}, 'Q_solar = min(Q_draw, m cp(Tset-Tmains))', X.Q_solar;
     'Qh', {'Tm', 'Md'},       'Q_load = m cp(Tset-Tmains)',     X.Q_load;
     'Pr', {'P'},              'Pump running (1 or 0)',             X.pump_on};
blk(S, L.mux, 'Mux totals', at(1680, 120, 6, 640), '[0 0 0]', 'Inputs', '6', 'DisplayOption', 'bar', 'ShowName', 'off');
for i = 1:6
    y = 110 + 115 * (i - 1);
    row(S, R{i, 1}, R{i, 2}, R{i, 3}, R{i, 4}, 1060, y, C.rate);
    ln(S, [R{i, 3} '/1'], sprintf('Mux totals/%d', i));
end
blk(S, L.int, 'Yearly totals (J, s)', at(1730, 420, 90, 40), C.out, 'InitialCondition', 'zeros(6,1)');
ln(S, 'Mux totals/1', 'Yearly totals (J, s)/1');
blk(S, L.to, 'E to workspace', at(1860, 420, 110, 40), C.out, 'VariableName', 'E', ...
    'SaveFormat', 'Array', 'SampleTime', '3600', 'MaxDataPoints', 'inf');
ln(S, 'Yearly totals (J, s)/1', 'E to workspace/1');
note(S, sprintf('E = [Q_coll Q_loss Q_draw Q_solar Q_load pump_s]\n(J, s; hourly)'), 1720, 480, 10, false);
blk(S, L.mux, 'Mux T', at(1760, 620, 6, 60), '[0 0 0]', 'Inputs', '2', 'DisplayOption', 'bar', 'ShowName', 'off');
gfr(S, 'out Tc', 'Tc', at(1700, 625, 40, 20)); ln(S, 'out Tc/1', 'Mux T/1');
gfr(S, 'out Tt', 'Tt', at(1700, 655, 40, 20)); ln(S, 'out Tt/1', 'Mux T/2');
blk(S, L.to, 'T to workspace', at(1860, 630, 110, 40), C.out, 'VariableName', 'T', ...
    'SaveFormat', 'Array', 'SampleTime', '60', 'MaxDataPoints', 'inf');
ln(S, 'Mux T/1', 'T to workspace/1');
note(S, 'T = [Tc Tt] (K, every 60 s)', 1720, 690, 10, false);

% ---- solver ------------------------------------------------------------------------------------
set_param(mdl, 'StopTime', num(8760 * 3600), 'Solver', 'ode15s', 'RelTol', '1e-6', ...
          'AbsTol', '1e-6', 'MaxStep', '60');
save_system(mdl, fullfile(folder, [mdl '.slx']));
end

function blk(S, lib, name, pos, col, varargin)
add_block(lib, [S.mdl '/' name], 'Position', pos, 'BackgroundColor', col, varargin{:});
end

function gto(S, tag, pos)
blk(S, S.L.gto, ['Goto ' tag], pos, S.tagC.(tag), 'GotoTag', tag, 'ShowName', 'off');
end

function gfr(S, name, tag, pos)
blk(S, S.L.gfr, name, pos, S.tagC.(tag), 'GotoTag', tag, 'ShowName', 'off');
end

function ln(S, src, dst)
add_line(S.mdl, src, dst, 'autorouting', 'on');
end

function row(S, prefix, tags, fcnName, expr, x, y, col)
% From tags -> Mux -> Fcn, left to right, 30 px per input
k = numel(tags); h = 30 * k;
mname = ['Mux ' prefix];
blk(S, S.L.mux, mname, [x + 70, y, x + 76, y + h], '[0 0 0]', 'Inputs', num2str(k), ...
    'DisplayOption', 'bar', 'ShowName', 'off');
for i = 1:k
    f = sprintf('%s in %d', prefix, i);
    yy = y + 30 * (i - 1) + 5;
    gfr(S, f, tags{i}, [x, yy, x + 40, yy + 20]);
    ln(S, [f '/1'], sprintf('%s/%d', mname, i));
end
blk(S, S.L.fcn, fcnName, [x + 110, y + h / 2 - 20, x + 300, y + h / 2 + 20], col, 'Expr', expr);
ln(S, [mname '/1'], [fcnName '/1']);
end

function note(S, txt, x, y, sz, bold)
% Text label. Layout only; skipped silently if this release's annotation API differs.
try
    a = Simulink.Annotation(S.mdl, txt);
    try, a.Position = [x, y, x + 600, y + 20 * (1 + count(txt, newline))];
    catch, a.Position = [x, y]; end
    a.FontSize = sz;
    if bold, a.FontWeight = 'bold'; end
catch
end
end

function sec_area(S, title, pos, col)
% Coloured section background. Layout only; skipped silently if not supported.
try
    add_block('built-in/Area', [S.mdl '/' title], 'Position', pos, 'BackgroundColor', col);
catch
end
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
