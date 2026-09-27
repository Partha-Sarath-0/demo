"""GRAIL CFD — cross-section contours and 3-D views, identical colour scales throughout."""
import numpy as np, os
import pyvista as pv
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.tri import Triangulation

CASE = "/home/claude/grail_cfd/04_baseline/ch05_flow"
FIG = "/home/claude/grail_cfd/12_figures"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 8.5,
                     "figure.dpi": 170, "savefig.dpi": 170, "savefig.bbox": "tight"})

foam = os.path.join(CASE, "case.foam"); open(foam, "w").close()
r = pv.OpenFOAMReader(foam); r.set_active_time_value(max(r.time_values))
r.cell_to_point_creation = True
m = r.read()["internalMesh"].cell_data_to_point_data()
m.point_data["Umag"] = np.linalg.norm(m.point_data["U"], axis=1) * 1000.0
m.point_data["Tc"] = m.point_data["T"] - 273.15

XI = [0.0, 0.10, 0.25, 0.50, 0.75, 0.90, 1.0]
slices = []
for xi in XI:
    xs = -0.550 + 1.100 * xi
    xs = min(max(xs, -0.5499), 0.5499)
    slices.append((xi, m.slice(normal="x", origin=(xs, 0, 0))))

umax = max(s.point_data["Umag"].max() for _, s in slices)
tmin = min(s.point_data["Tc"].min() for _, s in slices)
tmax = max(s.point_data["Tc"].max() for _, s in slices)
print("common scales:  U 0 - %.2f mm/s     T %.2f - %.2f degC" % (umax, tmin, tmax))


def panel(field, cmap, vmin, vmax, label, fname, title):
    fig, axs = plt.subplots(1, len(slices), figsize=(2.05 * len(slices), 2.5))
    for ax, (xi, s) in zip(axs, slices):
        p = s.points
        y = (p[:, 1] + 0.060) * 1000.0     # mm, centred on the channel
        z = p[:, 2] * 1000.0
        v = s.point_data[field]
        tri = Triangulation(y, z)
        tc = ax.tricontourf(tri, v, levels=24, cmap=cmap, vmin=vmin, vmax=vmax)
        ax.tricontour(tri, v, levels=8, colors="k", linewidths=0.18, alpha=0.35)
        ax.set_aspect("equal")
        ax.set_title("$\\xi$ = %.2f" % xi, fontsize=8.5)
        ax.set_xlim(-5.0, 5.0); ax.set_ylim(-0.3, 4.4)
        ax.set_xticks([-4, 0, 4])
        if ax is axs[0]:
            ax.set_ylabel("z  (mm)")
        else:
            ax.set_yticklabels([])
        ax.set_xlabel("y  (mm)")
        ax.tick_params(labelsize=7)
    sm = plt.cm.ScalarMappable(cmap=cmap, norm=plt.Normalize(vmin=vmin, vmax=vmax))
    cb = fig.colorbar(sm, ax=axs, fraction=0.016, pad=0.012)
    cb.set_label(label, fontsize=8.5); cb.ax.tick_params(labelsize=7)
    fig.suptitle(title, fontsize=10, y=1.06)
    fig.savefig(os.path.join(FIG, fname)); plt.close(fig)
    print("  wrote", fname)


panel("Umag", "viridis", 0.0, umax, "velocity  (mm/s)", "S3_velocity_sections.png",
      "GRAIL CH05 — velocity magnitude, common scale, sections from the channel's own inlet")
panel("Tc", "inferno", tmin, tmax, "temperature  ($^\\circ$C)", "S4_temperature_sections.png",
      "GRAIL CH05 — fluid temperature, common scale, wall flux 1264.07 W/m$^2$")

# ---- 3-D view, temperature on the wall, vertical exaggeration for legibility
warped = m.copy()
warped.points[:, 0] *= 0.012          # compress x so the 1100 mm channel fits the frame
pl = pv.Plotter(off_screen=True, window_size=(1500, 620))
pl.add_mesh(warped, scalars="Tc", cmap="inferno", show_edges=False,
            scalar_bar_args=dict(title="T  (degC)", n_labels=5, fmt="%.0f",
                                 title_font_size=15, label_font_size=12))
pl.camera_position = [(0.0, -0.30, 0.16), (0.0, -0.060, 0.002), (0, 0, 1)]
pl.add_text("GRAIL CH05 - fluid temperature, x compressed 83:1", position="upper_left",
            font_size=10, color="black")
pl.set_background("white")
pl.screenshot(os.path.join(FIG, "S5_3d_temperature.png"))
print("  wrote S5_3d_temperature.png")

pl = pv.Plotter(off_screen=True, window_size=(1500, 620))
pl.add_mesh(warped, scalars="Umag", cmap="viridis", show_edges=False,
            scalar_bar_args=dict(title="|U|  (mm/s)", n_labels=5, fmt="%.0f",
                                 title_font_size=15, label_font_size=12))
pl.camera_position = [(0.0, -0.30, 0.16), (0.0, -0.060, 0.002), (0, 0, 1)]
pl.add_text("GRAIL CH05 - velocity magnitude, x compressed 83:1", position="upper_left",
            font_size=10, color="black")
pl.set_background("white")
pl.screenshot(os.path.join(FIG, "S6_3d_velocity.png"))
print("  wrote S6_3d_velocity.png")
