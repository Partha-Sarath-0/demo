function mdl = build_grail_simulink(p, mdl, Tc0, Tt0)
% BUILD_GRAIL_SIMULINK  Build the GRAIL SDHW system as a Simulink block diagram and save it.
%
%   mdl = build_grail_simulink(p)                 % model name 'GRAIL_system', saved as .slx
%   mdl = build_grail_simulink(p, 'name', Tc0, Tt0)
%
% p   : parameter struct from grail_sim_params.m (collector, tank, correlation coefficients)
% Tc0 : initial collector temperature (K), default 293.15;  Tt0 : initial tank temperature (K), 298.15
%
% The diagram is the same system as the Scilab Xcos model (14_Xcos_block_diagram_model):
%   inputs      From Workspace  Vg (G_eff W/m2), Va (T_amb K), Vm (T_mains K), Vd (draw kg/s);
%               each is a [time_s, value] matrix in the base workspace, held constant per hour
%   states      Integrator Tc (collector node) and Integrator Tt (tank)
%   pump        Fcn (Tc-Tt) -> Relay (on at 7 K, off at 2 K) -> Fcn (demand * (Tt <= Tmax))
%   equations   Fcn blocks; the expressions come from grail_sim_expressions.m
%   energies    6 heat rates -> Mux -> Integrator (6 states) -> To Workspace 'E' every 3600 s
%   log         [Tc; Tt] -> To Workspace 'T' every 60 s
% Solver: ode15s, RelTol 1e-6, AbsTol 1e-6, MaxStep 60 s, stop time 8760 h.
%
% Library blocks are found by their BlockType (find_system on the 'simulink' library), so the
% script does not depend on the library path names of a particular MATLAB release.

if nargin < 2 || isempty(mdl), mdl = 'GRAIL_system'; end
if nargin < 3 || isempty(Tc0), Tc0 = 293.15; end
if nargin < 4 || isempty(Tt0), Tt0 = 298.15; end
X = grail_sim_expressions(p);
num = @(v) sprintf('%.17g', v);

if bdIsLoaded(mdl), close_system(mdl, 0); end
new_system(mdl);
load_system('simulink');
L.fcn  = libpath('Fcn', 'Fcn');
L.int  = libpath('Integrator', 'Integrator');
L.rel  = libpath('Relay', 'Relay');
L.mux  = libpath('Mux', 'Mux');
L.from = libpath('FromWorkspace', 'From Workspace');
L.to   = libpath('ToWorkspace', 'To Workspace');

    function b = blk(lib, name, pos, varargin)
        b = [mdl '/' name];
        add_block(lib, b, 'Position', pos, varargin{:});
    end
    function mux(name, n, pos)
        blk(L.mux, name, pos, 'Inputs', num2str(n), 'DisplayOption', 'bar');
    end
    function fcn(name, expr, pos)
        blk(L.fcn, name, pos, 'Expr', expr);
    end
    function ln(src, dst)                       % 'Block/port' -> 'Block/port'
        add_line(mdl, src, dst, 'autorouting', 'on');
    end
    function r = at(x, y, w, h)                 % [left top right bottom]
        r = [x, y, x + w, y + h];
    end

% ---------------------------------------------------------------- inputs (column 1)
blk(L.from, 'G_eff (W per m2)',  at(20,  60, 110, 36), 'VariableName', 'Vg', 'Interpolate', 'off');
blk(L.from, 'T_amb (K)',         at(20, 160, 110, 36), 'VariableName', 'Va', 'Interpolate', 'off');
blk(L.from, 'T_mains (K)',       at(20, 260, 110, 36), 'VariableName', 'Vm', 'Interpolate', 'off');
blk(L.from, 'Draw (kg per s)',   at(20, 360, 110, 36), 'VariableName', 'Vd', 'Interpolate', 'off');

% ---------------------------------------------------------------- collector and tank states
mux('Mux dTc', 5, at(230,  40, 8, 130));
fcn('dTc/dt collector', X.dTc, at(290,  85, 200, 40));
blk(L.int, 'Tc collector (K)', at(540,  85, 60, 40), 'InitialCondition', num(Tc0), 'LimitOutput', 'off');

mux('Mux dTt', 6, at(230, 230, 8, 160));
fcn('dTt/dt tank', X.dTt, at(290, 290, 200, 40));
blk(L.int, 'Tt tank (K)', at(540, 290, 60, 40), 'InitialCondition', num(Tt0), 'LimitOutput', 'off');

% ---------------------------------------------------------------- pump control
mux('Mux pump dT', 2, at(660, 470, 8, 50));
fcn('Tc - Tt', X.dT, at(700, 475, 80, 40));
blk(L.rel, 'Pump hysteresis 7 K on, 2 K off', at(820, 475, 70, 40), ...
    'OnSwitchValue', '7', 'OffSwitchValue', '2', 'OnOutputValue', '1', 'OffOutputValue', '0');
mux('Mux pump enable', 2, at(930, 470, 8, 50));
fcn('Pump (off above Tmax)', X.pump, at(970, 475, 120, 40));

% ---------------------------------------------------------------- heat rates and energies
mux('Mux Q_coll', 3, at(1150,  40, 8, 60));   fcn('Q collector to tank (W)', X.Q_coll,  at(1190,  50, 170, 40));
mux('Mux Q_loss', 2, at(1150, 130, 8, 50));   fcn('Q tank loss (W)',         X.Q_loss,  at(1190, 135, 170, 40));
mux('Mux Q_draw', 3, at(1150, 210, 8, 60));   fcn('Q drawn from tank (W)',   X.Q_draw,  at(1190, 220, 170, 40));
mux('Mux Q_solar', 3, at(1150, 300, 8, 60));  fcn('Q solar delivered (W)',   X.Q_solar, at(1190, 310, 170, 40));
mux('Mux Q_load', 2, at(1150, 390, 8, 50));   fcn('Q hot-water load (W)',    X.Q_load,  at(1190, 395, 170, 40));
fcn('Pump running (1 or 0)', X.pump_on, at(1190, 470, 170, 40));

mux('Mux energies', 6, at(1420, 40, 8, 470));
blk(L.int, 'Energies (J, s)', at(1470, 255, 70, 40), 'InitialCondition', 'zeros(6,1)', 'LimitOutput', 'off');
blk(L.to, 'To Workspace E', at(1590, 255, 90, 40), 'VariableName', 'E', 'SaveFormat', 'Array', ...
    'SampleTime', '3600', 'MaxDataPoints', 'inf');

mux('Mux temperatures', 2, at(1420, 560, 8, 50));
blk(L.to, 'To Workspace T', at(1590, 565, 90, 40), 'VariableName', 'T', 'SaveFormat', 'Array', ...
    'SampleTime', '60', 'MaxDataPoints', 'inf');

% ---------------------------------------------------------------- wiring
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

% ---------------------------------------------------------------- solver settings
set_param(mdl, 'StopTime', num(8760 * 3600), 'Solver', 'ode15s', 'RelTol', '1e-6', ...
          'AbsTol', '1e-6', 'MaxStep', '60');
save_system(mdl, fullfile(fileparts(mfilename('fullpath')), [mdl '.slx']));
end

function p = libpath(blockType, name)
% Library path of the standard block with this BlockType and name (e.g. 'Integrator', 'Integrator').
% If a release renamed the block, the first block of that BlockType is used and a warning is shown.
hits = find_system('simulink', 'LookUnderMasks', 'all', 'FollowLinks', 'on', ...
                   'BlockType', blockType, 'Name', name);
if isempty(hits)
    hits = find_system('simulink', 'LookUnderMasks', 'all', 'FollowLinks', 'on', 'BlockType', blockType);
    if isempty(hits)
        error('No block of type %s found in the Simulink library.', blockType);
    end
    warning('Block "%s" not found by name; using %s', name, hits{1});
end
p = hits{1};
end
