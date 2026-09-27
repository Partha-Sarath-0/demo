"""
GRAIL — group B: the absorber upper sheet and the 12 fluid voids.

These carry the 1100 mm B-spline channel walls. Every B-spline face is evaluated directly
on its own parametric domain (the verified Gate-1 route: wall area +0.007 %, enclosed
volume -0.0015 % against CAD); the remaining Plane faces of the upper sheet are meshed by
gmsh with the same 20 mm cap used for the rest of the assembly.

SELECTIVE_COATING is excluded: it translated through STEP with a negative volume
(-111.8 mm3) and is represented in the model as a surface property, not a body (CR-03).

Output: 02_geometry/asm/groupB.npz   xyz, tris, owner   owner 0 = upper sheet,
        1..12 = fluid voids in ascending y.
"""
import gmsh, json, time, os, re
import numpy as np

STEP = "/home/claude/grail_cfd/01_cad/Grail_Collector_2.step"
OUT = "/home/claude/grail_cfd/02_geometry/asm"
SIZE_MAX, SIZE_MIN = 20.0, 4.0
NU_CH, NV_CH = 40, 56           # channel wall sampling (perimeter x axial)
H_SEC, H_AX = 1.2, 20.0         # target edge length across the section / along the plate

t0 = time.time()
gmsh.initialize(); gmsh.option.setNumber("General.Terminal", 0)
gmsh.option.setNumber("Geometry.OCCImportLabels", 1)
gmsh.merge(STEP); gmsh.model.occ.synchronize()

upper = coating = None
voids = {}
for d, t in gmsh.model.getEntities(3):
    leaf = gmsh.model.getEntityName(d, t).split('/')[-1]
    if leaf == 'ABSORBER_UPPER_SHEET':
        upper = t
    elif leaf == 'SELECTIVE_COATING':
        coating = t
    elif leaf == 'ABSORBER_FLUID_VOID_REF':
        bb = gmsh.model.getBoundingBox(d, t)
        voids[round((bb[1] + bb[4]) / 2, 1)] = t
ys = sorted(voids)
print("upper sheet %s   coating %s (excluded)   %d fluid voids at y = %s"
      % (upper, coating, len(ys), ys), flush=True)


def eval_grid(face, nu, nv):
    lo, hi = gmsh.model.getParametrizationBounds(2, face)
    us = np.linspace(lo[0], hi[0], nu); vs = np.linspace(lo[1], hi[1], nv)
    uv = np.empty(2 * nu * nv)
    uv[0::2] = np.tile(us, nv); uv[1::2] = np.repeat(vs, nu)
    return np.array(gmsh.model.getValue(2, face, uv)).reshape(nv, nu, 3)


def quad_tris(nv, nu, close_u):
    idx = np.arange(nv * nu).reshape(nv, nu)
    lim = nu if close_u else nu - 1
    i2 = np.roll(np.arange(nu), -1) if close_u else np.arange(1, nu)
    a = idx[:-1, :lim]; b = idx[:-1][:, i2][:, :lim]
    c = idx[1:][:, i2][:, :lim]; d = idx[1:, :lim]
    return np.vstack([np.column_stack([a.ravel(), b.ravel(), c.ravel()]),
                      np.column_stack([a.ravel(), c.ravel(), d.ravel()])])


def fan_cap(ring, flip=False):
    C = ring.mean(axis=0); n = len(ring)
    pts = np.vstack([ring, C[None, :]])
    i = np.arange(n); j = (i + 1) % n
    tri = np.column_stack([i, j, np.full(n, n)])
    if flip:
        tri = tri[:, ::-1]
    return pts, tri


XYZ, TRI, OWN, n0 = [], [], [], 0
stats = {"channels": []}

# ---------------------------------------------------------------- 12 fluid voids
for ci, y in enumerate(ys):
    v = voids[y]
    fs = gmsh.model.getBoundary([(3, v)], oriented=False)
    wall = [ft for fd, ft in fs if gmsh.model.getType(fd, ft) == 'BSpline surface'][0]
    P = eval_grid(wall, NU_CH + 1, NV_CH)[:, :NU_CH, :]          # closed ring in u
    tri = quad_tris(NV_CH, NU_CH, close_u=True)
    XYZ.append(P.reshape(-1, 3)); TRI.append(tri + n0); OWN.append(np.full(len(tri), ci + 1))
    n0 += NV_CH * NU_CH
    for ring, flip in ((P[0], True), (P[-1], False)):
        pts, ct = fan_cap(ring, flip)
        XYZ.append(pts); TRI.append(ct + n0); OWN.append(np.full(len(ct), ci + 1))
        n0 += len(pts)
    Q = P.reshape(-1, 3)[tri]
    A = 0.5 * np.linalg.norm(np.cross(Q[:, 1] - Q[:, 0], Q[:, 2] - Q[:, 0]), axis=1).sum()
    occV = gmsh.model.occ.getMass(3, v)
    stats["channels"].append({"y_mm": y, "tag": v, "wall_area_mm2": float(A),
                              "occ_volume_mm3": float(occV)})
    print("  channel %2d  y %+7.1f   wall %9.2f mm2   OCC volume %9.3f mm3"
          % (ci + 1, y, A, occV), flush=True)

# ---------------------------------------------------------------- upper sheet
fs = [abs(ft) for fd, ft in gmsh.model.getBoundary([(3, upper)], oriented=False)]
bsf = [f for f in fs if gmsh.model.getType(2, f) == 'BSpline surface']
plf = [f for f in fs if gmsh.model.getType(2, f) != 'BSpline surface']
print("upper sheet: %d faces  (%d B-spline, %d other)" % (len(fs), len(bsf), len(plf)),
      flush=True)
def adaptive(f, h_u, h_v, lo_n=6, hi_n=160):
    """Sample counts for face f from its own arc lengths, targeting edge h_u / h_v."""
    Q = eval_grid(f, 12, 12)
    lu = np.linalg.norm(np.diff(Q, axis=1), axis=2).sum(axis=1).max()
    lv = np.linalg.norm(np.diff(Q, axis=0), axis=2).sum(axis=0).max()
    return (int(np.clip(round(lu / h_u), lo_n, hi_n)) + 1,
            int(np.clip(round(lv / h_v), lo_n, hi_n)) + 1)


for f in bsf:
    # dome faces: u runs across the section (fine), v runs along the plate (coarse)
    nu, nv = adaptive(f, H_SEC, H_AX)
    P = eval_grid(f, nu, nv)
    closed = np.allclose(P[:, 0, :], P[:, -1, :], atol=1e-6)
    P = P[:, :-1, :] if closed else P
    tri = quad_tris(P.shape[0], P.shape[1], close_u=closed)
    XYZ.append(P.reshape(-1, 3)); TRI.append(tri + n0); OWN.append(np.zeros(len(tri), int))
    n0 += P.shape[0] * P.shape[1]

# the plane faces of the upper sheet, meshed by gmsh
gmsh.option.setNumber("Mesh.MeshSizeMax", SIZE_MAX)
gmsh.option.setNumber("Mesh.MeshSizeMin", SIZE_MIN)
gmsh.option.setNumber("Mesh.MeshSizeFromCurvature", 0)
gmsh.option.setNumber("Mesh.MeshSizeFromPoints", 0)
gmsh.option.setNumber("Mesh.Algorithm", 6)
gmsh.option.setNumber("Mesh.MeshOnlyVisible", 1)
skipped = []
for _ in range(30):
    gmsh.model.setVisibility(gmsh.model.getEntities(), 0)
    keep = [(2, f) for f in plf if f not in skipped]
    gmsh.model.setVisibility(keep, 1, recursive=True)
    try:
        gmsh.model.mesh.generate(2); break
    except Exception as e:
        m = re.search(r"surface (\d+)", str(e))
        if not m or int(m.group(1)) in skipped:
            raise
        skipped.append(int(m.group(1))); gmsh.model.mesh.clear()
        print("   deferred sheet face %d" % skipped[-1], flush=True)

nt, cd, _ = gmsh.model.mesh.getNodes()
gx = np.array(cd).reshape(-1, 3)
imap = np.zeros(int(max(nt)) + 1, dtype=np.int64)
imap[np.array(nt, dtype=np.int64)] = np.arange(len(nt))
sheet_tris = []
for f in plf:
    if f in skipped:
        continue
    et, _, en = gmsh.model.mesh.getElements(2, f)
    for k, ty in enumerate(et):
        if ty == 2:
            sheet_tris.append(imap[np.array(en[k], dtype=np.int64).reshape(-1, 3)])
sheet_tris = np.vstack(sheet_tris)
XYZ.append(gx); TRI.append(sheet_tris + n0); OWN.append(np.zeros(len(sheet_tris), int))
n0 += len(gx)
print("  upper-sheet plane faces: %d triangles, %d deferred faces"
      % (len(sheet_tris), len(skipped)), flush=True)
gmsh.finalize()

xyz = np.vstack(XYZ); tris = np.vstack(TRI).astype(np.int32); own = np.concatenate(OWN).astype(np.int32)
Q = xyz[tris]
A = 0.5 * np.linalg.norm(np.cross(Q[:, 1] - Q[:, 0], Q[:, 2] - Q[:, 0]), axis=1).sum()
print("group B : %d triangles  %d nodes  area %.1f mm2" % (len(tris), len(xyz), A))
os.makedirs(OUT, exist_ok=True)
np.savez_compressed(OUT + "/groupB.npz", xyz=xyz.astype(np.float32), tris=tris, owner=own)
stats.update({"ntri": int(len(tris)), "nnode": int(len(xyz)), "area_mm2": float(A),
              "nu_channel": NU_CH, "nv_channel": NV_CH,
              "coating_excluded": "SELECTIVE_COATING: negative STEP volume, surface property (CR-03)",
              "sheet_deferred_faces": skipped})
json.dump(stats, open(OUT + "/groupB.json", "w"), indent=1)
print("total %.1f s" % (time.time() - t0))
