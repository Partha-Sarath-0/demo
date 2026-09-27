import gmsh, numpy as np, importlib.util, sys
spec = importlib.util.spec_from_file_location("T", "/home/claude/grail_cfd/02_geometry/tessellate.py")
T = importlib.util.module_from_spec(spec); sys.modules["T"] = T; spec.loader.exec_module(T)
T.start()
low, up, fluid = T.find_parts()
plate, _ = gmsh.model.occ.fuse(gmsh.model.occ.copy([(3, low)]), gmsh.model.occ.copy([(3, up)]))
box = gmsh.model.occ.addBox(-550.0, -80.0, -20.0, 1100.0, 80.0, 45.0)
sol, _ = gmsh.model.occ.intersect(plate, [(3, box)], removeObject=True, removeTool=True)
gmsh.model.occ.synchronize()
st = sol[0][1]
print("face  type             occ_area    grid_area    dev%     inside/400   u_range            v_range")
for fd, ft in gmsh.model.getBoundary([(3, st)], oriented=False):
    typ = gmsh.model.getType(fd, ft)
    A = gmsh.model.occ.getMass(fd, ft)
    lo, hi = gmsh.model.getParametrizationBounds(2, ft)
    n = 0
    for u in np.linspace(lo[0], hi[0], 20):
        for v in np.linspace(lo[1], hi[1], 20):
            n += int(gmsh.model.isInside(2, ft, [u, v], parametric=True))
    P = T.eval_grid(ft, 120, 120)
    ga = T.area(T.tris_from_grid(P))
    print("%-5d %-16s %10.3f %12.3f %+8.2f%%   %4d/400   [%7.3f %7.3f] [%7.3f %7.3f]"
          % (ft, typ, A, ga, (100 * (ga - A) / A if A else 0), n, lo[0], hi[0], lo[1], hi[1]))
gmsh.finalize()
