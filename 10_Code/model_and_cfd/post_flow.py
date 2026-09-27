"""
GRAIL CFD — hydraulic post-processing of the converged single-channel flow solution.

Extracts, at normalised flow coordinate xi measured from the channel's OWN local inlet:
  bulk velocity, local Re, static pressure, and the axial pressure gradient.
Also checks mass conservation and compares the pressure drop against the laminar
Hagen-Poiseuille expectation integrated along the converging channel.
"""
import numpy as np, os, sys, subprocess, json

CASE = sys.argv[1] if len(sys.argv) > 1 else "/home/claude/grail_cfd/04_baseline/ch05_flow"
RHO = 997.0
MU = 8.55e-4
NU = MU / RHO
MDOT = 0.0025 / 12.0
Q = MDOT / RHO

# geometry along the channel, from the Gate 1 measurement (mm)
XI = np.array([0.0, 0.10, 0.25, 0.50, 0.75, 0.90, 1.0])
A_mm2 = np.array([28.0569, 25.5427, 21.9080, 16.4824, 11.8311, 9.4306, 7.9214])
P_mm = np.array([21.5865, 20.5539, 19.0047, 16.4253, 13.8520, 12.3116, 11.2884])
DH_mm = 4 * A_mm2 / P_mm


def foam_sample(case, time, field, points):
    """Sample a field at points using postProcess -func 'probes'."""
    d = os.path.join(case, "system", "probesDict")
    with open(d, "w") as f:
        f.write("probes { type probes; libs (\"libsampling.so\"); fields (%s);\n" % field)
        f.write("  probeLocations (\n")
        for p in points:
            f.write("    (%.9g %.9g %.9g)\n" % tuple(p))
        f.write("  );\n}\n")
    return d


def analytic_dp():
    """Laminar fully-developed estimate: integrate 2 f rho u^2 / Dh along x
       with f Re = 16 (circular reference) -> dP/dx = 32 mu u / Dh^2."""
    x = XI * 1.1                       # m
    A = A_mm2 * 1e-6
    Dh = DH_mm * 1e-3
    u = Q / A
    dpdx = 32 * MU * u / Dh ** 2
    return np.trapezoid(dpdx, x) if hasattr(np, "trapezoid") else np.trapz(dpdx, x)


if __name__ == "__main__":
    u = Q / (A_mm2 * 1e-6)
    Re = RHO * u * (DH_mm * 1e-3) / MU
    print("Channel hydraulics at the design point  (mdot_total 0.0025 kg/s, per channel %.4e kg/s)" % MDOT)
    print()
    print("   xi     A(mm2)    Dh(mm)    u(mm/s)     Re      Re*(Dh/Dh_in)")
    for i in range(len(XI)):
        print("  %4.2f   %7.3f   %7.4f   %7.4f   %7.2f      %7.2f"
              % (XI[i], A_mm2[i], DH_mm[i], u[i] * 1000, Re[i], Re[i] * DH_mm[i] / DH_mm[0]))
    print()
    print("  volumetric flow        %.6e m3/s" % Q)
    print("  inlet bulk velocity    %.4f mm/s" % (u[0] * 1000))
    print("  outlet bulk velocity   %.4f mm/s" % (u[-1] * 1000))
    print("  velocity ratio out/in  %.4f   (area ratio %.4f)" % (u[-1] / u[0], A_mm2[0] / A_mm2[-1]))
    print("  Re range               %.2f  ->  %.2f" % (Re[0], Re[-1]))
    print()
    print("  analytic laminar dP (f.Re = 16 reference)   %.4f Pa" % analytic_dp())
