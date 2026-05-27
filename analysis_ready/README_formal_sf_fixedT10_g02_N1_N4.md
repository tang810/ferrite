# Historical formal SF experiment: fixedT10_g02, N=1..4

This file is now historical. The active next experiment has moved to manufacturable thin ferrite sheets:

```text
0.08 mm <= ferrite layer thickness <= 0.60 mm
```

Use these files for the current experiment:

```text
next_round_design_points.csv
analysis_ready/manufacturable_thin_ferrite_sim_matrix.csv
analysis_ready/README_manufacturable_thin_ferrite_sim.md
```

The old `fixedT10_g02` matrix can still be used as a thick-shell reference, but it should not be the next priority because its per-layer thickness is outside the current mechanical constraint.

## Original Purpose

## Purpose

Compare 1--4 ferrite-layer cylindrical shells under the same radial design space:

```text
T_space = 10 mm
g = 0.2 mm for N >= 2
a = (T_space - (N - 1)g) / N
```

The key output is not only whether `SF` increases. The useful check is:

```text
SF_multi >= SF_single or close to the target
material_volume_multi < material_volume_single
B_avg_1_30_fT or IntH2_total is not unacceptably higher
```

## Files

- `formal_sf_fixedT10_g02_N1_N4_matrix.csv`: run matrix and material volume.
- `formal_sf_fixedT10_g02_N1_N4_center_fields_template.csv`: fill this after AEDT exports center fields.

## AEDT exports for each layer count

Use the same external-field excitation for both models:

1. No-shield reference model: ferrite changed to vacuum, export `B0_T`, `B0_Bx_T`, `B0_By_T`, `B0_Bz_T`.
2. Shield model: ferrite material retained, export `Bcenter_T`, `Bcenter_Bx_T`, `Bcenter_By_T`, `Bcenter_Bz_T`.
3. For noise, export `IntH2_total` and every available `IntH2_Li`.

Then compute:

```text
SF = abs(B0_T) / abs(Bcenter_T)
LeakageRatio = abs(Bcenter_T) / abs(B0_T)
```

## Current status

The 4-layer case has a partial formal SF result in:

```text
SF_4ceng_fixedT10_g02_summary.csv
```

It should be reused only after confirming that the external-field excitation and center point are identical to the N=1--3 models.
