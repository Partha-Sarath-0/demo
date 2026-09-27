# Thesis abstract (final, Dataset Rev 4.1; replaces all earlier drafts)

A roll-bond solar absorber with twelve converging channels (G = 0.539935) was studied by computational fluid dynamics to compare alternating counter-current flow with parallel flow.

- **Hydraulics:** channel hydraulics were resolved with 3-D OpenFOAM simulations on grid-studied meshes.
- **Conjugate model:** the plate–fluid problem was solved with a reduced-order model (GRAIL-CHT). Its Nusselt closure came from 3-D conjugate CFD of a periodic two-channel strip, made possible by solving the energy equation on a frozen, separately converged flow.
- **Nusselt number:** three axial and three cross-section grids give 4.48 (GCI 2.1 %). This is consistent with the published H1 value for a semicircular duct. It replaces an earlier value of 2.92, which had been obtained under a non-physical peripheral boundary condition.
- **Model accuracy:** with this closure the reduced model reproduces the co-current 3-D solution to within 0.6 % in plate temperature spread. It overstates the uniformity benefit of alternating flow by about 2 percentage points.
- **Design space:** a 300-case Latin-Hypercube campaign compares two independent groups of 150 cases each. Alternating flow lowered mean thermal efficiency by 7.3 % (p = 2 × 10⁻⁸), and it did so at every flow rate. Its effect on plate-temperature uniformity was not significant overall (−1.1 %), but it depended on flow: the median plate standard deviation fell by 13 % above 3.3 g/s and rose by 17 % below 2.2 g/s.
- **Mechanism:** the 3-D solutions show why. Counter-flowing channels exchange heat through the plate, and about 40 % of the heat each channel absorbs is returned upstream.
- **Validation:** all comparisons are CFD-to-CFD or CFD-to-correlation. No experimental validation is claimed.
