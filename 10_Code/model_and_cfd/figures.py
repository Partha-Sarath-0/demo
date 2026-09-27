"""GRAIL CFD — figures from the converged single-channel flow + thermal solution."""
import numpy as np, os, sys
import pyvista as pv
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

pv.OFF_SCREEN = True
CASE = "/home/claude/grail_cfd/04_baseline/ch05_flow"
FIG = "/home/claude/grail_cfd/12_figures"
os.makedirs(FIG, exist_ok=True)

plt.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 9, "axes.linewidth": 0.8,
    "axes.grid": True, "grid.alpha": 0.25, "grid.linewidth": 0.5,
    "figure.dpi": 160, "savefig.dpi": 160, "savefig.bbox": "tight",
})
ACC = "#17557d"; ACC2 = "#b3452c"; ACC3 = "#3d7a5a"

foam = os.path.join(CASE, "case.foam")
open(foam, "w").close()
r = pv.OpenFOAMReader(foam)
r.set_active_time_value(max(r.time_values))
r.cell_to_point_creation = True
mesh = r.read()
internal = mesh["internalMesh"]
print("cells:", internal.n_cells, "points:", internal.n_points)
print("arrays:", internal.array_names)

internal = internal.cell_data_to_point_data()
U = internal.point_data["U"]
internal.point_data["Umag"] = np.linalg.norm(U, axis=1) * 1000.0     # mm/s
if "T" in internal.point_data:
    internal.point_data["Tc"] = internal.point_data["T"] - 273.15     # degC
internal.point_data["p_Pa"] = internal.point_data["p"] * 997.0

pts = internal.points
x = pts[:, 0]

# ---------------------------------------------------------------- axial profiles
XI = np.array([0.0, 0.05, 0.10, 0.20, 0.25, 0.35, 0.50, 0.65, 0.75, 0.85, 0.90, 0.95, 1.0])
A_mm2 = None
rows = []
for xi in XI:
    xs = -0.550 + 1.100 * xi
    sl = internal.slice(normal="x", origin=(xs, 0, 0))
    if sl.n_points == 0:
        continue
    a = sl.compute_cell_sizes(length=False, area=True, volume=False)
    area = a.cell_data["Area"].sum()
    spd = sl.point_data["Umag"]
    row = {"xi": xi, "x_mm": xs * 1000, "A_mm2": area * 1e6,
           "u_max": spd.max(), "u_mean": spd.mean(),
           "p_Pa": sl.point_data["p_Pa"].mean()}
    if "Tc" in sl.point_data:
        row["T_mean"] = sl.point_data["Tc"].mean()
        row["T_max"] = sl.point_data["Tc"].max()
        row["T_min"] = sl.point_data["Tc"].min()
    rows.append(row)

import json
json.dump([{k: float(v) for k, v in r_.items()} for r_ in rows], open(os.path.join(FIG, "axial_profiles.json"), "w"), indent=1)
print("\n  xi    x(mm)    A(mm2)   u_max(mm/s)  u_mean   p(Pa)    T_mean(C)  T_max(C)")
for r_ in rows:
    print("  %4.2f %8.1f %9.3f %10.3f %8.3f %8.3f %9.3f %9.3f"
          % (r_["xi"], r_["x_mm"], r_["A_mm2"], r_["u_max"], r_["u_mean"], r_["p_Pa"],
             r_.get("T_mean", np.nan), r_.get("T_max", np.nan)))

xi = np.array([r_["xi"] for r_ in rows])
# ---- Figure: hydraulics
fig, ax = plt.subplots(1, 3, figsize=(10.5, 3.0))
ax[0].plot(xi, [r_["A_mm2"] for r_ in rows], "o-", color=ACC, ms=3.5, lw=1.4)
ax[0].set_xlabel("normalised flow coordinate  $\\xi$"); ax[0].set_ylabel("section area  (mm$^2$)")
ax[0].set_title("Converging section", fontsize=9.5)
ax[1].plot(xi, [r_["u_max"] for r_ in rows], "o-", color=ACC2, ms=3.5, lw=1.4, label="peak")
ax[1].plot(xi, [r_["u_mean"] for r_ in rows], "s--", color=ACC, ms=3.5, lw=1.4, label="mean")
ax[1].set_xlabel("$\\xi$"); ax[1].set_ylabel("velocity  (mm/s)")
ax[1].set_title("Velocity along the channel", fontsize=9.5); ax[1].legend(frameon=False, fontsize=8)
ax[2].plot(xi, [r_["p_Pa"] for r_ in rows], "o-", color=ACC3, ms=3.5, lw=1.4)
ax[2].set_xlabel("$\\xi$"); ax[2].set_ylabel("static pressure  (Pa)")
ax[2].set_title("Pressure", fontsize=9.5)
fig.suptitle("GRAIL channel CH05 — hydraulics, $\\dot m_{total}$ = 0.0025 kg/s", fontsize=10, y=1.04)
fig.savefig(os.path.join(FIG, "S1_hydraulics.png")); plt.close(fig)

# ---- Figure: thermal
if "T_mean" in rows[0]:
    fig, ax = plt.subplots(1, 2, figsize=(7.4, 3.0))
    ax[0].plot(xi, [r_["T_mean"] for r_ in rows], "o-", color=ACC, ms=3.5, lw=1.4, label="section mean")
    ax[0].plot(xi, [r_["T_max"] for r_ in rows], "^--", color=ACC2, ms=3.5, lw=1.2, label="section max")
    ax[0].plot(xi, [r_["T_min"] for r_ in rows], "v--", color=ACC3, ms=3.5, lw=1.2, label="section min")
    ax[0].set_xlabel("$\\xi$"); ax[0].set_ylabel("temperature  ($^\\circ$C)")
    ax[0].set_title("Fluid temperature along the channel", fontsize=9.5)
    ax[0].legend(frameon=False, fontsize=8)
    dT = np.array([r_["T_mean"] for r_ in rows]) - rows[0]["T_mean"]
    ax[1].plot(xi, dT, "o-", color=ACC, ms=3.5, lw=1.4, label="CFD")
    ax[1].plot(xi, 26.23 * xi, "k--", lw=1.0, label="$Q\\xi/(\\dot m c_p)$")
    ax[1].set_xlabel("$\\xi$"); ax[1].set_ylabel("$\\Delta T$  (K)")
    ax[1].set_title("Temperature rise vs energy balance", fontsize=9.5)
    ax[1].legend(frameon=False, fontsize=8)
    fig.suptitle("GRAIL channel CH05 — thermal, wall flux 1264.07 W/m$^2$", fontsize=10, y=1.04)
    fig.savefig(os.path.join(FIG, "S2_thermal.png")); plt.close(fig)

print("\nfigures written to", FIG)
