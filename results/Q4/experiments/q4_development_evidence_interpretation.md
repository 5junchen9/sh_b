# Q4 开发期证据解释与下一步试验接口

> **状态**：development_evidence_only；不是最终推荐，也不替代 Secondary 压力测试。  
> **口径版本**：Q2-B P3 仅用于新策略 `Q2_provisional` 提名；已有策略使用 M2-k=100 的 Q3 开发池聚合。Primary 的旧脚本标签已在 `methods/Q3/q3_round2_scope_update.md` 中重标为 M2。

## 1. 当前数据能够支持什么

| 证据对象 | 已完成的计算 | 可写出的客观结论 | 不能写成 |
|---|---|---|---|
| 60 个已有实验策略 | Train 的策略分组 OOF 与 Primary 一次受限确认聚合；电芯内 2,000 次 bootstrap | 其中 19 个策略有至少 2 枚物理电芯，4 个在“理论 0–80% 时间更短、经验 P10 寿命摘要更大”的开发池比较中非支配 | 最终最优策略、独立外部验证、经全流程重拟合的寿命置信下界 |
| 4 个开发池非支配案例 | 见 `existing_policy_round2_m2k100/tables/q4_existing_policy_development_pareto.csv` | 它们可作为“已有策略的开发期对照案例” | 稳健 Pareto 前沿：4 点均仅 `n=2`，`n≥3` 与留一电芯敏感性下保留率均为 0 |
| 3,653 个策略格点 | Train-only 双空间 5-NN 与 1,000 次 barcode bootstrap 支持域审计 | 1,775 个格点在冻结规则下可列为 `Q2_provisional` 待试验候选 | 已被 Q3 确认，或可据 P3 点预测宣布寿命排名 |
| 三个代表 pilot | 从 15 个“理论时间—P3 点预测”非支配候选中选取快速、均衡、寿命端各一个 | 可形成每策略 3 枚、共 9 枚的最小试验排程 | 已验证的推荐策略或正式 Pareto 点 |

## 2. 为什么当前不从 4 个已有策略中选“最佳”

四个非支配案例都由 2 枚电芯支撑，且恰为 1 枚 Train OOF 与 1 枚已经探索暴露的 Primary 确认记录。将准入收紧到 `n≥3`，或在每个策略内留出 1 枚电芯时，四点保留率均为 0。这说明数据足以展示开发期的时间—寿命权衡形状，但不足以把其中任一点包装为稳定、可推广的最优方案。

因此，Q4 的当期交付应为“证据分级 + pilot 方案”，而非唯一最优点：

1. 已有策略：列为开发池对照案例，表中固定写明 `n=2` 与 `development_pool_non_dominated_not_external`。
2. 新策略：仅列为 `Q2_provisional`，必须与已有策略的 Q2+Q3 证据分表呈现。
3. 结论强度：只说“在当前开发数据与冻结准入规则下的候选/案例”，不说“最优”或“安全”。

## 3. 已冻结的 pilot 接口

| 角色 | C1 (C) | Q1 (SOC) | C2 (C) | 理论 0–80% 时间 (min) | P3 点预测寿命 (cycle) | 支持率 | 最少电芯 |
|---|---:|---:|---:|---:|---:|---:|---:|
| 快速端代表 | 6.00 | 65% | 4.50 | 8.500 | 313.7 | 0.810 | 3 |
| 中间权衡代表 | 5.20 | 71% | 3.50 | 9.735 | 874.7 | 1.000 | 3 |
| 寿命端代表 | 4.40 | 71% | 3.50 | 11.225 | 984.4 | 1.000 | 3 |

上述 P3 值仅用于使三条 pilot 覆盖不同的设计前权衡，不能作为保守下界或正式寿命排序。完整登记模板位于 `data/pilot/q4_k100_pilot_registry_template.csv`。

## 4. 新策略的升级路径

1. 每条 pilot 先运行到 k=5；只生成最早筛查、异常预警与资源调度记录，不以 k=5 单独升级或淘汰策略。
2. 同一物理电芯继续运行到 k=100；按已冻结 P0 掩码、M2-k=100 早期特征与 SOH 模板得到真实的 Q3 证据。
3. 只有在获得真实 k=100 数据并通过事先锁定的 Q3 规则后，才可标为 `Q3_confirmed` 并与已有策略一起计算正式 Pareto。
4. 模型、特征、窗口、指标与可信域规则不再通过 Primary 回调；完全冻结后才读取 Secondary 做一次跨批次压力测试。

## 5. 证据文件

- `results/Q4/experiments/existing_policy_round2_m2k100/q4_existing_policy_report.md`
- `robustness/Q4/round2_m2k100/q4_robustness_report.md`
- `results/Q4/experiments/train_dry_run_round1/q4_train_only_dry_run_report.md`
- `results/Q4/experiments/pilot_design_round1/q4_pilot_batch_design_report.md`
- `outputs/experiments/primary_confirmation_manifest_post_exposure.json`
