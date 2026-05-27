# Remaining TODO Before IEEE TIM Submission

中文说明：以下项目仍缺真实 AEDT 或实验导出。不得将这些项目写成已完成结果，不得用于最终论文结论。

## 1. Boundary-Domain Convergence

Missing exports:

- `C2_N4_t015_g008_x`, air-domain scale `2R`
- `C2_N4_t015_g008_x`, air-domain scale `3R`
- `C2_N4_t015_g008_x`, air-domain scale `5R`
- optional `7R`

Required output:

- `data/raw/boundary_convergence_exports.csv`
- `data/processed/boundary_convergence_metrics.csv`
- `figures/boundary_convergence.png`

Acceptance target:

- 3R to 5R SFx change < 1%
- 3R to 5R IntH2_total change < 2%

## 2. Axial Shielded Cases

B0_reference_z is available and validated. The following shielded cases are still missing:

- `C1_N1_t060_z`
- `C2_N3_t020_g010_z`
- `C2_N4_t015_g008_z`

Required exports:

- `Bcenter_Bx_T`
- `Bcenter_By_T`
- `Bcenter_Bz_T`
- `Bcenter_Mag_T`
- `IntH2_total` if virtual-coil z-direction comparison is required

No SFz conclusion may be written until these exports exist.

## 3. Segmented-Shell Correction

Missing AEDT segmented cases:

- `S_N4_t015_g008_seg12_aligned_x`
- `S_N4_t015_g008_seg12_staggered_x`

Required geometry:

- `Nseg = 12`
- `g_phi = 1.6 mm`
- `coverage_phi = 0.95`
- aligned slots and staggered slots

Required exports:

- `Bcenter_Bx_T`
- `SFx`
- `LeakageRatiox`
- `IntH2_total`

No manufacturability claim should be made from continuous-shell results alone.

## 4. Permeability Sensitivity

Only `mu_r'=1000` baseline rows are available. Missing sweeps:

- `C1_N1_t060_x`: `mu_r'=500, 2000, 5000`
- `C2_N4_t015_g008_x`: `mu_r'=500, 2000, 5000`

Required exports:

- `Bcenter_Bx_T`
- `SFx`
- `LeakageRatiox`
- `IntH2_total`
- `etaS_star`
- `rhoH`
- `chiH`

No robustness claim with respect to `mu_r'` may be made until the sweep is complete.

## 5. Field-Map Figures

Missing AEDT field-map exports:

- `H_vc` magnitude contour
- `H_vc^2` contour
- external-field `B` distribution
- external-field flux lines

Required comparisons:

- `C1_N1_t060_x`
- `C2_N4_t015_g008_x`

These maps are needed to support the physical interpretation of flux redistribution and outer-layer IntH2 dominance.

## 6. Prototype SF Measurement

No prototype-level SF data are available.

Required minimum measurement:

- no-shield `B0_x`
- shielded `Bcenter_x`
- optional no-shield and shielded z-direction measurements
- at least three repeats
- uncertainty budget

Use `data/raw/experimental_sfx_measurement.csv` as the input template.

## 7. Mesh Metadata

Mesh convergence values exist, but the following metadata are missing:

- total element count
- air-domain size used in each mesh run

These should be exported before final manuscript submission.
