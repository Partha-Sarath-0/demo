"""
GRAIL — local Nusselt number from the 3-D conjugate solution, per channel, per axial station.

Everything from first principles and raw files; nothing from solver-reported integrals.

  station      the structured mesh has NX axial layers per channel; each axial face plane is a
               station. Axial faces are internal fluid faces whose unit normal is ~ +/- x.
  T_b(x)       bulk (mixing-cup) temperature at a station: sum(phi_f T_f) / sum(phi_f) over the
               station's axial faces, T_f linearly interpolated from the two adjacent cells
  q'(x)        heat entering the fluid per unit length, from the slab energy balance between two
               stations:  q' = mdot cp (T_b,k+1 - T_b,k) / dx
  T_w(x)       perimeter-average of the fluid-side interface temperature over the slab
  P, D_h, A    wetted perimeter from the slab's interface faces; flow area from the station faces
  Nu(x)        q' / (P (T_w - T_b,mid)) * D_h / k_f

The flow here is laminar, with constant properties, so this is the local Nusselt number of the
real conjugate problem: neither uniform wall flux nor uniform wall temperature, but whatever the
coupled metal actually imposes. That is the quantity the reduced-order model's single constant is
standing in for.
"""
import os, sys, json
import numpy as np
sys.path.insert(0, os.path.dirname(__file__))
import cht_post as P

CP, K_F = 4180.0, 0.610


def _neigh(mesh):
    s = open(os.path.join(mesh, "neighbour")).read()
    i = s.index("FoamFile") + 50 if "FoamFile" in s else 0
    n, j = P._foam_list(s, i)
    return np.array(s[j:].split(")")[0].split()[:n], int)


def _internal_face_scalar(path, n_int):
    s = open(path).read()
    import re
    m = re.search(r"internalField\s+nonuniform\s+List<scalar>\s*\n?(\d+)\s*\n?\(", s)
    return np.array(s[m.end():].split(")")[0].split()[:n_int], float)


def extract(case, time):
    mesh = os.path.join(case, "constant/fluid/polyMesh")
    pts = P.read_points(os.path.join(mesh, "points"))
    faces = P.read_faces(os.path.join(mesh, "faces"))
    own = P.read_owner(os.path.join(mesh, "owner"))
    nei = _neigh(mesh)
    nint = len(nei)
    ncell = own.max() + 1

    # face geometry
    Sf = np.zeros((len(faces), 3)); Cf = np.zeros((len(faces), 3))
    for k, f in enumerate(faces):
        p = pts[f]; c0 = p.mean(0); v = np.zeros(3); cen = np.zeros(3); at = 0.0
        for i in range(len(f)):
            tri = 0.5 * np.cross(p[i] - c0, p[(i + 1) % len(f)] - c0)
            a = np.linalg.norm(tri); v += tri; cen += a * (p[i] + p[(i + 1) % len(f)] + c0) / 3; at += a
        Sf[k] = v; Cf[k] = cen / at if at > 0 else c0
    Af = np.linalg.norm(Sf, axis=1)
    nx_f = Sf[:, 0] / np.maximum(Af, 1e-30)

    # cell centres as face-centre averages, and cell temperatures
    acc = np.zeros((ncell, 3)); cnt = np.zeros(ncell)
    np.add.at(acc, own, Cf); np.add.at(cnt, own, 1)
    np.add.at(acc, nei, Cf[:nint]); np.add.at(cnt, nei, 1)
    Cc = acc / cnt[:, None]
    Tc = P.internal_scalar(os.path.join(case, time, "fluid/T"))
    phi = _internal_face_scalar(os.path.join(case, time, "fluid/phi"), nint)

    # interface faces
    bnd = P.read_boundary(os.path.join(mesh, "boundary"))
    st, nw = bnd["fluid_to_solid"]
    Tw_f = np.atleast_1d(P.boundary_values(os.path.join(case, time, "fluid/T"), "fluid_to_solid"))
    wall_idx = np.arange(st, st + nw)

    out = {}
    ymid = np.median(Cc[:, 1])
    for tag, sel_y in (("y_low", Cc[:, 1] < ymid), ("y_high", Cc[:, 1] >= ymid)):
        cells = np.where(sel_y)[0]
        cellset = np.zeros(ncell, bool); cellset[cells] = True
        # axial internal faces of this channel
        ax = np.where((np.abs(nx_f[:nint]) > 0.999) & cellset[own[:nint]] & cellset[nei])[0]
        xs = np.round(Cf[ax, 0], 7)
        stations = np.unique(xs)
        Tb = []; Aflow = []; mflow = []
        for x in stations:
            f = ax[xs == x]
            Tf = 0.5 * (Tc[own[f]] + Tc[nei[f]])
            ph = phi[f] * np.sign(nx_f[f])            # flux in +x direction
            m = ph.sum()
            Tb.append((ph * Tf).sum() / m); Aflow.append(Af[f].sum()); mflow.append(m)
        Tb = np.array(Tb); Aflow = np.array(Aflow); mflow = np.array(mflow)
        mdot = abs(np.median(mflow))
        # wall faces belonging to this channel's cells
        wf = wall_idx[cellset[own[wall_idx]]]
        wx = Cf[wf, 0]
        rows = []
        for k in range(len(stations) - 1):
            x0, x1 = stations[k], stations[k + 1]
            sel = (wx > x0) & (wx < x1)
            if sel.sum() == 0:
                continue
            aw = Af[wf[sel]]
            Tw = float((Tw_f[wf[sel] - st] * aw).sum() / aw.sum())
            dx = x1 - x0
            Pw = aw.sum() / dx
            qprime = mdot * CP * abs(Tb[k + 1] - Tb[k]) / dx * np.sign(Tb[k + 1] - Tb[k]) \
                * np.sign(np.median(mflow))
            Tbm = 0.5 * (Tb[k] + Tb[k + 1])
            Am = 0.5 * (Aflow[k] + Aflow[k + 1])
            Dh = 4 * Am / Pw
            h = qprime / (Pw * (Tw - Tbm))
            rows.append({"x": float(0.5 * (x0 + x1)), "Tb": float(Tbm), "Tw": float(Tw),
                         "qprime": float(qprime), "P": float(Pw), "A": float(Am),
                         "Dh": float(Dh), "h": float(h), "Nu": float(h * Dh / K_F)})
        out[tag] = {"mdot": float(mdot), "flow_sign": float(np.sign(np.median(mflow))),
                    "stations": rows,
                    "Tb_stations_along_flow": [float(t) for t in
                                               (Tb if np.median(mflow) > 0 else Tb[::-1])]}
    return out


def heat_budget(res, T_in, T_out_by_channel):
    """Per-channel budget INCLUDING the two end segments the slab list omits:
         inlet segment   mdot cp (T_b,first station - T_in)
         slabs           sum of q' dx, split into intake (q' > 0) and return (q' < 0)
         outlet segment  mdot cp (T_out - T_b,last station)
       net must equal mdot cp (T_out - T_in); the closure is reported, not assumed."""
    out = {}
    for tag, v in res.items():
        s = v["stations"]; x = np.array([q["x"] for q in s])
        o = np.argsort(x) if v["flow_sign"] > 0 else np.argsort(-x)
        qp = np.array([q["qprime"] for q in s])[o]
        dx = np.abs(np.diff(np.sort(x))).mean()
        Tb = np.array(v["Tb_stations_along_flow"])
        C = v["mdot"] * CP
        Tout = T_out_by_channel[tag]
        seg_in = C * (Tb[0] - T_in); seg_out = C * (Tout - Tb[-1])
        intake = (qp[qp > 0] * dx).sum() + max(seg_in, 0) + max(seg_out, 0)
        ret = -(qp[qp < 0] * dx).sum() - min(seg_in, 0) - min(seg_out, 0)
        net = intake - ret
        # NOTE: net == mdot cp (T_out - T_in) holds IDENTICALLY (the slab sums telescope), so it
        # is a decomposition of the channel's heat, not an independent check. The independent
        # check is the global 3-D energy balance from cht_post.analyse.
        out[tag] = {"intake_W": float(intake), "returned_W": float(ret), "net_W": float(net),
                    "returned_fraction": float(ret / intake),
                    "Tb_peak": float(Tb.max()), "Tb_out": float(Tout),
                    "frac_length_returning": float((qp < 0).mean())}
    return out


if __name__ == "__main__":
    r = extract(sys.argv[1], sys.argv[2])
    json.dump(r, open(sys.argv[3], "w"), indent=1)
    for tag, v in r.items():
        s = v["stations"]; Nu = np.array([q["Nu"] for q in s]); x = np.array([q["x"] for q in s])
        print("%s: mdot %.6e  flow %+d  %d slabs  Nu: inlet-end %.2f  mid %.2f  outlet-end %.2f  "
              "median %.3f" % (tag, v["mdot"], v["flow_sign"], len(s),
                               Nu[np.argmin(x)] if v["flow_sign"] > 0 else Nu[np.argmax(x)],
                               Nu[len(Nu) // 2],
                               Nu[np.argmax(x)] if v["flow_sign"] > 0 else Nu[np.argmin(x)],
                               np.median(Nu)))
