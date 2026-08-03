# Q4 图表与表格计划（开发期）

> **状态**：开发期可用。所有新增策略均为 `Q2_provisional`，没有真实 pilot 或 Secondary 结果；已有策略的 4 个非支配点仅是开发池案例。

## 1. 图形清单

### Type 2：开发证据比较图

| ID | 图题 | 比较内容 | 来源 | 开发稿位置 | 状态 | 建议图注 |
|---|---|---|---|---|---|---|
| Q4-F1 | Train-only 候选流量 | 3,653 格点经过数学可行、双空间 5-NN 与 bootstrap 支持率的筛选 | `results/Q4/experiments/train_dry_run_round1/figures/q4_train_only_candidate_flow.png` | Q4 方法 | 存在 | “新策略候选的可信域筛选流程；通过者仍仅为 Q2_provisional。” |
| Q4-F2 | 已有策略开发池 Pareto 案例 | 60 个已有策略中的时间—经验寿命摘要权衡 | `results/Q4/experiments/existing_policy_round2_m2k100/figures/q4_existing_policy_pareto.png` | Q4 结果 | 存在 | “开发池非支配案例；所有点均需保留 n=2 和非外部验证边界。” |
| Q4-F3 | 三策略 pilot 排程代表 | 快速、均衡和寿命端候选 | `results/Q4/experiments/pilot_design_round1/figures/q4_pilot_representatives.png` | Q4 后续试验 | 存在 | “用于覆盖设计前权衡的最小 pilot 排程，不是最终推荐。” |

### Type 1：诊断图

| ID | 图题 | 诊断目的 | 来源 | 状态 |
|---|---|---|---|---|
| Q4-D1 | 既有策略 Pareto 留一/样本量敏感性 | 检查 n=2 非支配点的脆弱性 | `robustness/Q4/round2_m2k100/figures/q4_existing_policy_sensitivity.png` | 存在 |

## 2. 表格清单

| ID | 表题 | 类型 | 来源 | 状态 |
|---|---|---|---|---|
| Q4-T1 | Train-only 候选流量与阈值 | parameter_table | `results/Q4/experiments/train_dry_run_round1/tables/q4_candidate_flow.csv` | 存在 |
| Q4-T2 | 4 个已有策略开发池非支配案例 | model_result_table | `results/Q4/experiments/existing_policy_round2_m2k100/tables/q4_existing_policy_development_pareto.csv` | 存在 |
| Q4-T3 | 三策略、九电芯 pilot 配置 | parameter_table | `results/Q4/experiments/pilot_design_round1/tables/q4_k100_pilot_representatives.csv` | 存在 |
| Q4-T4 | Pareto 样本量/留一敏感性 | sensitivity_table | `robustness/Q4/round2_m2k100/tables/q4_existing_policy_sensitivity.csv` | 存在 |

## 3. 风险与冻结条件

- 4 个非支配案例全为 n=2，收紧为 n≥3 或留一电芯时保留率为 0；不得从中输出“最佳”。
- P3 仅给出设计前点预测，不能构造新策略的 Q3 寿命或 SOH 证据。
- 正式 Type 3 Pareto 图必须等到模型/窗口/指标冻结、真实 pilot 已执行且 Secondary 一次性压力测试完成后再生成。
