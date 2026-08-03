# P0 Python 代码复审

> **状态**：passed_with_warnings  
> **复审时间**：2026-08-02  
> **对象**：`src/build_p0_model_view.py`  
> **脚本 SHA-256**：`52f3f804e3b1b93b05bbb15b997dbc5543ff1864a77d150e8e2e26b5761a5d8c`

## 明确通过项

1. ✅ `build_p0_model_view.py:177` 仅保留 `global_cycle_index < cycle_life_table9`；本次重建得到 99,279 行、124 枚电芯，且每枚恰为 `L-1` 行。
2. ✅ `:53-62, :193-207` 对持久化布尔字段做显式解析，不会把字符串 `False` 当成真；发现非布尔值会立即阻断。
3. ✅ `:200-215` 为七个字段分别保存原值、`valid_*` 与 `mask_reason_*`；异常只屏蔽相应“字段—循环”，没有静默删除整枚电芯。
4. ✅ `:218-227` 对每一行有限温度执行 `Tmin≤Tavg≤Tmax` 检查；已修复旧版“任一非有限值导致跳过全表检查”的边界错误。
5. ✅ `:231-239` 的充电时间统计上界只由 Train 结构有效行拟合，再冻结应用于三个分区；Primary/Secondary 未参与阈值估计。
6. ✅ `:242-251` 只用有效 cycle 2 容量计算 `SOH_rel`，并用 `QDischarge/1.1` 计算 `SOH_nom`，没有用未来循环回填早期特征。
7. ✅ `:285-302` 独立生成 `k=5/10/20/50/100` 五套早期特征；窗口只含 cycle 2 到 k，寿命标签仍只保留在 `cell_labels.csv`。
8. ✅ `:162, :304-305` 在运行前后重算六个原始 MAT/XLSX 文件 SHA-256，确认原始文件字节未改变。
9. ✅ `:343-358` 在 `p0_summary.json` 保存脚本、输入、原始源文件和六个主要输出哈希；当前摘要脚本哈希与文件完全一致。
10. ✅ 已实际执行 `python -W error l1/src/build_p0_model_view.py`，无警告或异常，输出 `p0_status=pass`。

## 已修复问题

| 问题 | 修复 | 结果 |
|---|---|---|
| 温度顺序检查使用全表标量有限性判断 | 改为逐行有限掩码后检查 `Tmin≤Tavg≤Tmax` | fixed |
| CSV 布尔列可能被 `astype(bool)` 误读 | 新增严格 `true/false/1/0` 解析 | fixed |

## 剩余边界

- P0 只执行已预注册的结构与物理边界；没有根据结果临时新增容量、温度或内阻阈值。
- RAW 曲线六字段长度、NaN/Inf、时间倒序和电压等深层检查由 `outputs/data_audit/` 的上游审计产物负责；P0 通过四字段键一对一继承其掩码。
- `IR` 单位为 Ω、`chargetime` 单位为 min；测量时点与充电时间起止定义仍应在论文中保守说明。

## 复现命令

```powershell
.\.venv\Scripts\python.exe -W error l1\src\build_p0_model_view.py
```

