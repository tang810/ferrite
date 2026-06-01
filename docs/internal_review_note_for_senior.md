# 给师兄的内部审阅说明

## 当前稿件完成了什么

当前版本已经整理为一版 IEEE TIM-oriented internal review draft，重点不是声称结果已经完整，而是把论文的测量表征逻辑和投稿前验证路线写清楚。稿件已经完成以下核心内容：

1. 建立了低噪声磁测量仪器中的问题定义：屏蔽体同时影响外界泄漏场和材料损耗相关磁噪声。
2. 明确将磁屏蔽体作为 measurement chain 的一部分，而不是只作为被动外壳。
3. 给出了方向性屏蔽因子 `SFq` 和泄漏比 `LeakageRatioq` 的分量化定义，正式计算不使用 `BMag`。
4. 给出了 no-shield directional reference 的验证逻辑。
5. 给出了 virtual pickup-coil 下的 IntH2 定义，并明确 IntH2 只是 magnetic-noise-related loss indicator，不是 measured noise。
6. 给出了 multilayer thin-ferrite cylindrical shield 的几何定义、体积计算和 fixed-volume comparison 逻辑。
7. 给出了 paper-use criteria：只有 raw export、B0 direction validation、方向分量 SF、layerwise IntH2 check 都满足的 case 才能进入正式结论。

## 为什么适合 IEEE TIM

该选题与 IEEE TIM 的适配点在于：它不是单纯做材料或结构仿真，而是围绕“测量仪器中的屏蔽体表征”建立可复现的方法。稿件强调方向性校准参考、分量化 shielding factor、虚拟拾取线圈损耗积分、层分解 loss integral、固定体积公平比较和验证门控的数据使用规则。这些内容对应 instrumentation and measurement 中对测量定义、校准参考、数据一致性和不确定性控制的要求。

## 后续还需要补哪些实验/仿真

投稿前建议优先完成以下验证：

1. Mesh and boundary-domain convergence：补齐 total elements、adaptive passes、air-domain scale，并完成 2R、3R、5R air-domain convergence。
2. Axial shielding：完成 `C1_N1_t060_z`、`C2_N3_t020_g010_z`、`C2_N4_t015_g008_z`，输出 `SFz`、`LeakageRatioz`、`SFz/SFx`。
3. Segmented-shell correction：完成 `C2_N4_t015_g008_x` 的 aligned 和 staggered 分段模型，参数为 `Nseg=12`、`g_phi=1.6 mm`。
4. Permeability sensitivity：对 `C1_N1_t060_x` 和 `C2_N4_t015_g008_x` 扫描 `mu_r'=500,1000,2000,5000`。
5. Field maps：导出 external-field B distribution、flux lines、`Hvc`、`Hvc^2`，用于支撑物理解释。
6. Optional prototype measurement：如果条件允许，补 Helmholtz/triaxial coil + calibrated magnetometer 的 `SFx_exp`、`SFz_exp` 和 uncertainty budget。

## 哪些结果不能提前写入正式投稿结论

当前不能提前写入正式结论的内容包括：

1. 不能声称 numerical robustness 已完整验证，因为 mesh metadata 和 boundary-domain convergence 还不完整。
2. 不能把 transverse `SFx` 排名推广到 axial `SFz`。
3. 不能把 continuous-shell 结果直接写成 manufacturable segmented assembly 结果。
4. 不能声称四层结构 ranking 对 permeability variation 鲁棒。
5. 不能对外层 IntH2 贡献最高给出强物理机制解释，除非 field maps 支撑。
6. 不能把 IntH2 写成实测噪声；它只能作为 magnetic-noise-related loss indicator。
7. 不能写 final optimal design 或 final instrument-level recommendation。
