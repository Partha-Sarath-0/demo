# GRAIL CFD — Environment Audit
Performed before any case was created, as the brief requires.

## Platform
| Item | Value |
|---|---|
| OS | Ubuntu 24.04.4 LTS (x86_64) |
| CPU cores | 2 |
| RAM | 7 GB |
| Free disk | 26 GB |
| MPI | Open MPI 4.1.6 |
| gmsh | 4.15.2 |
| Python | numpy 2.4.4, scipy 1.17.1, pyvista 0.48.4 |

## OpenFOAM
| Item | Value |
|---|---|
| Distribution | OpenFOAM ESI (openfoam Ubuntu package) |
| Version | v1912 (WM_PROJECT_VERSION=v1912) |
| Package | 1912.200626-2build3 |
| WM_PROJECT_DIR | /usr/share/openfoam |

## Capability matrix (verified by inspecting the installed binaries/libraries)
| Requirement | Available | Implementation |
|---|---|---|
| Steady multi-region CHT | YES | chtMultiRegionSimpleFoam |
| Transient multi-region CHT | YES | chtMultiRegionFoam |
| Laminar incompressible flow | YES | simpleFoam / icoFoam (verification stages) |
| Pure conduction verification | YES | laplacianFoam |
| Surface-to-surface radiation | YES | radiationModel `viewFactor` (+ viewFactorsGen) |
| Participating-media radiation | YES | fvDOM, P1 |
| Solar load | YES | radiationModel `solarLoad` |
| Opaque diffuse wall radiation | YES | boundaryRadiationProperties: opaqueDiffuse / opaqueReflective / transparent |
| CHT + radiation coupled interface | YES | turbulentTemperatureRadCoupledMixed |
| CHT interface (no radiation) | YES | turbulentTemperatureCoupledBaffleMixed |
| External convection + radiation + ambient | YES | externalWallHeatFluxTemperature |
| Thin thermal layers / contact resistance | YES | externalWallHeatFluxTemperature `thicknessLayers`/`kappaLayers`; thermalBaffle |
| PCM phase change | YES | fvOption `solidificationMeltingSource` (apparent-Cp / enthalpy-porosity) |
| Cyclic (periodic) patches | YES | createPatch cyclic; checked by patch area/face match |
| Region splitting | YES | splitMeshRegions -cellZones |
| Mesh import | YES | gmshToFoam, fluentMeshToFoam, snappyHexMesh |
| Mesh quality metrics | YES | checkMesh (non-orthogonality, skewness, aspect ratio, volume, face pyramids) |
| Parallel | YES | decomposePar / reconstructPar, Open MPI 4.1.6 |
| Post-processing | YES | postProcess, foamToVTK, function objects, pyvista |

## Not natively available — routes identified
| Gap | Route |
|---|---|
| Temperature-dependent glazing transmittance (thermotropic) | Not a native BC. Implement as a time/temperature-updated absorbed-flux source via `codedFixedValue`/`codedMixed` (requires runtime compilation, available) or an outer-loop controller script that updates the absorbed heat flux from the previous iterate's layer temperature. Continuous logistic transition, no discontinuity. |
| Anisotropic / graphite-enhanced PCM conductivity | v1912 solid thermo supports isotropic kappa per region. Enhanced PCM to be represented by documented effective isotropic properties, clearly distinguished from base PCM. No invented anisotropy. |

## Binding constraint
2 cores / 7 GB RAM. This does not limit fidelity; it limits CAMPAIGN SIZE.
Per-case cost must be measured on the real mesh before a campaign size is committed.
