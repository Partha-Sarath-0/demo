"""Engineering convergence of a simpleFoam flow: mass flow and pressure drop per channel."""
import os, re, sys
import numpy as np
sys.path.insert(0, os.path.dirname(__file__))
import cht_post as P

RHO = 997.0


def monitor(case, pairs):
    """pairs: list of (inlet_patch, outlet_patch) per channel."""
    mesh = os.path.join(case, "constant/polyMesh")
    A = {}
    for i, o in pairs:
        for pt in (i, o):
            A[pt] = P.patch_geometry(mesh, pt)[0]
    times = sorted([d for d in os.listdir(case) if re.fullmatch(r"\d+", d) and d != "0"], key=int)
    rows = []
    for t in times:
        row = [int(t)]
        for i, o in pairs:
            phi_o = np.atleast_1d(P.boundary_values(os.path.join(case, t, "phi"), o))
            phi_i = np.atleast_1d(P.boundary_values(os.path.join(case, t, "phi"), i))
            p_i = P.face_values(os.path.join(case, t, "p"), mesh, i)
            p_o = P.face_values(os.path.join(case, t, "p"), mesh, o)
            if p_i.size == 1: p_i = np.full(A[i].size, float(p_i[0]))
            if p_o.size == 1: p_o = np.full(A[o].size, float(p_o[0]))
            dp = RHO * ((p_i * A[i]).sum() / A[i].sum() - (p_o * A[o]).sum() / A[o].sum())
            row += [phi_o.sum() * RHO, (phi_o.sum() + phi_i.sum()) / phi_o.sum(), dp]
        rows.append(row)
    return rows


if __name__ == "__main__":
    case = sys.argv[1]
    pairs = [tuple(p.split(":")) for p in sys.argv[2:]]
    for r in monitor(case, pairs):
        s = "it %4d " % r[0]
        for k in range(len(pairs)):
            s += "| ch%d mdot %.8e  imbalance %+.2e  dp %.6f Pa " % (k, r[1 + 3 * k], r[2 + 3 * k], r[3 + 3 * k])
        print(s)
