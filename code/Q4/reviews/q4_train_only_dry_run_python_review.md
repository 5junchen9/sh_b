# Q4 Train-only Dry-run Python Code Review

> **状态**：passed_with_warnings  
> **审查者**：python-code-reviewer  
> **日期**：2026-08-02  
> **审查脚本**：`code/Q4/q4_train_only_dry_run.py`
> **当前脚本 SHA-256**：`f6862238241494411dc0b088cc098acccb7c6f4bd2ea841d082ba870d861d69b`

## 通过项

1. `code/Q4/q4_train_only_dry_run.py:4-5` 明确声明不读取 Q3 特征、Primary/Secondary 标签、寿命 LCB 或正式 Pareto；实际输入代码在 `:222-227` 仅打开 P0 与 `cell_labels.csv` 并筛选 `dataset_table9 == 'Train'`。
2. `code/Q4/q4_train_only_dry_run.py:62-79` 用 `tau_0_80_min=60[q/C1+(0.8-q)/C2]` 推导理论 0–80% 时间和四段 SOC 暴露；`q=0.8` 时将 `C2_effective=C1`，与 Train 中单阶段编码一致。
3. `code/Q4/q4_train_only_dry_run.py:125-136` 只由 Train 已观测离散水平生成候选，并对 `Q1=80%` 采用单阶段分支；运行结果恰为 3,653 个格点，未在参数 min/max 长方体内任意细分。
4. `code/Q4/q4_train_only_dry_run.py:105-122, :241-250` 用 Train 中位数/IQR 标准化 raw/SOC 两空间、留一第 5 邻居距离的 95% 分位设阈值，并以 1,000 次 barcode 重抽样检查支持率；重复 barcode 在每次抽样中先去重，未被当成多个邻居。
5. `code/Q4/q4_train_only_dry_run.py:88-101, :253-256` 在全 Train 上以策略分组 CV 从已冻结 P3 网格选择参数、再 refit 加性样条 GAM；预测输入仍仅为 `C1/Q1_percent/C2`，没有使用未来可见信息。
6. `code/Q4/q4_train_only_dry_run.py:258-261` 只有同时通过双空间 5-NN 和 80% bootstrap 支持的候选才标为 `Q2_provisional`，状态原因固定为“仍须 pilot 与 Q3 k=100 确认”；`model_disagreement_log` 显式写为 `N/A`，未伪造为 0。
7. `code/Q4/q4_train_only_dry_run.py:262-299` 保存完整候选、暂定候选、调参表、候选流量、阈值 JSON、中文 PNG/SVG、日志与运行摘要；输出均位于 `results/Q4/experiments/train_dry_run_round1/`。
8. 已执行 `python -m py_compile` 及 `python -W error l1/code/Q4/q4_train_only_dry_run.py`，均返回 0；独立断言确认总候选 3,653、`Q2_provisional` 1,775，且每条均双空间通过、bootstrap 通过、单模型分歧为 `N/A`。
9. 已目视检查 `results/Q4/experiments/train_dry_run_round1/figures/q4_train_only_candidate_flow.png`：中文标题、坐标、图例和状态标识可读；图明确写有“非正式推荐／不等于 Pareto”，未提升到 `paper/figures/`。
10. 2026-08-02 最终追溯重跑后，P0 输入哈希、脚本哈希均与当前文件匹配，目标字段显式记为 `ln(cycle_life_table9)`；候选流量仍为 `3653→2858→2398→2329→1775`。

## 失败／已修复项

| # | 文件:位置 | 问题 | 处理 | 状态 |
|---|---|---|---|---|
| 1 | `code/Q4/q4_train_only_dry_run.py:169`（修复前） | 中文字体缺少 Unicode 下标 `₀/₋/₈`；严格 `-W error` 在 `tight_layout()` 处中断。 | 坐标标签改为兼容字符 `τ0-80`，重跑通过。 | 已修复 |
| 2 | `code/Q4/q4_train_only_dry_run.py:274`（修复前） | 流量表的末级仅统计 bootstrap 通过，语义可能与最终暂定候选交集混淆。 | 改为统计 `status == Q2_provisional`，并将标签改为“**双空间且**支持率≥80%”。 | 已修复 |
| 3 | `code/Q4/q4_train_only_dry_run.py:156`（修复前） | 左图长阶段标签挤压横轴。 | 使用短标签和柱顶数量，完整阶段名称保留在 CSV/报告。 | 已修复 |

## 约束方向审查

本脚本无资源分配或物理不等式约束。唯一门槛关系为 `d5 <= c` 与 `support_rate >= 0.80`，均与 `methods/Q4/q4_train_only_dry_run_protocol.md` 的支持域定义一致；未自动修改任何物理安全阈值。

## 剩余风险

- 1,775 条仅表示候选格点在 Train 支持域内稳定，不等于有 1,775 个值得实际试验的“最优策略”；后续仍须去重、工程可实施性审查和 pilot 资源约束。
- P3 点预测没有 Train 全流程 bootstrap 寿命下界，按协议不能用于正式寿命排名或 Pareto。
- Q3 对新策略没有真实 early features，当前任何新点都不能升级为 `Q3_confirmed`。
- 此图是内部 Type 2 诊断图，未写入人工确认的论文核心主张，故不可直接升入论文主图。

## 运行说明

```powershell
.\.venv\Scripts\python.exe -W error l1\code\Q4\q4_train_only_dry_run.py
```

## 预期输出

- `results/Q4/experiments/train_dry_run_round1/tables/q4_train_only_all_candidates.csv`
- `results/Q4/experiments/train_dry_run_round1/tables/q4_q2_provisional_candidates.csv`
- `results/Q4/experiments/train_dry_run_round1/tables/q4_candidate_flow.csv`
- `results/Q4/experiments/train_dry_run_round1/metrics/q4_train_only_dry_run_summary.json`
- `results/Q4/experiments/train_dry_run_round1/figures/q4_train_only_candidate_flow.svg`
- `results/Q4/experiments/train_dry_run_round1/q4_train_only_dry_run_report.md`

## 建议下一步

不要输出正式 Q4 最优点。应先冻结 Primary 受限确认协议；对通过的 `Q2_provisional` 候选安排至少 3 枚不同物理电芯的 pilot，运行到 k=100 后由 Q3 进行确认，再形成正式 Q2+Q3 Pareto。
