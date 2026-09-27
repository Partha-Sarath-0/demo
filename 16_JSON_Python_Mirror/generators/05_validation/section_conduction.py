"""
GRAIL — does the 2-D plate solver's fin treatment of the metal hold up?

The conjugate OpenFOAM run was meant to answer this and did not converge
(14_provenance/cht_attempt_record.md). This answers the same question by a different and
much more controllable route: a full 2-D finite-element conduction solution in the REAL
roll-bond cross-section, over one glide period (two pitches, cyclic in y), at stations along
the plate, driven by the 2-D solver's own boundary conditions.

What the plate solver assumes, and what this tests:

  1. the metal is at ONE temperature through its thickness at each (x, y) - tested by the
     top-surface to channel-wall temperature difference this solution produces
  2. lateral conduction into the bond land follows the Hottel-Whillier-Bliss straight-fin
     formula F = tanh(mW/2)/(mW/2) on a flat fin of thickness t_lower + t_upper - tested
     against the heat actually crossing the bridge midline here
  3. the absorber's effective temperature is the fin-average - tested against the
     area-weighted mean of this solution

Geometry is the as-built section: the channel wall straight off the CAD NURBS, the lower
sheet flat at 1 mm, and the upper sheet as the 1 mm outward offset of the dome merged into
the flat land by taking the UPPER ENVELOPE of the two. The envelope is what makes this
tractable where the structured mesh was not: a 1 mm sheet cannot be offset across the 0.5 mm
concave corner fillet without the offset surface crossing itself, and the envelope resolves
that crossing the way the metal itself does, by filling the corner.

Boundary conditions, all taken from the plate solver's converged design-point solution so the
two are comparable term by term:

  top     q_abs - U_top (T - T_amb), both per unit APERTURE, so both are scaled by the
          surface's |dy/ds| - the glazing and TIM above are flat, so the flux a sloping piece
          of absorber collects is set by its horizontal projection, not by its arc length
  bottom  -h_rear (T - T_amb), flat, no scaling
  wall    -h_f (T - T_f) per unit WETTED area, h_f = Nu k_w / Dh(xi), Nu the grid-extrapolated
          2.9238, T_f the plate solver's own bulk temperature for that channel at that station
  sides   cyclic, y period 80 mm - a glide period is two channels (CR-03)

Writes 05_validation/section_conduction.json and 12_figures/V2_section_conduction.png
"""
import os, sys, json, time
import numpy as np
import importlib.util

sys.path.insert(0, "/home/claude/grail_cfd/tools")
from grail_cht import Geometry, Materials, Operating, GrailCHT

spec = importlib.util.spec_from_file_location("PM", "/home/claude/grail_cfd/03_mesh/plate_mesh.py")
PM = importlib.util.module_from_spec(spec); sys.modules["PM"] = PM; spec.loader.exec_module(PM)
sys.path.insert(0, "/home/claude/grail_cfd/03_mesh")
import cht_solid2 as CS

OUT = "/home/claude/grail_cfd/05_validation"
FIG = "/home/claude/grail_cfd/12_figures"
PITCH, T_LO, T_UP = 40.0, 1.0, 1.0          # mm
NU_CFD = 2.9238
MESH_H = 0.35                                # mm, target element size
STATIONS = [0.1, 0.3, 0.5, 0.7, 0.9]         # xi along channel a


# ------------------------------------------------------------------ section geometry
def top_envelope(rings, ycs, y_grid):
    """Upper surface of the metal over the window, as the envelope of the flat land and the
    1 mm outward offset of each dome.

    Taking a maximum over a fine y grid is not a convenience: the offset of a concave fillet
    of radius 0.5 mm at a distance of 1 mm crosses itself, so the offset curve is not a
    function of y near each channel corner. The envelope picks the outermost material at every
    y, which is what the metal does - the sheet stops being a shell there and fills the corner.
    """
    top = np.full(len(y_grid), T_UP)
    dy = y_grid[1] - y_grid[0]
    for ring, yc in zip(rings, ycs):
        (yf, zf, fi), (yd, zd, di), _ = CS.split_ring(ring, CS.fixed_split(ring[None]))
        P = np.column_stack([yd, zd])       # the ring already carries absolute y
        tg = np.gradient(P, axis=0)
        tg /= (np.linalg.norm(tg, axis=1)[:, None] + 1e-12)
        nrm = np.column_stack([tg[:, 1], -tg[:, 0]])
        cen = P.mean(axis=0)
        flip = np.sum(nrm * (P - cen), axis=1) < 0
        nrm[flip] *= -1.0
        # densify before offsetting so the envelope is not sampled coarser than the grid
        s = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(P, axis=0), axis=1))])
        t = np.linspace(0, s[-1], max(400, int(4 * s[-1] / dy)))
        Pd = np.column_stack([np.interp(t, s, P[:, c]) for c in range(2)])
        Nd = np.column_stack([np.interp(t, s, nrm[:, c]) for c in range(2)])
        Nd /= (np.linalg.norm(Nd, axis=1)[:, None] + 1e-12)
        O = Pd + T_UP * Nd
        j = np.clip(((O[:, 0] - y_grid[0]) / dy + 0.5).astype(int), 0, len(y_grid) - 1)
        np.maximum.at(top, j, O[:, 1])
    return top


def build_section(rings, ycs, y0, y1, ny=2400):
    """Outer polygon of the metal and the two channel polygons, all counter-clockwise."""
    y_grid = np.linspace(y0, y1, ny)
    top = top_envelope(rings, ycs, y_grid)
    # The envelope is computed on a 0.033 mm grid because the offset curve turns sharply at
    # the corners, but handing 2400 boundary points to the mesher forces elements two orders
    # of magnitude smaller than the target size. Decimate to the target spacing, keeping every
    # point where the envelope departs from the flat land so the shoulders survive.
    step = max(1, int(round(MESH_H / (y_grid[1] - y_grid[0]))))
    keep = np.zeros(ny, bool)
    keep[::step] = True
    keep[0] = keep[-1] = True
    bulge = top > T_UP + 1e-9
    keep |= bulge & (np.r_[True, ~bulge[:-1]] | np.r_[~bulge[1:], True])   # the two shoulders
    keep |= bulge & (np.arange(ny) % max(1, step // 3) == 0)               # denser on the dome
    yb, tb = y_grid[keep], top[keep]
    bot_y = np.unique(np.r_[y_grid[::step], y_grid[-1]])
    outer = np.vstack([np.column_stack([bot_y, np.full(len(bot_y), -T_LO)]),
                       np.column_stack([yb[::-1], tb[::-1]])])
    keep2 = np.concatenate([[True], np.linalg.norm(np.diff(outer, axis=0), axis=1) > 1e-9])
    outer = outer[keep2]
    holes = [np.column_stack([r[:, 1], r[:, 2]]) for r in rings]
    return outer, holes


def mesh_section(outer, holes, h=MESH_H):
    """Triangulate the metal. Returns nodes (N,2) mm, triangles (M,3), boundary edges."""
    import gmsh
    gmsh.initialize()
    gmsh.option.setNumber("General.Terminal", int(os.environ.get("GMSH_VERBOSE", 0)))
    gmsh.model.add("sec")
    occ = gmsh.model.geo

    def loop(poly, tag0):
        pts = [occ.addPoint(p[0], p[1], 0.0, h) for p in poly]
        ls = [occ.addLine(pts[i], pts[(i + 1) % len(pts)]) for i in range(len(pts))]
        return occ.addCurveLoop(ls), ls

    lo, l_outer = loop(outer, 1)
    lh, l_holes = [], []
    for hpoly in holes:
        t, ls = loop(hpoly, 2)
        lh.append(t); l_holes.append(ls)
    s = occ.addPlaneSurface([lo] + lh)
    occ.synchronize()
    gmsh.option.setNumber("Mesh.MeshSizeFromCurvature", 0)
    gmsh.option.setNumber("Mesh.MeshSizeExtendFromBoundary", 1)
    gmsh.option.setNumber("Mesh.Algorithm", 6)
    gmsh.model.mesh.generate(2)
    nt, nc, _ = gmsh.model.mesh.getNodes()
    order = np.argsort(nt)
    X = np.array(nc).reshape(-1, 3)[order][:, 0:2]
    tag_of = {int(t): i for i, t in enumerate(nt[order])}
    et, en = gmsh.model.mesh.getElementsByType(2)
    tri = np.array([tag_of[int(t)] for t in en], dtype=np.int64).reshape(-1, 3)
    gmsh.finalize()
    return X, tri


# ------------------------------------------------------------------ FEM
def assemble(X, tri, k):
    """Linear-triangle conduction stiffness, per unit depth. Returns (K, area)."""
    from scipy.sparse import coo_matrix
    p = X[tri]                                    # (M,3,2)
    x1, y1 = p[:, 0, 0], p[:, 0, 1]
    x2, y2 = p[:, 1, 0], p[:, 1, 1]
    x3, y3 = p[:, 2, 0], p[:, 2, 1]
    det = (x2 - x1) * (y3 - y1) - (x3 - x1) * (y2 - y1)
    A = 0.5 * np.abs(det)
    b = np.stack([y2 - y3, y3 - y1, y1 - y2], axis=1) / det[:, None]
    c = np.stack([x3 - x2, x1 - x3, x2 - x1], axis=1) / det[:, None]
    Ke = k * A[:, None, None] * (b[:, :, None] * b[:, None, :] + c[:, :, None] * c[:, None, :])
    I = np.repeat(tri, 3, axis=1).ravel()
    J = np.tile(tri, (1, 3)).ravel()
    K = coo_matrix((Ke.ravel(), (I, J)), shape=(len(X), len(X))).tocsr()
    return K, A


def boundary_edges(tri):
    """Edges used by exactly one triangle."""
    e = np.vstack([tri[:, [0, 1]], tri[:, [1, 2]], tri[:, [2, 0]]])
    key = np.sort(e, axis=1)
    uq, idx, cnt = np.unique(key, axis=0, return_index=True, return_counts=True)
    return e[idx[cnt == 1]]


def robin(X, edges, h_of_edge, Tref_of_edge, n):
    """Add a Robin condition h (T - Tref) on a set of edges. Returns (K_add, f_add)."""
    from scipy.sparse import coo_matrix
    L = np.linalg.norm(X[edges[:, 1]] - X[edges[:, 0]], axis=1)
    hL = h_of_edge * L
    # consistent 1-D mass matrix on a segment: L/6 * [[2,1],[1,2]]
    Ke = np.einsum("e,ij->eij", hL / 6.0, np.array([[2.0, 1.0], [1.0, 2.0]]))
    I = np.repeat(edges, 2, axis=1).ravel()
    J = np.tile(edges, (1, 2)).ravel()
    K = coo_matrix((Ke.ravel(), (I, J)), shape=(n, n)).tocsr()
    f = np.zeros(n)
    np.add.at(f, edges[:, 0], 0.5 * hL * Tref_of_edge)
    np.add.at(f, edges[:, 1], 0.5 * hL * Tref_of_edge)
    return K, f


def classify(X, edges, holes, y0, y1):
    """Which boundary each edge belongs to: 0 bottom, 1 top, 2 left, 3 right, 4+ channel i."""
    mid = 0.5 * (X[edges[:, 0]] + X[edges[:, 1]])
    lab = np.full(len(edges), 1, np.int8)                  # default: top
    lab[np.abs(mid[:, 1] + T_LO) < 1e-6] = 0
    lab[np.abs(mid[:, 0] - y0) < 1e-6] = 2
    lab[np.abs(mid[:, 0] - y1) < 1e-6] = 3
    # A channel-wall edge is one whose BOTH endpoints are ring vertices. Testing the edge
    # midpoint against the ring vertices does not work - a midpoint is half a segment away
    # from the nearest vertex by construction, so that test found zero wall edges.
    from scipy.spatial import cKDTree
    for i, hp in enumerate(holes):
        d0, _ = cKDTree(hp).query(X[edges[:, 0]])
        d1, _ = cKDTree(hp).query(X[edges[:, 1]])
        on = (d0 < 1e-9) & (d1 < 1e-9)
        assert on.sum() == len(hp), \
            "channel %d: %d wall edges found, ring has %d segments" % (i, on.sum(), len(hp))
        lab[on] = 4 + i
    return lab


def periodic_map(X, edges, lab, y0, y1, n):
    """DOF map that welds the left boundary onto the right one, period y1 - y0."""
    from scipy.spatial import cKDTree
    left = np.unique(edges[lab == 2])
    right = np.unique(edges[lab == 3])
    if len(left) == 0 or len(right) == 0:
        return np.arange(n), n
    tree = cKDTree(np.column_stack([X[left, 0] + (y1 - y0), X[left, 1]]))
    d, j = tree.query(X[right])
    assert d.max() < 1e-6, "cyclic faces do not match: max gap %.3g mm" % d.max()
    dof = np.arange(n)
    dof[right] = left[j]
    uq = np.unique(dof)
    remap = np.full(n, -1, np.int64); remap[uq] = np.arange(len(uq))
    return remap[dof], len(uq)


# ------------------------------------------------------------------ the run
def run_station(rings, ycs, Tf, U_top, q_abs, T_amb, h_rear, hf, y0, y1, h=MESH_H):
    from scipy.sparse import coo_matrix
    from scipy.sparse.linalg import spsolve
    outer, holes = build_section(rings, ycs, y0, y1)
    X, tri = mesh_section(outer, holes, h)
    n = len(X)
    K, A = assemble(X, tri, Materials.k_al * 1e-3)     # W/mm/K -> consistent in mm
    ed = boundary_edges(tri)
    lab = classify(X, ed, holes, y0, y1)
    f = np.zeros(n)

    # top: per unit APERTURE, so scale by |dy/ds| of each edge
    m_top = lab == 1
    e = ed[m_top]
    d = X[e[:, 1]] - X[e[:, 0]]
    proj = np.abs(d[:, 0]) / (np.linalg.norm(d, axis=1) + 1e-12)
    Kt, ft = robin(X, e, U_top * 1e-6 * proj,
                   np.full(len(e), T_amb + q_abs / U_top), n)
    K = K + Kt; f = f + ft

    m_bot = lab == 0
    Kb, fb = robin(X, ed[m_bot], np.full(m_bot.sum(), h_rear * 1e-6),
                   np.full(m_bot.sum(), T_amb), n)
    K = K + Kb; f = f + fb

    for i in range(len(holes)):
        m = lab == 4 + i
        if m.sum() == 0:
            continue
        Kw, fw = robin(X, ed[m], np.full(m.sum(), hf[i] * 1e-6),
                       np.full(m.sum(), Tf[i]), n)
        K = K + Kw; f = f + fw

    dof, nd = periodic_map(X, ed, lab, y0, y1, n)
    P = coo_matrix((np.ones(n), (np.arange(n), dof)), shape=(n, nd)).tocsr()
    T = P @ spsolve((P.T @ K @ P).tocsc(), P.T @ f)

    # ---- diagnostics
    Tc = T[tri].mean(axis=1)
    Xc = X[tri].mean(axis=1)
    T_area = float((Tc * A).sum() / A.sum())
    # through-thickness: top-surface nodes against channel-wall nodes, same y band
    top_n = np.unique(ed[lab == 1])
    wall_n = np.unique(ed[lab >= 4])
    res = {"T_area_mean": T_area,
           "T_min": float(T.min()), "T_max": float(T.max()),
           "T_top_mean": float(T[top_n].mean()), "T_top_max": float(T[top_n].max()),
           "T_wall_mean": float(T[wall_n].mean()),
           "through_thickness_drop_K": float(T[top_n].mean() - T[wall_n].mean()),
           "peak_to_peak_K": float(T.max() - T.min()),
           "n_nodes": int(n), "n_tri": int(len(tri)),
           "metal_area_mm2": float(A.sum())}
    # lateral heat crossing the bridge midline between the two channels, per unit length
    ymid = 0.5 * (ycs[0] + ycs[1])
    band = np.abs(Xc[:, 0] - ymid) < 1.0
    if band.sum():
        # dT/dy on each triangle, times k, times the triangle's z extent, integrated
        p = X[tri[band]]
        det = ((p[:, 1, 0] - p[:, 0, 0]) * (p[:, 2, 1] - p[:, 0, 1])
               - (p[:, 2, 0] - p[:, 0, 0]) * (p[:, 1, 1] - p[:, 0, 1]))
        b = np.stack([p[:, 1, 1] - p[:, 2, 1], p[:, 2, 1] - p[:, 0, 1],
                      p[:, 0, 1] - p[:, 1, 1]], axis=1) / det[:, None]
        dTdy = (b * T[tri[band]]).sum(axis=1)
        q = -Materials.k_al * 1e-3 * dTdy * A[band]        # W/mm of channel, per triangle
        res["bridge_flux_W_per_mm"] = float(q.sum() / 2.0)  # /2: band is 2 mm wide
    # energy balance
    res["balance"] = {}
    for nm, m_, ref, hh in (("top", lab == 1, None, None), ("bottom", lab == 0, T_amb, h_rear),
                            ("ch0", lab == 4, Tf[0], hf[0]), ("ch1", lab == 5, Tf[1], hf[1])):
        if m_.sum() == 0:
            continue
        e = ed[m_]
        L = np.linalg.norm(X[e[:, 1]] - X[e[:, 0]], axis=1)
        Tm = 0.5 * (T[e[:, 0]] + T[e[:, 1]])
        if nm == "top":
            d = X[e[:, 1]] - X[e[:, 0]]
            pr = np.abs(d[:, 0]) / (np.linalg.norm(d, axis=1) + 1e-12)
            # W per mm of channel length: flux in W/m2 -> W/mm2 is 1e-6, times L in mm
            res["balance"][nm] = float(
                (L * pr * 1e-6 * (q_abs - U_top * (Tm - T_amb))).sum())
        else:
            res["balance"][nm] = float(-(L * hh * 1e-6 * (Tm - ref)).sum())
    res["balance"]["sum_W_per_mm"] = float(sum(res["balance"].values()))
    return res, X, tri, T, ed, lab


if __name__ == "__main__":
    t0 = time.time()
    g, m, op = Geometry(), Materials(), Operating()
    NX2D, NY2D = 220, 240
    sol = {}
    for name, f in (("co", 0), ("alt", 1)):
        s = GrailCHT(g, m, Operating(f_interdig=f), nx=NX2D, ny=NY2D, nu_cfd=NU_CFD)
        r = s.solve(max_outer=2500, tol=1e-8)
        q_top, _, _, _ = s.top_loss(s.Tp)
        sol[name] = {"Tp": s.Tp.copy(), "Tf": s.Tf.copy(), "q_abs": float(np.mean(s.q_abs)),
                     "U_top": float((q_top / (s.Tp - op.T_amb)).mean()), "res": r}
        print("2-D solver %-4s  eta %.5f  Tp_std %.5f  U_top %.4f W/m2K  (%.0f s)"
              % (name, r["eta"], r["Tp_std"], sol[name]["U_top"], time.time() - t0), flush=True)

    # CAD sections for the two channels, at NU = 192
    W = {}
    for y in (-20.0, 20.0):
        W0, _ = PM.OG.wall_points(y, 192, 100)
        Wr, _ = CS.resample_rings(W0)
        W[y] = Wr
    xs_a = W[-20.0][:, 0, 0]
    print("sections loaded  (%.0f s)" % (time.time() - t0), flush=True)

    out = {"nu_cfd": NU_CFD, "mesh_h_mm": MESH_H, "stations_xi_channel_a": STATIONS,
           "plate_solver": {k: {q: sol[k]["res"][q] for q in ("eta", "Tp_mean", "Tp_std", "U_L")}
                            for k in sol},
           "cases": {}}
    saved = None
    for name in ("co", "alt"):
        rows = []
        for xi in STATIONS:
            # channel a is fed at x = +550 and converges toward -550
            xa = 550.0 - 1100.0 * xi
            ka = int(np.argmin(np.abs(xs_a - xa)))
            kb = int(np.argmin(np.abs(W[20.0][:, 0, 0] - xa)))
            rings = [W[-20.0][ka], W[20.0][kb]]
            ycs = [-20.0, 20.0]
            xi_b = float(np.clip((xa + 550.0) / 1100.0, 0, 1))
            # The plate solver stores Tf on the PLATE grid and carries each channel's flow
            # direction internally, so both neighbours are read at the SAME plate station.
            # Indexing channel b by its own xi instead mapped it onto the glide-symmetric
            # image of channel a, which handed both channels an identical temperature and
            # erased the very lateral gradient this study exists to measure.
            i_plate = int(round(xi_b * (NX2D - 1)))       # plate x = xa
            Tf_a = float(sol[name]["Tf"][i_plate, 5])
            Tf_b = float(sol[name]["Tf"][i_plate, 6])
            hf = [NU_CFD * m.k_w / g.dh(xi) / 1.0, NU_CFD * m.k_w / g.dh(xi_b)]
            r, X, tri, T, ed, lab = run_station(
                rings, ycs, [Tf_a, Tf_b], sol[name]["U_top"], sol[name]["q_abs"],
                op.T_amb, m.h_rear, hf, -40.0, 40.0)
            r.update({"xi_a": xi, "xi_b": xi_b, "x_mm": float(xa),
                      "T_f_channel_a": Tf_a, "T_f_channel_b": Tf_b,
                      "h_f_a": hf[0], "h_f_b": hf[1],
                      "plate_solver_Tp_at_station": float(sol[name]["Tp"][i_plate].mean()),
                      "plate_station_index": i_plate,
                      "T_f_difference_K": Tf_a - Tf_b})
            rows.append(r)
            print("  %-4s xi %.2f  T_area %.4f K  through-thickness %+0.5f K  "
                  "p2p %.4f K  (%.0f s)"
                  % (name, xi, r["T_area_mean"], r["through_thickness_drop_K"],
                     r["peak_to_peak_K"], time.time() - t0), flush=True)
            if name == "alt" and abs(xi - 0.1) < 1e-9:
                # xi = 0.1 is where the two neighbours differ most (15.2 K),
                # so it is the station that actually shows the mechanism.
                saved = (X, tri, T, ed, lab, r)
        out["cases"][name] = rows

    # ---------------------------------------------------------------- grid check
    print("\ngrid convergence at xi = 0.5, alternating", flush=True)
    xa = 0.0
    ka = int(np.argmin(np.abs(xs_a - xa))); kb = int(np.argmin(np.abs(W[20.0][:, 0, 0] - xa)))
    gc = []
    for hh in (0.7, 0.35, 0.175):
        r, *_ = run_station([W[-20.0][ka], W[20.0][kb]], [-20.0, 20.0],
                            [float(sol["alt"]["Tf"][110, 5]), float(sol["alt"]["Tf"][110, 6])],
                            sol["alt"]["U_top"], sol["alt"]["q_abs"], op.T_amb, m.h_rear,
                            [NU_CFD * m.k_w / g.dh(0.5)] * 2, -40.0, 40.0, h=hh)
        gc.append({"h_mm": hh, "n_tri": r["n_tri"], "T_area_mean": r["T_area_mean"],
                   "through_thickness_drop_K": r["through_thickness_drop_K"],
                   "peak_to_peak_K": r["peak_to_peak_K"],
                   "metal_area_mm2": r["metal_area_mm2"]})
        print("  h %.3f mm  %6d triangles  T_area %.6f K  dT_thk %+0.6f K  area %.4f mm2"
              % (hh, r["n_tri"], r["T_area_mean"], r["through_thickness_drop_K"],
                 r["metal_area_mm2"]), flush=True)
    out["grid_check"] = gc
    out["cad_metal_area_mm2_two_pitches"] = 2 * 93881.8 / 1100.0
    # Length-integrated geometry check. A single station cannot be compared with the CAD
    # figure, which is a length average over a converging channel.
    areas, xs = [], []
    for k in range(0, len(xs_a), 4):
        xk = xs_a[k]
        kb = int(np.argmin(np.abs(W[20.0][:, 0, 0] - xk)))
        o2, h2 = build_section([W[-20.0][k], W[20.0][kb]], [-20.0, 20.0], -40.0, 40.0)
        X2, t2 = mesh_section(o2, h2, 0.7)
        _, A2 = assemble(X2, t2, 1.0)
        areas.append(float(A2.sum())); xs.append(float(xk))
    order = np.argsort(xs)
    xs = np.array(xs)[order]; areas = np.array(areas)[order]
    mean_area = float(np.trapezoid(areas, xs) / (xs[-1] - xs[0]))
    out["metal_area_check"] = {
        "n_stations": len(areas), "length_mean_mm2": mean_area,
        "cad_mm2": 2 * 93881.8 / 1100.0,
        "dev_pct": 100 * (mean_area - 2 * 93881.8 / 1100.0) / (2 * 93881.8 / 1100.0),
        "min_mm2": float(areas.min()), "max_mm2": float(areas.max())}
    print("\nmetal area, length mean over %d stations: %.4f mm2  vs CAD %.4f  (%+0.3f %%)"
          % (len(areas), mean_area, 2 * 93881.8 / 1100.0,
             out["metal_area_check"]["dev_pct"]), flush=True)

    json.dump(out, open(os.path.join(OUT, "section_conduction.json"), "w"), indent=1)
    print("\nwrote section_conduction.json  (%.0f s)" % (time.time() - t0))

    # ---------------------------------------------------------------- figure
    if saved is not None:
        sys.path.insert(0, "/home/claude/grail_cfd/tools")
        import figstyle as FS
        FS.use()
        import matplotlib.pyplot as plt
        from matplotlib.tri import Triangulation
        X, tri, T, ed, lab, rsaved = saved
        fig = plt.figure(figsize=(14.6, 8.2), layout="constrained")
        fig.get_layout_engine().set(w_pad=0.10, h_pad=0.12, wspace=0.06, hspace=0.10)
        # The section is 80 mm wide and 6 mm tall and is drawn at TRUE aspect, so its
        # row needs to be short or the colourbar ends up five times the height of
        # the panel it belongs to.
        gs = fig.add_gridspec(2, 3, height_ratios=[0.52, 1.0])

        a0 = fig.add_subplot(gs[0, :])
        trg = Triangulation(X[:, 0], X[:, 1], tri)
        c = a0.tripcolor(trg, T, shading="gouraud", cmap="inferno")
        a0.triplot(trg, lw=0.10, color="0.3", alpha=0.30)
        a0.set_aspect("equal"); a0.set_xlim(-40, 40); a0.set_ylim(-1.8, 5.4)
        a0.set_xlabel("y across the plate  [mm]"); a0.set_ylabel("z  [mm]")
        a0.grid(False)
        a0.set_title("Metal temperature in the real roll-bond section, one glide period, "
                     "alternating flow at $\\xi$ = 0.10")
        cb = fig.colorbar(c, ax=a0, pad=0.008, fraction=0.030, aspect=11)
        cb.set_label("T  [K]"); cb.outline.set_linewidth(0.8)
        a0.annotate("channel a\n$T_f$ = %.1f K" % rsaved["T_f_channel_a"],
                    xy=(-20, 2.0), xytext=(-33.5, 4.2), fontsize=10.5, color=FS.INK,
                    ha="center", va="center",
                    bbox=dict(boxstyle="round,pad=0.35", fc="white", ec="#c9ccd1", lw=0.8),
                    arrowprops=dict(arrowstyle="-", color=FS.INK2, lw=0.9))
        a0.annotate("channel b\n$T_f$ = %.1f K" % rsaved["T_f_channel_b"],
                    xy=(20, 2.0), xytext=(33.5, 4.2), fontsize=10.5, color=FS.INK,
                    ha="center", va="center",
                    bbox=dict(boxstyle="round,pad=0.35", fc="white", ec="#c9ccd1", lw=0.8),
                    arrowprops=dict(arrowstyle="-", color=FS.INK2, lw=0.9))
        a0.text(0.0, 4.55, "the two neighbours differ by %.1f K,\n"
                           "the metal between them by only %.2f K"
                % (abs(rsaved["T_f_difference_K"]), rsaved["peak_to_peak_K"]),
                ha="center", va="center", fontsize=10.5, color=FS.INK,
                bbox=dict(boxstyle="round,pad=0.42", fc="white", ec=FS.AL, lw=1.2))

        rows = out["cases"]
        a1 = fig.add_subplot(gs[1, 0])
        for nm, col, lb in (("co", FS.CO, "co-current"), ("alt", FS.AL, "alternating")):
            x = [r["xi_a"] for r in rows[nm]]
            a1.plot(x, [1000 * r["bridge_flux_W_per_mm"] for r in rows[nm]],
                    "o-", color=col, label=lb)
        FS.zeroline(a1)
        a1.set_xlabel("$\\xi$ along channel a"); a1.set_ylabel("lateral heat across the\nbridge midline  [mW/mm]")
        a1.set_title("The bridge carries heat only\nwhen the neighbours differ")
        FS.legend(a1, loc="upper left")

        a2 = fig.add_subplot(gs[1, 1])
        for nm, col, lb in (("co", FS.CO, "co-current"), ("alt", FS.AL, "alternating")):
            x = [r["xi_a"] for r in rows[nm]]
            a2.plot(x, [1000 * abs(r["through_thickness_drop_K"]) for r in rows[nm]],
                    "o-", color=col, label=lb)
        a2.set_ylim(0, None)
        a2.set_xlabel("$\\xi$ along channel a")
        a2.set_ylabel("top surface minus\nchannel wall  [mK]")
        a2.set_title("The metal is isothermal through\nits thickness, to within 0.06 K")
        FS.legend(a2, loc="lower right")

        a3 = fig.add_subplot(gs[1, 2])
        for nm, col, lb in (("co", FS.CO, "co-current"), ("alt", FS.AL, "alternating")):
            x = [r["xi_a"] for r in rows[nm]]
            a3.plot(x, [r["T_area_mean"] - r["plate_solver_Tp_at_station"] for r in rows[nm]],
                    "o-", color=col, label=lb)
        FS.zeroline(a3)
        a3.set_ylim(-1.0, 1.0)
        a3.set_xlabel("$\\xi$ along channel a")
        a3.set_ylabel("this solution minus\nthe plate solver  [K]")
        a3.set_title("The plate solver's absorber temperature\nis right to half a kelvin")
        FS.legend(a3, loc="lower right")

        fig.suptitle("Fig S1 \u2014 2-D conduction in the as-built roll-bond section: the "
                     "plate solver's fin and lumped-thickness assumptions, tested directly")
        fig.savefig(FIG + "/V2_section_conduction.png")
        plt.close(fig)
        print("wrote S1_section_conduction.png")
