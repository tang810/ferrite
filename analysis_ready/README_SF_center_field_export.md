# SF 中心场导出说明

当前 `Project100_4ceng_fixedT10_g02` 只有内部 torus 电流激励，不能直接给出正式屏蔽系数 SF。正式 SF 需要外部场模型：

`SF = abs(B0_T) / abs(Bcenter_T)`

其中：

- `B0_T`：无屏蔽、同一外部场激励下的中心点磁场
- `Bcenter_T`：有屏蔽、同一外部场激励下的中心点磁场
- `Bcenter_Bx_T/Bcenter_By_T/Bcenter_Bz_T`：有屏蔽中心点残余场三个分量

## 需要导出的数据

先做一组 4ceng fixedT10 g0.2：

| 字段 | 含义 |
|---|---|
| `B0_T` | 无 ferrite 时中心点磁场幅值，单位 T |
| `Bcenter_T` | 有 ferrite 时中心点磁场幅值，单位 T |
| `Bcenter_Bx_T` | 有 ferrite 时中心点 Bx，单位 T |
| `Bcenter_By_T` | 有 ferrite 时中心点 By，单位 T |
| `Bcenter_Bz_T` | 有 ferrite 时中心点 Bz，单位 T |

把数值填入：

`analysis_ready/SF_required_center_fields_template.csv`

然后运行：

```powershell
python analysis_ready/merge_sf_center_fields.py
```

输出：

`analysis_ready/SF_center_fields_clean.csv`

## AEDT 中的最小闭环

1. 复制当前 4ceng 工程，保留 ferrite，作为有屏蔽模型。
2. 在同一个外部场激励下求中心点 `Mag_B`、`B_x`、`B_y`、`B_z`。
3. 再复制一份，把 ferrite 层材料改为 vacuum，其他外部场激励保持完全相同，求 `B0_T`。
4. 不使用内部 torus 线圈中心场作为正式 SF。
