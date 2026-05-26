# 下一轮实验怎么做

## 结论先说

当前文件夹已经完成了 1-4 层结构的第一轮闭环：

`Maxwell 参数扫描 -> 导出 IntH2_total -> MATLAB 换算 B_avg_1_30_fT -> 响应面拟合 -> 找候选最优点`

下一轮不要直接继续堆更多随机点。先把评价指标补齐，再扩展层数。

## 1. 先保留现有工程，不要覆盖

现有工程：

- `Project100_1ceng.aedt`
- `Project100_2ceng.aedt`
- `Project100_3ceng.aedt`
- `Project100_4ceng.aedt`

建议新建工程副本：

- `Project100_5ceng.aedt`
- `Project100_6ceng.aedt`
- `Project100_7ceng.aedt`

如果要改 1-4 层，也先另存为：

- `Project100_1ceng_next.aedt`
- `Project100_2ceng_next.aedt`
- `Project100_3ceng_next.aedt`
- `Project100_4ceng_next.aedt`

原因：目录里有 `.aedt.lock`，说明这些工程近期被 AEDT 打开过。不要在原工程上直接乱改。

## 2. 下一轮必须导出的量

会议里强调的方向是：看最内层积分值、屏蔽效果，以及层数增加后的规律。

每个设计点至少导出这些列：

```text
experiment
layer
T_mm
a_mm
g_mm
IntH2_total
IntH2_L1
IntH2_L2
...
B0_T
Bcenter_T
```

含义：

- `IntH2_total`：所有铁氧体层的 H^2 体积分
- `IntH2_L1`：最内层铁氧体的 H^2 体积分
- `IntH2_Li`：第 i 层贡献，用来算每层贡献比例
- `B0_T`：没有屏蔽体时中心参考磁场
- `Bcenter_T`：有屏蔽体时中心残余磁场
- `SF = B0_T / Bcenter_T`：屏蔽系数，MATLAB 脚本已经能自动识别这两列并计算

## 3. 优先做的参数表

我已经放了一个表：

`next_round_design_points.csv`

优先级：

1. `priority=1`：固定总厚度 `T=10 mm`，间隙 `g=0.2 mm`，扫 `N=1..7`
2. `priority=2`：固定总厚度 `T=10 mm`，间隙 `g=0.5 mm`，扫 `N=1..7`
3. `priority=3`：会议里提到的薄层可实现性，`a=0.3 mm, g=0.2 mm`，扫 `N=4..8`

第一轮先跑 priority 1。跑完之后就能回答一个核心问题：

在总厚度固定时，增加层数到底是降低噪声，还是因为气隙占用厚度导致噪声升高？

## 4. Maxwell 里具体怎么设

对每一个层数 N 建一个独立 design，别在同一个模型里硬切层数。

参数定义：

```text
Rin = 100mm
H = 200mm
a = 单层铁氧体厚度
g = 层间空气间隙
T = N*a + (N-1)*g
```

建模顺序：

```text
内层空气/测量区域
铁氧体 L1
空气间隙 G1
铁氧体 L2
空气间隙 G2
...
铁氧体 LN
外部空气区域
```

每一层铁氧体单独命名：

```text
ferrite_L1
ferrite_L2
ferrite_L3
...
```

不要把所有层 Unite 成一个实体，否则后面不能导出分层积分。

## 5. Field Calculator 怎么导出

对每一层做一次：

```text
Quantity: H
Operation: Mag
Operation: Square
Geometry: ferrite_Li
Operation: Integrate
Add Named Expression: IntH2_Li
```

总积分：

```text
IntH2_total = IntH2_L1 + IntH2_L2 + ... + IntH2_LN
```

最内层积分值就是：

```text
IntH2_inner = IntH2_L1
```

如果 AEDT 里表达式名不方便，就至少导出 `IntH2_L1` 和 `IntH2_total`。

## 6. 屏蔽系数怎么做

同一套激励下做两个工况：

1. 无屏蔽体：得到中心磁场 `B0_T`
2. 有屏蔽体：得到中心磁场 `Bcenter_T`

然后：

```text
SF = abs(B0_T) / abs(Bcenter_T)
ResidualRatio = abs(Bcenter_T) / abs(B0_T)
```

MATLAB 脚本已经支持：只要 CSV 里有 `B0_T` 和 `Bcenter_T`，会自动生成 `SF` 和 `ResidualRatio`。

## 7. 跑完之后怎么合并数据

把新导出的 CSV 整理成这个格式，追加到：

`analysis_ready/all_results_clean.csv`

推荐另存一个新文件：

`analysis_ready/all_results_round2.csv`

至少包含：

```text
experiment,layer,T_mm,a_mm,g_mm,IntH2_total,IntH2_L1,IntH2_L2,IntH2_L3,IntH2_L4,IntH2_L5,IntH2_L6,IntH2_L7,B0_T,Bcenter_T
```

没有的层留空。

## 8. MATLAB 后处理

运行：

```matlab
cd('D:\tangyumengnew\aaaaaaaaximukeji\matlab-B')
analyze_project100_results
```

我已经把 `analyze_project100_results.m` 的分层积分读取范围从 4 层扩展到了 10 层。后面导出 `IntH2_L5`、`IntH2_L6`、`IntH2_L7` 时，脚本可以自动计算：

```text
Qratio_Li = IntH2_Li / IntH2_total
```

## 9. 汇报时要回答的问题

下一次组会最关键的图：

1. `N` vs `B_avg_1_30_fT`
2. `N` vs `IntH2_L1`
3. `N` vs `SF`
4. 各层 `Qratio_Li` 堆叠柱状图
5. `低噪声 + 高屏蔽系数 + 少材料体积` 的 Pareto 对比

关键判断：

- 如果增加层数让 `B_avg` 降低、`SF` 增大，说明多层结构有效。
- 如果增加层数让 `B_avg` 升高但 `SF` 增大，说明多层结构有屏蔽收益，但有磁噪声代价。
- 如果增加层数让 `B_avg` 升高且 `SF` 变化不大，就说明当前静态模型下多层不划算，需要转向动态/涡流或材料实测验证。

## 10. 现在最先做哪一步

先跑 `next_round_design_points.csv` 里的 `priority=1`。

只要拿到这 7 个点，就能直接判断会议里“通过增加层数而不是增加厚度”这个方向是否成立。
