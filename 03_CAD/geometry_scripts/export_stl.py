import gmsh, os, sys
YMIN, YMAX = -80.0, 0.0
CH = [(-60.0,'ch05'), (-20.0,'ch06')]
outdir = "/home/claude/grail_cfd/03_mesh/2ch/constant/triSurface"
os.makedirs(outdir, exist_ok=True)

gmsh.initialize(); gmsh.option.setNumber("General.Terminal",0)
gmsh.option.setNumber("Geometry.OCCImportLabels",1)
gmsh.merge("/home/claude/grail_cfd/01_cad/Grail_Collector_2.step")
gmsh.model.occ.synchronize()

low=up=None; fluid={}
for d,t in gmsh.model.getEntities(3):
    leaf=gmsh.model.getEntityName(d,t).split('/')[-1]
    if leaf=='ABSORBER_LOWER_SHEET': low=t
    elif leaf=='ABSORBER_UPPER_SHEET': up=t
    elif leaf=='ABSORBER_FLUID_VOID_REF':
        bb=gmsh.model.getBoundingBox(d,t); fluid[round((bb[1]+bb[4])/2,1)]=t

plate,_ = gmsh.model.occ.fuse(gmsh.model.occ.copy([(3,low)]), gmsh.model.occ.copy([(3,up)]))
box = gmsh.model.occ.addBox(-550.0, YMIN, -20.0, 1100.0, YMAX-YMIN, 45.0)
sol,_ = gmsh.model.occ.intersect(plate,[(3,box)],removeObject=True,removeTool=True)
fl = [(nm, gmsh.model.occ.copy([(3,fluid[yc])])[0][1]) for yc,nm in CH]
gmsh.model.occ.synchronize()

keep = [t for d,t in sol] + [t for nm,t in fl]
for d,t in gmsh.model.getEntities(3):
    if t not in keep:
        gmsh.model.occ.remove([(3,t)], recursive=True)
gmsh.model.occ.synchronize()
gmsh.model.occ.removeAllDuplicates(); gmsh.model.occ.synchronize()
print("volumes retained:", len(gmsh.model.getEntities(3)))
for d,t in gmsh.model.getEntities(3):
    bb=gmsh.model.getBoundingBox(d,t)
    print("  vol tag %-4d V=%12.3f  y[%8.2f %8.2f]" % (t, gmsh.model.occ.getMass(d,t), bb[1], bb[4]))

gmsh.option.setNumber("Mesh.MeshSizeMin", 0.12)
gmsh.option.setNumber("Mesh.MeshSizeMax", 2.5)
gmsh.option.setNumber("Mesh.MeshSizeFromCurvature", 0)
gmsh.option.setNumber("Mesh.MeshSizeExtendFromBoundary", 0)
gmsh.option.setNumber("Mesh.Algorithm", 1)
gmsh.option.setNumber("Mesh.StlOneSolidPerSurface", 0)

def write(vtag, path):
    gmsh.model.removePhysicalGroups()
    surf = [ft for fd,ft in gmsh.model.getBoundary([(3,vtag)], oriented=False)]
    gmsh.model.addPhysicalGroup(2, surf, 1)
    gmsh.model.mesh.clear()
    gmsh.model.mesh.generate(2)
    gmsh.write(path)
    els = gmsh.model.mesh.getElements(2)
    n = sum(len(x) for x in els[1]) if els[1] else 0
    print("  %-24s %8d triangles  %8.2f MB" % (os.path.basename(path), n, os.path.getsize(path)/1e6))

vol_sorted = sorted([(gmsh.model.occ.getMass(3,t), t) for d,t in gmsh.model.getEntities(3)], reverse=True)
solid_tag = vol_sorted[0][1]
print("solid tag:", solid_tag)
write(solid_tag, outdir+"/solid.stl")
for nm,t in fl:
    write(t, outdir+"/fluid_%s.stl" % nm)
gmsh.finalize()
