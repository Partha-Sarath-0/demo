import gmsh, numpy as np, time

gmsh.initialize(); gmsh.option.setNumber("General.Terminal", 0)
gmsh.option.setNumber("Geometry.OCCImportLabels", 1)
gmsh.merge("/home/claude/grail_cfd/01_cad/Grail_Collector_2.step")
gmsh.model.occ.synchronize()

fluid = {}
for d, t in gmsh.model.getEntities(3):
    if gmsh.model.getEntityName(d, t).split('/')[-1] == 'ABSORBER_FLUID_VOID_REF':
        bb = gmsh.model.getBoundingBox(d, t); fluid[round((bb[1]+bb[4])/2, 1)] = t

tag = fluid[-60.0]
faces = gmsh.model.getBoundary([(3, tag)], oriented=False)
print("CH05 faces:")
for fd, ft in faces:
    typ = gmsh.model.getType(fd, ft)
    bb = gmsh.model.getBoundingBox(fd, ft)
    print("  face %-5d %-18s x[%9.3f %9.3f] area=%.4f"
          % (ft, typ, bb[0], bb[3], gmsh.model.occ.getMass(fd, ft)))

wall = [ft for fd, ft in faces if gmsh.model.getType(fd, ft) == 'BSpline surface'][0]
lo, hi = gmsh.model.getParametrizationBounds(2, wall)
print("\nwall face tag %d  param bounds u[%.6f %.6f] v[%.6f %.6f]" % (wall, lo[0], hi[0], lo[1], hi[1]))

t0 = time.time()
NU, NV = 9, 9
us = np.linspace(lo[0], hi[0], NU)
vs = np.linspace(lo[1], hi[1], NV)
uv = np.array([[u, v] for v in vs for u in us]).flatten()
pts = np.array(gmsh.model.getValue(2, wall, uv)).reshape(-1, 3)
print("evaluated %d points in %.3fs" % (len(pts), time.time() - t0))
print("  x range %.3f .. %.3f" % (pts[:, 0].min(), pts[:, 0].max()))
print("  y range %.3f .. %.3f" % (pts[:, 1].min(), pts[:, 1].max()))
print("  z range %.3f .. %.3f" % (pts[:, 2].min(), pts[:, 2].max()))
print("\nfirst row (v=%.4f):" % vs[0])
for p in pts[:NU]:
    print("   %9.3f %9.4f %9.4f" % (p[0], p[1], p[2]))
print("\nWhich parameter runs along x?")
row0 = pts[:NU]; col0 = pts[0::NU]
print("  varying u  -> dx=%.3f dy=%.4f dz=%.4f" % (np.ptp(row0[:,0]), np.ptp(row0[:,1]), np.ptp(row0[:,2])))
print("  varying v  -> dx=%.3f dy=%.4f dz=%.4f" % (np.ptp(col0[:,0]), np.ptp(col0[:,1]), np.ptp(col0[:,2])))

t0 = time.time()
NU, NV = 200, 400
us = np.linspace(lo[0], hi[0], NU); vs = np.linspace(lo[1], hi[1], NV)
uv = np.array([[u, v] for v in vs for u in us]).flatten()
pts = np.array(gmsh.model.getValue(2, wall, uv)).reshape(-1, 3)
print("\nfull %dx%d = %d points in %.2fs" % (NU, NV, len(pts), time.time() - t0))
gmsh.finalize()
