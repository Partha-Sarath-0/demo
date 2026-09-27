"""
GRAIL — reduced-order side of the 3-D conjugate benchmark.

The 3-D conjugate case (06_cht) cannot reproduce the campaign's full loss model: the glazing
stack with T^4 radiation and the PCM + VIP rear path have no stock OpenFOAM boundary condition.
It uses a LINEAR loss instead, on the solid's outer faces:

    top     q"_abs - U_top (T - T_amb),   U_top = 1 / (t_TIM/k_TIM + 1/h_wind) = 4.191176 W/m2K
    rear    - h_rear (T - T_amb),          h_rear = 3.0 W/m2K, applied directly to the metal

Both are ENGINEERING_ASSUMPTION benchmark conditions, not campaign conditions.

A benchmark is only meaningful if the two models solve the SAME problem. This subclass
therefore replaces the reduced-order model's two loss functions with exactly that linear
model and changes nothing else: the plate conduction, the per-channel 1-D fluid marching, the
Nusselt closure h = Nu k / Dh, the lumped sheet thickness and the periodic lateral boundary
are all inherited unchanged. What remains different between the two models is then precisely
the reduced-order MODEL FORM, which is what the benchmark exists to measure:

    - one constant Nu instead of the resolved wall heat transfer, including the entrance
    - a lumped through-thickness plate instead of the resolved roll-bond cross-section
    - 1-D bulk fluid temperature instead of the resolved channel cross-section

Nothing in grail_cht.py or grail_ext.py is modified, so every earlier result reproduces.
"""
import numpy as np
from grail_ext import GrailDomain, make_geom, make_op, lateral_bridge_profile
from grail_cht import Materials

U_TOP = 4.191176          # W/m2K, from 06_cht/*/case.params
H_REAR = 3.0              # W/m2K
T_AMB = 298.15            # K
T_IN = 300.0              # K
Q_ABS = 519.1256          # W/m2 at G_T = 800


class GrailBench(GrailDomain):
    """GrailDomain with the 3-D benchmark's linear loss model.

    taper = "flow"  geometry follows each channel's own flow direction, exactly as in the
                    production campaign: under co-current flow EVERY channel converges the same
                    way, which is a different roll-bond pattern from the CAD plate.
    taper = "cad"   the CAD plate: taper alternates channel to channel REGARDLESS of flow, so
                    co-current flow runs half the channels diverging. This is the geometry the
                    3-D mesh has, and it isolates the effect of flow direction from the effect
                    of the metal distribution.
    """

    def __init__(self, *a, taper="flow", **kw):
        assert taper in ("flow", "cad")
        self.taper = taper
        super().__init__(*a, **kw)

    def _build_masks(self):
        if self.taper == "flow":
            return super()._build_masks()
        f_flow = self.op.f_interdig
        self.op.f_interdig = 1                 # geometry: alternating taper, as in the CAD
        super()._build_masks()
        self.op.f_interdig = f_flow
        # flow direction set independently; self.xi stays the GEOMETRIC coordinate
        g = self.g
        self.ch_dir = (np.where(np.arange(g.N_CH) % 2 == 0, +1, -1) if f_flow
                       else np.ones(g.N_CH, dtype=int))

    def top_loss(self, Tp):
        q = U_TOP * (Tp - self.op.T_amb)
        # (total, conductive part, radiative part, glass temperature). There is no glazing
        # or radiation in the benchmark, so the radiative part is zero and Tg is a dummy.
        return q, q, np.zeros_like(Tp), np.full_like(Tp, self.op.T_amb)

    def _R_rear(self):
        return 1.0 / H_REAR


MDOT_CH_3D = 2.077072e-4   # kg/s per channel ACTUALLY carried by the 3-D case: its meshed inlet
                           # area at NU = 64 is 27.9726 mm2 against the CAD's 28.0569 (-0.30 %)


def run(f_interdig, nu=2.9238, nx=220, ny=80, nu_fn=None, taper="cad", mdot_ch=MDOT_CH_3D):
    """2-channel periodic strip at the 3-D benchmark's operating point."""
    g = make_geom(2)
    op = make_op(2, mdot_full=mdot_ch * 12, G_T=800.0, T_in=T_IN, T_amb=T_AMB, v_wind=1.0,
                 f_interdig=f_interdig)
    assert abs(op.mdot_ch - mdot_ch) < 1e-15
    s = GrailBench(g, Materials(), op, nx=nx, ny=ny, taper=taper,
                   nu_cfd=(nu_fn if nu_fn is not None else nu), lateral="periodic")
    r = s.solve(max_outer=4000, tol=1e-9)
    r["bridge_W"] = lateral_bridge_profile(s)
    return s, r


if __name__ == "__main__":
    import json, sys
    out = {}
    for f, taper, tag in ((1, "cad", "alternating"), (0, "cad", "co_current_cad_taper"),
                          (0, "flow", "co_current_co_taper")):
        s, r = run(f, taper=taper)
        qa = s.op.G_T * s.m.tau_glz_sys * s.m.tau_tim * s.m.alpha_abs
        out[tag] = {k: (float(r[k]) if np.ndim(r[k]) == 0 else None)
                    for k in ("eta", "T_out", "dT", "Q_u", "Tp_mean", "Tp_std", "dTp",
                              "Tp_max", "Tp_min", "energy_error_pct", "outer", "converged")}
        out[tag]["q_abs"] = float(qa)
        out[tag]["bridge_W"] = r["bridge_W"]
        print("%-12s eta %.5f  Q_u %.4f W  dT %.4f K  Tp mean %.3f  std %.4f  spread %.4f  "
              "bridge %s W  E-err %.2e %%  outer %d"
              % (tag, r["eta"], r["Q_u"], r["dT"], r["Tp_mean"], r["Tp_std"], r["dTp"],
                 ["%.3f" % b for b in r["bridge_W"]], r["energy_error_pct"], r["outer"]))
    json.dump(out, open(sys.argv[1] if len(sys.argv) > 1 else "/dev/null", "w"), indent=1)
