# 下一轮实验怎么做

## 结论先说

下一轮不再优先做 `T=10 mm` 的厚壳固定总厚度实验。实物结构和机械约束已经改变了问题边界：

```text
MnZn 铁氧体单层厚度范围：0.08 mm <= a <= 0.60 mm
```

因此现在的仿真目标改为：

```text
在可制造薄片厚度范围内，比较单层、多层和真实周向分段结构的屏蔽系数、材料体积和磁噪声。
```

旧的 `fixedT10_g02 / fixedT10_g05` 只作为历史厚壳参考，不作为下一步优先实验。

## 1. 当前主入口

优先参数表已经改为：

```text
next_round_design_points.csv
```

详细薄片实验矩阵在：

```text
analysis_ready/manufacturable_thin_ferrite_sim_matrix.csv
```

说明文件：

```text
analysis_ready/README_manufacturable_thin_ferrite_sim.md
```

## 2. 两级仿真策略

### 第一级：连续圆柱壳快速筛选

先把铁氧体看成连续圆柱壳，忽略周向拼缝。这样模型简单、求解快，用来判断多层结构在 `0.08-0.60 mm` 厚度范围内是否有希望。

优先跑：

```text
B0 reference: no shield

N=1, a=0.08 mm
N=1, a=0.20 mm
N=1, a=0.40 mm
N=1, a=0.60 mm

N=2, a=0.20 mm, g=0.10 mm
N=3, a=0.20 mm, g=0.10 mm
N=4, a=0.15 mm, g=0.08 mm
```

其中：

```text
T = N*a + (N-1)*g
```

### 第二级：真实周向分段 3D 校正

实物不是连续壳，而是薄片沿周向拼成的圆柱结构。连续壳筛出候选点后，再做少量真实 3D 分段模型。

先用占位参数：

```text
N_segments = 12
circumferential_gap_mm = 1.6
coverage_phi = 0.95
```

等实物量完后，把这三个参数替换成真实值。

优先校正：

```text
N=1, a=0.20 mm
N=1, a=0.60 mm
N=3, a=0.20 mm, g=0.10 mm
N=4, a=0.15 mm, g=0.08 mm
```

## 3. 每个点必须导出什么

无屏蔽参考模型导出：

```text
B0_T
B0_Bx_T
B0_By_T
B0_Bz_T
```

有屏蔽模型导出：

```text
Bcenter_T
Bcenter_Bx_T
Bcenter_By_T
Bcenter_Bz_T
IntH2_total
IntH2_L1
IntH2_L2
...
```

如果 `Bcenter_T` 直接导出不稳定，就导出三分量，后处理用：

```text
Bcenter_T = sqrt(Bcenter_Bx_T^2 + Bcenter_By_T^2 + Bcenter_Bz_T^2)
```

## 4. 正式屏蔽系数

正式屏蔽系数必须来自外部场模型：

```text
SF = abs(B0_T) / abs(Bcenter_T)
ResidualRatio = abs(Bcenter_T) / abs(B0_T)
```

不要用内部 pickup/torus 线圈中心场替代正式 SF。

## 5. 材料体积

连续壳第 i 层体积：

```text
V_i = pi * H * ((r_i + a_i)^2 - r_i^2)
```

总材料体积：

```text
V_f = sum(V_i)
```

分段壳可先用覆盖率修正：

```text
V_segmented ~= coverage_phi * V_continuous
```

正式结果最好由 3D 几何体积直接导出或按真实分段尺寸计算。

## 6. 判据

多层结构能支持“省材料”观点，必须同时满足：

```text
SF_multi >= SF_target
V_multi < V_single_at_same_SF
IntH2_total_multi 或 B_avg_1_30_fT 不明显变差
```

第一轮先不急着设很高的 `SF_target`。先画：

```text
SF vs V_f
IntH2_total vs V_f
eta_S = ln(SF) / V_f
```

如果多层曲线没有高于单层曲线，就说明在当前薄片结构下，多层不能直接宣称省材料。

## 7. 立即执行顺序

1. 建无屏蔽参考模型，导出 `B0`。
2. 跑连续壳 `N=1, a=0.08/0.20/0.40/0.60 mm`。
3. 跑连续壳 `N=2,3,4` 的 priority 1 多层候选。
4. 后处理 `SF - V_f - IntH2_total`。
5. 只对最好的 2-3 个结构做真实周向分段 3D 校正。
