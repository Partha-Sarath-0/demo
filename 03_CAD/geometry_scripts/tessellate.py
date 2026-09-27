"""
GRAIL CFD — exact surface tessellation by direct NURBS evaluation.

gmsh's 2-D mesher cannot tessellate the 1100 mm B-spline channel walls in reasonable
time (see 14_provenance/gate2_mesh_strategy.md). Every surface here is instead sampled
directly on its own parametric domain, which lands exactly on the CAD surface and takes
milliseconds.

Writes binary STL, one solid per named surface, for snappyHexMesh.
"""
import gmsh, numpy as np, struct, os, sys, json, time

STEP = "/home/claude/grail_cfd/01_cad/Grail_Collector_2.step"


def start():
    gmsh.initialize()
    gmsh.option.setNumber("General.Terminal", 0)
    gmsh.option.setNumber("Geometry.OCCImportLabels", 1)
    gmsh.merge(STEP)
    gmsh.model.occ.synchronize()


def find_parts():
    low = up = None
    fluid = {}
    for d, t in gmsh.model.getEntities(3):
        leaf = gmsh.model.getEntityName(d, t).split('/')[-1]
        if leaf == 'ABSORBER_LOWER_SHEET':
            low = t
        elif leaf == 'ABSORBER_UPPER_SHEET':
            up = t
        elif leaf == 'ABSORBER_FLUID_VOID_REF':
            bb = gmsh.model.getBoundingBox(d, t)
            fluid[round((bb[1] + bb[4]) / 2, 1)] = t
    return low, up, fluid


def eval_grid(face, nu, nv):
    """Sample a face on an nu x nv structured grid of its parametric domain."""
    lo, hi = gmsh.model.getParametrizationBounds(2, face)
    us = np.linspace(lo[0], hi[0], nu)
    vs = np.linspace(lo[1], hi[1], nv)
    uv = np.empty(2 * nu * nv)
    uv[0::2] = np.tile(us, nv)
    uv[1::2] = np.repeat(vs, nu)
    pts = np.array(gmsh.model.getValue(2, face, uv)).reshape(nv, nu, 3)
    return pts


def tris_from_grid(P, close_u=False):
    """Triangulate a structured point grid P[nv][nu][3]."""
    nv, nu, _ = P.shape
    tris = []
    ulim = nu if close_u else nu - 1
    for j in range(nv - 1):
        for i in range(ulim):
            i2 = (i + 1) % nu
            a, b, c, d = P[j, i], P[j, i2], P[j + 1, i2], P[j + 1, i]
            tris.append((a, b, c))
            tris.append((a, c, d))
    return tris


def fan_cap(ring, flip=False):
    """Triangulate a closed ring of points by fanning from its centroid."""
    C = ring.mean(axis=0)
    tris = []
    n = len(ring)
    for i in range(n):
        a, b = ring[i], ring[(i + 1) % n]
        tris.append((C, b, a) if flip else (C, a, b))
    return tris


def write_stl(path, named_tris):
    """Binary STL, but snappy prefers ASCII multi-solid for named regions."""
    with open(path, 'w') as f:
        for name, tris in named_tris:
            f.write("solid %s\n" % name)
            for a, b, c in tris:
                n = np.cross(b - a, c - a)
                ln = np.linalg.norm(n)
                n = n / ln if ln > 0 else np.array([0.0, 0.0, 1.0])
                f.write("  facet normal %.6e %.6e %.6e\n   outer loop\n" % tuple(n))
                for p in (a, b, c):
                    f.write("    vertex %.6e %.6e %.6e\n" % tuple(p))
                f.write("   endloop\n  endfacet\n")
            f.write("endsolid %s\n" % name)


def signed_volume(tris):
    v = 0.0
    for a, b, c in tris:
        v += np.dot(a, np.cross(b, c)) / 6.0
    return v


def area(tris):
    return sum(0.5 * np.linalg.norm(np.cross(b - a, c - a)) for a, b, c in tris)


def channel_surface(vol_tag, nu, nv):
    """Exact closed tessellation of one fluid channel: wall + two end caps."""
    faces = gmsh.model.getBoundary([(3, vol_tag)], oriented=False)
    wall = [ft for fd, ft in faces if gmsh.model.getType(fd, ft) == 'BSpline surface'][0]
    P = eval_grid(wall, nu + 1, nv)        # nu+1 so last column duplicates the first
    P = P[:, :nu, :]                       # drop the duplicate -> closed ring of nu points
    wall_tris = tris_from_grid(P, close_u=True)
    cap_a = fan_cap(P[0], flip=True)    # outward normal is -x
    cap_b = fan_cap(P[-1])              # outward normal is +x
    return wall, P, wall_tris, cap_a, cap_b


if __name__ == "__main__":
    NU = int(sys.argv[1]) if len(sys.argv) > 1 else 96
    NV = int(sys.argv[2]) if len(sys.argv) > 2 else 401
    outdir = "/home/claude/grail_cfd/03_mesh/2ch/constant/triSurface"
    os.makedirs(outdir, exist_ok=True)

    t0 = time.time()
    start()
    low, up, fluid = find_parts()
    print("STEP loaded %.1fs" % (time.time() - t0))

    report = {}
    for yc, name in [(-60.0, 'ch05'), (-20.0, 'ch06')]:
        t1 = time.time()
        wall, P, wt, ca, cb = channel_surface(fluid[yc], NU, NV)
        allt = wt + ca + cb
        V = signed_volume(allt)
        if V < 0:                       # mirrored channel: parameterisation runs the other way
            wt = [(a, c, b) for a, b, c in wt]
            ca = [(a, c, b) for a, b, c in ca]
            cb = [(a, c, b) for a, b, c in cb]
            allt = wt + ca + cb
            V = signed_volume(allt)
            print("   (orientation flipped: mirrored parameterisation)")
        Aw = area(wt)
        occV = gmsh.model.occ.getMass(3, fluid[yc])
        occA = gmsh.model.occ.getMass(2, wall)
        write_stl(os.path.join(outdir, "fluid_%s.stl" % name),
                  [("%s_wall" % name, wt),
                   ("%s_endA" % name, ca),
                   ("%s_endB" % name, cb)])
        print("\nfluid_%s.stl   %d triangles   %.2fs" % (name, len(allt), time.time() - t1))
        print("   closed volume  %12.3f mm3   OCC %12.3f   dev %+.4f %%"
              % (V, occV, 100 * (V - occV) / occV))
        print("   wall area      %12.3f mm2   OCC %12.3f   dev %+.4f %%"
              % (Aw, occA, 100 * (Aw - occA) / occA))
        report[name] = {"tris": len(allt), "V": V, "occV": occV, "A": Aw, "occA": occA}

    json.dump(report, open("/home/claude/grail_cfd/02_geometry/tessellate_report.json", "w"),
              indent=1)
    gmsh.finalize()
    print("\ntotal %.1fs" % (time.time() - t0))
