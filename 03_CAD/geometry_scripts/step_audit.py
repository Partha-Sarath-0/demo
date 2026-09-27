import gmsh, json, sys
gmsh.initialize()
gmsh.option.setNumber("General.Terminal", 0)
gmsh.option.setNumber("Geometry.OCCImportLabels", 1)
gmsh.merge("/home/claude/grail_cfd/01_cad/Grail_Collector_2.step")
vols = gmsh.model.getEntities(3)
print("solids imported:", len(vols))
rows = []
for dim, tag in vols:
    mass = gmsh.model.occ.getMass(dim, tag) if False else None
    bb = gmsh.model.getBoundingBox(dim, tag)
    name = gmsh.model.getEntityName(dim, tag)
    rows.append({"tag": tag, "name": name, "bb": bb})
gmsh.model.occ.synchronize()
for r in rows:
    r["vol_mm3"] = gmsh.model.occ.getMass(3, r["tag"]) 
json.dump(rows, open("step_solids.json", "w"), indent=1)
tot = sum(r["vol_mm3"] for r in rows)
print("total volume mm3: %.3f" % tot)
xs = [r["bb"] for r in rows]
print("overall bbox: x[%.3f %.3f] y[%.3f %.3f] z[%.3f %.3f]" % (
    min(b[0] for b in xs), max(b[3] for b in xs),
    min(b[1] for b in xs), max(b[4] for b in xs),
    min(b[2] for b in xs), max(b[5] for b in xs)))
named = [r for r in rows if r["name"]]
print("solids carrying a name:", len(named))
for r in rows[:5]:
    print("  tag%-4d %-40s vol=%12.3f" % (r["tag"], r["name"][:40], r["vol_mm3"]))
gmsh.finalize()
