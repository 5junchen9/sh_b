# L1 MAT 深层审计代码复核

复核日期：2026-08-02  
方式：独立只读复核；未重新运行耗时的 MATLAB 全量扫描。

## 结论

没有阻塞问题。审计脚本、循环掩码、摘要和说明文档一致，满足“只做字段—循环掩码，不静默删除整枚电芯”的要求。

## 已处理的审查意见

原先 `prepare_cycle_data.py` 只读取深层审计摘要。现已改为在生成派生数据前强制校验 `mat_deep_cycle_flags.csv`：

- 摘要 JSON 与掩码 CSV 必须同时存在；
- 必须存在 `source_index/batch_index/cycle_index`、名册标识和可用性标识等关键列；
- `(source_index, batch_index, cycle_index)` 必须唯一；
- 总循环数、正式名册循环数、可用循环数和掩码循环数必须与摘要一致，否则中止。

后续新增曲线特征脚本仍必须显式按这组三元键连接该 CSV，并只使用 `in_official_roster=1` 且 `usable_for_curve_features=1` 的循环。

## 通过项

1. 每个循环均检查 `t/Qc/I/V/T/Qd` 六字段长度，未发现长度不一致。
2. 每个字段均检查 NaN/Inf，未发现非有限值。
3. 已检查负时间、相邻时间倒序、`Qc/Qd` 负值、`abs(I)>12 A`、`V` 超出 0–5 V 和 `T` 超出 -40–100 °C。
4. 审计只写出 flags CSV 和 summary JSON；脚本没有写回 MAT、删除记录或按电芯过滤的路径。
5. flags CSV 的 114,738 个 `(source_index, batch_index, cycle_index)` 键唯一；全部可用循环的 `failure_reason` 为空，不可用循环均保留原因。
6. 输出重汇总为：正式名册 100,501 个循环，可用 100,243 个，掩码 258 个；时间倒序 209 个、电流越界 3 个、电压越界 5 个（均为正式名册口径）。
7. `mat_deep_cycle_summary.json`、`data_preparation_summary.json`、数据报告和交接文档的规则与核心计数一致。
