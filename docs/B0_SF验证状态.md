# B0/SF 数据链路状态

只记录 B0 reference 和横向 SF 的可信性排查。当前不写多层优于单层的结论，不扩展 N=6，不跑分段壳。

## 当前结论边界

数据流水线已就绪。B0_reference_x 已重建并通过方向验证。单层和多层连续壳 x 向导出均已完成。

## 已发现的问题

旧 `analysis_ready/manufacturable_thin_center_fields_exported.csv` 里 C1_N1_t008 行的 B0 数据有问题：B0_Bx_T = -1.65e-08, B0_By_T = 5.64e-09, B0_Bz_T = 3.33e-08, B0_Mag_T = 3.66e-08。对 x 向外场，B0_Bx_T 的绝对值应该明显大于 By 和 Bz，但这组数据里 Bz 比 Bx 大，说明这组 B0 不可信。因此旧表里用 Mag_B 算出来的 SF=0.6265 不能进论文。

正式计算必须用 SFx = |B0_Bx_T| / |Bcenter_Bx_T|，LeakageRatiox = |Bcenter_Bx_T| / |B0_Bx_T|。Mag_B 只做辅助检查。

## 排查确认项

1. B0_reference_x 和屏蔽 case 用同一套外部场设置 — 已确认（都是 x 向切向 H 场）
2. B0_reference_x 工程里铁氧体已替换为 vacuum — 已确认
3. 外场方向是 x，不是 z 或混合 — 已确认（方向比 6.47e+06）
4. 中心观测点是同一个 BcenterPoint_0_0_0 — 已确认
5. 后处理没用 Mag_B 做正式 SF — 已确认
6. B0 和 shield 都重新求解后再导出 — 已确认
7. 四个单层 case SFx >= 1 且随厚度趋势合理 — 已确认，然后才继续做 N=2/3/4

## B0_reference_x

工程位置：`aedt/reference/B0_reference_x.aedt`。从单层 shield 复制模板，删掉 torus/current 外场，Cylinder2 改成 vacuum，Box1 的 y/z 面加 x 向切向 H，x 端面加零切向 H。

导出：`data/raw/B0_reference_x.csv`

B0_Bx_T = 1.2566e-06 T, B0_By_T = -3.83e-15 T, B0_Bz_T = -1.94e-13 T, B0_Mag_T = 1.2566e-06 T, 方向比 = 6.47e+06, validation_status = passed。

## 已完成的 case

B0_reference_x、C1_N1_t008_x、C1_N1_t020_x、C1_N1_t040_x、C1_N1_t060_x、C2_N2_t020_g010_x、C2_N3_t020_g010_x、C2_N4_t015_g008_x — 全部导出并验证通过。

## 暂停项

N=6、分段壳 aligned/staggered、z 向扩展、灵敏度/收敛性研究 — 暂时不进批处理。
