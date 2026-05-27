# AEDT 手动操作清单

多层圆柱薄铁氧体磁屏蔽项目的 AEDT 操作步骤。每完成一个 case 就导出中心场和 IntH2，然后跑后处理和验证脚本。没导出完的 case 不要放进论文图表。哪步做不了就把对应 case 在 `data/experiment_matrix_main.csv` 里标成 `missing` 或 `failed`，写清楚原因。

## 1. 建 B0_reference_x

1. 打开 AEDT
2. 新建或复制一个无屏蔽模型，空气域、边界尺寸、坐标系、中心观测点和屏蔽模型保持一致
3. 把铁氧体删掉或改成 vacuum
4. x 方向均匀外场
5. 静磁求解
6. 导出中心点 B0_Bx_T, B0_By_T, B0_Bz_T, B0_Mag_T
7. 存为 `data/raw/B0_reference_x.csv`

## 2. 建 B0_reference_z

1. 复制 B0_reference_x
2. 外场方向改成 z（圆柱轴向）
3. 空气域、边界、网格、观测点保持不变
4. 静磁求解
5. 导出 B0_Bx_T, B0_By_T, B0_Bz_T, B0_Mag_T
6. 存为 `data/raw/B0_reference_z.csv`

## 3. 单层连续壳工程

用现有单层工程做模板，另存为 C1_N1_t008_x / t020_x / t040_x / t060_x。参数：N=1, g=0, Rin=100mm, H=200mm。铁氧体 mu_r=1000, sigma=0.01 S/m。圆柱两端开口（除非矩阵明确说封闭）。

## 4. 多层连续壳工程

用现有多层工程做模板，case_id 严格按 `data/experiment_matrix_main.csv` 来。每层铁氧体是独立实体（ferrite_L1, L2, L3, L4），不要合并。半径递推：R_i,in = Rin + (i-1)(a+g), R_i,out = R_i,in + a。总径向占位 T_space = N*a + (N-1)*g。

## 5. x 向外场设置

所有 x 向 case 用同一种边界方式（切向 H 场边界或 AEDT 均匀场设置）。确保无屏蔽模型中心点 B0_Bx_T 占主导。激励幅值 B0 和屏蔽 case 保持一致。

## 6. z 向外场设置

从 x 向 setup 复制，激励方向改成 z。确保无屏蔽模型中心点 B0_Bz_T 占主导。不要用横向结果推断轴向屏蔽性能。

## 7. 导出中心场

每个屏蔽 case 在几何中心建观测点，导出 Bcenter_Bx_T, Bcenter_By_T, Bcenter_Bz_T, Bcenter_Mag_T，追加到 `data/raw/center_field_raw.csv`。行里带上 case_id, model_type, field_dir, source_project, status。

无屏蔽参考导出到 `data/raw/B0_reference_x.csv` 或 `B0_reference_z.csv`。

## 8. 设 IntH2 命名表达式

在 Field Calculator 里对每层铁氧体做：选 H → Mag → 平方 → 对该层体积积分。命名：IntH2_L1, IntH2_L2, IntH2_L3, IntH2_L4。IntH2_total = 各层之和。新建工程不要用 InH2_s4, IntH2_s1, IntH2_cyl2 等旧名字。旧工程如果带着 legacy 名字，导出时记一笔 warning，在 notes 里标 legacy-compatible。

## 9. 校验 IntH2 分层一致性

导出后跑 `python scripts\postprocess\validate_layerwise_intH2.py`，要求 |IntH2_total - sum(IntH2_Li)| / IntH2_total < 1e-3。不通过的不标 used_in_paper。

## 10. 分段对齐壳 (Segmented Aligned)

从连续壳候选开始，每层切成 N_segments=12 个周向铁氧体条，周向缝隙 gphi=1.6mm。各层缝隙角度对齐。case_id 里带 aligned。导出中心场和 IntH2_total。

## 11. 分段错位壳 (Segmented Staggered)

从 aligned 开始，相邻层缝隙错开 Delta_phi_i = (i-1)*pi/N_segments。确保一层缝隙对着邻层铁氧体。case_id 里带 staggered。导出中心场和 IntH2_total。

## 12. 命名规则

case_id 严格来自 `data/experiment_matrix_main.csv`。工程名如 B0_reference_x.aedt, C1_N1_t008_x.aedt, C2_N2_t020_g010_x.aedt, S2_N3_t020_g010_seg12_aligned_x.aedt 等。导出表路径固定为 data/raw/ 下的 B0_reference_x.csv, B0_reference_z.csv, center_field_raw.csv, intH2_layerwise_raw.csv。

## 导出后的流水线

```
python scripts\postprocess\build_dataset.py
python scripts\postprocess\compute_metrics.py
python scripts\postprocess\validate_B0_reference.py
python scripts\postprocess\validate_layerwise_intH2.py
python scripts\plotting\plot_paper_figures.py
```

只有导出完整且验证通过的才能标 used_in_paper。
