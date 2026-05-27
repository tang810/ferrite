# Validation Changelog for IEEE TIM Preparation

中文说明：本文档记录本轮为 IEEE TIM 投稿准备新增的数据闭环、脚本、图件和论文结构。所有缺失数据均以 TODO 或 pending 标记，未编造任何 AEDT 或实验数值。

## Added Data Templates and Processed Tables

- Added `data/raw/mesh_convergence_exports.csv`.
  - Contains exported mesh-convergence values for `C1_N1_t008_x` and `C2_N4_t015_g008_x`.
  - `total_elements` and `air_domain_size` remain blank because they were not exported.
- Added `data/raw/boundary_convergence_exports.csv`.
  - Template for 2R/3R/5R/7R air-domain convergence.
- Added `data/raw/axial_shielding_exports.csv`.
  - Template for `C1_N1_t060_z`, `C2_N3_t020_g010_z`, and `C2_N4_t015_g008_z`.
- Added `data/raw/segmented_shell_exports.csv`.
  - Includes real continuous baseline row for `C2_N4_t015_g008_x`.
  - Aligned and staggered segmented cases remain pending.
- Added `data/raw/permeability_sweep_exports.csv`.
  - Includes real `mu_r'=1000` baseline rows for `C1_N1_t060_x` and `C2_N4_t015_g008_x`.
  - `mu_r'=500/2000/5000` rows remain pending.
- Added `data/raw/experimental_sfx_measurement.csv`.
  - Prototype SF measurement template only; no experimental data are present.

## Added Scripts

- Added `scripts/postprocess/process_validation_studies.py`.
  - Generates:
    - `data/processed/mesh_convergence_metrics.csv`
    - `data/validation/mesh_convergence_validation.csv`
    - `data/processed/boundary_convergence_metrics.csv`
    - `data/processed/axial_shielding_metrics.csv`
    - `data/processed/segmented_shell_metrics.csv`
    - `data/processed/permeability_sensitivity_metrics.csv`
    - `data/processed/experimental_sfx_metrics.csv`
    - `data/processed/uncertainty_budget.csv`
- Added `scripts/plotting/plot_validation_figures.py`.
  - Generates real plots where processed data exist.
  - Generates explicit TODO placeholder PNGs where AEDT or experimental exports are missing.

## Added Figures

- `figures/Fig1_measurement_framework.png` placeholder.
- `figures/Fig2_multilayer_cylindrical_geometry.png` placeholder.
- `figures/Fig3_SFx_vs_Vf.png` from processed transverse data.
- `figures/Fig4_fixed_volume_comparison.png` from processed transverse data.
- `figures/Fig5_Hvc2_field_map.png` placeholder.
- `figures/Fig6_external_B_field_comparison.png` placeholder.
- `figures/mesh_convergence_sfx.png` from mesh-convergence data.
- `figures/mesh_convergence_intH2.png` from mesh-convergence data.
- `figures/boundary_convergence.png` placeholder.
- `figures/sfx_sfz_comparison.png` placeholder because shielded z cases are missing.
- `figures/segmented_shell_comparison.png` placeholder because segmented exports are missing.
- `figures/permeability_sensitivity_sfx.png`, `figures/permeability_sensitivity_intH2.png`, and `figures/permeability_sensitivity_ranking.png` placeholders because the mu sweep is incomplete.
- `figures/experimental_vs_fem_sfx.png` placeholder because experimental data are absent.

## Manuscript Updates

- Added Results subsections for:
  - Mesh and Boundary-Domain Convergence
  - Axial Shielding Check for Equal-Volume Candidates
  - Segmented-Shell Correction for Manufacturable Assembly
  - Permeability Sensitivity
  - Prototype-Level Shielding-Factor Measurement Protocol
- Added real B0_reference_z validation values.
- Added mesh convergence table using available exported values.
- Explicitly marked missing shielded z, segmented, boundary-domain, permeability-sweep, field-map, and experimental data as TODO/pending.
- Revised the Abstract and Conclusion to distinguish completed data from pending validation.
