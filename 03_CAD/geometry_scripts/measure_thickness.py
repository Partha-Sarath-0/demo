"""Measure the true local metal thickness of the roll-bonded upper sheet.

For points on the channel inner wall, march outward along the surface normal and find
where the solid ends. Establishes whether a constant-thickness offset is defensible and,
if so, quantifies its error.
"""
import gmsh, numpy as np, importlib.util, sys
spec = importlib.util.spec_from_file_location("T", "/home/claude/grail_cfd/02_geometry/tessellate.py")
T = importlib.util.module_from_spec(spec); sys.modules["T"] = T; spec.loader.exec_module(T)

T.start()
low, up, fluid = T.find_parts()
# upper sheet only: the dome shell lives here
faces = gmsh.model.getBoundary([(3, up)], oriented=False)
print("upper sheet: %d faces, volume %.3f mm3" % (len(faces), gmsh.model.occ.getMass(3, up)))

ch = fluid[-60.0]
wf = [ft for fd, ft in gmsh.model.getBoundary([(3, ch)], oriented=False)
      if gmsh.model.getType(fd, ft) == 'BSpline surface'][0]
NU, NV = 64, 5
P = T.eval_grid(wf, NU + 1, NV)[:, :NU, :]

def outward_normal(ring, i):
    n = len(ring)
    t = ring[(i + 1) % n] - ring[(i - 1) % n]
    t /= np.linalg.norm(t)
    c = ring.mean(axis=0)
    r = ring[i] - c
    r -= np.dot(r, np.array([1.0, 0, 0])) * np.array([1.0, 0, 0])
    nvec = r - np.dot(r, t) * t
    ln = np.linalg.norm(nvec)
    return nvec / ln if ln > 1e-12 else np.array([0.0, 0.0, 1.0])

print("\nmarching outward from the channel wall into the upper sheet")
print(" station x(mm)   perimeter pts sampled   thickness: min    mean     max     std")
for k in range(NV):
    ring = P[k]
    ths = []
    for i in range(0, NU, 2):
        p = ring[i]
        if p[2] < 0.05:          # skip the flat bottom, it is the lower sheet interface
            continue
        nvec = outward_normal(ring, i)
        t_hit = None
        for d in np.arange(0.02, 3.0, 0.02):
            q = p + d * nvec
            try:
                ins = gmsh.model.isInside(3, up, [q[0], q[1], q[2]], parametric=False)
            except Exception:
                ins = 0
            if not ins:
                t_hit = d
                break
        if t_hit: ths.append(t_hit)
    ths = np.array(ths)
    if len(ths):
        print("  %8.1f          %3d           %8.3f %8.3f %8.3f %8.4f"
              % (ring[:, 0].mean(), len(ths), ths.min(), ths.mean(), ths.max(), ths.std()))
gmsh.finalize()
