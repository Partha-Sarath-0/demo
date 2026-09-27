import gmsh, json, sys
gmsh.initialize(); gmsh.option.setNumber("General.Terminal", 0)
gmsh.option.setNumber("Geometry.OCCImportLabels", 1)
gmsh.merge("/home/claude/grail_cfd/01_cad/Grail_Collector_2.step")
gmsh.model.occ.synchronize()

low=up=None; fluid={}
for d,t in gmsh.model.getEntities(3):
    leaf = gmsh.model.getEntityName(d,t).split('/')[-1]
    if leaf=='ABSORBER_LOWER_SHEET': low=t
    elif leaf=='ABSORBER_UPPER_SHEET': up=t
    elif leaf=='ABSORBER_FLUID_VOID_REF':
        bb=gmsh.model.getBoundingBox(d,t); fluid[round((bb[1]+bb[4])/2,1)]=t
print("lower",low,"upper",up,"fluid channels",len(fluid))
print("lower vol %.3f  upper vol %.3f  sum %.3f" % (
    gmsh.model.occ.getMass(3,low), gmsh.model.occ.getMass(3,up),
    gmsh.model.occ.getMass(3,low)+gmsh.model.occ.getMass(3,up)))

def build(name, ymin, ymax, chans, path):
    plate,_ = gmsh.model.occ.fuse(gmsh.model.occ.copy([(3,low)]),
                                  gmsh.model.occ.copy([(3,up)]))
    gmsh.model.occ.synchronize()
    box = gmsh.model.occ.addBox(-550.0, ymin, -20.0, 1100.0, ymax-ymin, 45.0)
    sol,_ = gmsh.model.occ.intersect(plate, [(3,box)], removeObject=True, removeTool=True)
    gmsh.model.occ.synchronize()
    vsol = sum(gmsh.model.occ.getMass(3,t) for d,t in sol if d==3)
    fl=[]
    for yc in chans:
        c = gmsh.model.occ.copy([(3,fluid[yc])]); fl += c
    gmsh.model.occ.synchronize()
    vfl = [gmsh.model.occ.getMass(3,t) for d,t in fl]
    # periodic / cut faces on the solid at ymin and ymax
    faces={}
    for d,t in sol:
        for fd,ft in gmsh.model.getBoundary([(d,t)], oriented=False):
            bb=gmsh.model.getBoundingBox(fd,ft)
            if abs(bb[1]-bb[4])<1e-6:
                y=round(bb[1],3)
                if abs(y-ymin)<1e-6 or abs(y-ymax)<1e-6:
                    faces[y]=faces.get(y,0.0)+gmsh.model.occ.getMass(2,ft)
    gmsh.write(path)
    print("\n%s  -> %s" % (name, path))
    print("   solid volume  %.3f mm3   (%d solid(s))" % (vsol, len(sol)))
    print("   fluid volumes " + ", ".join("%.3f" % v for v in vfl))
    for y in sorted(faces): print("   face y=%+7.2f  area %.6f mm2" % (y, faces[y]))
    return {'name':name,'solid_vol':vsol,'n_solid':len(sol),'fluid_vols':vfl,'faces':faces}

r3 = build('STRIP_3CH', -80.0,  40.0, [-60.0,-20.0, 20.0], '/home/claude/grail_cfd/02_geometry/strip_3ch.step')
gmsh.clear(); gmsh.option.setNumber("Geometry.OCCImportLabels",1)
gmsh.merge("/home/claude/grail_cfd/01_cad/Grail_Collector_2.step"); gmsh.model.occ.synchronize()
low=up=None; fluid={}
for d,t in gmsh.model.getEntities(3):
    leaf = gmsh.model.getEntityName(d,t).split('/')[-1]
    if leaf=='ABSORBER_LOWER_SHEET': low=t
    elif leaf=='ABSORBER_UPPER_SHEET': up=t
    elif leaf=='ABSORBER_FLUID_VOID_REF':
        bb=gmsh.model.getBoundingBox(d,t); fluid[round((bb[1]+bb[4])/2,1)]=t
r2 = build('STRIP_2CH', -80.0, 0.0, [-60.0,-20.0], '/home/claude/grail_cfd/02_geometry/strip_2ch.step')
json.dump({'3ch':r3,'2ch':r2}, open('strip_build.json','w'), indent=1, default=str)
gmsh.finalize()
