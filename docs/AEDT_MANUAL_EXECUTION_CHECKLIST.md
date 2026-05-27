# AEDT Manual Execution Checklist

中文说明：
本文档是手动补全 AEDT 实验的逐步操作清单。每完成一个 case，都应按本文档导出中心场和
IntH2 分层结果，再运行后处理和验证脚本。没有完成导出的 case 不应进入论文图表。

This checklist is for the multilayer cylindrical thin-ferrite shell project. It must be followed without inventing missing exports. If a step cannot be completed, mark the corresponding case as `missing` or `failed` in `data/experiment_matrix_main.csv` and document the reason.

## 1. Build `B0_reference_x`

1. Open AEDT / Ansys Electronics Desktop.
2. Create or copy a no-shield model with the same air domain, boundary size, coordinate system, and center observation point as the shielded models.
3. Assign ferrite bodies to vacuum or remove them from the reference model.
4. Set external uniform field in the Cartesian `x` direction.
5. Solve the magnetostatic setup.
6. Export center point fields:
   - `B0_Bx_T`
   - `B0_By_T`
   - `B0_Bz_T`
   - `B0_Mag_T`
7. Save the export as `data/raw/B0_reference_x.csv`.

## 2. Build `B0_reference_z`

1. Copy `B0_reference_x`.
2. Rotate the external uniform field direction to Cartesian `z`, the cylinder axis.
3. Keep the same air domain, boundary condition, mesh strategy, and center observation point.
4. Solve the magnetostatic setup.
5. Export:
   - `B0_Bx_T`
   - `B0_By_T`
   - `B0_Bz_T`
   - `B0_Mag_T`
6. Save the export as `data/raw/B0_reference_z.csv`.

## 3. Copy Single-Layer Continuous-Shell Projects and Modify `a`

1. Use the existing single-layer project as a template.
2. Save as `C1_N1_t008_x`, `C1_N1_t020_x`, `C1_N1_t040_x`, or `C1_N1_t060_x`.
3. Set:
   - `N_layers = 1`
   - `t_ferrite_mm = a`
   - `g_radial_mm = 0`
   - `Rin_mm = 100`
   - `H_mm = 200`
4. Confirm the cylinder is open-ended unless the matrix explicitly says otherwise.
5. Keep ferrite material as the screening material, currently `mu_r = 1000`, `sigma = 0.01 S/m`.

## 4. Copy Multilayer Continuous-Shell Projects and Modify `N`, `a`, `g`

1. Use an existing multilayer shell project as a template.
2. Save with the exact case ID from `data/experiment_matrix_main.csv`.
3. Keep each ferrite layer as an independent solid body:
   - `ferrite_L1`
   - `ferrite_L2`
   - `ferrite_L3`
   - `ferrite_L4`
4. Set layer radii from:
   - `R_i,in = Rin + (i - 1)(a + g)`
   - `R_i,out = R_i,in + a`
5. Do not unite ferrite layers.
6. Confirm total radial occupation:
   - `T_space = N*a + (N - 1)*g`

## 5. Set External `x`-Directed Uniform Field

1. Use the same boundary method for every `x` case, such as tangential `H`-field boundary or AEDT uniform magnetic field setup.
2. Confirm that the no-shield model produces dominant `B0_Bx_T` at the center.
3. Keep the excitation amplitude identical across B0 and shielded cases.

## 6. Set External `z`-Directed Uniform Field

1. Copy the `x` setup.
2. Rotate the excitation to `z`, the cylinder axis.
3. Confirm that the no-shield model produces dominant `B0_Bz_T` at the center.
4. Do not infer axial shielding from transverse results.

## 7. Export Center Point `Bx`, `By`, `Bz`, and `Mag_B`

For each shielded case:

1. Create a center point at the geometric center of the cylindrical protected volume.
2. Export:
   - `Bcenter_Bx_T`
   - `Bcenter_By_T`
   - `Bcenter_Bz_T`
   - `Bcenter_Mag_T`
3. Append or save to `data/raw/center_field_raw.csv`.
4. Include:
   - `case_id`
   - `model_type`
   - `field_dir`
   - `source_project`
   - `status`

For no-shield reference cases, export to `data/raw/B0_reference_x.csv` or `data/raw/B0_reference_z.csv`.

## 8. Set `IntH2_Li` and `IntH2_total`

For each continuous-shell case:

1. Open Field Calculator.
2. Select `H`.
3. Take magnitude `Mag`.
4. Square it.
5. Integrate over one ferrite layer body.
6. Save named expression:
   - `IntH2_L1`
   - `IntH2_L2`
   - `IntH2_L3`
   - `IntH2_L4`
7. Define:
   - `IntH2_total = IntH2_L1 + IntH2_L2 + ... + IntH2_LN`
8. Do not use old names such as `InH2_s4`, `IntH2_s1`, or `IntH2_cyl2` in new projects.
9. If an old project contains legacy names, log a warning and mark that case as `legacy-compatible` in notes until renamed.

## 9. Check `IntH2_total` Against Layerwise Sum

1. Export `IntH2_total` and all `IntH2_Li`.
2. Run:

```powershell
python scripts\postprocess\validate_layerwise_intH2.py
```

3. Accept the case only if:

```text
abs(IntH2_total - sum(IntH2_Li)) / IntH2_total < 1e-3
```

4. Failed cases must not be marked `used_in_paper`.

## 10. Build Segmented Aligned Models

1. Select the continuous-shell candidate.
2. Split each cylindrical layer into `N_segments = 12` ferrite strips.
3. Set circumferential arc gap `gphi = 1.6 mm`.
4. Align all slot angular positions across layers.
5. Save with `aligned` in the case ID.
6. Export center field and `IntH2_total`.

## 11. Build Segmented Staggered Models

1. Start from the aligned segmented model.
2. Rotate the slot pattern of adjacent layers by:

```text
Delta_phi_i = (i - 1) * pi / N_segments
```

3. Confirm that a slot in one layer is covered by ferrite in the neighboring layer.
4. Save with `staggered` in the case ID.
5. Export center field and `IntH2_total`.

## 12. Naming Rules

Use exact case IDs from `data/experiment_matrix_main.csv`.

Recommended project naming:

```text
B0_reference_x.aedt
B0_reference_z.aedt
C1_N1_t008_x.aedt
C1_N1_t020_x.aedt
C1_N1_t040_x.aedt
C1_N1_t060_x.aedt
C2_N2_t020_g010_x.aedt
C2_N3_t020_g010_x.aedt
C2_N4_t015_g008_x.aedt
S2_N3_t020_g010_seg12_aligned_x.aedt
S2_N3_t020_g010_seg12_staggered_x.aedt
```

Recommended export table names:

```text
data/raw/B0_reference_x.csv
data/raw/B0_reference_z.csv
data/raw/center_field_raw.csv
data/raw/intH2_layerwise_raw.csv
```

## Pipeline After Manual Export

After exports are complete, run:

```powershell
python scripts\postprocess\build_dataset.py
python scripts\postprocess\compute_metrics.py
python scripts\postprocess\validate_B0_reference.py
python scripts\postprocess\validate_layerwise_intH2.py
python scripts\plotting\plot_paper_figures.py
```

Only rows with complete exports and passed validation may be promoted to `used_in_paper`.
