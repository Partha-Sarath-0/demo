function P = grail_params()
% GRAIL_PARAMS  All inputs of the GRAIL system model (Stage 6) and annual/techno-economic
% analysis (Stage 7). SI units throughout; temperatures in kelvin.
% Runs unchanged in GNU Octave (>= 7) and MATLAB (>= R2016b).
%
% Collector efficiency correlations come from the GRAIL-CHT virtual test (Stage 6a) and are read
% from efficiency_correlations.json, so this model and the Python model use the same numbers.
% Every item tagged ENGINEERING_ASSUMPTION is an assumption, not a measured value.

here = fileparts(mfilename('fullpath'));
C = jsondecode(fileread(fullfile(here, 'efficiency_correlations.json')));
P.corr.alternating = [C.alternating.eta0, C.alternating.a1_W_m2K, C.alternating.a2_W_m2K2];
P.corr.parallel    = [C.parallel.eta0,    C.parallel.a1_W_m2K,    C.parallel.a2_W_m2K2];

P.weather_file = fullfile(here, 'tmy_19.313_84.810_2005_2023_Berhampur.csv');
P.lat = 19.313; P.lon = 84.810; P.elev = 19.0;        % PVGIS TMY point, Berhampur
P.tilt = 19.3; P.azim = 180.0; P.albedo = 0.20;       % ENGINEERING_ASSUMPTION: latitude tilt, due south
P.iam_b0 = 0.10; P.Kd = 0.90;                         % ENGINEERING_ASSUMPTION: IAM
P.cp = 4180.0;                                        % J/kg K, water
P.A_mod = 0.528;                                      % m2 aperture per module (dataset definition)
P.mdot_mod = 0.00275;                                 % kg/s per module, design flow
P.C_eff = 33500.0;                                    % J/m2 K, ENGINEERING_ASSUMPTION (PCM sensible only)
P.n_mod = 4;
P.tank_kg = 100.0; P.tank_UA = 1.5;                   % kg, W/K   ENGINEERING_ASSUMPTION
P.T_set = 318.15; P.draw_kg_day = 100.0;              % K, kg/day ENGINEERING_ASSUMPTION
P.prof = zeros(1, 24); P.prof([7 8 13 19 20]) = 0.20; % IST hours 6,7,12,18,19 (1-based index)
P.dT_on = 7.0; P.dT_off = 2.0; P.T_tank_max = 358.15; % K
P.pump_W = 15.0; P.geyser_eff = 0.95;
P.dt = 60.0;                                          % s, model time step

% economics - TPSODL LT domestic, 470 paise/kWh (FY 2025-26, retained FY 2026-27)
P.tariff = 4.70; P.tariff_high = 5.70;
P.capex = 30000.0; P.capex_fixed = 12000.0; P.capex_per_mod = 4500.0;   % Rs, ENGINEERING_ASSUMPTION
P.om = 0.01; P.life = 15; P.disc = 0.08;
end
