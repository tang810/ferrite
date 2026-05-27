# Data Directory 中文说明

本目录存放 ferrite 项目的实验矩阵、AEDT 原始导出、后处理数据和验证结果。

注意：CSV 文件必须保持第一行为英文表头，不能在 CSV 顶部直接加入中文说明行，否则 pandas、MATLAB 和 Python `csv.DictReader` 会读取失败。因此中文说明统一放在本文件和 `docs/` 文档中。

## 文件说明

| 文件 | 中文说明 | 是否可直接作为论文结果 |
|---|---|---|
| `data/experiment_matrix_main.csv` | 主实验矩阵。定义每个 case 的几何、材料、外场方向、线圈方向、优先级和当前状态。 | 否，这是计划/状态表 |
| `data/raw/B0_reference_x.csv` | 手动或脚本导出的 x 向无屏蔽参考场。当前如果不存在，则 x 向 SF 仍为 missing。 | 只有通过验证后才可用于计算 |
| `data/raw/B0_reference_z.csv` | 手动或脚本导出的 z 向无屏蔽参考场。当前如果不存在，则 z 向 SF 仍为 missing。 | 只有通过验证后才可用于计算 |
| `data/raw/center_field_raw.csv` | 有屏蔽 case 的中心点 Bcenter_Bx/By/Bz/Mag_B 原始导出。 | 否，需后处理 |
| `data/raw/intH2_layerwise_raw.csv` | 虚拟 pickup coil 工况下 IntH2_total 和 IntH2_Li 原始导出。 | 否，需验证 |
| `data/processed/main_dataset.csv` | 由 `build_dataset.py` 合并矩阵、B0、中心场和 IntH2 后生成。 | 否，需计算指标与验证 |
| `data/processed/metrics_table.csv` | 由 `compute_metrics.py` 计算 SFq、LeakageRatioq、Vf、etaS、etaS_star、rhoH、chiH 后生成。 | 仅验证通过且标记 used_in_paper 的行可用 |
| `data/validation/B0_reference_validation.csv` | 检查 B0_reference_x/z 方向是否正确。 | 验证文件，不是结果图表 |
| `data/validation/layerwise_intH2_validation.csv` | 检查 IntH2_total 是否等于各层 IntH2_Li 之和。 | 验证文件，不是结果图表 |

## 状态含义

| status | 中文含义 |
|---|---|
| `planned` | 已计划，但还没有建模或导出 |
| `built` | AEDT 工程已存在，但还没有可靠导出 |
| `solved` | AEDT 已求解，但导出尚未进入 pipeline |
| `exported` | 已导出原始数据 |
| `processed` | 已完成后处理 |
| `used_in_paper` | 已通过验证并允许进入论文 |
| `missing` | 必需文件或字段缺失 |
| `failed` | 运行或验证失败 |

## 当前原则

- 不使用 legacy thick-shell 数据混入 manufacturable thin-ferrite 主结果。
- 没有 B0 reference 的方向，不能计算正式 SF。
- 没有通过 IntH2 分层验证的 case，不能进入论文图表。
- `Mag_B` 只作为辅助检查，正式 `SFx/SFz` 分别使用 `Bx/Bz` 分量计算。
