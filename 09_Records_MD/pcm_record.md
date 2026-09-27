# GRAIL CFD — Graded PCM tray. Filing 2.

## Model

RT55 + 10 % expanded graphite from the roadmap material table: solid rho 880 / cp 2000 /
k 2.80, liquid 770 / 2200 / 2.40, latent heat **170 kJ/kg** across **51 - 57 C**. Apparent heat
capacity c_eff = c_p(f) + L df/dT with a linear liquid fraction over the 6 K interval - the form
the roadmap itself specifies.

The tray is one lumped node per plate cell, eliminated analytically each time step so the
plate-tray coupling stays fully implicit. The rear path is split about the tray: half the tray
thickness to the plate, the other half plus VIP plus the external film to ambient.

**Stated simplification:** lateral conduction inside the PCM is neglected. k_pcm x t_pcm is
0.028 W/K against the absorber's 0.458 W/K, so the tray carries about 6 % of the plate's
in-plane conductance and cannot redistribute heat on these timescales.

Each scenario is run twice: with latent capacity, and with the tray as the steady solver
treats it - a pure resistance with no capacity. The difference is what the PCM buys.

## Results

| scenario | peak plate T with tray | without | benefit | largest difference | stored |
|---|---|---|---|---|---|
| charge, cold start at the design point, 4 h | 59.0 C | 61.5 C | **-2.5 K** | +10.7 K at 900 s | 1.07 MJ/m2, f_liq 0.471 |
| cloud, irradiance to zero for 2 h | 53.5 C | 54.7 C | **-1.2 K** | +18.9 K at 1200 s | -0.00 MJ/m2, f_liq 0.000 |
| stagnation, flow cut to 2 %, 1000 W/m2, 4 h | 205.3 C | 263.8 C | **-58.5 K** | +134.4 K at 4200 s | 4.23 MJ/m2, f_liq 1.000 |

## What the tray actually does

**Stagnation is where it earns its place.** Peak plate temperature falls from 264 C to 205 C,
a **58 K** reduction, while the tray absorbs 4.23 MJ/m2 and melts completely.

**During charging it is nearly free.** The tray holds the plate 2.07 K cooler at 4 h and delays
warm-up by up to 10.7 K early on, at the design point, which is a small and mostly transient
cost in delivered heat.

**On cloud passage it buffers.** The plate stays up to 18.9 K warmer during the discharge.
The tray gives back what it stored: liquid fraction returns to 0.000 and stored energy to
-0.001 MJ/m2.

## The caveat that matters, stated plainly

At stagnation the model runs the tray to **200 C**. RT55 is a paraffin; it would have
decomposed long before that. The apparent-heat-capacity formulation has no degradation,
no vapour pressure and no upper service limit in it, so it will happily report protection a
real tray could not deliver more than once.

**That is itself the design finding.** The 58 K stagnation benefit is real in the model and
conditional in the hardware: it holds only if the tray is kept below its decomposition
temperature, which on this collector means the stagnation problem has to be solved by
something else - the thermotropic layer, a drain-back, or a relief path - before the PCM can
be relied on for it. The charge and cloud results, which stay inside 51 - 62 C, are not
subject to this caveat.

## Numerics

Grid 110 x 120, dt = 10 s, implicit Euler. A dt-sensitivity check is NOT included and is
listed as outstanding: the plate time constant is about 4 s, so dt = 10 s under-resolves the
first minute of each transient. The hours-scale behaviour these conclusions rest on is well
inside the resolved range, but the very early transient is not converged in time.

One reporting artefact, recorded rather than hidden: the two 'cloud-precondition' lines in the
log print 300.00 K because their save interval exceeded the run length, so only the initial
frame was stored. The preconditioned state passed forward is the solver's final field, not that
print, and the cloud results are unaffected.

