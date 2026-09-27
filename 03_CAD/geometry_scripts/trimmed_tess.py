"""
General tessellator for trimmed CAD faces, by direct evaluation.

For every face: sample its parametric domain on a grid, keep the points that lie inside
the trim, add the exact boundary-curve points, triangulate in (u,v) with Delaunay, reject
triangles whose centroid falls outside the trim, then map every vertex to 3-D with
gmsh.model.getValue. Lands exactly on the CAD surface and keeps the true trim edges, so
adjacent faces share identical boundary points and the assembled shell is watertight.
"""
import gmsh, numpy as np
from scipy.spatial import Delaunay


def face_loops(face, npts=200):
    """Ordered boundary points of a face in its own (u,v) parameter space."""
    loops = []
    for cd, ct in gmsh.model.getBoundary([(2, face)], oriented=False):
        ct = abs(ct)
        lo, hi = gmsh.model.getParametrizationBounds(1, ct)
        ts = np.linspace(lo[0], hi[0], npts)
        xyz = np.array(gmsh.model.getValue(1, ct, ts)).reshape(-1, 3)
        uv = np.array(gmsh.model.reparametrizeOnSurface(1, ct, ts, face)).reshape(-1, 2)
        loops.append(uv)
    return loops


def inside_mask(pts, loops):
    """Ray-casting point-in-polygon against every loop, XOR-combined (handles holes)."""
    inside = np.zeros(len(pts), dtype=bool)
    for uv in loops:
        x, y = pts[:, 0], pts[:, 1]
        res = np.zeros(len(pts), dtype=bool)
        n = len(uv)
        for i in range(n):
            x1, y1 = uv[i]
            x2, y2 = uv[(i + 1) % n]
            cond = ((y1 > y) != (y2 > y))
            with np.errstate(divide='ignore', invalid='ignore'):
                xin = (x2 - x1) * (y - y1) / (y2 - y1 + 1e-300) + x1
            res ^= cond & (x < xin)
        inside ^= res
    return inside


def tessellate_face(face, nu=80, nv=80, bnd=240):
    lo, hi = gmsh.model.getParametrizationBounds(2, face)
    loops = face_loops(face, bnd)
    us = np.linspace(lo[0], hi[0], nu)
    vs = np.linspace(lo[1], hi[1], nv)
    U, V = np.meshgrid(us, vs)
    grid = np.column_stack([U.ravel(), V.ravel()])
    keep = inside_mask(grid, loops)
    pts = np.vstack([np.vstack(loops), grid[keep]])
    # de-duplicate
    scale = np.ptp(pts, axis=0); scale[scale == 0] = 1.0
    _, idx = np.unique(np.round(pts / scale, 9), axis=0, return_index=True)
    pts = pts[np.sort(idx)]
    tri = Delaunay(pts)
    cent = pts[tri.simplices].mean(axis=1)
    good = inside_mask(cent, loops)
    simp = tri.simplices[good]
    uvflat = pts.ravel()
    xyz = np.array(gmsh.model.getValue(2, face, uvflat)).reshape(-1, 3)
    return xyz, simp


def tris_of(xyz, simp):
    return [(xyz[a], xyz[b], xyz[c]) for a, b, c in simp]


def area(tris):
    return sum(0.5 * np.linalg.norm(np.cross(b - a, c - a)) for a, b, c in tris)
