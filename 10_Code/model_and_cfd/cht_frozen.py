"""
GRAIL — 3-D conjugate benchmark by one-way (frozen-flow) coupling.

WHY THIS IS EXACT, NOT A WORKAROUND
The benchmark uses constant rho, mu, k and cp in the fluid (rhoConst, const transport). The
momentum and continuity equations then contain no temperature at all, so the velocity field is
independent of the energy solution. Solving the flow first and the conjugate energy second on
that flow gives the same steady solution as a fully coupled solve. It would NOT be exact with
temperature-dependent properties, and this route must not be used for such a case.

WHY IT IS NEEDED
chtMultiRegionSimpleFoam's fluid region uses the buoyant p_rgh formulation, which diverges on
this mesh family (proven in 14_provenance/cht_rootcause_record.md): buoyantSimpleFoam diverges
identically on the fluid region alone and on the validated single-channel baseline mesh, while
simpleFoam converges on both. The failure is in reconstructing cell velocity from face fluxes
on strongly anisotropic cells, not in the conjugate coupling.

PIPELINE
  1. simpleFoam solves the flow on the fluid mesh (incompressible, kinematic p).
  2. Its volumetric face flux phi [m3/s] is converted to mass flux x rho [kg/s], and U is copied.
  3. chtMultiRegionSimpleFoam runs with `frozenFlow yes` in the fluid region's SIMPLE dict, so
     only the energy equation is solved in the fluid and the solid.

`frozenFlow` was confirmed present in the installed v1912 binary before use. Whether the solver
reads the supplied phi rather than rebuilding it from U is verified empirically after the run by
comparing the written phi with the supplied one.
"""
import os, re, shutil, sys
import numpy as np

RHO = 997.0


def _scale_numbers_in_list(txt, fac):
    """Scale every number inside a nonuniform List<scalar> body."""
    def rep(m):
        head, body = m.group(1), m.group(2)
        vals = np.array(body.split(), float) * fac
        return head + "\n".join("%.17g" % v for v in vals) + "\n)"
    return re.sub(r"(nonuniform\s+List<scalar>\s*\n?\d+\s*\n?\()\s*([^)]*)\)", rep, txt, flags=re.S)


def volumetric_to_mass_flux(src, dst):
    s = open(src).read()
    assert "[0 3 -1 0 0 0 0]" in s, "expected a volumetric flux [m3/s]"
    s = s.replace("[0 3 -1 0 0 0 0]", "[1 0 -1 0 0 0 0]")
    s = _scale_numbers_in_list(s, RHO)
    # uniform boundary values (e.g. 'value uniform 0;' on walls) are zero, scaling is a no-op
    def rep_uni(m):
        return "%s%.17g;" % (m.group(1), float(m.group(2)) * RHO)
    s = re.sub(r"(value\s+uniform\s+)([-\d.eE+]+);", rep_uni, s)
    open(dst, "w").write(s)


def projected_top_h(case, U_top):
    """Per-face h on solid_top so absorbed flux and top loss act per unit PLAN area.

    The solid_top patch follows the domed upper sheet, so its true area (0.098723 m2 on the
    2-channel strip) is 12.2 % larger than the plan area (0.088 m2). Sunlight is intercepted per
    unit plan area, and the TIM and glazing sit parallel to the plate, so a face tilted by theta
    must carry q"cos(theta) dA, i.e. h_face = U_top * n_z. Summing n_z dA recovers the plan area
    exactly. The earlier case applied q" per unit CURVED area and over-applied solar input by
    12.2 %. Ta_eff = T_amb + q"/U_top is unchanged, so h (Ta_eff - T) = n_z [q" - U_top (T - T_amb)].
    """
    sys.path.insert(0, os.path.dirname(__file__))
    import cht_post as P
    sm = os.path.join(case, "constant/solid/polyMesh")
    pts = P.read_points(os.path.join(sm, "points"))
    faces = P.read_faces(os.path.join(sm, "faces"))
    st, n = P.read_boundary(os.path.join(sm, "boundary"))["solid_top"]
    nz = np.zeros(n); A = np.zeros(n)
    for k in range(n):
        p = pts[faces[st + k]]; c0 = p.mean(0); v = np.zeros(3)
        for i in range(len(p)):
            v += 0.5 * np.cross(p[i] - c0, p[(i + 1) % len(p)] - c0)
        A[k] = np.linalg.norm(v); nz[k] = v[2] / A[k]
    assert (nz > 0).all(), "solid_top has a downward-facing face"
    # the flat solid_bottom IS the plan area; the projected top must reproduce it
    A_bot, _ = P.patch_geometry(sm, "solid_bottom")
    assert abs((nz * A).sum() - A_bot.sum()) < 1e-6 * A_bot.sum(), \
        "projected top %.9f != plan %.9f" % ((nz * A).sum(), A_bot.sum())
    Tf = os.path.join(case, "0/solid/T")
    s = open(Tf).read()
    h_list = "nonuniform List<scalar> %d\n(\n%s\n)" % (n, "\n".join("%.10g" % (U_top * z) for z in nz))
    s2, cnt = re.subn(r"(solid_top\s*\{[^}]*?\bh\s+)uniform\s+[-\d.eE+]+;",
                      lambda m: m.group(1) + h_list + ";", s, flags=re.S)
    assert cnt == 1, "could not rewrite h on solid_top"
    open(Tf, "w").write(s2)
    return float(A.sum()), float((nz * A).sum())


def latest_time(case):
    ts = [d for d in os.listdir(case) if re.fullmatch(r"\d+(\.\d+)?", d) and d != "0"]
    return max(ts, key=float)


def swap_channel_b(case):
    """Co-current on the CAD plate: channel b is fed at its NARROW end (patch 'outlet_b') and
    leaves through 'inlet_b'. Only the fluid temperature BCs need swapping; U and phi come from
    the flow solution and p/p_rgh are not solved under frozenFlow."""
    Tf = os.path.join(case, "0/fluid/T")
    s = open(Tf).read()
    blk = lambda name: re.search(r"\n(\s*)" + name + r"\s*\{[^}]*\}", s)
    bi, bo = blk("inlet_b"), blk("outlet_b")
    assert bi and bo
    inl = re.sub(r"inlet_b", "outlet_b", bi.group(0))
    out = re.sub(r"outlet_b", "inlet_b", bo.group(0))
    s = s.replace(bi.group(0), "\n@@A@@").replace(bo.group(0), "\n@@B@@")
    s = s.replace("\n@@A@@", out).replace("\n@@B@@", inl)
    open(Tf, "w").write(s)


def build(cht_template, flow_case, out, end_time=4000, co_current=False):
    """Copy a CHT case, install the frozen flow, and switch the fluid to frozenFlow."""
    if os.path.exists(out):
        shutil.rmtree(out)
    shutil.copytree(cht_template, out,
                    ignore=shutil.ignore_patterns("[1-9]*", "log.run", "processor*"))
    tf = latest_time(flow_case)
    shutil.copy(os.path.join(flow_case, tf, "U"), os.path.join(out, "0/fluid/U"))
    volumetric_to_mass_flux(os.path.join(flow_case, tf, "phi"), os.path.join(out, "0/fluid/phi"))

    fvs = os.path.join(out, "system/fluid/fvSolution")
    s = open(fvs).read()
    if "frozenFlow" not in s:
        s = s.replace("SIMPLE\n{", "SIMPLE\n{\n    frozenFlow      yes;", 1)
    open(fvs, "w").write(s)
    assert "frozenFlow      yes;" in open(fvs).read(), "frozenFlow not inserted"

    if co_current:
        swap_channel_b(out)

    a_curved, a_plan = projected_top_h(out, 4.191176)
    print("solid_top: curved %.6f m2, projected %.6f m2 -> h scaled by n_z" % (a_curved, a_plan))

    cd = os.path.join(out, "system/controlDict")
    c = open(cd).read()
    c = re.sub(r"endTime\s+[^;]+;", "endTime         %d;" % end_time, c)
    c = re.sub(r"writeInterval\s+[^;]+;", "writeInterval   %d;" % end_time, c)
    open(cd, "w").write(c)
    return tf


if __name__ == "__main__":
    tf = build(sys.argv[1], sys.argv[2], sys.argv[3],
               int(sys.argv[4]) if len(sys.argv) > 4 else 4000,
               co_current=(len(sys.argv) > 5 and sys.argv[5] == "co"))
    print("built %s from flow time %s" % (sys.argv[3], tf))
