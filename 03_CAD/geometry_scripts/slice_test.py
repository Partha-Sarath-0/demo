"""Does slicing the long faces fix gmsh's pathological surface meshing?"""
import gmsh, numpy as np, importlib.util, sys, time
spec = importlib.util.spec_from_file_location("T", "/home/claude/grail_cfd/02_geometry/tessellate.py")
T = importlib.util.module_from_spec(spec); sys.modules["T"] = T; spec.loader.exec_module(T)

NSLICE = int(sys.argv[1]) if len(sys.argv) > 1 else 20
T.start()
low, up, fluid = T.find_parts()
plate, _ = gmsh.model.occ.fuse(gmsh.model.occ.copy([(3, low)]), gmsh.model.occ.copy([(3, up)]))
box = gmsh.model.occ.addBox(-550.0, -80.0, -20.0, 1100.0, 80.0, 45.0)
sol, _ = gmsh.model.occ.intersect(plate, [(3, box)], removeObject=True, removeTool=True)
gmsh.model.occ.synchronize()

t0 = time.time()
tools = []
for x in np.linspace(-550.0, 550.0, NSLICE + 1)[1:-1]:
    p = gmsh.model.occ.addRectangle(-200, -200, 0, 400, 400)
    gmsh.model.occ.rotate([(2, p)], 0, 0, 0, 0, 1, 0, np.pi / 2)
    gmsh.model.occ.translate([(2, p)], x, -40.0, 2.0)
    tools.append((2, p))
frag, _ = gmsh.model.occ.fragment(sol, tools)
gmsh.model.occ.synchronize()
vols = [(d, t) for d, t in gmsh.model.getEntities(3)]
print("fragment into %d pieces: %.1fs" % (len(vols), time.time() - t0))
tot = sum(gmsh.model.occ.getMass(3, t) for d, t in vols)
print("total volume after slicing %.3f  (was 187736.130)" % tot)

# drop leftover surface pieces outside the solid
for d, t in gmsh.model.getEntities(2):
    if not gmsh.model.getBoundary([(2, t)], oriented=False):
        pass
allf = gmsh.model.getEntities(2)
print("faces in model: %d" % len(allf))

gmsh.option.setNumber("Mesh.MeshSizeMin", 0.4)
gmsh.option.setNumber("Mesh.MeshSizeMax", 4.0)
gmsh.option.setNumber("Mesh.MeshSizeFromCurvature", 12)
gmsh.option.setNumber("Mesh.MeshSizeExtendFromBoundary", 0)
gmsh.option.setNumber("Mesh.Algorithm", 5)

surf = set()
for d, t in vols:
    for fd, ft in gmsh.model.getBoundary([(d, t)], oriented=False):
        surf.add(abs(ft))
gmsh.model.removePhysicalGroups()
gmsh.model.addPhysicalGroup(2, sorted(surf), 1)
print("meshing %d faces ..." % len(surf))
t0 = time.time()
gmsh.model.mesh.generate(2)
el = gmsh.model.mesh.getElements(2)
print("SURFACE MESH: %.1fs   %d triangles" % (time.time() - t0, sum(len(x) for x in el[1])))
gmsh.write("/home/claude/grail_cfd/02_geometry/solid_sliced.stl")
gmsh.finalize()
