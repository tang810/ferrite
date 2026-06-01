# Remaining TODO Before IEEE TIM Submission

This file lists results that still cannot enter the paper conclusions under the current data-use rules.

## Data Currently Eligible for Conclusions

- `B0_reference_x`: passed direction validation and is used for `SFx`.
- `B0_reference_z`: passed direction validation, but is only a reference until shielded z-directed exports exist.
- Seven transverse continuous-shell cases are valid for current conclusions:
  - `C1_N1_t008_x`
  - `C1_N1_t020_x`
  - `C1_N1_t040_x`
  - `C1_N1_t060_x`
  - `C2_N2_t020_g010_x`
  - `C2_N3_t020_g010_x`
  - `C2_N4_t015_g008_x`
- Layerwise IntH2 checks passed for the seven transverse continuous-shell cases.
- Mesh convergence numeric checks passed for `C1_N1_t008_x` and `C2_N4_t015_g008_x`; total elements, adaptive passes, and air-domain metadata were not exported.
  These checks support scalar mesh-trend reporting only; they do not support a complete numerical-robustness claim.

## Results Still Excluded

### Boundary-Domain Convergence

Missing valid exports for `C2_N4_t015_g008_x` at:

- `2R`
- `3R`
- `5R`

Until these are exported, the manuscript must not claim full numerical robustness or completed boundary-domain convergence.

### Mesh Metadata

The mesh convergence rows still lack:

- total element count
- adaptive-pass count
- air-domain scale

These columns are present in the updated CSV schema, but the values remain blank because no raw export was available.

### Axial Shielding

`B0_reference_z` is valid, but the following shielded z cases are still missing:

- `C1_N1_t060_z`
- `C2_N3_t020_g010_z`
- `C2_N4_t015_g008_z`

Therefore `SFz`, `LeakageRatioz`, and `SFz/SFx` cannot enter conclusions, and the `SFx` ranking cannot be generalized to axial shielding.

### Segmented-Shell Correction

Missing valid segmented exports for `C2_N4_t015_g008_x` with `Nseg=12` and `g_phi=1.6 mm`:

- aligned slots
- staggered slots

Therefore `SFx_seg/SFx_cont` and `IntH2_seg/IntH2_cont` cannot be reported as results, and manufacturable segmented assembly performance remains unverified.

### Permeability Sensitivity

Only `mu_r'=1000` baseline rows are available. Missing:

- `C1_N1_t060_x`: `mu_r'=500`, `2000`, `5000`
- `C2_N4_t015_g008_x`: `mu_r'=500`, `2000`, `5000`

Therefore ranking robustness against permeability variation cannot be claimed.

### Field-Map Exports

Missing real AEDT field-map exports:

- external-field `B` distribution for `C1_N1_t060_x` and `C2_N4_t015_g008_x`
- flux lines for the same comparison
- virtual-coil `H_vc` contours
- virtual-coil `H_vc^2` contours

Therefore Discussion may describe the scalar layerwise IntH2 distribution, but must not give a strong physical mechanism explanation for the high outer-layer contribution.

### Prototype Measurement

No prototype SF measurement data are available. The prototype section remains a protocol only.
