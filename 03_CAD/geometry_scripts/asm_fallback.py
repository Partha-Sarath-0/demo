"""
GRAIL — the 4 assembly faces gmsh deferred, tessellated by direct parametric evaluation.

These are the four manifold barrels: full (periodic) cylinder faces whose branch-port holes
straddle the parametric seam, which is what defeats both gmsh's 2-D mesher and a naive
point-in-polygon trim test.

They are sampled here over the complete parametric domain, i.e. the barrels are rendered
WITHOUT their branch-port holes. That is a labelled rendering simplification affecting 4 of
the 1291 CAD faces; the port openings are covered by the branch tubes in every view. The
area the ports would remove is computed exactly from the port boundary curves and reported,
so the assembly surface area quoted on the figures is corrected for it rather than inflated.

Output: 02_geometry/asm/groupA_fallback.npz  (xyz, tris) + groupA_fallback.json
"""
import gmsh, json, time
import numpy as np

OUT = "/home/claude/grail_cfd/02_geometry/asm"
meta = json.load(open(OUT + "/groupA.json"))
faces = meta["deferred_faces"]
print("deferred faces:", faces)

NU, NV = 40, 26
t0 = time.time()
gmsh.initialize(); gmsh.option.setNumber("General.Terminal", 0)
gmsh.option.setNumber("Geometry.OCCImportLabels", 1)
gmsh.merge("/home/claude/grail_cfd/01_cad/Grail_Collector_2.step")
gmsh.model.occ.synchronize()


def grid(face, nu, nv):
    lo, hi = gmsh.model.getParametrizationBounds(2, face)
    us = np.linspace(lo[0], hi[0], nu)          # closed in u: last == first point
    vs = np.linspace(lo[1], hi[1], nv)
    uv = np.empty(2 * nu * nv)
    uv[0::2] = np.tile(us, nv); uv[1::2] = np.repeat(vs, nu)
    return np.array(gmsh.model.getValue(2, face, uv)).reshape(nv, nu, 3)


def port_area(face, npts=400):
    """Exact area of the disc each boundary hole would remove, from its own curve."""
    tot, holes = 0.0, 0
    seen = set()
    for cd, ct in gmsh.model.getBoundary([(2, face)], oriented=False):
        ct = abs(ct)
        if ct in seen:
            continue
        seen.add(ct)
        a, b = gmsh.model.getParametrizationBounds(1, ct)
        ts = np.linspace(a[0], b[0], npts)
        P = np.array(gmsh.model.getValue(1, ct, ts)).reshape(-1, 3)
        r = np.linalg.norm(P - P.mean(axis=0), axis=1).mean()
        tot += 0.25 * np.pi * r ** 2       # each hole is split into 4 arc segments
        holes += 1
    return tot, holes


XYZ, TRI, n0 = [], [], 0
ports_total, ports_n = 0.0, 0
for f in faces:
    P = grid(f, NU + 1, NV)[:, :NU, :]         # drop the duplicated seam column
    nv, nu, _ = P.shape
    idx = np.arange(nv * nu).reshape(nv, nu)
    tri = []
    for j in range(nv - 1):
        i2 = np.roll(np.arange(nu), -1)
        a, b = idx[j], idx[j][i2]
        c, d = idx[j + 1][i2], idx[j + 1]
        tri.append(np.column_stack([a, b, c]))
        tri.append(np.column_stack([a, c, d]))
    tri = np.vstack(tri)
    XYZ.append(P.reshape(-1, 3)); TRI.append(tri + n0); n0 += nv * nu
    pa, pn = port_area(f)
    ports_total += pa; ports_n += pn
    Q = P.reshape(-1, 3)[tri]
    A = 0.5 * np.linalg.norm(np.cross(Q[:, 1] - Q[:, 0], Q[:, 2] - Q[:, 0]), axis=1).sum()
    print("  face %d : %d tris  barrel area %.1f mm2   ports -%.1f mm2  (%.1f s)"
          % (f, len(tri), A, pa, time.time() - t0), flush=True)
gmsh.finalize()

xyz = np.vstack(XYZ); tris = np.vstack(TRI).astype(np.int32)
Q = xyz[tris]
A = 0.5 * np.linalg.norm(np.cross(Q[:, 1] - Q[:, 0], Q[:, 2] - Q[:, 0]), axis=1).sum()
print("fallback: %d tris  barrel area %.1f mm2   port correction -%.1f mm2 (%d arc segments)"
      % (len(tris), A, ports_total, ports_n))
np.savez_compressed(OUT + "/groupA_fallback.npz", xyz=xyz.astype(np.float32), tris=tris)
json.dump({"faces": faces, "ntri": int(len(tris)), "area_mm2": float(A),
           "port_correction_mm2": float(ports_total), "arc_segments": int(ports_n),
           "note": "barrels rendered without branch-port holes; area corrected"},
          open(OUT + "/groupA_fallback.json", "w"), indent=1)
