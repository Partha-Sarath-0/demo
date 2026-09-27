"""Probe: which assembly solids gmsh can surface-mesh quickly, and which need
direct NURBS evaluation. No geometry is modified."""
import gmsh, json, time, numpy as np, sys

STEP = "/home/claude/grail_cfd/01_cad/Grail_Collector_2.step"
gmsh.initialize()
gmsh.option.setNumber("General.Terminal", 0)
gmsh.option.setNumber("Geometry.OCCImportLabels", 1)
gmsh.merge(STEP)
gmsh.model.occ.synchronize()

solids = gmsh.model.getEntities(3)
print("solids", len(solids))

# classify every face
kinds = {}
bspline_faces = []
for d, t in gmsh.model.getEntities(2):
    k = gmsh.model.getType(d, t)
    kinds[k] = kinds.get(k, 0) + 1
    if k == 'BSpline surface':
        bspline_faces.append(t)
print("face types:", kinds)
print("bspline faces:", len(bspline_faces))

# which solids own a bspline face
bs = set(bspline_faces)
owners = []
for d, t in solids:
    fs = [abs(ft) for fd, ft in gmsh.model.getBoundary([(d, t)], oriented=False)]
    if bs & set(fs):
        owners.append((t, gmsh.model.getEntityName(d, t).split('/')[-1], len(fs)))
print("solids containing a BSpline face:", len(owners))
for o in owners[:20]:
    print("   ", o)
gmsh.finalize()
