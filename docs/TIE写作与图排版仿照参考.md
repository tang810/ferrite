# TIE 写作与图排版风格参考

参考论文：
`D:\ferrite\论文\Modeling_and_Application_of_Magnetic_Shaking_for_Improving_Permeability_and_Performance_of_Magnetic_Shields.pdf`

目标不是复制原图，而是仿照其 TIE 工程论文风格：先提出物理机制和模型，再给材料/结构参数曲线，随后给仿真与实验对比，最后落到系统级磁强计或屏蔽应用验证。

## 一、参考论文的写作结构

参考文的主线是：

1. 应用需求：弱磁测量需要高性能磁屏蔽。
2. 问题定义：低频/准静态屏蔽性能受材料磁性能限制。
3. 方法：提出 magnetic shaking，并建立模型。
4. 材料层面验证：测磁化曲线、磁导率。
5. 屏蔽器件验证：测 SF，比较测试和计算。
6. 系统层面验证：残余场、PSD、实际 MSR 屏蔽性能。

你的论文可以对应为：

1. 应用需求：SERF-MEG / 磁强计需要低残余场、低噪声屏蔽环境。
2. 问题定义：纯多层铁氧体 SF 偏低，尤其轴向端部漏磁明显。
3. 方法：多层铁氧体基体 + 外层高磁导材料 + 单边封盖。
4. 结构层面验证：N=1-6 或当前四层候选的 SF/IntH2 权衡。
5. hybrid 验证：非晶/纳米晶外层的 SFx 与 IntH2 对比。
6. 轴向封盖验证：P0、开口四层、单边纳米晶盖的 SFz/IntH2/地磁残余场。
7. 系统验证：实物 SF + 补偿线圈调零 + 磁强计 PSD。

## 二、参考论文的图排版特征

参考文图片风格有几个明显特点：

- 单栏图用于简单曲线或小型原理图。
- 双栏图用于系统装置、三维模型、照片、总览图。
- 多子图常用 `(a)`, `(b)`, `(c)`，图题一句话说明总主题，再解释每个子图。
- 曲线图偏简洁：白底、黑色坐标轴、少量红/蓝/绿/紫线，marker 区分测试和计算。
- 图中直接标注关键结构，例如 coil、shielding layers、test platform。
- 结果图常把 measured 和 calculated 放在同一张图，突出模型可信度。
- 系统验证图通常包含一张 3D 模型或照片，再配频响曲线、PSD 或残余场热图。

## 三、你这篇论文建议的图序

### Fig. 1 结构与研究路线图

建议双栏。

内容：

- 多层铁氧体屏蔽桶截面图。
- 外层非晶/纳米晶包覆示意。
- 单边封盖示意。
- 磁强计、补偿线圈、外加场方向标注。

作用：

让审稿人第一眼知道这不是单纯材料论文，而是 SERF-MEG / 磁强计用的工程屏蔽结构。

图题示例：

`Fig. 1. Concept of the hybrid multilayer ferrite shield for magnetometer applications. (a) Multilayer ferrite base. (b) Outer high-permeability layer. (c) Single-ended cap and magnetometer placement.`

### Fig. 2 四层铁氧体基体选择

建议单栏或双栏。

内容：

- N=1-6，固定总铁氧体厚度约 0.60 mm。
- 横轴为层数 N。
- 左轴 SF，右轴 IntH2 或噪声代理。
- 标出 N=4 是候选验证结构。

论文写法：

不要写“四层全局最优”。写“四层是在当前总厚度、径向尺寸和装配约束下的折中验证候选”。

### Fig. 3 hybrid 外层增强结果

建议单栏。

已有 MATLAB 输出可用：

`analysis_ready/matlab_B_results/current_paper_hybrid_SF_IntH2.png`

建议进一步改成两子图：

- `(a)` SFx 对比柱状图：铁氧体、+非晶、+纳米晶。
- `(b)` IntH2 对比，使用 log 轴。

核心数值：

- 四层铁氧体：SFx = 3.629，IntH2 = 4.160e-06。
- +非晶外层：SFx = 8.548，IntH2 = 6.283e-07。
- +纳米晶外层：SFx = 25.146，IntH2 = 5.333e-08。

论文写法：

在相同外层厚度 0.20 mm 下，纳米晶同时给出更高 SFx 和更低 IntH2，因此作为优先 hybrid 候选。

### Fig. 4 轴向封盖权衡

建议单栏或双栏。

已有 MATLAB 输出可用：

`analysis_ready/matlab_B_results/current_paper_axial_cap_tradeoff.png`

建议改成三子图：

- `(a)` 结构示意：开口四层、P0 非晶壳+盖、四层+纳米晶盖。
- `(b)` SFz 对比。
- `(c)` IntH2_total 对比，log 轴。

核心数值：

- 四层铁氧体开口：SFz = 2.412，IntH2 = 2.971e-06。
- P0 非晶单层壳+单边非晶盖：SFz = 2.526，IntH2 = 3.960e-07。
- 四层铁氧体+单边纳米晶盖：SFz = 2.907，IntH2 = 3.736e-06。

论文写法：

单边纳米晶盖提升轴向 SFz，但 IntH2 增加；P0 的 IntH2 较低但 SFz 提升有限。因此封盖结构必须结合 PSD 实测评价。

### Fig. 5 50 uT 地磁残余场估算

建议单栏。

已有 MATLAB 输出：

`analysis_ready/matlab_B_results/current_paper_geomagnetic_residual_estimates.csv`

建议图：

- 横向 x 和轴向 z 分成两组柱状图。
- 纵轴为 `Estimated residual field under 50 uT geomagnetic field (uT)`。

核心数值：

- x 向四层铁氧体：13.78 uT。
- x 向 +非晶：5.85 uT。
- x 向 +纳米晶：1.99 uT。
- z 向四层开口：20.73 uT。
- z 向 P0：19.79 uT。
- z 向四层+纳米晶盖：17.20 uT。

论文写法：

这些是线性磁导率假设下由 SF 缩放得到的地磁残余场估计，不是非线性 B-H 地磁仿真。该结果说明仍需要补偿线圈调零。

### Fig. 6 材料损耗敏感性

建议单栏。

已有 MATLAB 输出：

`analysis_ready/matlab_B_results/current_paper_material_loss_sensitivity.csv`

建议图：

- 横轴 `mu''_metal / mu''_ferrite`，log 轴。
- 纵轴 `noise amplitude ratio`。
- 曲线：非晶外层、纳米晶外层、P0、纳米晶封盖。

作用：

防止审稿人质疑：非晶/纳米晶虽然提高 SF，但金属软磁材料磁损耗可能更大。

论文写法：

在缺少材料实测 `mu''` 时，本研究使用参数敏感性分析界定 hybrid 结构在不同损耗假设下的噪声风险。

### Fig. 7 实物样机与 SF 测试系统

建议双栏。

内容：

- 样机照片。
- 测试线圈、磁强计、补偿线圈布置。
- 测试流程图。

风格参考原文 Fig. 7 和 Fig. 12：一张照片或 3D 模型 + 一张流程图。

### Fig. 8 实测 SF 与仿真对比

建议单栏。

数据来源：

`data/raw/prototype_sf_measurement.csv`

建议图：

- 横轴样品：P0、P1 四层铁氧体、P2 hybrid。
- 柱状图比较 simulation 和 measurement。
- x/z 分方向。

### Fig. 9 磁强计 PSD

建议单栏或双栏。

数据来源：

`data/raw/magnetometer_sensitivity_measurement.csv`

建议图：

- PSD 曲线，log-log 坐标。
- 对比：sensor baseline、P1、P2、补偿后 P2。
- 标出 1 Hz、10 Hz、1-30 Hz 平均噪声。

论文写法：

只有这张图能支撑“灵敏度改善”。仿真 SF 和 IntH2 不能替代 PSD 实测。

## 四、TIE 图形细节建议

曲线图：

- 白底。
- 坐标轴黑色。
- 字体 Times New Roman。
- 线宽 1.2-1.5 pt。
- marker 使用 `o`, `s`, `^`, `d`。
- measured 用 marker，simulated/calculated 用实线。
- log 图只在必要时使用，例如 IntH2 和 PSD。

配色：

- ferrite only：黑色或深灰。
- amorphous：蓝色。
- nanocrystalline：红色。
- P0：绿色或紫色。

图题格式：

`Fig. X. Test and simulation results of ... . (a) ... . (b) ... .`

避免：

- 大面积渐变色。
- 过多装饰。
- 中文图中文字。
- 一张图里塞太多颜色。
- 把没有实测的数据写成 measured。

## 五、论文结果段落建议

### hybrid 结果段落

可以写：

The transverse shielding performance of the four-layer ferrite base was first evaluated and then compared with hybrid structures using an additional amorphous or nanocrystalline outer layer. Under the same outer-layer thickness of 0.20 mm, the nanocrystalline layer increased SFx from 3.63 to 25.15, while reducing IntH2_total from 4.16e-6 to 5.33e-8. The amorphous layer also improved SFx, but the improvement was smaller. Therefore, the nanocrystalline outer layer was selected as the preferred hybrid candidate in the present simulation stage.

### 轴向封盖段落

可以写：

The single-ended cap was introduced to evaluate the axial leakage path of the open cylindrical shield. The nanocrystalline cap increased SFz from 2.41 to 2.91, whereas IntH2_total increased from 2.97e-6 to 3.74e-6. In contrast, the P0 amorphous shell with a single amorphous cap showed a lower IntH2_total but only a moderate improvement in SFz. These results indicate that the axial cap improves leakage suppression but should be further evaluated by magnetometer PSD measurements.

### 地磁残余场段落

可以写：

Assuming linear permeability, the simulated SF values were further scaled to a representative geomagnetic field of 50 uT. The estimated transverse residual field was reduced from 13.78 uT for the ferrite base to 1.99 uT for the nanocrystalline hybrid structure. In the axial direction, the residual field remained above 17 uT even with the single-ended nanocrystalline cap, indicating that compensation coils are required for magnetometer operation.

## 六、当前还缺的结果

必须补：

- 实物 SF：P0、P1、P2，至少 x/z 两方向。
- 磁强计 PSD：无屏蔽/基准、P1、P2、补偿后 P2。
- 补偿线圈调零后的 residual DC field 和 drift。

建议补：

- 50 uT 地磁代表性仿真，用于验证线性缩放。
- 非晶/纳米晶材料 `mu''` 的厂家数据、文献数据或实测估计。

