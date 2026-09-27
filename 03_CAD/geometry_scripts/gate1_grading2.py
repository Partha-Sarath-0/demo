import gmsh, json
gmsh.initialize(); gmsh.option.setNumber("General.Terminal", 0)
gmsh.option.setNumber("Geometry.OCCImportLabels", 1)
gmsh.merge("/home/claude/grail_cfd/01_cad/Grail_Collector_2.step")
gmsh.model.occ.synchronize()

targets = {}
for d,t in gmsh.model.getEntities(3):
    if gmsh.model.getEntityName(d,t).split('/')[-1] == 'ABSORBER_FLUID_VOID_REF':
        bb = gmsh.model.getBoundingBox(d,t); yc = round((bb[1]+bb[4])/2,1)
        if yc in (-60.0,-20.0): targets[yc] = (t, bb)

def section(tag, bb, x):
    """Intersect the solid with a plane at x; return (area, perimeter)."""
    cp = gmsh.model.occ.copy([(3,tag)])
    dy = (bb[4]-bb[1]); dz = (bb[5]-bb[2])
    pl = gmsh.model.occ.addRectangle(bb[1]-dy, bb[2]-dz, x, 3*dy, 3*dz)   # in y-z at const x
    gmsh.model.occ.rotate([(2,pl)], 0,0,x, 0,1,0, 0)  # addRectangle is in xy-plane -> rotate
    gmsh.model.occ.synchronize()
    # build the plane properly instead: rectangle in XY then rotate about Y by 90deg
    gmsh.model.occ.remove([(2,pl)], recursive=True)
    pl = gmsh.model.occ.addRectangle(-1.5*dz, bb[1]-dy, 0, 3*dz, 3*dy)    # x'=z, y'=y
    gmsh.model.occ.rotate([(2,pl)], 0,0,0, 0,1,0, 1.5707963267948966)
    gmsh.model.occ.translate([(2,pl)], x, 0, 0)
    gmsh.model.occ.synchronize()
    out,_ = gmsh.model.occ.intersect([(2,pl)], cp, removeObject=True, removeTool=True)
    gmsh.model.occ.synchronize()
    A = sum(gmsh.model.occ.getMass(2,tt) for dd,tt in out if dd==2)
    P = 0.0
    for dd,tt in out:
        if dd!=2: continue
        for cd,ct in gmsh.model.getBoundary([(dd,tt)], oriented=False):
            P += gmsh.model.occ.getMass(1,ct)
    gmsh.model.occ.remove(out, recursive=True); gmsh.model.occ.synchronize()
    return A,P

XI = [0.0,0.10,0.25,0.50,0.75,0.90,1.0]
EPS = 0.05
res_all={}
for yc,(tag,bb) in sorted(targets.items()):
    ch = 'CH05' if yc==-60.0 else 'CH06'
    x_in = -550.0 if yc==-60.0 else 550.0
    sgn = 1.0 if yc==-60.0 else -1.0
    rows=[]
    for xi in XI:
        x = x_in + sgn*1100.0*xi
        x = x_in + sgn*EPS if xi==0.0 else (x - sgn*EPS if xi==1.0 else x)
        A,P = section(tag,bb,x)
        rows.append({'xi':xi,'x':x,'A':A,'P':P,'Dh':4*A/P})
    res_all[ch]=rows
    Dh0=rows[0]['Dh']
    print("\n%s  local inlet x=%+.1f" % (ch,x_in))
    print("   xi      x_mm       A_mm2     P_mm      Dh_mm    Dh/Dh_in   law(lam=1)   dev%")
    for r in rows:
        law = 1-(1-0.540339)*r['xi']; rat=r['Dh']/Dh0
        print("  %4.2f  %9.2f  %9.4f  %8.4f  %8.5f  %8.6f  %8.6f  %+7.3f"
              % (r['xi'],r['x'],r['A'],r['P'],r['Dh'],rat,law,100*(rat-law)/law))
json.dump(res_all, open('gate1_grading.json','w'), indent=1)
gmsh.finalize()
