import gmsh, json
gmsh.initialize(); gmsh.option.setNumber("General.Terminal", 0)
gmsh.option.setNumber("Geometry.OCCImportLabels", 1)
gmsh.merge("/home/claude/grail_cfd/01_cad/Grail_Collector_2.step")
gmsh.model.occ.synchronize()

ch = {}
for d,t in gmsh.model.getEntities(3):
    if gmsh.model.getEntityName(d,t).split('/')[-1]=='ABSORBER_FLUID_VOID_REF':
        bb=gmsh.model.getBoundingBox(d,t); ch[round((bb[1]+bb[4])/2,1)]=(t,bb)

T=0.02
def area_slab(tag,bb,x):
    cp=gmsh.model.occ.copy([(3,tag)])
    bx=gmsh.model.occ.addBox(x-T/2, bb[1]-1, bb[2]-1, T, (bb[4]-bb[1])+2, (bb[5]-bb[2])+2)
    o,_=gmsh.model.occ.intersect(cp,[(3,bx)],removeObject=True,removeTool=True)
    gmsh.model.occ.synchronize()
    v=sum(gmsh.model.occ.getMass(3,tt) for dd,tt in o if dd==3)
    gmsh.model.occ.remove(o,recursive=True); gmsh.model.occ.synchronize()
    return v/T

def perim_plane(tag,bb,x):
    cp=gmsh.model.occ.copy([(3,tag)])
    pl=gmsh.model.occ.addRectangle(-20,-20,0,40,40)
    gmsh.model.occ.rotate([(2,pl)],0,0,0,0,1,0,1.5707963267948966)
    gmsh.model.occ.translate([(2,pl)],x,(bb[1]+bb[4])/2,(bb[2]+bb[5])/2)
    gmsh.model.occ.synchronize()
    o,_=gmsh.model.occ.intersect([(2,pl)],cp,removeObject=True,removeTool=True)
    gmsh.model.occ.synchronize()
    P=0.0
    for dd,tt in o:
        if dd!=2: continue
        for cd,ct in gmsh.model.getBoundary([(dd,tt)],oriented=False):
            P+=gmsh.model.occ.getMass(1,ct)
    gmsh.model.occ.remove(o,recursive=True); gmsh.model.occ.synchronize()
    return P

# end-face areas straight off the solid (exact)
def endfaces(tag):
    r={}
    for fd,ft in gmsh.model.getBoundary([(3,tag)],oriented=False):
        bb=gmsh.model.getBoundingBox(fd,ft)
        if abs(bb[0]-bb[3])<1e-6 and abs(abs(round(bb[0],1))-550)<1e-3:
            r[round(bb[0],1)]=gmsh.model.occ.getMass(2,ft)
    return r

XI=[0.0,0.10,0.25,0.50,0.75,0.90,1.0]
res={}
for yc,name,xin,sgn in [(-60.0,'CH05',-550.0,1.0),(-20.0,'CH06',550.0,-1.0)]:
    tag,bb=ch[yc]; ef=endfaces(tag); rows=[]
    for xi in XI:
        x=xin+sgn*1100.0*xi
        if xi==0.0:   A=ef[xin];             P=perim_plane(tag,bb,xin+sgn*0.05)
        elif xi==1.0: A=ef[-xin];            P=perim_plane(tag,bb,-xin-sgn*0.05)
        else:         A=area_slab(tag,bb,x); P=perim_plane(tag,bb,x)
        rows.append({'xi':xi,'x':x,'A':A,'P':P,'Dh':4*A/P})
    res[name]=rows
json.dump(res,open('gate1_profile.json','w'),indent=1)

for name,rows in res.items():
    Dh0=rows[0]['Dh']
    print("\n%s   local inlet x=%+.1f" % (name, rows[0]['x']))
    print("   xi      x_mm      A_mm2      P_mm     Dh_mm    Dh/Dh_in   law(lam=1)   dev%")
    for r in rows:
        law=1-(1-0.540339)*r['xi']; rat=r['Dh']/Dh0
        print("  %4.2f  %8.1f  %9.4f  %8.4f  %8.5f  %8.6f  %8.6f  %+7.3f"
              % (r['xi'],r['x'],r['A'],r['P'],r['Dh'],rat,law,100*(rat-law)/law))
gmsh.finalize()
