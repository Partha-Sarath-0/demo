function W = grail_weather(P)
% GRAIL_WEATHER  Read the PVGIS TMY file (unchanged) and build hourly plane-of-array irradiance.
%   Solar position: NOAA / Meeus algorithm with standard refraction, evaluated at the stated UTC
%   timestamp (the GHI closure test in Stage 7 showed this is the correct alignment).
%   Transposition: Hay-Davies, extraterrestrial DNI by the Spencer formula.
% Output struct W (8760 x 1 vectors): GHI DNI DHI G_T G_beam G_diff aoi T_amb hour_ist month doy

fid = fopen(P.weather_file, 'r'); txt = textscan(fid, '%s', 'Delimiter', '\n'); fclose(fid);
L = txt{1};
i0 = find(strncmp(L, 'time(UTC)', 9), 1);
n = 0; D = zeros(8760, 10); key = zeros(8760, 1);
for k = i0+1:numel(L)
    s = L{k};
    if numel(s) < 14 || ~all(isstrprop(s(1:8), 'digit')) || s(9) ~= ':'
        continue
    end
    parts = strsplit(s, ',');
    n = n + 1;
    mo = str2double(s(5:6)); dy = str2double(s(7:8)); hr = str2double(s(10:11));
    D(n, :) = [mo, dy, hr, str2double(parts(2:8))];   % T2m RH G(h) Gb(n) Gd(h) IR(h) WS10m
    key(n) = mo * 1e4 + dy * 1e2 + hr;
end
assert(n == 8760, 'expected 8760 hourly rows');
[~, o] = sort(key); D = D(o, :);                      % canonical non-leap year order

mo = D(:, 1); dy = D(:, 2); hr = D(:, 3);
cum = [0 31 59 90 120 151 181 212 243 273 304 334];
doy = cum(mo)' + dy;                                    % 2019 (non-leap) day of year
% ---- NOAA solar position at UTC hh:00 ----
jd = 2458484.5 + (doy - 1) + hr / 24;                   % JD of 2019-01-01 00:00 UTC = 2458484.5
T = (jd - 2451545.0) / 36525;
L0 = mod(280.46646 + T .* (36000.76983 + T * 0.0003032), 360);
M = 357.52911 + T .* (35999.05029 - 0.0001537 * T);
e = 0.016708634 - T .* (0.000042037 + 0.0000001267 * T);
Cc = sind(M) .* (1.914602 - T .* (0.004817 + 0.000014 * T)) + sind(2 * M) .* (0.019993 - 0.000101 * T) + sind(3 * M) * 0.000289;
lam = L0 + Cc - 0.00569 - 0.00478 * sind(125.04 - 1934.136 * T);
eps0 = 23 + (26 + (21.448 - T .* (46.815 + T .* (0.00059 - T * 0.001813))) / 60) / 60;
epsc = eps0 + 0.00256 * cosd(125.04 - 1934.136 * T);
decl = asind(sind(epsc) .* sind(lam));
y = tand(epsc / 2) .^ 2;
eot = 4 * (180 / pi) * (y .* sind(2 * L0) - 2 * e .* sind(M) + 4 * e .* y .* sind(M) .* cosd(2 * L0) ...
      - 0.5 * y .^ 2 .* sind(4 * L0) - 1.25 * e .^ 2 .* sind(2 * M));        % minutes
tst = mod(hr * 60 + eot + 4 * P.lon, 1440);
ha = tst / 4 - 180;
cz = sind(P.lat) * sind(decl) + cosd(P.lat) * cosd(decl) .* cosd(ha);
zen = acosd(max(min(cz, 1), -1));
elev = 90 - zen;
R = zeros(size(elev));                                    % NOAA refraction, arcmin -> deg
a = elev > 85; R(a) = 0;
b = elev > 5 & elev <= 85;  te = tand(elev(b)); R(b) = 58.1 ./ te - 0.07 ./ te .^ 3 + 0.000086 ./ te .^ 5;
c = elev > -0.575 & elev <= 5; E = elev(c); R(c) = 1735 + E .* (-518.2 + E .* (103.4 + E .* (-12.79 + E * 0.711)));
d = elev <= -0.575; R(d) = -20.772 ./ tand(elev(d));
zen_app = zen - R / 3600;
azn = acosd(max(min((sind(P.lat) * cz - sind(decl)) ./ (cosd(P.lat) * sind(zen)), 1), -1));
az = zeros(size(ha)); az(ha > 0) = mod(azn(ha > 0) + 180, 360); az(ha <= 0) = mod(540 - azn(ha <= 0), 360);

% ---- Hay-Davies ----
GHI = max(D(:, 6), 0); DNI = max(D(:, 7), 0); DHI = max(D(:, 8), 0);
B = 2 * pi * (doy - 1) / 365;
Iext = 1367 * (1.00011 + 0.034221 * cos(B) + 0.00128 * sin(B) + 0.000719 * cos(2 * B) + 0.000077 * sin(2 * B));
cos_aoi = cosd(zen_app) * cosd(P.tilt) + sind(zen_app) * sind(P.tilt) .* cosd(az - P.azim);
aoi = acosd(max(min(cos_aoi, 1), -1));
Rb = max(cos_aoi, 0) ./ max(cosd(zen_app), 0.01745);
AI = DNI ./ Iext;
sky = DHI .* (AI .* Rb + (1 - AI) * (1 + cosd(P.tilt)) / 2);
gnd = GHI * P.albedo * (1 - cosd(P.tilt)) / 2;
beam = max(DNI .* cos_aoi, 0);
W.G_beam = beam; W.G_T = max(beam + sky + gnd, 0); W.G_diff = max(W.G_T - W.G_beam, 0);
W.GHI = GHI; W.DNI = DNI; W.DHI = DHI; W.aoi = aoi; W.zen = zen_app;
W.T_amb = D(:, 4) + 273.15;                                % kelvin from here on
W.wind = D(:, 10);
W.hour_ist = mod(hr + 5, 24);
W.month = mo; W.doy = doy;
% effective irradiance after incidence-angle losses
th = min(aoi, 89.9);
Kb = 1 - P.iam_b0 * (1 ./ cosd(th) - 1); Kb = min(max(Kb, 0), 1); Kb(aoi >= 80) = 0;
W.G_eff = Kb .* W.G_beam + P.Kd * W.G_diff;
end
