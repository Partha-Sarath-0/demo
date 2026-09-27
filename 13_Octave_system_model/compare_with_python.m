% COMPARE_WITH_PYTHON  Checks the Octave/MATLAB model against the Python Stage 7 results.
% Reads sizing_sweep.csv and stage7_results.json from the Python Stage 7 folder (see py_dir) and the
% octave_*.csv files written by run_grail_annual.m. PASS if every quantity agrees within tolerance.
% Tolerance note: max_collector_K was first checked at 0.1 K and differed by 0.17 K. The cause is the
% solar-position algorithm (NOAA here, NREL SPA in Python): hourly irradiance differs by at most
% 0.17 W/m2 (0.01 kWh/m2/yr). A single-hour stagnation peak inherits that, so 0.5 K is used.
clear; clc;
% Python results folder: ../20_annual in the working tree, ../12_Stages_3-5-6-7/annual in the delivered package.
cand = {fullfile('..', '20_annual'), fullfile('..', '12_Stages_3-5-6-7', 'annual')};
py_dir = '';
for k = 1:numel(cand)
    if exist(fullfile(cand{k}, 'stage7_results.json'), 'file'), py_dir = cand{k}; break; end
end
if isempty(py_dir), error('Python Stage 7 results not found in ../20_annual or ../12_Stages_3-5-6-7/annual'); end
fprintf('Python results read from %s\n', py_dir);
R = jsondecode(fileread(fullfile(py_dir, 'stage7_results.json')));
fid = fopen(fullfile(py_dir, 'sizing_sweep.csv')); hdr = strsplit(fgetl(fid), ','); py = textscan(fid, repmat('%s', 1, numel(hdr)), 'Delimiter', ','); fclose(fid);
fid = fopen('octave_results.csv'); hdo = strsplit(fgetl(fid), ','); oc = textscan(fid, repmat('%s', 1, numel(hdo)), 'Delimiter', ','); fclose(fid);
col = @(T, H, name) str2double(T{strcmp(H, name)});
checks = {'solar_fraction', 'solar_fraction', 1e-3; 'Q_solar_kWh', 'Q_solar_kWh', 0.5; ...
          'max_collector_K', 'max_collector_K', 0.5; 'simple_payback_yr', 'simple_payback_yr', 0.01; ...
          'LCOH_Rs_kWh', 'LCOH_Rs_kWh', 0.005; 'NPV_Rs', 'NPV_Rs', 5};
ok = true;
fprintf('%-20s %12s %12s %12s  %s\n', 'quantity', 'max |diff|', 'tolerance', 'python mean', 'result');
for k = 1:size(checks, 1)
    a = col(py, hdr, checks{k, 1}); b = col(oc, hdo, checks{k, 2});
    d = max(abs(a - b)); pass = d <= checks{k, 3}; ok = ok && pass;
    fprintf('%-20s %12.3g %12.3g %12.4g  %s\n', checks{k, 1}, d, checks{k, 3}, mean(a), pass_str(pass));
end
fid = fopen('octave_collector_only.csv'); fgetl(fid); co = textscan(fid, '%s %f %f %f %f', 'Delimiter', ','); fclose(fid);
pyv = [R.alternating.collector_only_Tin_313_K.kWh_m2_yr, R.alternating.collector_only_Tin_333_K.kWh_m2_yr, ...
       R.parallel.collector_only_Tin_313_K.kWh_m2_yr, R.parallel.collector_only_Tin_333_K.kWh_m2_yr];
d = max(abs(pyv(:) - co{3})); pass = d <= 0.5; ok = ok && pass;
fprintf('%-20s %12.3g %12.3g %12.4g  %s\n', 'collector_only', d, 0.5, mean(pyv), pass_str(pass));
if ok, fprintf('\nOVERALL: PASS - Octave/MATLAB model reproduces the Python model\n');
else,  fprintf('\nOVERALL: FAIL\n'); end

