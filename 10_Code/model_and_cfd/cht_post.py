"""
GRAIL — independent post-processing of the 3-D conjugate benchmark.

Everything is computed from the raw polyMesh and field files, not from solver-reported
integrals, so the energy balance is a genuine check and not the solver agreeing with itself.

    Q_u       = sum over each outlet patch of phi_f * cp * (T_f - T_in)     [mass-flux weighted]
    Q_abs     = q"_abs * A_top
    Q_top     = sum over solid_top faces of U_top (T_f - T_amb) A_f
    Q_rear    = sum over solid_bottom faces of h_rear (T_f - T_amb) A_f
    balance   = Q_abs - Q_u - Q_top - Q_rear

The absorber temperature statistics are taken on the solid_top faces, area-weighted. That is
the physical absorber surface. The reduced-order model's plate temperature is a lumped
through-thickness value, and the 2-D section study measured the through-thickness difference at
0.02 - 0.06 K, so the two are directly comparable at the level that matters here.
"""
import os, re, json, sys
import numpy as np

CP = 4180.0


def _foam_list(s, start):
    m = re.compile(r"(\d+)\s*\n?\(").search(s, start)
    return int(m.group(1)), m.end()


def read_points(path):
    s = open(path).read()
    n, i = _foam_list(s, s.index("FoamFile") + 50 if "FoamFile" in s else 0)
    body = s[i:]
    a = re.findall(r"\(\s*([-\d.eE+]+)\s+([-\d.eE+]+)\s+([-\d.eE+]+)\s*\)", body)[:n]
    return np.array(a, float)


def read_faces(path):
    s = open(path).read()
    n, i = _foam_list(s, s.index("FoamFile") + 50 if "FoamFile" in s else 0)
    out = []
    for m in re.finditer(r"(\d+)\(([\d\s]+)\)", s[i:]):
        out.append([int(x) for x in m.group(2).split()])
        if len(out) == n:
            break
    return out


def read_boundary(path):
    s = open(path).read()
    pats = {}
    for m in re.finditer(r"\n\s*([A-Za-z_][\w]*)\s*\n\s*\{([^}]*)\}", s):
        body = m.group(2)
        nf = re.search(r"nFaces\s+(\d+);", body)
        sf = re.search(r"startFace\s+(\d+);", body)
        if nf and sf:
            pats[m.group(1)] = (int(sf.group(1)), int(nf.group(1)))
    return pats


def face_area_centre(pts, face):
    p = pts[face]
    c0 = p.mean(0)
    area_vec = np.zeros(3); cen = np.zeros(3); atot = 0.0
    for k in range(len(face)):
        a, b = p[k], p[(k + 1) % len(face)]
        tri = 0.5 * np.cross(a - c0, b - c0)
        ta = np.linalg.norm(tri)
        area_vec += tri
        cen += ta * (a + b + c0) / 3.0
        atot += ta
    return np.linalg.norm(area_vec), (cen / atot if atot > 0 else c0)


def patch_geometry(mesh_dir, patch):
    pts = read_points(os.path.join(mesh_dir, "points"))
    faces = read_faces(os.path.join(mesh_dir, "faces"))
    start, n = read_boundary(os.path.join(mesh_dir, "boundary"))[patch]
    A = np.zeros(n); C = np.zeros((n, 3))
    for k in range(n):
        A[k], C[k] = face_area_centre(pts, faces[start + k])
    return A, C


def top_normal_z(mesh_dir, patch="solid_top"):
    pts = read_points(os.path.join(mesh_dir, "points"))
    faces = read_faces(os.path.join(mesh_dir, "faces"))
    start, n = read_boundary(os.path.join(mesh_dir, "boundary"))[patch]
    nz = np.zeros(n)
    for k in range(n):
        p = pts[faces[start + k]]; c0 = p.mean(0); v = np.zeros(3)
        for i in range(len(p)):
            v += 0.5 * np.cross(p[i] - c0, p[(i + 1) % len(p)] - c0)
        nz[k] = v[2] / np.linalg.norm(v)
    return nz


def read_owner(path):
    s = open(path).read()
    i = s.index("FoamFile") + 50 if "FoamFile" in s else 0
    n, j = _foam_list(s, i)
    return np.array(s[j:].split(")")[0].split()[:n], int)


def internal_scalar(field_path):
    s = open(field_path).read()
    m = re.search(r"internalField\s+nonuniform\s+List<scalar>\s*\n?(\d+)\s*\n?\(", s)
    if m:
        return np.array(s[m.end():].split(")")[0].split()[: int(m.group(1))], float)
    return float(re.search(r"internalField\s+uniform\s+([-\d.eE+]+);", s).group(1))


def face_values(field_path, mesh_dir, patch):
    """Patch face values; for patches that store none (zeroGradient), the owner-cell value,
    which is exactly what zeroGradient means."""
    try:
        return np.atleast_1d(boundary_values(field_path, patch))
    except ValueError:
        start, n = read_boundary(os.path.join(mesh_dir, "boundary"))[patch]
        own = read_owner(os.path.join(mesh_dir, "owner"))[start:start + n]
        v = internal_scalar(field_path)
        return np.full(n, v) if np.ndim(v) == 0 else v[own]


def boundary_values(field_path, patch):
    s = open(field_path).read()
    bi = s.index("boundaryField")
    m = re.search(r"\n\s*" + re.escape(patch) + r"\s*\n?\s*\{", s[bi:])
    if m is None:
        raise KeyError(patch)
    j = bi + m.end()
    depth, k = 1, j
    while depth:
        if s[k] == "{": depth += 1
        elif s[k] == "}": depth -= 1
        k += 1
    blk = s[j:k]
    mv = re.search(r"value\s+nonuniform\s+List<scalar>\s*\n?(\d+)\s*\n?\(([^)]*)\)", blk)
    if mv:
        return np.array(mv.group(2).split()[: int(mv.group(1))], float)
    mu = re.search(r"value\s+uniform\s+([-\d.eE+]+);", blk)
    if mu:
        return float(mu.group(1))
    raise ValueError("no value for %s in %s" % (patch, field_path))


def analyse(case, time, params, outlets=("outlet_a", "outlet_b")):
    q_abs, U_top, h_rear = params["q_abs"], params["U_top"], params["h_rear"]
    T_amb, T_in, G_T = params["T_amb"], params["T_in"], params["G_T"]
    fm = os.path.join(case, "constant/fluid/polyMesh")
    sm = os.path.join(case, "constant/solid/polyMesh")
    res = {"per_channel": {}}

    Qu = 0.0
    for pt in outlets:
        phi = np.atleast_1d(boundary_values(os.path.join(case, time, "fluid/phi"), pt))
        T = np.atleast_1d(boundary_values(os.path.join(case, time, "fluid/T"), pt))
        if T.size == 1: T = np.full(phi.size, float(T))
        mdot = phi.sum()
        Tb = float((phi * T).sum() / mdot)
        q = float(mdot * CP * (Tb - T_in))
        res["per_channel"][pt] = {"mdot": float(mdot), "T_out_bulk": Tb, "Q_u": q}
        Qu += q

    A_top, C_top = patch_geometry(sm, "solid_top")
    nz = top_normal_z(sm)
    A_bot, _ = patch_geometry(sm, "solid_bottom")
    Tt = np.atleast_1d(boundary_values(os.path.join(case, time, "solid/T"), "solid_top"))
    Tb_ = np.atleast_1d(boundary_values(os.path.join(case, time, "solid/T"), "solid_bottom"))

    # absorbed flux and top loss act per unit PLAN area: weight each face by n_z dA
    Aproj = A_top * nz
    Qabs = q_abs * Aproj.sum()
    Qtop = float((U_top * (Tt - T_amb) * Aproj).sum())
    Qrear = float((h_rear * (Tb_ - T_amb) * A_bot).sum())
    bal = Qabs - Qu - Qtop - Qrear

    # plate statistics on the absorber surface, weighted by PLAN area so they are directly
    # comparable with the reduced-order model's per-plan-area plate grid
    w = Aproj / Aproj.sum()
    Tm = float((w * Tt).sum())
    std = float(np.sqrt((w * (Tt - Tm) ** 2).sum()))

    res.update({
        "A_top_m2": float(A_top.sum()), "A_top_plan_m2": float(Aproj.sum()),
        "A_bottom_m2": float(A_bot.sum()),
        "Q_abs_W": Qabs, "Q_u_W": Qu, "Q_top_W": Qtop, "Q_rear_W": Qrear,
        "balance_W": bal, "balance_pct": 100 * bal / Qabs,
        "eta": Qu / (G_T * Aproj.sum()),
        "Tp_mean": Tm, "Tp_std": std,
        "Tp_max": float(Tt.max()), "Tp_min": float(Tt.min()),
        "Tp_spread": float(Tt.max() - Tt.min()),
        "n_top_faces": int(Tt.size),
    })
    return res


if __name__ == "__main__":
    case, time = sys.argv[1], sys.argv[2]
    params = {"q_abs": 519.1256, "U_top": 4.191176, "h_rear": 3.0,
              "T_amb": 298.15, "T_in": 300.0, "G_T": 800.0}
    r = analyse(case, time, params)
    print(json.dumps(r, indent=1))
