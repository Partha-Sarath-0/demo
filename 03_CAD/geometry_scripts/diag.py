import gmsh, time
from collections import Counter

gmsh.initialize(); gmsh.option.setNumber("General.Terminal", 0)
gmsh.option.setNumber("Geometry.OCCImportLabels", 1)
gmsh.merge("/home/claude/grail_cfd/01_cad/Grail_Collector_2.step")
gmsh.model.occ.synchronize()

low = up = None; fluid = {}
for d, t in gmsh.model.getEntities(3):
    leaf = gmsh.model.getEntityName(d, t).split('/')[-1]
    if leaf == 'ABSORBER_LOWER_SHEET': low = t
    elif leaf == 'ABSORBER_UPPER_SHEET': up = t
    elif leaf == 'ABSORBER_FLUID_VOID_REF':
        bb = gmsh.model.getBoundingBox(d, t); fluid[round((bb[1]+bb[4])/2, 1)] = t

t0 = time.time()
plate, _ = gmsh.model.occ.fuse(gmsh.model.occ.copy([(3, low)]), gmsh.model.occ.copy([(3, up)]))
box = gmsh.model.occ.addBox(-550.0, -80.0, -20.0, 1100.0, 80.0, 45.0)
sol, _ = gmsh.model.occ.intersect(plate, [(3, box)], removeObject=True, removeTool=True)
gmsh.model.occ.synchronize()
print("boolean %.1fs" % (time.time() - t0))

st = sol[0][1]
faces = gmsh.model.getBoundary([(3, st)], oriented=False)
print("solid faces:", len(faces))
c = Counter()
for fd, ft in faces:
    c[gmsh.model.getType(fd, ft)] += 1
print("solid face types:", dict(c))

f = gmsh.model.occ.copy([(3, fluid[-60.0])])[0][1]
gmsh.model.occ.synchronize()
ffaces = gmsh.model.getBoundary([(3, f)], oriented=False)
cf = Counter()
for fd, ft in ffaces:
    cf[gmsh.model.getType(fd, ft)] += 1
print("fluid faces:", len(ffaces), dict(cf))

for d, t in gmsh.model.getEntities(3):
    if t not in (st, f):
        gmsh.model.occ.remove([(3, t)], recursive=True)
gmsh.model.occ.synchronize()

gmsh.option.setNumber("Mesh.MeshSizeMin", 1.0)
gmsh.option.setNumber("Mesh.MeshSizeMax", 5.0)
gmsh.option.setNumber("Mesh.MeshSizeFromCurvature", 0)
gmsh.option.setNumber("Mesh.MeshSizeExtendFromBoundary", 0)
gmsh.option.setNumber("Mesh.Algorithm", 5)

gmsh.model.removePhysicalGroups()
gmsh.model.addPhysicalGroup(2, [ft for fd, ft in ffaces], 1)
t0 = time.time(); gmsh.model.mesh.generate(2)
print("FLUID coarse 2D: %.1fs  tris=%d" % (time.time() - t0,
      sum(len(x) for x in gmsh.model.mesh.getElements(2)[1])))

gmsh.model.mesh.clear(); gmsh.model.removePhysicalGroups()
gmsh.model.addPhysicalGroup(2, [ft for fd, ft in faces], 1)
t0 = time.time(); gmsh.model.mesh.generate(2)
print("SOLID coarse 2D: %.1fs  tris=%d" % (time.time() - t0,
      sum(len(x) for x in gmsh.model.mesh.getElements(2)[1])))
gmsh.finalize()
