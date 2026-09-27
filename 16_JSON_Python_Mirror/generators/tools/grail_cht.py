"""
GRAIL-CHT — conjugate solver for the full 12-channel absorber.

Why a solver of my own rather than more OpenFOAM: the blocker for 3-D conjugate heat
transfer is meshing the trimmed roll-bond CAD surfaces, not the physics. This solver takes
the geometry and the heat-transfer closure straight from the verified 3-D CFD and solves
the conjugate problem on the whole panel, which is what the central hypothesis needs and
what a 3-D strip could never give on two cores.

Physics
  Plate   2-D steady conduction over the whole absorber, anisotropic sheet thickness,
          solar gain, top loss through the real glazing stack with explicit radiation,
          rear loss through PCM + VIP, and local convective coupling to each channel.
  Fluid   1-D energy per channel, marched in that channel's OWN flow direction, so an
          alternating arrangement is represented exactly rather than approximated.
  Closure h(x) = Nu k / Dh(x). The constructor default nu_cfd = 3.428 is the Rev 1 value and is
          kept only so earlier revisions reproduce exactly. The final campaign (Rev 4 / 4.1 / 4.2,
          campaign4.py) passes the grid-converged conjugate value Nu = 4.48 explicitly.

Everything is SI internally. Kelvin everywhere a fourth power appears.
"""
import numpy as np
import scipy.sparse as sp
import scipy.sparse.linalg as spla

SIGMA = 5.670374419e-8


class Geometry:
    """As-measured GRAIL absorber geometry (Gate 1, converged direct NURBS integration)."""
    L = 1.100                 # m, channel length
    W = 0.480                 # m, plate width
    N_CH = 12
    PITCH = 0.040             # m
    T_LOWER = 1.0e-3          # m, lower sheet
    T_UPPER = 1.0e-3          # m, upper sheet
    # section at xi = 0 and 1, from Gate 1
    A_IN, A_OUT = 28.056939e-6, 7.921436e-6      # m2
    P_IN, P_OUT = 21.5865e-3, 11.2884e-3         # m
    DH_IN, DH_OUT = 5.198875e-3, 2.807053e-3     # m
    W_CH_IN = 8.714056e-3                        # m, widest channel footprint
    G_RATIO = 0.539935
    LAM_G = 1.0

    def __init__(self, g_ratio=None, lam_g=None, bridge=None):
        self.g_ratio = self.G_RATIO if g_ratio is None else g_ratio
        self.lam_g = self.LAM_G if lam_g is None else lam_g
        # bridge width is set by the channel footprint: bridge = pitch - w_ch
        self.bridge = (self.PITCH - self.W_CH_IN) if bridge is None else bridge
        self.w_ch_in = self.PITCH - self.bridge

    def dh(self, xi):
        return self.DH_IN * (1.0 - (1.0 - self.g_ratio) * xi ** self.lam_g)

    def scale(self, xi):
        """Linear size scale of the section, from the Dh law."""
        return self.dh(xi) / self.DH_IN

    def area(self, xi):
        s = self.scale(xi)
        return self.A_IN * s ** 2

    def perim(self, xi):
        s = self.scale(xi)
        return self.P_IN * s

    def w_ch(self, xi):
        return self.w_ch_in * self.scale(xi)


class Materials:
    k_al = 229.0              # AA1050
    rho_w, cp_w, k_w, mu_w = 997.0, 4180.0, 0.610, 8.55e-4
    alpha_abs = 0.95
    eps_abs = 0.04            # TiNOX
    eps_glass = 0.88
    tau_glz_sys = 0.833
    tau_tim = 0.82
    k_air = 0.026
    # stack, from roadmap 5.1 / 5.3
    t_tim, k_tim = 0.010, 0.075
    t_gap_lo, t_gap_up = 7.45e-3, 4.30e-3
    t_glass, k_glass = 3.2e-3, 1.05
    t_pcm, k_pcm = 0.010, 2.80
    t_vip, k_vip = 0.020, 0.006
    h_rear = 3.0


class Operating:
    def __init__(self, G_T=800.0, T_in=300.0, T_amb=298.15, v_wind=1.0,
                 mdot_total=0.0025, f_interdig=1):
        self.G_T = G_T
        self.T_in = T_in
        self.T_amb = T_amb
        self.v_wind = v_wind
        self.mdot_total = mdot_total
        self.f_interdig = f_interdig          # 0 = parallel, 1 = alternating counter-current

    @property
    def T_sky(self):
        return 0.0552 * self.T_amb ** 1.5

    @property
    def h_wind(self):
        return 5.7 + 3.8 * self.v_wind

    @property
    def mdot_ch(self):
        return self.mdot_total / Geometry.N_CH


def k_water(T):
    """Thermal conductivity of saturated liquid water, W/m.K, T in kelvin.

    Least-squares cubic through the handbook values at 0, 20, 40, 60, 80 and 100 C
    (0.5562, 0.5984, 0.6305, 0.6540, 0.6700, 0.6791). Maximum deviation from those
    points is 0.016 %. Valid 273-373 K; clipped outside.

    Added for Rev 3. The audit of Rev 2 found that viscosity was carried as mu(T)
    through the Vogel relation while conductivity was held fixed at 0.610 W/m.K, which
    is the value at 26.6 C. Because h = Nu k / Dh, that understates h by up to 10.4 %
    in the hottest cases. This restores consistency between the two properties.
    """
    t = np.clip(np.asarray(T, dtype=float) - 273.15, 0.0, 100.0)
    return 5.56231746e-01 + 2.36703704e-03 * t - 1.36140873e-05 * t ** 2 \
        + 2.23379630e-08 * t ** 3


class GrailCHT:
    def __init__(self, geo, mat, op, nx=220, ny=240, nu_cfd=3.428, k_of_T=False):
        self.g, self.m, self.op = geo, mat, op
        self.nx, self.ny = nx, ny
        self.nu_cfd = nu_cfd
        # Rev 3 option. Default False so Rev 1 and Rev 2 stay bit-reproducible.
        self.k_of_T = k_of_T
        self.dx = geo.L / nx
        self.dy = geo.W / ny
        self.xc = -geo.L / 2 + (np.arange(nx) + 0.5) * self.dx
        self.yc = -geo.W / 2 + (np.arange(ny) + 0.5) * self.dy
        self.X, self.Y = np.meshgrid(self.xc, self.yc, indexing='ij')
        self._build_masks()

    # ------------------------------------------------------------------ geometry maps
    def _build_masks(self):
        g = self.g
        y0 = -g.W / 2 + g.PITCH / 2                      # centre of channel 1
        self.ch_y = y0 + np.arange(g.N_CH) * g.PITCH
        # which channel each column belongs to, and whether it is inside the footprint
        self.ch_index = np.full(self.ny, -1, dtype=int)
        for j, yc in enumerate(self.ch_y):
            self.ch_index[np.abs(self.yc - yc) <= g.PITCH / 2] = j
        # flow direction per channel: +1 or -1 along x
        if self.op.f_interdig:
            self.ch_dir = np.where(np.arange(g.N_CH) % 2 == 0, +1, -1)
        else:
            self.ch_dir = np.ones(g.N_CH, dtype=int)
        # xi for each (i, channel) pair, measured from that channel's OWN inlet
        self.xi = np.zeros((self.nx, g.N_CH))
        s = (self.xc + g.L / 2) / g.L
        for j in range(g.N_CH):
            self.xi[:, j] = s if self.ch_dir[j] > 0 else (1.0 - s)
        # channel footprint with FRACTIONAL cell coverage, so the coupled width is exact
        # (a binary mask quantises w_ch to the cell size and breaks the energy balance)
        self.cov = np.zeros((self.nx, self.ny))        # fraction of each cell over a channel
        self.cov_ch = np.zeros((self.nx, self.ny), dtype=int)
        ylo = self.yc - self.dy / 2
        yhi = self.yc + self.dy / 2
        for j, yc in enumerate(self.ch_y):
            w = self.g.w_ch(self.xi[:, j])                       # (nx,)
            for i in range(self.nx):
                a, b = yc - w[i] / 2, yc + w[i] / 2
                ov = np.clip(np.minimum(yhi, b) - np.maximum(ylo, a), 0.0, None) / self.dy
                sel = ov > 0
                self.cov[i, sel] = ov[sel]
                self.cov_ch[i, sel] = j
        self.in_ch = self.cov > 0

        # sheet thickness for in-plane conduction
        # x-direction: both sheets conduct everywhere -> 2 mm
        # y-direction: over a channel only the lower sheet gives a direct path
        self.t_x = np.full((self.nx, self.ny), g.T_LOWER + g.T_UPPER)
        self.t_y = (g.T_LOWER + g.T_UPPER) - self.cov * g.T_UPPER

    # ------------------------------------------------------------------ loss model
    def _R_top_cond(self):
        m = self.m
        return (m.t_tim / m.k_tim + m.t_gap_lo / m.k_air + m.t_glass / m.k_glass
                + m.t_gap_up / m.k_air + m.t_glass / m.k_glass)

    def _R_rear(self):
        m = self.m
        return m.t_pcm / m.k_pcm + m.t_vip / m.k_vip + 1.0 / m.h_rear

    def top_loss(self, Tp):
        """Top loss per unit plate area, with radiation kept as a fourth power.

        Plate radiates through the selective coating to the glazing; the glazing sheds heat
        to sky and ambient. Glass temperature is solved from its own balance each call.
        """
        m, op = self.m, self.op
        Rc = self._R_top_cond()
        Tg = 0.5 * (Tp + op.T_amb)
        for _ in range(30):
            hr_pg = SIGMA * (Tp ** 2 + Tg ** 2) * (Tp + Tg) / (1 / m.eps_abs + 1 / m.eps_glass - 1)
            q_in = (Tp - Tg) / Rc + hr_pg * (Tp - Tg)
            q_out = m.h_wind_val * (Tg - op.T_amb) + m.eps_glass * SIGMA * (Tg ** 4 - op.T_sky ** 4)
            f = q_in - q_out
            dTg = 1e-4
            hr2 = SIGMA * (Tp ** 2 + (Tg + dTg) ** 2) * (Tp + Tg + dTg) / (1 / m.eps_abs + 1 / m.eps_glass - 1)
            f2 = ((Tp - Tg - dTg) / Rc + hr2 * (Tp - Tg - dTg)
                  - m.h_wind_val * (Tg + dTg - op.T_amb)
                  - m.eps_glass * SIGMA * ((Tg + dTg) ** 4 - op.T_sky ** 4))
            d = (f2 - f) / dTg
            step = np.where(np.abs(d) > 1e-12, -f / d, 0.0)
            Tg = Tg + np.clip(step, -20, 20)
            if np.max(np.abs(step)) < 1e-8:
                break
        hr_pg = SIGMA * (Tp ** 2 + Tg ** 2) * (Tp + Tg) / (1 / m.eps_abs + 1 / m.eps_glass - 1)
        q_cond = (Tp - Tg) / Rc
        q_rad = hr_pg * (Tp - Tg)
        return q_cond + q_rad, q_cond, q_rad, Tg

    # --------------------------------------------------------------- extension hooks
    def _q_absorbed(self, Tg):
        """Absorbed flux. Constant by default; a subclass may make it depend on Tg."""
        m, op = self.m, self.op
        return op.G_T * m.tau_glz_sys * m.tau_tim * m.alpha_abs

    def _extra_couplings(self, kt_y, idx):
        """Extra matrix entries, e.g. a periodic lateral boundary. Empty by default."""
        return [], [], [], None

    # ------------------------------------------------------------------ solve
    def solve(self, tol=1e-6, max_outer=200, verbose=False):
        g, m, op = self.g, self.m, self.op
        m.h_wind_val = op.h_wind
        nx, ny = self.nx, self.ny
        n = nx * ny
        Tg = np.full((nx, ny), op.T_amb)
        q_abs = self._q_absorbed(Tg)
        R_rear = self._R_rear()

        # local heat-transfer coefficient per (i, channel)
        h_map = np.zeros((nx, g.N_CH))
        P_map = np.zeros((nx, g.N_CH))
        nu_map = np.zeros((nx, g.N_CH))
        dh_map = np.zeros((nx, g.N_CH))
        for j in range(g.N_CH):
            dh = g.dh(self.xi[:, j])
            # nu_cfd may be a constant or a callable Nu(xi); the callable form lets the
            # thermal entrance be represented instead of collapsed into one number
            nu_loc = self.nu_cfd(self.xi[:, j]) if callable(self.nu_cfd) else self.nu_cfd
            h_map[:, j] = nu_loc * m.k_w / dh
            P_map[:, j] = g.perim(self.xi[:, j])
            nu_map[:, j] = nu_loc
            dh_map[:, j] = dh
        # With k(T) the closure depends on the fluid temperature, which is itself being
        # solved for, so h_map is refreshed inside the outer loop from the current Tf.
        # It sits inside an existing fixed-point iteration and converges with it.

        Tp = np.full((nx, ny), op.T_in + 20.0)
        Tf = np.full((nx, g.N_CH), op.T_in)

        idx = np.arange(n).reshape(nx, ny)
        for outer in range(max_outer):
            if self.k_of_T:
                h_map = nu_map * k_water(Tf) / dh_map

            # ---- fluid: march each channel in its own direction
            Tf_new = np.zeros_like(Tf)
            for j in range(g.N_CH):
                order = range(nx) if self.ch_dir[j] > 0 else range(nx - 1, -1, -1)
                T = op.T_in
                col = self.ch_index == j
                for i in order:
                    wgt = self.cov[i] * (self.cov_ch[i] == j)
                    sw = wgt.sum()
                    Tp_loc = float((Tp[i] * wgt).sum() / sw) if sw > 0 else float(Tp[i].mean())
                    hP = h_map[i, j] * P_map[i, j]
                    C = op.mdot_ch * m.cp_w
                    T = (C * T + hP * self.dx * Tp_loc) / (C + hP * self.dx)
                    Tf_new[i, j] = T
            Tf = 0.5 * Tf + 0.5 * Tf_new

            # ---- plate: linearise loss about the current field
            q_top, q_cond_t, q_rad_t, Tg = self.top_loss(Tp)
            q_abs = self._q_absorbed(Tg)
            dT = 1e-3
            q_top2, _, _, _ = self.top_loss(Tp + dT)
            U_top = (q_top2 - q_top) / dT
            src_top = q_top - U_top * Tp                     # q_top = U_top*Tp + src_top
            U_rear = 1.0 / R_rear
            src_rear = -U_rear * op.T_amb

            # fluid coupling, spread over the channel footprint
            U_f = np.zeros((nx, ny))
            src_f = np.zeros((nx, ny))
            for j in range(g.N_CH):
                for i in range(nx):
                    wgt = self.cov[i] * (self.cov_ch[i] == j)
                    sw = wgt.sum()
                    if sw <= 0:
                        continue
                    hP = h_map[i, j] * P_map[i, j]          # W/m per unit channel length
                    # spread hP over the covered cells so sum(U_f * cov * dy) == hP exactly
                    u = hP / (sw * self.dy)
                    U_f[i] += u * wgt
                    src_f[i] += -u * wgt * Tf[i, j]

            # conduction coefficients (harmonic mean of k*t on faces)
            kt_x = m.k_al * self.t_x
            kt_y = m.k_al * self.t_y
            ax = np.zeros((nx, ny)); ay = np.zeros((nx, ny))
            ax[:-1, :] = 2 * kt_x[:-1, :] * kt_x[1:, :] / (kt_x[:-1, :] + kt_x[1:, :]) / self.dx ** 2
            ay[:, :-1] = 2 * kt_y[:, :-1] * kt_y[:, 1:] / (kt_y[:, :-1] + kt_y[:, 1:]) / self.dy ** 2

            rows, cols, vals = [], [], []
            diag = np.zeros((nx, ny))
            for (sh, a, axis) in ((1, ax, 0), (1, ay, 1)):
                if axis == 0:
                    src = idx[:-1, :].ravel(); dst = idx[1:, :].ravel(); c = a[:-1, :].ravel()
                else:
                    src = idx[:, :-1].ravel(); dst = idx[:, 1:].ravel(); c = a[:, :-1].ravel()
                rows += [src, dst]; cols += [dst, src]; vals += [-c, -c]
                np.add.at(diag.reshape(-1), src, c)
                np.add.at(diag.reshape(-1), dst, c)
            diag += U_top + U_rear + U_f
            er, ec, ev, ediag = self._extra_couplings(kt_y, idx)
            if ediag is not None:
                rows += er; cols += ec; vals += ev; diag += ediag
            rows.append(idx.ravel()); cols.append(idx.ravel()); vals.append(diag.ravel())
            A = sp.coo_matrix((np.concatenate(vals),
                               (np.concatenate(rows), np.concatenate(cols))), shape=(n, n)).tocsr()
            b = (q_abs - src_top - src_rear - src_f).ravel()
            Tp_new = spla.spsolve(A, b).reshape(nx, ny)

            delta = np.max(np.abs(Tp_new - Tp))
            Tp = 0.7 * Tp_new + 0.3 * Tp
            if verbose and outer % 10 == 0:
                print("   outer %3d  max dT %.3e  Tp mean %.3f" % (outer, delta, Tp.mean()))
            if delta < tol:
                break

        self.Tp, self.Tf, self.Tg, self.q_abs = Tp, Tf, Tg, q_abs
        self.outer = outer + 1
        self.converged = delta < tol
        self.delta = delta
        return self._results(q_abs)

    # ------------------------------------------------------------------ results
    def _results(self, q_abs):
        g, m, op = self.g, self.m, self.op
        Ac = g.L * g.W
        q_top, q_cond_t, q_rad_t, Tg = self.top_loss(self.Tp)
        cell = self.dx * self.dy
        Q_solar = float(np.mean(q_abs)) * Ac
        Q_top = q_top.sum() * cell
        Q_rad = q_rad_t.sum() * cell
        Q_conv_t = q_cond_t.sum() * cell
        Q_rear = ((self.Tp - op.T_amb) / self._R_rear()).sum() * cell
        T_out = np.array([self.Tf[-1, j] if self.ch_dir[j] > 0 else self.Tf[0, j]
                          for j in range(g.N_CH)])
        Tout_mix = T_out.mean()
        Q_u = op.mdot_total * m.cp_w * (Tout_mix - op.T_in)
        Tp = self.Tp.ravel()
        res = dict(
            topology="alternating" if op.f_interdig else "parallel",
            G_T=op.G_T, T_in=op.T_in, T_amb=op.T_amb, v_wind=op.v_wind,
            mdot_total=op.mdot_total, mdot_ch=op.mdot_ch,
            bridge_mm=g.bridge * 1000, g_ratio=g.g_ratio, lam_g=g.lam_g,
            T_out=float(Tout_mix), dT=float(Tout_mix - op.T_in),
            Q_u=float(Q_u), eta=float(Q_u / (Ac * op.G_T)),
            Q_solar=float(Q_solar), Q_rad=float(Q_rad), Q_conv=float(Q_conv_t),
            Q_rear=float(Q_rear),
            Tp_max=float(Tp.max()), Tp_min=float(Tp.min()), Tp_mean=float(Tp.mean()),
            dTp=float(Tp.max() - Tp.min()), Tp_std=float(Tp.std()),
            P90=float(np.percentile(Tp, 90)), P95=float(np.percentile(Tp, 95)),
            P99=float(np.percentile(Tp, 99)),
            R4=float(np.mean(Tp ** 4)), mean_T_pow4=float(np.mean(Tp) ** 4),
            U_L=float((float(np.mean(q_abs)) - Q_u / Ac) / (Tp.mean() - op.T_amb)),
            T_glass_mean=float(Tg.mean()),
            energy_error_pct=float(100 * (Q_solar - Q_u - Q_top - Q_rear) / Q_solar),
            outer=self.outer, converged=bool(self.converged), residual=float(self.delta),
        )
        res["T_out_per_channel"] = [float(t) for t in T_out]
        return res
