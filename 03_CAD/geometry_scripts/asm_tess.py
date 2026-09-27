"""
GRAIL — assembly-level surface tessellation of the CORRECTED CAD (group A).

Group A = the 115 solids whose faces are all Plane or Cylinder. gmsh's own 2-D mesher
handles these exactly and quickly, with a 20 mm edge cap.
Group B = ABSORBER_UPPER_SHEET, the 12 ABSORBER_FLUID_VOID_REF bodies and SELECTIVE_COATING,
which carry the 1100 mm B-spline channel walls gmsh cannot mesh
(14_provenance/gate2_mesh_strategy.md). Those are built by direct NURBS evaluation in
asm_absorber.py. Group B solids are removed from the model here before meshing.

Output: 02_geometry/asm/groupA.npz  (xyz, tris, owner)  + groupA.json
"""
import gmsh, json, time, os
import numpy as np

STEP = "/home/claude/grail_cfd/01_cad/Grail_Collector_2.step"
OUT = "/home/claude/grail_cfd/02_geometry/asm"
os.makedirs(OUT, exist_ok=True)
SIZE_MAX, SIZE_MIN = 20.0, 2.0

t0 = time.time()
gmsh.initialize()
gmsh.option.setNumber("General.Terminal", 0)
gmsh.option.setNumber("Geometry.OCCImportLabels", 1)
gmsh.merge(STEP)
gmsh.model.occ.synchronize()

bs = {t for d, t in gmsh.model.getEntities(2) if gmsh.model.getType(d, t) == 'BSpline surface'}
groupA, groupB = [], []
for d, t in gmsh.model.getEntities(3):
    nm = gmsh.model.getEntityName(d, t)
    fs = {abs(ft) for fd, ft in gmsh.model.getBoundary([(d, t)], oriented=False)}
    (groupB if (bs & fs) else groupA).append((t, nm, sorted(fs)))
print("group A %d solids   group B %d solids" % (len(groupA), len(groupB)), flush=True)

gmsh.model.occ.remove([(3, t) for t, _, _ in groupB], recursive=True)
gmsh.model.occ.synchronize()
left = {t for d, t in gmsh.model.getEntities(2)}
assert not (left & bs), "B-spline faces survived removal"
print("after removal: %d solids, %d faces (%.1f s)"
      % (len(gmsh.model.getEntities(3)), len(left), time.time() - t0), flush=True)

gmsh.option.setNumber("Mesh.MeshSizeMax", SIZE_MAX)
gmsh.option.setNumber("Mesh.MeshSizeMin", SIZE_MIN)
gmsh.option.setNumber("Mesh.MeshSizeFromCurvature", 12)
gmsh.option.setNumber("Mesh.Algorithm", 6)
gmsh.option.setNumber("Mesh.MeshOnlyVisible", 1)

# Mesh only the faces gmsh can handle. A full (periodic) cylinder face carrying many
# trimmed ports defeats the 2-D mesher; those faces are hidden here and rebuilt by
# direct parametric evaluation in asm_fallback.py. Nothing is approximated away: the
# failing faces are recorded by tag.
import re
skipped = []
for _ in range(40):
    gmsh.model.setVisibility(gmsh.model.getEntities(), 1, recursive=False)
    for f in skipped:
        gmsh.model.setVisibility([(2, f)], 0)
    try:
        gmsh.model.mesh.generate(2)
        break
    except Exception as e:
        m = re.search(r"surface (\d+)", str(e))
        if not m:
            raise
        bad = int(m.group(1))
        if bad in skipped:
            raise
        skipped.append(bad)
        gmsh.model.mesh.clear()
        print("   deferred face %d : %s" % (bad, str(e)[:60]), flush=True)
print("2-D mesh done, %d faces deferred (%.1f s)" % (len(skipped), time.time() - t0), flush=True)

nodeTags, coord, _ = gmsh.model.mesh.getNodes()
xyz = np.array(coord).reshape(-1, 3)
imap = np.zeros(int(max(nodeTags)) + 1, dtype=np.int64)
imap[np.array(nodeTags, dtype=np.int64)] = np.arange(len(nodeTags))

face_tris = {}
for d, f in gmsh.model.getEntities(2):
    et, _, en = gmsh.model.mesh.getElements(2, f)
    for k, ty in enumerate(et):
        if ty == 2:
            face_tris[f] = imap[np.array(en[k], dtype=np.int64).reshape(-1, 3)].astype(np.int32)

tris, sol_index = [], []
for t, nm, fs in groupA:
    cnt = 0
    for f in fs:
        T = face_tris.get(f)
        if T is not None and len(T):
            tris.append(T); cnt += len(T)
    sol_index.append({"tag": t, "name": nm, "ntri": cnt})
tris = np.vstack(tris)
owner = np.concatenate([np.full(s["ntri"], i, np.int32) for i, s in enumerate(sol_index)])

P = xyz[tris]
area = 0.5 * np.linalg.norm(np.cross(P[:, 1] - P[:, 0], P[:, 2] - P[:, 0]), axis=1).sum()
print("group A : %d triangles   %d nodes   area %.1f mm2 = %.4f m2"
      % (len(tris), len(xyz), area, area / 1e6))

np.savez_compressed(OUT + "/groupA.npz", xyz=xyz.astype(np.float32), tris=tris, owner=owner)
json.dump({"solids": sol_index, "ntri": int(len(tris)), "nnode": int(len(xyz)),
           "area_mm2": float(area), "size_max_mm": SIZE_MAX, "size_min_mm": SIZE_MIN,
           "deferred_faces": skipped,
           "groupB": [{"tag": t, "name": n} for t, n, _ in groupB]},
          open(OUT + "/groupA.json", "w"), indent=1)
gmsh.finalize()
print("total %.1f s" % (time.time() - t0))
