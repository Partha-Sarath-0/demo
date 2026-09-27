"""Stage 7a - Berhampur TMY -> hourly plane-of-array (POA) irradiance, beam incidence angle.

Source: PVGIS TMY 19.313 N 84.810 E, 2005-2023 (file stored unchanged; md5 checked here).
Timing: solar position is evaluated at the stated UTC timestamp (hh:00). This was chosen by an
explicit closure test, not assumed: GHI = DNI cos(z) + DHI closes to 0.17 W/m2 mean absolute error
at hh:00 versus 14.3 W/m2 at hh:30 (see stage7_closure.txt).
Collector plane: tilt = 19.3 deg (latitude), azimuth 180 deg (due south) - ENGINEERING_ASSUMPTION
(standard fixed mount; an optimum-tilt sensitivity is reported).
Transposition: Hay-Davies (pvlib) with ground albedo 0.20 - standard choice; isotropic and Perez
are computed as a sensitivity.
Temperatures are converted to kelvin HERE and used in kelvin everywhere downstream.
"""
import hashlib, numpy as np, pandas as pd, pvlib

F = "/home/claude/grail_cfd/20_annual/weather/tmy_19.313_84.810_2005_2023_Berhampur.csv"
MD5 = "63855e6fa512876fb45c2d7a9c0c1e05"
LAT, LON, ELEV = 19.313, 84.810, 19.0


def load(tilt=19.3, azim=180.0, model="haydavies", albedo=0.20):
    assert hashlib.md5(open(F, "rb").read()).hexdigest() == MD5, "weather file changed"
    L = open(F).read().splitlines()
    i = [k for k, l in enumerate(L) if l.startswith("time(UTC)")][0]
    rows = [l for l in L[i + 1:] if l[:8].isdigit() and ":" in l[:14]]
    d = pd.DataFrame([r.split(",") for r in rows], columns=L[i].split(","))
    for c in d.columns[1:]:
        d[c] = d[c].astype(float)
    assert len(d) == 8760
    # TMY months come from different years: build a canonical non-leap year index for ordering
    mmddhh = d["time(UTC)"].str[4:8] + d["time(UTC)"].str[9:11]
    t = pd.to_datetime("2019" + mmddhh, format="%Y%m%d%H", utc=True)
    d.index = t
    d = d.sort_index()
    sp = pvlib.solarposition.get_solarposition(d.index, LAT, LON, altitude=ELEV)
    ghi, dni, dhi = d["G(h)"].clip(lower=0), d["Gb(n)"].clip(lower=0), d["Gd(h)"].clip(lower=0)
    dni_extra = pvlib.irradiance.get_extra_radiation(d.index)
    poa = pvlib.irradiance.get_total_irradiance(tilt, azim, sp.apparent_zenith, sp.azimuth, dni, ghi, dhi,
                                                dni_extra=dni_extra, albedo=albedo, model=model)
    aoi = pvlib.irradiance.aoi(tilt, azim, sp.apparent_zenith, sp.azimuth)
    w = pd.DataFrame(index=d.index)
    w["GHI"], w["DNI"], w["DHI"] = ghi, dni, dhi
    w["G_T"] = poa["poa_global"].fillna(0).clip(lower=0)
    w["G_beam"] = poa["poa_direct"].fillna(0).clip(lower=0)
    w["G_diff"] = (w.G_T - w.G_beam).clip(lower=0)          # sky + ground diffuse on the plane
    w["aoi_deg"] = aoi
    w["T_amb_K"] = d["T2m"] + 273.15                           # SI: kelvin from here on
    w["v_wind"] = d["WS10m"]
    w["local_hour"] = ((d.index + pd.Timedelta(hours=5, minutes=30)).hour).values  # IST
    w["doy"] = (d.index + pd.Timedelta(hours=5, minutes=30)).dayofyear.values
    w["month"] = d.index.month
    return w


if __name__ == "__main__":
    for model in ["isotropic", "haydavies", "perez"]:
        w = load(model=model)
        print(model, "GHI %.1f  POA(19.3 S) %.1f kWh/m2/yr" % (w.GHI.sum() / 1e3, w.G_T.sum() / 1e3))
    for tilt in (0, 10, 15, 19.3, 25, 30, 35):
        print("tilt", tilt, "%.1f" % (load(tilt=tilt).G_T.sum() / 1e3))
    w = load()
    print(w.groupby("month").G_T.sum().div(1e3).round(1).to_dict())
    print("hours G_T>0:", (w.G_T > 0).sum(), " max G_T %.0f" % w.G_T.max(),
          " hours G_T>1000:", (w.G_T > 1000).sum(), " wind>5 m/s hours:", (w.v_wind > 5).sum())
