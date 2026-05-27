# Results Section Skeleton

This file is a paper-ready scaffold for the multilayer cylindrical thin-ferrite shell study. It must not be converted into numerical claims until the required AEDT exports and validation outputs exist.

## III. Results

### A. Verification of B0 Reference Fields

Required data:

- `data/raw/B0_reference_x.csv`
- `data/raw/B0_reference_z.csv`
- `data/validation/B0_reference_validation.csv`

Required fields:

- `B0_Bx_T`
- `B0_By_T`
- `B0_Bz_T`
- `B0_Mag_T`

Planned table:

- Table: B0 reference direction check for x-directed and z-directed external fields.

Interpretation:

- For `B0_reference_x`, `B0_Bx_T` should dominate `B0_By_T` and `B0_Bz_T`.
- For `B0_reference_z`, `B0_Bz_T` should dominate `B0_Bx_T` and `B0_By_T`.
- If either reference is missing or fails direction validation, all corresponding shielding factors remain pending.

Status: pending.

### B. Continuous-Shell Single-Layer Baselines

Required data:

- `data/processed/main_dataset.csv`
- `data/processed/metrics_table.csv`

Cases:

- `C1_N1_t008_x`
- `C1_N1_t020_x`
- `C1_N1_t040_x`
- `C1_N1_t060_x`

Required figure:

- `figures/Fig3_SFx_vs_Vf.png`
- `figures/Fig7_SFx_vs_Tspace.png`

Interpretation:

- Compare single-layer transverse shielding efficiency as ferrite thickness increases.
- Report `SFx`, `LeakageRatiox`, `Vf_mm3`, `etaS_star`, and `IntH2_total` only for complete and validated rows.
- Missing rows remain pending.

Status: pending.

### C. Multilayer Continuous-Shell Screening

Required data:

- `data/processed/metrics_table.csv`

Cases:

- `C2_N2_t020_g010_x`
- `C2_N3_t020_g010_x`
- `C2_N4_t015_g008_x`

Required figures:

- `figures/Fig3_SFx_vs_Vf.png`
- `figures/Fig4_IntH2_vs_Vf.png`
- `figures/Fig7_SFx_vs_Tspace.png`

Interpretation:

- Compare multilayer continuous-shell cases against single-layer baselines.
- Do not include `C2_N6_t010_g008_x` in the main results unless priority-1 results show clear multilayer benefit and the optional case is solved, exported, processed, and validated.

Status: pending.

### D. Fixed-Ferrite-Volume Comparison

Required data:

- `data/processed/metrics_table.csv`

Candidate comparison:

- single-layer `a = 0.60 mm`
- three-layer `3 x 0.20 mm`
- four-layer `4 x 0.15 mm`

Required figure:

- `figures/Fig5_eta_chi_comparison.png`

Interpretation:

- Use exact ferrite volume `Vf_mm3`, not only `T_ferrite_total_mm`.
- Compare `SFx`, `LeakageRatiox`, `etaS_star`, `rhoH`, and `chiH`.
- Avoid claiming material saving unless the target shielding factor and validation conditions are both satisfied.

Status: pending.

### E. Layer-Resolved IntH2 Contributions

Required data:

- `data/raw/intH2_layerwise_raw.csv`
- `data/validation/layerwise_intH2_validation.csv`
- `data/processed/metrics_table.csv`

Required figure:

- `figures/Fig6_layerwise_IntH2_fraction.png`

Interpretation:

- Show `IntH2_Li / IntH2_total`.
- Cases with `failed_validation` must be excluded from paper figures.
- Discuss whether inner or outer layers dominate only after validation passes.

Status: pending.

### F. Axial-Field Extension for Selected Candidates

Required data:

- `data/raw/B0_reference_z.csv`
- z-directed selected shielded exports
- `data/processed/metrics_table.csv`

Required figure:

- `figures/Fig8_axial_vs_transverse_selected.png`

Interpretation:

- Compare `SFx` and `SFz` only for candidates with both x and z exports.
- Do not infer axial shielding from transverse results.

Status: pending.

### G. Segmented-Shell Correction

Required data:

- segmented aligned exports
- segmented staggered exports
- corresponding continuous-shell baseline rows

Required figure:

- `figures/Fig9_segmented_penalty.png`

Interpretation:

- Compare continuous shell, aligned slots, and staggered slots.
- Report segmentation penalty only after all paired rows are complete.

Status: pending.

### H. Mesh and Boundary Convergence

Required data:

- mesh convergence runs for `MESH_C1_N1_t008_x`
- mesh convergence runs for `MESH_C2_N4_t015_g008_x`
- boundary-domain convergence runs for selected cases

Planned table:

- Mesh density / boundary size versus `Bcenter`, `SFq`, and `IntH2_total`.

Interpretation:

- A row is accepted only when convergence is within the predefined tolerance.
- Missing convergence data means final numerical claims remain pending.

Status: pending.

### I. Permeability Sensitivity

Required data:

- `MU_C2_N3_t020_g010_x_mu500`
- `MU_C2_N3_t020_g010_x_mu2000`
- `MU_C2_N3_t020_g010_x_mu5000`
- baseline `C2_N3_t020_g010_x`

Planned figure:

- permeability sensitivity plot for `SFx`, `LeakageRatiox`, and `IntH2_total`.

Interpretation:

- Use this section to test ranking robustness.
- Do not treat screening permeability as measured material performance.

Status: pending.
