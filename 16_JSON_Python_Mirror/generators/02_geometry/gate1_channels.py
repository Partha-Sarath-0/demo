import gmsh, json, math
gmsh.initialize(); gmsh.option.setNumber("General.Terminal", 0)
gmsh.option.setNumber("Geometry.OCCImportLabels", 1)
gmsh.merge("/home/claude/grail_cfd/01_cad/Grail_Collector_2.step")
gmsh.model.occ.synchronize()

vols = [(d,t) for d,t in gmsh.model.getEntities(3)]
fluid = []
for d,t in vols:
    if gmsh.model.getEntityName(d,t).split('/')[-1] == 'ABSORBER_FLUID_VOID_REF':
        bb = gmsh.model.getBoundingBox(d,t)
        fluid.append({'tag':t,'yc':round((bb[1]+bb[4])/2,3),'vol':gmsh.model.occ.getMass(3,t)})
fluid.sort(key=lambda r:r['yc'])
for i,f in enumerate(fluid): f['ch'] = i+1

CAD = {'vol':18643.963,'Ain':28.0552,'Aout':7.9200,'Dhin':5.199685,'Dhout':2.809592}
print("ch  y_c      volume        A(x=-550)   A(x=+550)   P(-550)   P(+550)   Dh(-550)  Dh(+550)  large_end")
rows=[]
for f in fluid:
    faces = gmsh.model.getBoundary([(3,f['tag'])], oriented=False)
    ends = {}
    for fd,ft in faces:
        bb = gmsh.model.getBoundingBox(fd,ft)
        if abs(bb[0]-bb[3]) < 1e-6:            # planar face normal to x
            x = round(bb[0],1)
            if abs(abs(x)-550) < 1e-3:
                a = gmsh.model.occ.getMass(2,ft)
                # perimeter from the face's bounding curves
                per = sum(gmsh.model.occ.getMass(1,ct) for cd,ct in
                          gmsh.model.getBoundary([(fd,ft)], oriented=False))
                ends[x] = (a, per)
    am,pm = ends.get(-550.0,(float('nan'),)*2)
    ap,pp = ends.get( 550.0,(float('nan'),)*2)
    dhm = 4*am/pm; dhp = 4*ap/pp
    large = '-550' if am>ap else '+550'
    print("CH%02d %7.1f %11.3f %11.4f %11.4f %9.4f %9.4f %9.6f %9.6f   %s"
          % (f['ch'], f['yc'], f['vol'], am, ap, pm, pp, dhm, dhp, large))
    rows.append({'ch':f['ch'],'tag':f['tag'],'yc':f['yc'],'vol':f['vol'],
                 'A_xm550':am,'A_xp550':ap,'P_xm550':pm,'P_xp550':pp,
                 'Dh_xm550':dhm,'Dh_xp550':dhp,'large_end':large})
json.dump(rows, open('gate1_channels.json','w'), indent=1)
gmsh.finalize()
