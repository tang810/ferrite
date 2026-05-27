# Preliminary Figure Notes

These figures are preliminary continuous-shell transverse-field results. They do not include axial-field validation, segmented-shell correction, mesh convergence, boundary convergence, or permeability sensitivity.

## Data Sources

- Metrics: `data/processed/metrics_table.csv`
- Layerwise validation: `data/validation/layerwise_intH2_validation.csv`
- B0 validation: `data/validation/B0_reference_validation.csv`

## Included Cases

- `C1_N1_t008_x`
- `C1_N1_t020_x`
- `C1_N1_t040_x`
- `C1_N1_t060_x`
- `C2_N2_t020_g010_x`
- `C2_N3_t020_g010_x`
- `C2_N4_t015_g008_x`

## Figures

- `Fig3_SFx_vs_Vf.png`: `Vf_mm3` versus `SFx`.
- `Fig4_IntH2_vs_Vf.png`: `Vf_mm3` versus `IntH2_total`.
- `Fig5_eta_chi_comparison.png`: separate panels for `etaS_star`, `rhoH`, and `chiH`.
- `Fig6_layerwise_IntH2_fraction.png`: `IntH2_Li / IntH2_total` for validated multilayer cases.
- `Fig7_SFx_vs_Tspace.png`: `T_space_mm` versus `SFx`.

## Passed Checks

- `B0_reference_x` validation status is `passed`.
- The seven x-directed continuous-shell cases have `metric_status = processed`.
- Layerwise `IntH2_total` consistency is `passed` for all seven included cases.

## Pending Checks

- `B0_reference_z` and axial-field shielded cases remain pending.
- Segmented-shell aligned/staggered correction remains pending.
- Mesh and boundary convergence remain pending.
- Permeability sensitivity remains pending.

These figures should not be used as final paper conclusions until the pending checks are completed and the relevant rows are manually approved for `used_in_paper`.
