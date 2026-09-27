import gmsh, numpy as np, importlib.util, sys, time
spec = importlib.util.spec_from_file_location("T", "/home/claude/grail_cfd/02_geometry/tessellate.py")
T = importlib.util.module_from_spec(spec); sys.modules["T"] = T; spec.loader.exec_module(T)

T.start()
low, up, fluid = T.find_parts()
plate, _ = gmsh.model.occ.fuse(gmsh.model.occ.copy([(3, low)]), gmsh.model.occ.copy([(3, up)]))
box = gmsh.model.occ.addBox(-550.0, -80.0, -20.0, 1100.0, 80.0, 45.0)
sol, _ = gmsh.model.occ.intersect(plate, [(3, box)], removeObject=True, removeTool=True)
gmsh.model.occ.synchronize()
st = sol[0][1]
print("solid volume %.3f" % gmsh.model.occ.getMass(3, st))
faces = gmsh.model.getBoundary([(3, st)], oriented=False)
print("\n%d faces" % len(faces))
print("tag    type              area          x[min max]         y[min max]         z[min max]")
for fd, ft in faces:
    bb = gmsh.model.getBoundingBox(fd, ft)
    print("%-6d %-17s %11.3f  [%8.1f %8.1f] [%8.2f %8.2f] [%7.3f %7.3f]"
          % (ft, gmsh.model.getType(fd, ft), gmsh.model.occ.getMass(fd, ft),
             bb[0], bb[3], bb[1], bb[4], bb[2], bb[5]))

# is the trim test available and fast?
bs = [ft for fd, ft in faces if gmsh.model.getType(fd, ft) == 'BSpline surface']
f0 = bs[0]
lo, hi = gmsh.model.getParametrizationBounds(2, f0)
print("\nB-spline face %d param bounds u[%.4f %.4f] v[%.4f %.4f]" % (f0, lo[0], hi[0], lo[1], hi[1]))
t0 = time.time()
n = 0
try:
    for u in np.linspace(lo[0], hi[0], 20):
        for v in np.linspace(lo[1], hi[1], 20):
            n += int(gmsh.model.isInside(2, f0, [u, v], parametric=True))
    print("isInside: %d/400 inside, %.3fs" % (n, time.time() - t0))
except Exception as e:
    print("isInside unavailable:", str(e)[:120])
gmsh.finalize()
