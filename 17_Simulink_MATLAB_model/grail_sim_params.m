function p = grail_sim_params(arrangement, n_modules, json_file)
% GRAIL_SIM_PARAMS  Parameters of the GRAIL SDHW system model (SI units, kelvin).
%   p = grail_sim_params('parallel', 2)            % reads efficiency_correlations.json here
% The numbers are the same as in the Python, Octave and Xcos models (Stage 6/7):
%   aperture 0.528 m2 per module, C_eff 33.5 kJ/m2K (PCM sensible heat only), 0.00275 kg/s per module,
%   tank 100 kg with UA 1.5 W/K, delivery at 318.15 K, tank limit 358.15 K.
here = fileparts(mfilename('fullpath'));
if nargin < 3, json_file = fullfile(here, 'efficiency_correlations.json'); end
J = jsondecode(fileread(json_file));
c = J.(arrangement);
p.arrangement = arrangement;
p.n_modules = n_modules;
p.cp   = 4180;                              % J/kgK
p.A    = n_modules * 0.528;                 % m2 aperture
p.C    = 33500 * p.A;                       % J/K collector node capacity
p.g2   = 2 * (n_modules * 0.00275) * p.cp;  % W/K, as in the Stage 7 / Octave / Xcos models
p.e0   = c.eta0;                            % -
p.a1   = c.a1_W_m2K;                        % W/m2K
p.a2   = c.a2_W_m2K2;                       % W/m2K2
p.M    = 100;                               % kg tank
p.UA   = 1.5;                               % W/K tank loss
p.Tset = 318.15;                            % K delivery temperature
p.Tmax = 358.15;                            % K tank limit (pump off above)
end
