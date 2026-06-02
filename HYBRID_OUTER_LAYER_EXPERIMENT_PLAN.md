# Hybrid Outer-Layer Experiment Plan

本文件把“最外层加非晶/纳米晶提高总体 SF”和“把磁强计放进多层铁氧体屏蔽内给出灵敏度指标”拆成可执行步骤。原则是先仿真筛选，再做实物验证；没有仿真或实测支撑的结果不写成论文结论。

## 1. Baseline

当前基准结构采用已经验证的横向连续壳 case：

```text
case_id: C2_N4_t015_g008_x
Rin = 100 mm
L = 200 mm
N_ferrite = 4
t_ferrite = 0.15 mm
g_radial = 0.08 mm
T_ferrite_total = 0.60 mm
T_space = 0.84 mm
validated SFx = 3.629
validated IntH2_total = 4.160e-6
```

所有 hybrid 结果必须与这个 baseline 比较：

```text
SFx_gain = SFx_hybrid / SFx_baseline
IntH2_ratio = IntH2_hybrid / IntH2_baseline
chiH = IntH2_total / ln(SFx)
```

建议判据：

```text
pass:      SFx_gain >= 2 and IntH2_ratio <= 1.2
excellent: SFx_gain >= 3 and IntH2_ratio <= 1.0
reject:    SFx improves but IntH2_ratio is much larger than 1.2
```

## 2. AEDT Simulation Sequence

### 2.0 Actual AEDT Script Entry

已经新增可执行 AEDT 脚本：

```text
round2_working/run_hybrid_outer_layer_experiment.py
```

在 AEDT 中运行：

```text
Tools -> Run Script -> round2_working/run_hybrid_outer_layer_experiment.py
```

默认只运行第一优先级 case：

```text
H_C2_N4_t015_g008_x_outer_nanocrystalline_1wrap
```

脚本会执行：

```text
复制 baseline: round2_working/manufacturable_thin/C2_N4_t015_g008_shield.aedt
添加最外层 nanocrystalline 圆柱薄壳
求解 Setup1
导出 Bcenter_Bx/By/Bz
计算 SFx, SFx_gain, ResidualRatiox
计算 IntH2_total 和 IntH2_outer
写入 data/raw/hybrid_outer_layer_exports.csv
写入日志 round2_working/hybrid_outer_layer/run_hybrid_outer_layer_experiment.log
```

第一轮确认日志和导出没问题后，再打开脚本中的：

```text
CASE_ID_FILTER
```

依次加入非晶 1 层、纳米晶 2 层、非晶 2 层和开缝版本。

### 2.1 Run Continuous Outer-Layer Cases First

新增仿真矩阵见：

```text
next_round_design_points.csv
hybrid_outer_layer_design_points.csv
```

优先顺序：

```text
1. H_C2_N4_t015_g008_x_outer_nanocrystalline_1wrap
2. H_C2_N4_t015_g008_x_outer_amorphous_1wrap
3. H_C2_N4_t015_g008_x_outer_nanocrystalline_2wrap
4. H_C2_N4_t015_g008_x_outer_amorphous_2wrap
5. H_C2_N4_t015_g008_x_outer_nanocrystalline_1wrap_slit
```

先跑连续外层，得到理论最大 SF 提升；再跑带轴向断缝的外层，用于评估真实装配和闭合导电环风险。

### 2.2 Geometry Setup

以 `C2_N4_t015_g008_x` 为基础复制工程：

```text
内层 4 层 ferrite 保持不变
最外层外侧留 outer_gap_from_ferrite_mm = 0.20 mm
再添加 amorphous 或 nanocrystalline 薄带外层
连续版本：完整圆柱薄壳
开缝版本：一个轴向断缝，初始缝宽 1.6 mm
```

外层材料参数先按参数矩阵填入，后续必须替换成实测或厂家数据：

```text
outer_mu_r_prime
outer_mu_r_double_prime
outer_sigma_S_per_m
outer_t_per_wrap_mm
outer_total_t_mm
```

如果没有 `mu_r_double_prime`，不要给出绝对磁噪声结论，只报告 SFx、IntH2 和参数敏感性。

### 2.3 Required AEDT Exports

外场模型导出：

```text
Bcenter_Bx_T
Bcenter_By_T
Bcenter_Bz_T
Bcenter_Mag_T
```

噪声相关虚拟 pickup-coil 模型导出：

```text
IntH2_total
IntH2_L1
IntH2_L2
IntH2_L3
IntH2_L4
IntH2_outer
```

如果是开缝/分段外层，至少导出：

```text
IntH2_total
IntH2_outer
```

后处理必须使用：

```text
SFx = abs(B0_Bx_T) / abs(Bcenter_Bx_T)
ResidualRatiox = abs(Bcenter_Bx_T) / abs(B0_Bx_T)
```

不要用 `B_Mag` 作为正式 SF。

## 3. Physical Prototype Sequence

先做三个样机，不要一开始做大矩阵：

```text
P0: no shield reference
P1: four-layer ferrite only, matching C2_N4_t015_g008_x
P2: four-layer ferrite + selected outer amorphous/nanocrystalline layer
```

可选对照：

```text
P3: single-layer ferrite, matching C1_N1_t060_x
```

装配记录必须包含：

```text
真实内半径
真实长度
每层 ferrite 厚度
每层间隙
每层接缝位置
外层材料类型
外层厚度
外层是否开缝
外层缝宽
覆盖率
绝缘层材料和厚度
```

建议多层接缝错开；外层非晶/纳米晶至少保留一个轴向断缝版本，避免完整闭合导电环。

## 4. Shielding-Factor Measurement

### 4.1 Equipment

```text
三轴 Helmholtz 线圈或长螺线管
低噪声电流源
磁强计或标定磁场探头
样机支架
中心定位治具
数据采集系统
```

### 4.2 Procedure

对 x 和 z 两个方向分别测量。

1. 无屏蔽测参考场：

```text
sample = P0
apply calibrated field along q
record B0_q
```

2. 四层铁氧体测屏蔽后中心场：

```text
sample = P1
same coil current
same sensor position
record Bcenter_q
calculate SFq_ferrite
```

3. hybrid 样机测屏蔽后中心场：

```text
sample = P2
same coil current
same sensor position
record Bcenter_q
calculate SFq_hybrid
```

每个点至少重复 5 次：

```text
mean_B0_q
std_B0_q
mean_Bcenter_q
std_Bcenter_q
mean_SFq
std_SFq
```

输出表建议保存为：

```text
data/raw/prototype_sf_measurement.csv
```

建议字段：

```text
run_id,sample_id,case_id,field_dir,repeat_index,
B0_T,Bcenter_T,SFq,ResidualRatioq,
coil_current_A,drive_frequency_Hz,sensor_position,notes
```

## 5. Magnetometer Sensitivity Test

### 5.1 Required Outputs

把磁强计放进屏蔽内后，至少给出：

```text
noise_1Hz_fT_sqrtHz
noise_10Hz_fT_sqrtHz
noise_avg_1_30Hz_fT_sqrtHz
residual_DC_field_nT
drift_p2p_nT
optional Allan deviation
```

### 5.2 Procedure

1. 传感器基线：

```text
sample = sensor_baseline
duration = 300-600 s
record time series
calculate PSD
```

2. 四层铁氧体内测量：

```text
sample = P1
magnetometer at center
no applied calibration field
duration = 300-600 s
calculate PSD
```

3. Hybrid 屏蔽内测量：

```text
sample = P2
same magnetometer position
same sampling rate
same duration
calculate PSD
```

4. 小信号校准：

```text
apply 10 Hz sinusoidal calibration field
extract transfer coefficient fT/count or fT/V
```

输出表建议保存为：

```text
data/raw/magnetometer_sensitivity_measurement.csv
```

建议字段：

```text
run_id,sample_id,case_id,duration_s,sampling_rate_Hz,
noise_1Hz_fT_sqrtHz,noise_10Hz_fT_sqrtHz,noise_avg_1_30Hz_fT_sqrtHz,
residual_DC_field_nT,drift_p2p_nT,calibration_field_pT,notes
```

## 6. Claim Rules

可以写：

```text
The outer amorphous/nanocrystalline layer increased SFq by X while keeping IntH2 within Y of the ferrite-only baseline.
```

只有在磁强计实测 PSD 支持时，才可以写：

```text
The hybrid shield improved the measured 1-30 Hz magnetometer noise floor from A to B fT/sqrtHz.
```

不能写：

```text
Hybrid outer layer improves sensitivity
```

除非同时满足：

```text
SFq_hybrid > SFq_ferrite
noise_avg_1_30Hz_hybrid < noise_avg_1_30Hz_ferrite
measurement repeated and uncertainty reported
```
