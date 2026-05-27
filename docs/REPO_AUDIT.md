# Ferrite Repository Audit

中文说明：
本文档记录当前 ferrite 仓库的文件审计结果，用于区分 current manufacturable thin-ferrite
主实验、legacy thick-shell 历史数据、可直接用于论文的材料，以及仍缺失的数据。

Date: 2026-05-27

Branch: `experiment-completion-pipeline`

Scope: multilayer cylindrical thin-ferrite shell project for a finite-element-based design and evaluation framework. This audit does not treat any incomplete AEDT or CSV export as a paper result.

## Current AEDT Projects

### Manufacturable Thin-Ferrite Candidates

These are the most relevant AEDT projects for the current paper direction. They live under `round2_working/manufacturable_thin/`.

| Project | Interpreted role | Current use |
|---|---|---|
| `C1_N1_t008_B0.aedt` | no-shield/reference variant for single-layer 0.08 mm setup | candidate source project, exports still need verification |
| `C1_N1_t008_shield.aedt` | shielded continuous shell, N=1, a=0.08 mm | priority-1 candidate, not yet accepted as paper result |
| `C1_N1_t020_B0.aedt` | no-shield/reference variant for single-layer 0.20 mm setup | candidate source project, exports still need verification |
| `C1_N1_t020_shield.aedt` | shielded continuous shell, N=1, a=0.20 mm | priority-1 candidate, not yet accepted as paper result |
| `C1_N1_t040_B0.aedt` | no-shield/reference variant for single-layer 0.40 mm setup | candidate source project, exports still need verification |
| `C1_N1_t040_shield.aedt` | shielded continuous shell, N=1, a=0.40 mm | priority-1 candidate, not yet accepted as paper result |
| `C1_N1_t060_B0.aedt` | no-shield/reference variant for single-layer 0.60 mm setup | candidate source project, exports still need verification |
| `C1_N1_t060_shield.aedt` | shielded continuous shell, N=1, a=0.60 mm | priority-1 candidate, not yet accepted as paper result |
| `C2_N2_t020_g010_B0.aedt` | no-shield/reference variant for N=2 setup | candidate source project, exports still need verification |
| `C2_N2_t020_g010_shield.aedt` | shielded continuous shell, N=2, a=0.20 mm, g=0.10 mm | priority-1 candidate, not yet accepted as paper result |
| `C2_N3_t020_g010_B0.aedt` | no-shield/reference variant for N=3 setup | candidate source project, exports still need verification |
| `C2_N3_t020_g010_shield.aedt` | shielded continuous shell, N=3, a=0.20 mm, g=0.10 mm | priority-1 candidate, not yet accepted as paper result |
| `C2_N4_t015_g008_B0.aedt` | no-shield/reference variant for N=4 setup | candidate source project, exports still need verification |
| `C2_N4_t015_g008_shield.aedt` | shielded continuous shell, N=4, a=0.15 mm, g=0.08 mm | priority-1 candidate, not yet accepted as paper result |

### Legacy / Historical AEDT Projects

The following projects are useful historical context but are not the manufacturable thin-ferrite main matrix:

- Root-level `Project100_1ceng.aedt`, `Project100_2ceng.aedt`, `Project100_3ceng.aedt`, `Project100_4ceng.aedt`
- Root-level backups `Project100_*bak*`
- `Project100_4ceng_fixedT10_g02_ext_ferrite.aedt`
- `round2_working/Project100_*`
- `Cubic ferrite shielding(1).aedt`
- `Project1.aedt`, `Project2.aedt`, `Project3.aedt`, `Project4.aedt`, `Project5.aedt`
- `halbach_catapult.aedt`

These files should not be deleted. If they are later reorganized, they should be moved into `aedt/legacy/` with a note in the relevant README.

## Current CSV Results

### Current Manufacturable Thin-Ferrite Files

| File | Role | Paper readiness |
|---|---|---|
| `analysis_ready/manufacturable_thin_ferrite_sim_matrix.csv` | current/planned matrix | usable as planning input after normalization |
| `next_round_design_points.csv` | compact next-run matrix | usable as planning input after normalization |
| `analysis_ready/manufacturable_thin_center_fields_template.csv` | export template | usable as manual/AEDT export template |
| `analysis_ready/manufacturable_thin_center_fields_exported.csv` | partial exports | partial only; not sufficient for final paper results |
| `analysis_ready/manufacturable_thin_evaluated.csv` | legacy evaluation output | pipeline smoke input only; contains incomplete rows |
| `analysis_ready/manufacturable_thin_dataset.csv` | generated merged dataset | generated; paper use depends on complete exports |
| `analysis_ready/manufacturable_thin_metrics.csv` | generated metrics table | generated; values from incomplete rows must not be used as conclusions |
| `analysis_ready/layerwise_intH2_validation.csv` | generated validation table | usable for checking completeness/consistency |

### Legacy Thick-Shell / Historical Result Files

These files are legacy or exploratory results and must not be mixed into the manufacturable thin-ferrite main results:

- `analysis_ready/all_results_clean*.csv`
- `analysis_ready/all_results_layerwise.csv`
- `analysis_ready/agmatrix_clean.csv`
- `analysis_ready/asweep_clean.csv`
- `analysis_ready/Tcompare_clean.csv`
- `analysis_ready/formal_sf_fixedT10_g02_*`
- `analysis_ready/SF_4ceng_fixedT10_g02_*`
- `analysis_ready/matlab_B_results/*.csv`
- Root-level `result_*`, `P_*`, `100_*.csv`, `2.csv`, `3.csv`, `3ce.csv`, `4ceng_g.csv`

## Scripts

### Existing AEDT/Export Helpers

Most existing AEDT scripts are under `round2_working/` and were written for exploratory runs. They are useful references but not a clean reproducible paper pipeline yet.

Examples:

- `round2_working/run_manufacturable_thin_continuous.py`
- `round2_working/export_manufacturable_thin_results.py`
- `round2_working/export_Bcenter_*.py`
- `round2_working/solve_manufacturable_thin_projects.py`

### Existing Post-Processing Scripts

Some scripts exist under `analysis_ready/`, but they use older naming or mixed legacy concepts:

- `analysis_ready/evaluate_manufacturable_thin_results.py`
- `analysis_ready/compute_SF_from_B0_Bcenter.py`
- `analysis_ready/merge_*`

The new pipeline should live under:

- `scripts/aedt_export/`
- `scripts/postprocess/`
- `scripts/plotting/`

## Paper Files

Current draft:

- `多层圆柱壳磁屏蔽论文/paper_intro_methods_draft.md`

No file named `paper_intro_methods_draft(3).md` was found in the working tree at audit time. A standalone results skeleton should therefore be generated under `paper/results_skeleton.md`.

## Directly Usable for Paper

At audit time, the following are directly usable:

- Experiment definitions and planned matrix structure.
- AEDT project file inventory.
- Export field naming convention.
- Post-processing pipeline definitions.
- Manuscript Methods/Results skeleton text that explicitly marks missing data as pending.

The current partial CSV exports are not sufficient for final numerical conclusions.

## Completed Data

The following data have been verified and exported through the canonical pipeline:

- `B0_reference_x`: canonical x-directed tangential-H no-shield reference.
  Source: `aedt/reference/B0_reference_x.aedt`; `data/raw/B0_reference_x.csv`; `data/validation/B0_reference_validation.csv` reports `validation_status=passed`.
  B0_Bx_T = 1.257e-06 T, B0 direction ratio > 1e7.
- Single-layer transverse shielded center-field exports (C1_N1_t008_x, C1_N1_t020_x, C1_N1_t040_x, C1_N1_t060_x).
  All four cases rebuilt with x-directed tangential-H matching B0_reference_x, solved, and exported to `data/raw/center_field_raw.csv`.
  All four cases have metric_status=processed, SFx > 1, used_in_paper=no.
- Single-layer transverse layerwise IntH2 exports for the same four cases.
  Exported to `data/raw/intH2_layerwise_raw.csv`; IntH2_total = IntH2_L1 for all cases; `data/validation/layerwise_intH2_validation.csv` reports `validation_status=passed`.

## Missing Data

The following data are missing or incomplete for a reproducible paper result set:

- Verified `B0_reference_z` export with `B0_Bx_T`, `B0_By_T`, `B0_Bz_T`, `B0_Mag_T`.
- Shielded center-field exports for multilayer (`C2_*`), axial (`*_z`), segmented (`S*`), and sensitivity (`MU_*`, `MESH_*`) cases.
- Layerwise `IntH2_Li` exports for multilayer, axial, segmented, and sensitivity cases.
- Selected `z`-field axial extensions.
- Segmented aligned and staggered shell corrections.
- Mesh and boundary-domain convergence studies.
- Permeability sensitivity sweep for representative candidates.

## Reorganization Policy

No original files should be deleted. Reorganization should be additive unless explicitly approved:

- New canonical inputs go to `data/raw/`, `data/processed/`, and `data/validation/`.
- New scripts go to `scripts/`.
- New paper-facing figures go to `figures/`.
- Legacy and exploratory files remain in place until a separate archival commit moves them with documentation.
