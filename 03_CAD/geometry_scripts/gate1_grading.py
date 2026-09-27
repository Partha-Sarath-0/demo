import gmsh, json, math
gmsh.initialize(); gmsh.option.setNumber("General.Terminal", 0)
gmsh.option.setNumber("Geometry.OCCImportLabels", 1)
gmsh.merge("/home/claude/grail_cfd/01_cad/Grail_Collector_2.step")
gmsh.model.occ.synchronize()

# locate CH05 (y_c = -60) and CH06 (y_c = -20)
targets = {}
for d,t in gmsh.model.getEntities(3):
    if gmsh.model.getEntityName(d,t).split('/')[-1] == 'ABSORBER_FLUID_VOID_REF':
        bb = gmsh.model.getBoundingBox(d,t); yc = round((bb[1]+bb[4])/2,1)
        if yc in (-60.0,-20.0): targets[yc] = (t, bb)

XI = [0.0,0.10,0.25,0.50,0.75,0.90,1.0]
out = {}
for yc,(tag,bb) in sorted(targets.items()):
    res=[]
    for xi in XI:
        # local inlet is the LARGE end: CH05 large at -550, CH06 large at +550
        x = -550.0 + 1100.0*xi if yc==-60.0 else 550.0 - 1100.0*xi
        x = max(min(x, 549.999), -549.999)
        # thin slab of 0.02 mm, intersect with a COPY of the channel
        cp = gmsh.model.occ.copy([(3,tag)])
        box = gmsh.model.occ.addBox(x-0.01, bb[1]-1, bb[2]-1, 0.02, (bb[4]-bb[1])+2, (bb[5]-bb[2])+2)
        inter,_ = gmsh.model.occ.intersect(cp, [(3,box)], removeObject=True, removeTool=True)
        gmsh.model.occ.synchronize()
        vol = sum(gmsh.model.occ.getMass(3,tt) for dd,tt in inter if dd==3)
        A = vol/0.02
        # perimeter: lateral faces of the slab (those not normal to x)
        per = 0.0
        for dd,tt in inter:
            for fd,ft in gmsh.model.getBoundary([(dd,tt)], oriented=False):
                fbb = gmsh.model.getBoundingBox(fd,ft)
                if abs(fbb[0]-fbb[3]) > 1e-9:   # not an x-normal face
                    per += gmsh.model.occ.getMass(2,ft)/0.02
        Dh = 4*A/per if per else float('nan')
        res.append({'xi':xi,'x':x,'A':A,'P':per,'Dh':Dh})
        gmsh.model.occ.remove(inter, recursive=True); gmsh.model.occ.synchronize()
    out[yc]=res

for yc,res in out.items():
    ch = 'CH05' if yc==-60.0 else 'CH06'
    Dh0 = res[0]['Dh']
    print("\n%s  (local inlet at x=%.0f)" % (ch, res[0]['x']))
    print("   xi     x_mm       A_mm2      P_mm      Dh_mm     Dh/Dh_in   law(G=0.540339,lam=1)")
    for r in res:
        law = 1 - (1-0.540339)*r['xi']
        print("  %4.2f  %8.1f  %9.4f  %8.4f  %8.5f   %8.6f   %8.6f" % (r['xi'],r['x'],r['A'],r['P'],r['Dh'],r['Dh']/Dh0,law))
json.dump({str(k):v for k,v in out.items()}, open('gate1_grading.json','w'), indent=1)
gmsh.finalize()
