# 占位实验逐步补全清单

本文档把 `data/experiment_matrix_main.csv` 中的 planned/missing 占位实验拆成可执行步骤。执行时不要补假数据；每一步完成后再更新对应 case 的 `status`。

## 总体流程

1. 打开 `data/experiment_matrix_main.csv`，选择一个 `status` 为 `missing`、`planned` 或 `built` 的 case。
2. 按 `docs/AEDT_MANUAL_EXECUTION_CHECKLIST.md` 在 AEDT 中完成建模、求解和导出。
3. 将 B0 reference 放入：

```text
data/raw/B0_reference_x.csv
data/raw/B0_reference_z.csv
```

4. 将中心场导出追加到：

```text
data/raw/center_field_raw.csv
```

5. 将 IntH2 导出追加到：

```text
data/raw/intH2_layerwise_raw.csv
```

6. 运行：

```powershell
python scripts\postprocess\build_dataset.py
python scripts\postprocess\compute_metrics.py
python scripts\postprocess\validate_B0_reference.py
python scripts\postprocess\validate_layerwise_intH2.py
python scripts\plotting\plot_paper_figures.py
```

7. 只有验证通过后，才允许把 case 标记为 `used_in_paper`。

## 第一阶段：B0 Reference 必须先补

### 1. `B0_reference_x`

目标：建立横向 x 外场无屏蔽参考。

步骤：

1. 复制一个当前 open-ended cylinder 工作空间。
2. 删除 ferrite 或把 ferrite 材料改为 vacuum。
3. 设置 x 向外部均匀场。
4. 求解 magnetostatic setup。
5. 在中心点导出：
   - `B0_Bx_T`
   - `B0_By_T`
   - `B0_Bz_T`
   - `B0_Mag_T`
6. 保存为 `data/raw/B0_reference_x.csv`。
7. 运行 `validate_B0_reference.py`，确认 `B0_Bx_T` 主导。

完成后状态建议：

```text
missing -> exported -> processed
```

### 2. `B0_reference_z`

目标：建立轴向 z 外场无屏蔽参考。

步骤：

1. 复制 `B0_reference_x`。
2. 将外部均匀场方向改为 z。
3. 保持空气域、边界条件、中心观测点一致。
4. 导出：
   - `B0_Bx_T`
   - `B0_By_T`
   - `B0_Bz_T`
   - `B0_Mag_T`
5. 保存为 `data/raw/B0_reference_z.csv`。
6. 运行 `validate_B0_reference.py`，确认 `B0_Bz_T` 主导。

## 第二阶段：Priority 1 连续壳 x 向主矩阵

这些 case 是论文主筛选矩阵，必须完成：

```text
C1_N1_t008_x
C1_N1_t020_x
C1_N1_t040_x
C1_N1_t060_x
C2_N2_t020_g010_x
C2_N3_t020_g010_x
C2_N4_t015_g008_x
```

每个 case 的步骤：

1. 打开对应 AEDT 工程，或从模板复制。
2. 检查几何参数：
   - `Rin_mm = 100`
   - `H_mm = 200`
   - `N_layers`
   - `t_ferrite_mm`
   - `g_radial_mm`
3. 检查 ferrite 每层是独立实体，命名为 `ferrite_L1`、`ferrite_L2` 等。
4. 设置 x 向外部均匀场。
5. 求解。
6. 导出中心场到 `data/raw/center_field_raw.csv`：
   - `Bcenter_Bx_T`
   - `Bcenter_By_T`
   - `Bcenter_Bz_T`
   - `Bcenter_Mag_T`
7. 设置虚拟 pickup coil，coil direction = x。
8. 导出 IntH2：
   - `IntH2_total`
   - `IntH2_L1 ... IntH2_LN`
9. 运行后处理和验证脚本。
10. 若验证失败，保持 `failed` 或 `missing`，不要进入论文。

## 第三阶段：Priority 2 补充实验

### A. z 向轴向扩展

待补 case：

```text
C1_N1_t060_z
C2_N3_t020_g010_z
C2_N4_t015_g008_z
```

执行条件：priority-1 x 向主矩阵已有可比较结果。

关键要求：

- 必须使用 `B0_reference_z`。
- 正式 `SFz` 用 `Bz` 分量计算。
- 不能用 x 向结果推断 z 向性能。

### B. Segmented aligned / staggered

待补 case：

```text
S1_N1_t060_seg12_aligned_x
S1_N1_t060_seg12_staggered_x
S2_N3_t020_g010_seg12_aligned_x
S2_N3_t020_g010_seg12_staggered_x
S2_N4_t015_g008_seg12_aligned_x
S2_N4_t015_g008_seg12_staggered_x
```

执行条件：连续壳筛选后确定需要分段修正。

步骤：

1. 将连续圆柱壳分成 `N_segments = 12` 个周向 ferrite strips。
2. 设置 `circumferential_gap_mm = 1.6`。
3. aligned：每层缝隙角度对齐。
4. staggered：相邻层缝隙旋转 `pi / N_segments`。
5. 导出中心场和 `IntH2_total`。
6. 与连续壳基线比较。

### C. permeability sensitivity

代表 case：

```text
MU_C2_N3_t020_g010_x_mu500
MU_C2_N3_t020_g010_x_mu2000
MU_C2_N3_t020_g010_x_mu5000
```

要求：

- 只改变 `mu_r`。
- 其他几何、边界、网格策略保持一致。
- 结果只能解释结构排序对材料磁导率的敏感性，不能替代实测材料参数。

### D. mesh convergence

代表 case：

```text
MESH_C1_N1_t008_x
MESH_C2_N4_t015_g008_x
```

要求：

- 至少比较 coarse / medium / fine 三组局部网格。
- 监控 `Bcenter_Bx_T`、`SFx`、`IntH2_total`。
- 未完成收敛性检查前，最终论文结论保持 pending。

## 第四阶段：Priority 3 可选 N=6

case：

```text
C2_N6_t010_g008_x
```

执行条件：

- priority-1 结果显示多层结构确实有明显收益；
- N=6 的机械/制造可行性可以接受；
- 有足够时间补完整导出和验证。

否则保持 `planned`，不要写入主结果。
