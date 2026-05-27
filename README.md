# Ferrite Experiment Completion Pipeline

This repository supports a finite-element-based design and evaluation framework for multilayer cylindrical thin-ferrite shells.

The current goal is reproducibility, not claiming unsupported numerical results. Missing AEDT exports are marked as `planned`, `missing`, or `pending`; no script should fabricate field values or conclusions.

## Canonical Files

- Experiment matrix: `data/experiment_matrix_main.csv`
- Raw AEDT exports:
  - `data/raw/B0_reference_x.csv`
  - `data/raw/B0_reference_z.csv`
  - `data/raw/center_field_raw.csv`
  - `data/raw/intH2_layerwise_raw.csv`
- Processed outputs:
  - `data/processed/main_dataset.csv`
  - `data/processed/metrics_table.csv`
- Validation outputs:
  - `data/validation/B0_reference_validation.csv`
  - `data/validation/layerwise_intH2_validation.csv`
- Paper figures: `figures/`
- Manual AEDT checklist: `docs/AEDT_MANUAL_EXECUTION_CHECKLIST.md`
- Repository audit: `docs/REPO_AUDIT.md`

## From AEDT to Paper Figures

1. Complete or verify the AEDT projects listed in `data/experiment_matrix_main.csv`.
2. Export B0 references:

```text
B0_Bx_T;B0_By_T;B0_Bz_T;B0_Mag_T
```

3. Export shielded center fields:

```text
Bcenter_Bx_T;Bcenter_By_T;Bcenter_Bz_T;Bcenter_Mag_T
```

4. Export virtual pickup-coil integrals:

```text
IntH2_total;IntH2_L1;IntH2_L2;...
```

5. Run:

```powershell
python scripts\postprocess\build_dataset.py
python scripts\postprocess\compute_metrics.py
python scripts\postprocess\validate_B0_reference.py
python scripts\postprocess\validate_layerwise_intH2.py
python scripts\plotting\plot_paper_figures.py
```

## AEDT Batch Dry Run

Use dry-run mode to inspect eligible built/solved cases without launching AEDT:

```powershell
python scripts\aedt_export\run_aedt_batch.py --dry-run
```

Run a single case:

```powershell
python scripts\aedt_export\run_aedt_batch.py --dry-run --case-id C1_N1_t008_x
```

## Paper Use Rule

A case may be marked `used_in_paper` only if:

- required B0 reference exists;
- shielded center field is exported;
- required `IntH2` fields are exported;
- B0 direction validation passes;
- layerwise `IntH2` validation passes when applicable;
- the row is processed into `data/processed/metrics_table.csv`.

Legacy thick-shell data must not be mixed into manufacturable thin-ferrite main results.
