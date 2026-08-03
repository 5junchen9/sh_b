# Q4 Pilot 登记表门禁 Python 代码复审

> **状态**：passed_with_warnings  
> **复审者**：python-code-reviewer  
> **日期**：2026-08-02  
> **已审查脚本**：`code/Q4/q4_validate_pilot_registry.py`  
> **脚本 SHA-256**：`d69a448a15dcc3996521fc0683e0f8ccaef0e731a31e84c6aec5de0da92e6e20`

## 复审范围

该脚本只审查冻结 Q4 pilot 登记表是否可进入后续 k=5 筛查/k=100 确认流程。它不读取任何新电芯曲线，不生成 Q3 预测，也不产生最终推荐。

## 通过项（具体检查）

1. ✅ `code/Q4/q4_validate_pilot_registry.py:15-26` 将默认输入、冻结代表策略、协议和输出全部定位在项目相对路径；状态、k=5 状态、9 槽位和每策略 3 枚电芯规则均显式常量化。
2. ✅ `code/Q4/q4_validate_pilot_registry.py:33-43` 严格解析布尔字段并按 `(C1,Q1_percent,C2)` 构造稳定策略键；非法布尔值或数值无法转换都会阻断，而不是被隐式当作假值。
3. ✅ `code/Q4/q4_validate_pilot_registry.py:46-67` 核对完整字段、正好 9 个槽位、非空且唯一的 `pilot_id`、与三条冻结策略完全一致、以及每策略恰好 3 个槽位，防止 pilot 批次在运行后漂移。
4. ✅ `code/Q4/q4_validate_pilot_registry.py:69-93` 拒绝已分配条码重复、非 `planned` 行缺条码、k=5 状态与完成标志矛盾、k=100 未先完成 k=5、以及没有路径却标为 `Q3_confirmed` 的记录。
5. ✅ `code/Q4/q4_validate_pilot_registry.py:96-128` 提供 `--registry` 显式输入覆盖，保存逐行核验表、JSON 摘要、日志和输入/脚本 SHA-256；不修改传入登记表或任何原始数据。
6. ✅ 使用 `..\\.venv\\Scripts\\python.exe -W error code\\Q4\\q4_validate_pilot_registry.py` 实际运行通过：当前 9 个槽位均为 `planned`、条码均为空、`k5_screen_status=not_due`，摘要正确标记 `all_slots_unassigned`，未把空槽位误报为数据完成。
7. ✅ 以内存副本进行正反例检查：合法的空槽位登记表通过；“第 100 循环完成但第 5 循环未完成”和“两槽位复用同一条码”均按预期抛出阻断错误。

## 约束方向复核

本脚本没有优化求解器。它的硬条件是等式/集合成员检查：每策略**恰好** 3 槽位、总数**恰好** 9；第 100 循环完成必须以第 5 循环完成为前提。这些方向与冻结 pilot 协议一致。

## 失败/修复项

| # | 文件:行 | 问题 | 处理 | 状态 |
|---|---|---|---|---|
| — | — | 未发现需在不改变冻结流程的前提下修复的实现错误 | 未改动登记数据或模型 | 通过 |

## 剩余风险

- 该门禁只能验证登记信息和状态关系，不能代替 P0 对新 cycle 数据的字段—循环审计。
- `Q3_confirmed` 这里只校验第 100 循环和路径存在；真正的 Q3 评价仍需要冻结特征、模型与未来观测按协议运行。
- 当前所有条码为空，结果 `registry_preflight_passed` 仅表示空的计划批次结构正确，不表示 pilot 已启动。

## 运行命令

```powershell
.\.venv\Scripts\python.exe -W error l1\code\Q4\q4_validate_pilot_registry.py
.\.venv\Scripts\python.exe -W error l1\code\Q4\q4_validate_pilot_registry.py --registry l1\data\pilot\q4_k100_pilot_registry.csv
```

## 预期产物

- `results/Q4/experiments/pilot_registry_preflight_round1/tables/q4_pilot_registry_validation.csv`
- `results/Q4/experiments/pilot_registry_preflight_round1/metrics/q4_pilot_registry_preflight_summary.json`
- `results/Q4/experiments/pilot_registry_preflight_round1/run_summary.json`

## 建议下一步

为九个槽位分配不同物理条码后，先重跑本门禁；再以真实 cycle 2–5 数据走 k=5 筛查，以真实 cycle 2–100 数据走冻结 k=100 正式确认。不得用此门禁替代数据审计或 Q3 评价。
