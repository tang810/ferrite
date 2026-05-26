# 第二轮实验执行表

## 当前状态

本文件原来记录 `T=10 mm` 厚壳固定总厚度实验。由于实物机械约束已经明确：

```text
0.08 mm <= 单层铁氧体厚度 <= 0.60 mm
```

第二轮实验已改为“可制造薄片铁氧体仿真”。

## 主实验文件

```text
next_round_design_points.csv
analysis_ready/manufacturable_thin_ferrite_sim_matrix.csv
analysis_ready/README_manufacturable_thin_ferrite_sim.md
```

## 优先级 1：连续壳快速筛选

先跑以下结构：

```text
M0_B0: no shield

N=1, a=0.08 mm, g=0
N=1, a=0.20 mm, g=0
N=1, a=0.40 mm, g=0
N=1, a=0.60 mm, g=0

N=2, a=0.20 mm, g=0.10 mm
N=3, a=0.20 mm, g=0.10 mm
N=4, a=0.15 mm, g=0.08 mm
```

这些点的目的不是证明最终结论，而是筛选：

```text
在真实薄片厚度约束下，多层结构是否仍有屏蔽效率优势。
```

## 优先级 2：周向分段校正

连续壳筛选后，再跑真实分段模型。初始占位参数：

```text
N_segments = 12
circumferential_gap_mm = 1.6
coverage_phi = 0.95
```

如果实测片数或缝隙不同，优先改这些参数。

## 导出列

每个 shield case：

```text
experiment
stage
model_type
layer
T_mm
a_mm
g_mm
N_segments
circumferential_gap_mm
coverage_phi
IntH2_total
IntH2_L1
IntH2_L2
...
Bcenter_T
Bcenter_Bx_T
Bcenter_By_T
Bcenter_Bz_T
```

无屏蔽参考：

```text
B0_T
B0_Bx_T
B0_By_T
B0_Bz_T
```

## 后处理目标

```text
SF = abs(B0_T) / abs(Bcenter_T)
ResidualRatio = abs(Bcenter_T) / abs(B0_T)
eta_S = ln(SF) / V_f
```

最终输出图：

```text
SF vs V_f
IntH2_total vs V_f
eta_S vs layer
continuous shell vs segmented shell correction
```
