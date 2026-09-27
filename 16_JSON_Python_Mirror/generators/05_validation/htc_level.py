"""Extract local h(xi) and Nu(xi) from the converged 3-D OpenFOAM solution.

These are the closure quantities the reduced conjugate solver needs, so they must come
from the resolved CFD rather than from a textbook correlation.
"""
import numpy as np, os, json
import pyvista as pv

import sys
CASE = sys.argv[1]
K = 0.610
Q_WALL = 1264.07
RHO, CP, MU = 997.0, 4180.0, 8.55e-4
MDOT = 0.0025 / 12.0

foam = os.path.join(CASE, "case.foam"); open(foam, "w").close()
r = pv.OpenFOAMReader(foam); r.set_active_time_value(max(r.time_values))
r.cell_to_point_creation = True
data = r.read()
internal = data["internalMesh"].cell_data_to_point_data()

# wall patch
wall = None
for k in data.keys():
    if k == "boundary":
        for bk in data[k].keys():
            if "wall" in bk.lower():
                wall = data[k][bk]
print("wall patch:", None if wall is None else wall.n_cells)

XI = np.linspace(0.0, 1.0, 41)
rows = []
for xi in XI:
    xs = -0.550 + 1.100 * xi
    xs = min(max(xs, -0.5495), 0.5495)
    sl = internal.slice(normal="x", origin=(xs, 0, 0))
    if sl.n_points < 10:
        continue
    T = sl.point_data["T"]
    U = np.linalg.norm(sl.point_data["U"], axis=1)
    a = sl.compute_cell_sizes(length=False, area=True, volume=False)
    A = a.cell_data["Area"].sum()
    # flux-weighted bulk temperature
    Tb = float(np.sum(T * U) / np.sum(U))
    # wall temperature: hottest ring of points on the section boundary
    edges = sl.extract_feature_edges(boundary_edges=True, feature_edges=False,
                                     manifold_edges=False, non_manifold_edges=False)
    Tw = float(edges.point_data["T"].mean()) if edges.n_points else float(T.max())
    h = Q_WALL / (Tw - Tb) if Tw > Tb else np.nan
    # local Dh from this slice
    per = edges.compute_cell_sizes(length=True, area=False, volume=False).cell_data["Length"].sum() \
        if edges.n_cells else np.nan
    Dh = 4 * A / per if per and per > 0 else np.nan
    Nu = h * Dh / K
    u_mean = MDOT / (RHO * A)
    Re_phys = RHO * u_mean * Dh / MU
    Re_brief = 4 * MDOT / (np.pi * Dh * MU)
    rows.append(dict(xi=float(xi), x_mm=float(xs * 1000), A_mm2=float(A * 1e6),
                     Dh_mm=float(Dh * 1000), Tb=Tb, Tw=Tw, h=float(h), Nu=float(Nu),
                     Re_phys=float(Re_phys), Re_brief=float(Re_brief)))

json.dump(rows, open(sys.argv[2], "w"), indent=1)
print("\n   xi     Dh(mm)   T_bulk(K)  T_wall(K)   dT(K)    h(W/m2K)    Nu     Re_phys")
for r_ in rows[::4]:
    print("  %4.2f   %7.4f  %9.3f %9.3f %8.3f %10.2f %7.3f %9.2f"
          % (r_["xi"], r_["Dh_mm"], r_["Tb"], r_["Tw"], r_["Tw"] - r_["Tb"],
             r_["h"], r_["Nu"], r_["Re_phys"]))
nu = np.array([r_["Nu"] for r_ in rows])
ok = np.isfinite(nu) & (np.array([r_["xi"] for r_ in rows]) > 0.15)
print("\nNu over the developed region (xi > 0.15): mean %.3f  min %.3f  max %.3f"
      % (nu[ok].mean(), nu[ok].min(), nu[ok].max()))
print("(constant-q laminar reference: Nu = 4.36 circular, 8.23 parallel plates)")
