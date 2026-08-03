# Q4 Pilot 排程 Python 代码复审

> **状态**：passed_with_warnings  
> **复审者**：python-code-reviewer  
> **日期**：2026-08-02  
> **已审查脚本**：`code/Q4/q4_pilot_batch_design.py`  
> **脚本 SHA-256**：`f4be01a408f18d508448bc2a5066d27f533d4318fecb3fb276736c1e286f73e2`

## 复审范围

脚本从冻结的 1,775 条 `Q2_provisional` 候选中构造一个**最小三策略、每策略 3 枚物理电芯**的 k=100 pilot 排程批次。P3 点预测只能参与排程代表性，不能构成正式 Pareto、最终寿命排序或最优策略。

## 通过项（具体检查）

1. ✅ `code/Q4/q4_pilot_batch_design.py:19-26` 使用项目相对路径、固定输出目录和固定最小复现数；不读取 Primary、Secondary 或任何未登记的 pilot 结果。
2. ✅ `code/Q4/q4_pilot_batch_design.py:91-101` 验证冻结候选表、协议文件、必要字段、1,775 条记录、双空间支持、80% bootstrap 支持率以及关键数值有限性；输入漂移会直接报错而不是悄悄重新筛选。
3. ✅ `code/Q4/q4_pilot_batch_design.py:33-42` 的非支配定义同时要求更短 `tau_0_80_min` 和更大的 P3 点预测寿命，至少一项严格更优；没有把两个目标任意加权成单分数。
4. ✅ `code/Q4/q4_pilot_batch_design.py:45-99` 从非支配集选择快速端、中间时间权衡和寿命端三个不同策略三元组，并展开为每策略 3 个、共 9 个未分配物理电芯槽位；检查策略三元组和 `pilot_id` 均不重复。
5. ✅ `code/Q4/q4_pilot_batch_design.py:72-85` 输出中文标题、坐标、图例并保存 PNG/SVG；已人工核对 `figures/q4_pilot_representatives.png`，星标、坐标和文字均可读。
6. ✅ `code/Q4/q4_pilot_batch_design.py:139-165` 保存非支配候选、代表点、9 槽位分配表、JSON 运行摘要、Markdown 报告和日志；报告明确 k=5 仅筛查、k=100 才确认，摘要记录输入/脚本 SHA-256、环境、最小 9 枚电芯和每个代表点参数。
7. ✅ 使用 `..\\.venv\\Scripts\\python.exe -W error code\\Q4\\q4_pilot_batch_design.py` 实际运行通过；得到 15 条时间—P3 点预测非支配候选、3 条互异代表点和 9 条空条码的 `planned/not_due` 分配槽位，输入候选数为 1,775。

## 约束方向复核

本脚本是候选筛选与排程，不含优化变量或求解器不等式约束。硬门槛 `support_bootstrap_rate >= 0.8` 在 `:98` 显式按“支持率下限”实现；它来自已冻结协议，不应在 pilot 结果出现后调整。

## 失败/修复项

| # | 文件:行 | 问题 | 处理 | 状态 |
|---|---|---|---|---|
| 1 | `code/Q4/q4_pilot_batch_design.py:79` | 中文字体缺少 Unicode 下标 `₀/₋/₈`，在 `-W error` 下会阻断作图 | 将坐标标签改为 `tau_0-80`，保留中文含义 | 已修复并严格复跑 |

## 剩余风险

- 三个代表点是最低 9 枚电芯 pilot 的排程覆盖，不是最终推荐；P3 预测最高的点也不能写成真实寿命最高。
- “中间权衡”按时间区间的中点选取，是为覆盖取舍而设的冻结排程规则；若实际实验资源不是 3 策略×3 电芯，必须新开设计轮次，不可事后增删代表点。
- 现阶段没有新策略的真实 cycle 2–100 数据，因此本轮只能标为 `planned_not_executed`。

## 运行命令

从 `l1/` 目录运行：

```powershell
..\.venv\Scripts\python.exe -W error code\Q4\q4_pilot_batch_design.py
```

## 预期产物

- `results/Q4/experiments/pilot_design_round1/tables/q4_pilot_time_life_pareto_candidates.csv`
- `results/Q4/experiments/pilot_design_round1/tables/q4_k100_pilot_representatives.csv`
- `results/Q4/experiments/pilot_design_round1/tables/q4_k100_pilot_allocation_template.csv`
- `results/Q4/experiments/pilot_design_round1/figures/q4_pilot_representatives.png`
- `results/Q4/experiments/pilot_design_round1/metrics/q4_pilot_design_summary.json`
- `results/Q4/experiments/pilot_design_round1/q4_pilot_batch_design_report.md`

## 建议下一步

按 `methods/Q4/q4_k100_pilot_protocol.md` 为三条代表策略各登记 3 枚不同物理电芯；只有取得真实 cycle 2–100 数据后，才能运行冻结的 P0/Q3 步骤。后续不允许以 pilot 结果重选本批次代表点。
