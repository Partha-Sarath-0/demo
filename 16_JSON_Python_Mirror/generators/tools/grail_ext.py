"""
GRAIL — physics extensions on top of the verified conjugate solver.

Three additions, each built on the hooks added to grail_cht / transient rather than by
editing the solved equations, so every previously reported result reproduces bit-identically
(verified: co-current 110x120 gives eta 0.596553 and Tp_std 6.72400 before and after).

  GrailDomain   lateral boundary condition: adiabatic (as the full plate) or periodic,
                for the domain-equivalence study that closes CR-03
  GrailThermo   transmittance that falls as the glazing heats, for the thermotropic filing
  GrailPCM      a graded-PCM tray behind the absorber with latent heat, for the PCM filing
"""
import numpy as np
from grail_cht import Geometry, Materials, Operating, GrailCHT
from transient import GrailTransient


# --------------------------------------------------------------------------- geometry
def make_geom(n_ch, **kw):
    """A plate of n_ch channels at the same pitch, so W = n_ch x PITCH exactly."""
    class G(Geometry):
        N_CH = n_ch
        W = n_ch * Geometry.PITCH
    return G(**kw)


def make_op(n_ch, mdot_full=0.0025, **kw):
    """Operating point for an n_ch strip.

    Operating.mdot_ch divides by Geometry.N_CH, which is the BASE class attribute and stays
    12 however the geometry is subclassed. A strip must therefore carry its own share of the
    total flow so that per-channel flow is unchanged AND the useful gain is counted over the
    same area the efficiency is divided by. Getting this wrong gives efficiencies above 1.
    """
    class O(Operating):
        @property
        def mdot_ch(self):
            return self.mdot_total / n_ch
    return O(mdot_total=mdot_full * n_ch / Geometry.N_CH, **kw)


# --------------------------------------------------------------------------- CR-03
class GrailDomain(GrailCHT):
    """Conjugate plate with a selectable lateral boundary condition.

    'adiabatic'  zero flux at y = +/- W/2. This is what a symmetry plane imposes, and what
                 the full plate has at its physical edges.
    'periodic'   column ny-1 conducts to column 0, so a narrow domain behaves as an interior
                 slice of an infinite plate.

    The distinction matters because under alternating flow the field is glide-symmetric, not
    mirror-symmetric: an adiabatic plane on a bridge midline suppresses exactly the lateral
    conduction the mechanism depends on.
    """

    def __init__(self, *a, lateral="adiabatic", **kw):
        super().__init__(*a, **kw)
        assert lateral in ("adiabatic", "periodic")
        self.lateral = lateral

    def _extra_couplings(self, kt_y, idx):
        if self.lateral != "periodic":
            return [], [], [], None
        nx, ny = self.nx, self.ny
        a = (2 * kt_y[:, -1] * kt_y[:, 0] / (kt_y[:, -1] + kt_y[:, 0])) / self.dy ** 2
        s_ = idx[:, -1].ravel(); d_ = idx[:, 0].ravel()
        diag = np.zeros((nx, ny))
        diag[:, -1] += a
        diag[:, 0] += a
        return [s_, d_], [d_, s_], [-a, -a], diag


def lateral_bridge_profile(s):
    """Lateral conduction through every bridge midline, W, one entry per midline."""
    kt = s.m.k_al * s.t_y
    d = np.zeros_like(s.Tp)
    d[:, :-1] = (s.Tp[:, 1:] - s.Tp[:, :-1]) / s.dy
    kf = np.zeros_like(s.Tp)
    kf[:, :-1] = 2 * kt[:, :-1] * kt[:, 1:] / (kt[:, :-1] + kt[:, 1:])
    q = kf * d
    mids = 0.5 * (s.ch_y[:-1] + s.ch_y[1:])
    return [float(np.abs(q[:, int(np.argmin(np.abs(s.yc - ym)))]).sum() * s.dx) for ym in mids]


# --------------------------------------------------------------------------- filing 3
class GrailThermo(GrailCHT):
    """Thermotropic glazing: transmittance falls as the layer heats.

    The layer switches from tau_clear to tau_scattered across a band. What is applied here is
    the RATIO tau(T)/tau_clear multiplying the baseline system transmittance, not tau(T)
    itself. That keeps the clear-state baseline exactly as established (tau_glz_sys = 0.833,
    q" = 519.1 W/m2 at G_T = 800) and applies only the switching effect.

    DESIGN_REVIEW_REQUIRED: the roadmap's tau_glz_sys = 0.833 is two panes of low-iron glass
    (0.91^2 = 0.828) and does NOT visibly account for a thermotropic layer, yet the CAD
    carries THERMOTROPIC_LAYER_T2 as a separate body in the glazing stack. Either 0.833
    already absorbs the layer's clear-state transmittance, or the baseline optical chain omits
    a real optical element and overstates absorbed flux by roughly 12 %. This is not resolved
    here; the ratio formulation is the conservative reading of the two.
    """
    T_SWITCH_LO = 273.15 + 72.0
    T_SWITCH_HI = 273.15 + 78.0
    TAU_CLEAR = 0.88
    TAU_SCATTERED = 0.40

    def __init__(self, *a, driver="glass", **kw):
        super().__init__(*a, **kw)
        assert driver in ("glass", "plate")
        self.driver = driver
        self._Tp_last = None

    def liquid_like_fraction(self, T):
        return np.clip((T - self.T_SWITCH_LO) / (self.T_SWITCH_HI - self.T_SWITCH_LO), 0.0, 1.0)

    def tau_ratio(self, T):
        f = self.liquid_like_fraction(T)
        return (self.TAU_CLEAR + (self.TAU_SCATTERED - self.TAU_CLEAR) * f) / self.TAU_CLEAR

    def _q_absorbed(self, Tg):
        m, op = self.m, self.op
        T = Tg if self.driver == "glass" else (self._Tp_last if self._Tp_last is not None else Tg)
        base = op.G_T * m.tau_glz_sys * m.tau_tim * m.alpha_abs
        self.switch_f = self.liquid_like_fraction(T)
        return base * self.tau_ratio(T)

    def top_loss(self, Tp):
        self._Tp_last = Tp
        return super().top_loss(Tp)


# --------------------------------------------------------------------------- filing 2
class GrailPCM(GrailTransient):
    """Graded PCM tray behind the absorber, by apparent heat capacity.

    RT55 + 10 % expanded graphite, from the roadmap material table:
        solid   rho 880  cp 2000  k 2.80
        liquid  rho 770  cp 2200  k 2.40
        latent  L = 170 kJ/kg over T_m = 51 - 57 C
    Apparent capacity c_eff = c_p(f) + L df/dT with a linear liquid fraction across the
    6 K interval, which is the form the roadmap itself specifies.

    The tray is one lumped node per plate cell. Lateral conduction inside the PCM is
    neglected and that is a stated simplification, not an oversight: k_pcm x t_pcm is
    0.028 W/K against the absorber's 0.458 W/K, so the PCM carries about 6 % of the plate's
    in-plane conductance and cannot redistribute heat on the timescales here.

    Rear path, split about the tray:
        plate  --R1-->  PCM node  --R2-->  ambient
        R1 = half the tray thickness,  R2 = the other half + VIP + external film
    The node is eliminated analytically each step, so the coupling stays fully implicit.
    """
    T_M1 = 273.15 + 51.0
    T_M2 = 273.15 + 57.0
    L_FUS = 170.0e3
    RHO_S, CP_S, K_S = 880.0, 2000.0, 2.80
    RHO_L, CP_L, K_L = 770.0, 2200.0, 2.40

    def __init__(self, *a, pcm_on=True, T_pcm0=None, **kw):
        super().__init__(*a, **kw)
        self.pcm_on = pcm_on
        self.T_pcm0 = T_pcm0
        self.pcm_hist = []

    # ---- properties
    def liquid_fraction(self, T):
        return np.clip((T - self.T_M1) / (self.T_M2 - self.T_M1), 0.0, 1.0)

    def pcm_props(self, T):
        f = self.liquid_fraction(T)
        rho = self.RHO_S + (self.RHO_L - self.RHO_S) * f
        cp = self.CP_S + (self.CP_L - self.CP_S) * f
        k = self.K_S + (self.K_L - self.K_S) * f
        inside = (T > self.T_M1) & (T < self.T_M2)
        cp_eff = cp + np.where(inside, self.L_FUS / (self.T_M2 - self.T_M1), 0.0)
        return rho, cp_eff, k, f

    # ---- hooks
    def _rear_init(self, dt):
        m, op = self.m, self.op
        self.T_pcm = np.full((self.nx, self.ny),
                             op.T_in if self.T_pcm0 is None else self.T_pcm0)
        self.t_pcm = m.t_pcm
        self.R2_fixed = m.t_vip / m.k_vip + 1.0 / m.h_rear

    def _rear_coupling(self, Tp, dt):
        m, op = self.m, self.op
        if not self.pcm_on:
            U = 1.0 / self._R_rear()
            return U, U * op.T_amb
        rho, cp_eff, k, _ = self.pcm_props(self.T_pcm)
        R1 = 0.5 * self.t_pcm / k
        R2 = 0.5 * self.t_pcm / k + self.R2_fixed
        a = rho * cp_eff * self.t_pcm / dt                  # J/m2K per second
        D = a + 1.0 / R1 + 1.0 / R2
        self._pcm_cache = (R1, R2, a, D)
        U_eff = (1.0 - 1.0 / (R1 * D)) / R1
        src_eff = (a * self.T_pcm + op.T_amb / R2) / (R1 * D)
        return U_eff, src_eff

    def _rear_update(self, Tp_new, dt):
        if not self.pcm_on:
            return
        R1, R2, a, D = self._pcm_cache
        self.T_pcm = (a * self.T_pcm + Tp_new / R1 + self.op.T_amb / R2) / D
        self.pcm_hist.append((float(self.T_pcm.mean()),
                              float(self.liquid_fraction(self.T_pcm).mean())))

    def stored_energy_J_m2(self):
        """Sensible + latent energy held in the tray above the inlet temperature."""
        rho, _, _, f = self.pcm_props(self.T_pcm)
        cp_sens = self.CP_S + (self.CP_L - self.CP_S) * f
        dT = self.T_pcm - self.op.T_in
        return rho * self.t_pcm * (cp_sens * dT + self.L_FUS * f)
