"""Does the tessellated end-cap area converge to the CAD value or the OCC value?

CAD (Fusion, measured on the built solid):  inlet 28.0552   outlet 7.9200 mm2
OCC (gmsh getMass on the STEP face)      :  inlet 28.0652   outlet 7.8630 mm2

The wall area already converges to the OCC face area, so the SURFACE is faithful.
If the cap areas converge on the CAD numbers, then OCC's integration is the outlier
and correction CR-08 is wrong.
"""
import gmsh, numpy as np, importlib.util, sys

spec = importlib.util.spec_from_file_location("T", "/home/claude/grail_cfd/02_geometry/tessellate.py")
T = importlib.util.module_from_spec(spec); sys.modules["T"] = T; spec.loader.exec_module(T)

T.start()
low, up, fluid = T.find_parts()
tag = fluid[-60.0]
faces = gmsh.model.getBoundary([(3, tag)], oriented=False)
wall = [ft for fd, ft in faces if gmsh.model.getType(fd, ft) == 'BSpline surface'][0]
capA_occ = capB_occ = None
for fd, ft in faces:
    if gmsh.model.getType(fd, ft) == 'Plane':
        bb = gmsh.model.getBoundingBox(fd, ft)
        if bb[0] < 0: capA_occ = gmsh.model.occ.getMass(fd, ft)
        else:         capB_occ = gmsh.model.occ.getMass(fd, ft)

print("CAD  inlet 28.055200   outlet 7.920000")
print("OCC  inlet %9.6f   outlet %8.6f" % (capA_occ, capB_occ))
print()
print("  NU    inlet_area    dev_vs_CAD   dev_vs_OCC    outlet_area   dev_vs_CAD   dev_vs_OCC       Dh_in      Dh_out     G")
for NU in (96, 192, 288, 576, 1152, 2304):
    P = T.eval_grid(wall, NU + 1, 3)[:, :NU, :]
    ringA, ringB = P[0], P[-1]
    aA = T.area(T.fan_cap(ringA))
    aB = T.area(T.fan_cap(ringB))
    pA = np.linalg.norm(np.diff(np.vstack([ringA, ringA[:1]]), axis=0), axis=1).sum()
    pB = np.linalg.norm(np.diff(np.vstack([ringB, ringB[:1]]), axis=0), axis=1).sum()
    dhA, dhB = 4 * aA / pA, 4 * aB / pB
    print("%6d  %11.6f  %+10.4f%%  %+10.4f%%   %11.6f  %+10.4f%%  %+10.4f%%   %9.6f  %9.6f  %8.6f"
          % (NU, aA, 100*(aA-28.0552)/28.0552, 100*(aA-capA_occ)/capA_occ,
             aB, 100*(aB-7.92)/7.92, 100*(aB-capB_occ)/capB_occ, dhA, dhB, dhB/dhA))
gmsh.finalize()
