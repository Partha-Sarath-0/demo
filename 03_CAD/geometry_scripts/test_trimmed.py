import gmsh, numpy as np, importlib.util, sys, time
spec = importlib.util.spec_from_file_location("T", "/home/claude/grail_cfd/02_geometry/tessellate.py")
T = importlib.util.module_from_spec(spec); sys.modules["T"] = T; spec.loader.exec_module(T)
spec2 = importlib.util.spec_from_file_location("TT", "/home/claude/grail_cfd/02_geometry/trimmed_tess.py")
TT = importlib.util.module_from_spec(spec2); sys.modules["TT"] = TT; spec2.loader.exec_module(TT)

T.start()
low, up, fluid = T.find_parts()
plate, _ = gmsh.model.occ.fuse(gmsh.model.occ.copy([(3, low)]), gmsh.model.occ.copy([(3, up)]))
box = gmsh.model.occ.addBox(-550.0, -80.0, -20.0, 1100.0, 80.0, 45.0)
sol, _ = gmsh.model.occ.intersect(plate, [(3, box)], removeObject=True, removeTool=True)
gmsh.model.occ.synchronize()
st = sol[0][1]

faces = [abs(ft) for fd, ft in gmsh.model.getBoundary([(3, st)], oriented=False)]
print("face   occ_area     tess_area     dev%      tris     t(s)")
tot_occ = tot_t = 0.0
allt = []
t00 = time.time()
for ft in faces:
    A = gmsh.model.occ.getMass(2, ft)
    t0 = time.time()
    xyz, simp = TT.tessellate_face(ft, 70, 70, 200)
    tr = TT.tris_of(xyz, simp)
    a = TT.area(tr)
    allt += tr
    tot_occ += A; tot_t += a
    print("%-5d %10.3f %13.3f %+8.3f%%  %7d  %6.1f" % (ft, A, a, 100 * (a - A) / A, len(tr), time.time() - t0))
print("\nTOTAL  %10.3f %13.3f %+8.3f%%  %7d  %6.1f s" % (tot_occ, tot_t, 100 * (tot_t - tot_occ) / tot_occ, len(allt), time.time() - t00))
V = T.signed_volume(allt)
print("closed volume from shell: %12.3f mm3   (OCC 187736.130, CAD 187817.190)" % abs(V))
print("dev vs CAD %+.4f %%" % (100 * (abs(V) - 187817.190) / 187817.190))
gmsh.finalize()
