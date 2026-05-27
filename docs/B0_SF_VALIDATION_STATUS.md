# B0/SF 数据链路当前状态

中文说明：本文档只记录 B0 reference 和 transverse shielding factor 的可信性排查。当前不写多层优于单层的结论，不扩展 N=6，不运行分段壳。

## 当前结论边界

- data pipeline has been prepared.
- `B0_reference_x` has been rebuilt and passed direction validation.
- Shielded single-layer exports are still incomplete.

## 已发现的问题

旧的 `analysis_ready/manufacturable_thin_center_fields_exported.csv` 中 `C1_N1_t008` 行包含一组 B0 导出：

| quantity | value |
|---|---:|
| `B0_Bx_T` | `-1.64663946855e-08` |
| `B0_By_T` | `5.63735384572e-09` |
| `B0_Bz_T` | `3.32604898501e-08` |
| `B0_Mag_T` | `3.65943171503e-08` |

对于 x-directed external field，`abs(B0_Bx_T)` 应明显大于 `abs(B0_By_T)` 和 `abs(B0_Bz_T)`。当前 `abs(B0_Bz_T)` 大于 `abs(B0_Bx_T)`，因此这组 B0 不能作为可信的 `B0_reference_x`。

因此 `C1_N1_t008` 旧表中由 `Mag_B` 计算得到的 `SF=0.6265` 不应进入论文图表。正式计算必须使用：

```text
SFx = abs(B0_Bx_T) / abs(Bcenter_Bx_T)
LeakageRatiox = abs(Bcenter_Bx_T) / abs(B0_Bx_T)
```

`B0_Mag_T` 和 `Bcenter_Mag_T` 只作为辅助检查量。

## 优先排查顺序

1. 确认 `B0_reference_x` 和 shielded cases 使用同一个 external uniform-field setup。
2. 确认 `B0_reference_x` 工程中 ferrite 已替换为 vacuum，或直接使用 no-shield reference 工程。
3. 确认外部场方向为 x，不是 z 或混合方向。
4. 确认中心观测点为同一个 `BcenterPoint_0_0_0`。
5. 确认后处理没有使用 `Mag_B` 作为正式 SF 计算依据。
6. 确认 B0 工程和 shield 工程都重新求解后再导出。
7. 先完成四个单层 case，只有全部 `SFx >= 1` 且随厚度趋势合理后，再继续 N=2/3/4。

## 已重建的 x 向 B0 reference

`B0_reference_x` 已重建为：

```text
aedt/reference/B0_reference_x.aedt
```

采用方式：

- 复制单层 shield case 作为几何模板，以保持空气域、边界尺度和 `BcenterPoint_0_0_0` 一致。
- 删除旧的 torus/current 外场对象和边界。
- 将单层 ferrite object `Cylinder2` 设置为 `vacuum`。
- 在空气盒 y/z 外表面施加 x-directed tangential H-field boundary。
- x-normal 两端面使用 zero tangential H-field boundary，允许法向通量通过。

导出文件：

```text
data/raw/B0_reference_x.csv
```

验证结果：

| quantity | value |
|---|---:|
| `B0_Bx_T` | `1.25663682659e-06` |
| `B0_By_T` | `-3.82793442545e-15` |
| `B0_Bz_T` | `-1.9432455921e-13` |
| `B0_Mag_T` | `1.25663682659e-06` |
| `primary_to_largest_transverse_ratio` | `6466690.73` |
| `validation_status` | `passed` |

## 当前允许重跑的 case

| case_id | required exports |
|---|---|
| `B0_reference_x` | completed and passed |
| `C1_N1_t008_x` | `Bcenter_Bx_T;Bcenter_By_T;Bcenter_Bz_T;Bcenter_Mag_T;IntH2_total;IntH2_L1` |
| `C1_N1_t020_x` | `Bcenter_Bx_T;Bcenter_By_T;Bcenter_Bz_T;Bcenter_Mag_T;IntH2_total;IntH2_L1` |
| `C1_N1_t040_x` | `Bcenter_Bx_T;Bcenter_By_T;Bcenter_Bz_T;Bcenter_Mag_T;IntH2_total;IntH2_L1` |
| `C1_N1_t060_x` | `Bcenter_Bx_T;Bcenter_By_T;Bcenter_Bz_T;Bcenter_Mag_T;IntH2_total;IntH2_L1` |

## 暂停项

以下 case 暂时不进入批处理：

- `C2_N2_t020_g010_x`
- `C2_N3_t020_g010_x`
- `C2_N4_t015_g008_x`
- N=6 optional extension
- segmented aligned/staggered shell
