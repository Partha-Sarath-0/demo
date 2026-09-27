"""
GRAIL-CHT transient — startup from cold, for the animation set.

Adds thermal capacitance to both sides of the conjugate problem:
    plate   rho_al c_al t  dTp/dt = div(kt grad Tp) + q_abs - q_top - q_rear - q_fluid
    fluid   rho A c dTf/dt + mdot c dTf/ds = h P (Tp - Tf)
Implicit Euler in time, so the step is set by accuracy rather than stability.

Time constants that matter here:
    plate         rho c t / U_fluid  ~  4 s
    fluid transit L / u              ~ 73 s at the design flow
so the panel settles on the fluid timescale, and the counter-current pattern forms
progressively as each channel's thermal front travels its own way along the plate.
"""
import numpy as np
import scipy.sparse as sp
import scipy.sparse.linalg as spla
from grail_cht import GrailCHT, SIGMA

RHO_AL, CP_AL = 2705.0, 900.0


class GrailTransient(GrailCHT):
    # ---- rear-path hooks. Default: a pure resistance with no capacity, exactly as before.
    def _rear_init(self, dt):
        return None

    def _rear_coupling(self, Tp, dt):
        U = 1.0 / self._R_rear()
        return U, U * self.op.T_amb

    def _rear_update(self, Tp_new, dt):
        return None

    def run(self, t_end=240.0, dt=0.5, save_every=1, T0=None, verbose=False):
        g, m, op = self.g, self.m, self.op
        m.h_wind_val = op.h_wind
        nx, ny = self.nx, self.ny
        n = nx * ny
        q_abs = op.G_T * m.tau_glz_sys * m.tau_tim * m.alpha_abs
        R_rear = self._R_rear()
        U_rear = 1.0 / R_rear
        self._rear_init(dt)

        h_map = np.zeros((nx, g.N_CH)); P_map = np.zeros((nx, g.N_CH)); A_map = np.zeros((nx, g.N_CH))
        for j in range(g.N_CH):
            dh = g.dh(self.xi[:, j])
            h_map[:, j] = self.nu_cfd * m.k_w / dh
            P_map[:, j] = g.perim(self.xi[:, j])
            A_map[:, j] = g.area(self.xi[:, j])

        Tp = np.full((nx, ny), op.T_in if T0 is None else T0)
        Tf = np.full((nx, g.N_CH), op.T_in if T0 is None else T0)
        Cp_plate = RHO_AL * CP_AL * (g.T_LOWER + g.T_UPPER)          # J/m2K
        idx = np.arange(n).reshape(nx, ny)

        # constant conduction coefficients
        kt_x = m.k_al * self.t_x
        kt_y = m.k_al * self.t_y
        ax = np.zeros((nx, ny)); ay = np.zeros((nx, ny))
        ax[:-1, :] = 2 * kt_x[:-1, :] * kt_x[1:, :] / (kt_x[:-1, :] + kt_x[1:, :]) / self.dx ** 2
        ay[:, :-1] = 2 * kt_y[:, :-1] * kt_y[:, 1:] / (kt_y[:, :-1] + kt_y[:, 1:]) / self.dy ** 2

        frames, times = [], []
        nsteps = int(round(t_end / dt))
        for step in range(nsteps + 1):
            t = step * dt
            if step % save_every == 0:
                frames.append(Tp.copy()); times.append(t)
            if step == nsteps:
                break

            # ---- fluid, implicit upwind with capacitance
            Tf_new = np.zeros_like(Tf)
            for j in range(g.N_CH):
                order = range(nx) if self.ch_dir[j] > 0 else range(nx - 1, -1, -1)
                T_up = op.T_in
                for i in order:
                    wgt = self.cov[i] * (self.cov_ch[i] == j)
                    sw = wgt.sum()
                    Tp_loc = float((Tp[i] * wgt).sum() / sw) if sw > 0 else float(Tp[i].mean())
                    hP = h_map[i, j] * P_map[i, j]
                    C = op.mdot_ch * m.cp_w
                    cap = m.rho_w * A_map[i, j] * m.cp_w * self.dx / dt
                    Tf_new[i, j] = (cap * Tf[i, j] + C * T_up + hP * self.dx * Tp_loc) \
                        / (cap + C + hP * self.dx)
                    T_up = Tf_new[i, j]
            Tf = Tf_new

            # ---- plate, implicit with linearised loss
            q_top, q_cond_t, q_rad_t, Tg = self.top_loss(Tp)
            dT = 1e-3
            q_top2, _, _, _ = self.top_loss(Tp + dT)
            U_top = (q_top2 - q_top) / dT
            src_top = q_top - U_top * Tp

            U_f = np.zeros((nx, ny)); src_f = np.zeros((nx, ny))
            for j in range(g.N_CH):
                for i in range(nx):
                    wgt = self.cov[i] * (self.cov_ch[i] == j)
                    sw = wgt.sum()
                    if sw <= 0:
                        continue
                    u = h_map[i, j] * P_map[i, j] / (sw * self.dy)
                    U_f[i] += u * wgt
                    src_f[i] += -u * wgt * Tf[i, j]

            rows, cols, vals = [], [], []
            diag = np.zeros((nx, ny))
            for a, axis in ((ax, 0), (ay, 1)):
                if axis == 0:
                    s_ = idx[:-1, :].ravel(); d_ = idx[1:, :].ravel(); c_ = a[:-1, :].ravel()
                else:
                    s_ = idx[:, :-1].ravel(); d_ = idx[:, 1:].ravel(); c_ = a[:, :-1].ravel()
                rows += [s_, d_]; cols += [d_, s_]; vals += [-c_, -c_]
                np.add.at(diag.reshape(-1), s_, c_)
                np.add.at(diag.reshape(-1), d_, c_)
            U_rear_eff, src_rear_eff = self._rear_coupling(Tp, dt)
            cap_p = Cp_plate / dt
            diag += U_top + U_rear_eff + U_f + cap_p
            rows.append(idx.ravel()); cols.append(idx.ravel()); vals.append(diag.ravel())
            A = sp.coo_matrix((np.concatenate(vals),
                               (np.concatenate(rows), np.concatenate(cols))), shape=(n, n)).tocsr()
            b = (q_abs - src_top + src_rear_eff - src_f + cap_p * Tp).ravel()
            Tp = spla.spsolve(A, b).reshape(nx, ny)
            self._rear_update(Tp, dt)
            if verbose and step % 40 == 0:
                print("   t = %6.1f s   Tp mean %.3f  max %.3f" % (t, Tp.mean(), Tp.max()), flush=True)

        self.frames = frames
        self.times = times
        self.Tp = Tp
        self.Tf = Tf
        return frames, times
