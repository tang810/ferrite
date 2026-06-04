# Hybrid Outer-Layer Results Snippet

Under the same outer-layer geometry, with an outer-layer thickness of 0.20 mm
and a 0.40 mm radial assembly gap outside the four-layer ferrite shield, the
nanocrystalline case provides a larger transverse shielding factor and a lower
magnetic-noise-related integral than the amorphous case.

| Configuration | mu_r | SFx | SFx gain | IntH2_total | IntH2 ratio |
|---|---:|---:|---:|---:|---:|
| Four-layer ferrite baseline | 1000 | 3.629 | 1.000 | 4.160e-06 | 1.000 |
| Ferrite + amorphous outer layer | 10000 | 8.548 | 2.355 | 6.283e-07 | 0.151 |
| Ferrite + nanocrystalline outer layer | 50000 | 25.146 | 6.929 | 5.333e-08 | 0.0128 |

The nanocrystalline outer layer gives approximately 2.94 times the
SFx of the amorphous outer-layer case and approximately 0.085 times
its IntH2_total. Therefore, for the current simulation assumptions, the
nanocrystalline outer layer is selected as the preferred P2 prototype candidate.

These results should be described as simulation-based screening results. The
outer-layer permeabilities, loss parameters, and electrical conductivities must
be replaced or checked against vendor data or measurements before making final
material claims, and magnetometer sensitivity must still be verified by PSD
measurements.
