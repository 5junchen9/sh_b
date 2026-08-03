# Q2 图表与表格计划（开发期）

> **状态**：开发期可用。M1 是保守策略关联基线，M2 仅为交互敏感性分析，P3 仅为 Q4 `Q2_provisional` 提名代理。

## 1. 图形清单

### Type 2：模型比较图

| ID | 图题 | 比较内容 | 来源 | 开发稿位置 | 状态 | 建议图注 |
|---|---|---|---|---|---|---|
| Q2-F1 | M1 与 M2 的策略分组折外误差 | 主效应 Ridge 与二阶交互 Ridge | `results/Q2/experiments/round1/figures/m1_m2_oof_comparison.png` | Q2 方法选择 | 存在 | “策略组折外误差比较；M2 的点估计更低，但 bootstrap 差值区间跨 0。” |
| Q2-F2 | Q2-B 代理误差比较 | Ridge、ElasticNet、GAM 与受限提升树 | `results/Q2/experiments/q2b_proxy_round1/figures/q2b_proxy_error_comparison.png` | Q2→Q4 过渡 | 存在 | “设计前代理的 Train-only 误差比较；复杂模型不因单次点估计自动取代简单模型。” |
| Q2-F3 | 过预测风险比较 | 候选代理的单侧高估风险 | `results/Q2/experiments/q2b_proxy_round1/figures/q2b_proxy_overprediction_risk.png` | Q2→Q4 过渡 | 存在 | “候选代理的过预测风险诊断；P3 的角色仅限于待试验候选提名。” |

### Type 1：诊断图

| ID | 图题 | 诊断目的 | 来源 | 状态 |
|---|---|---|---|---|
| Q2-D1 | M1 特征解释性 | 检查主效应系数和消融结果是否稳定 | `results/Q2/experiments/m1_explainability_round1/figures/q2_m1_factor_explainability.png` | 存在 |
| Q2-D2 | P3 Primary 观察—预测 | 记录一次固定确认的误差形态，不作选型 | `results/Q2/experiments/q2b_primary_confirmation_round1/figures/q2b_primary_observed_vs_predicted.png` | 存在 |

## 2. 表格清单

| ID | 表题 | 类型 | 来源 | 状态 |
|---|---|---|---|---|
| Q2-T1 | M1/M2 策略组折外误差 | comparison_table | `results/Q2/experiments/round1/metrics/comparison_metrics.json` | 存在 |
| Q2-T2 | P3 与 challenger 比较及选择规则 | comparison_table | `results/Q2/experiments/q2b_proxy_round1/tables/q2b_model_comparison_and_selection.csv` | 存在 |
| Q2-T3 | M2 bootstrap 误差差与符号稳定性 | sensitivity_table | `robustness/Q2/tables/q2_policy_block_bootstrap.csv`、`q2_interaction_sign_stability.csv` | 存在 |

## 3. 风险与冻结条件

- 禁止把 M2 的点估计改善写作显著优于 M1，或将系数写作因果贡献。
- 禁止把 P3 的 Primary 观察图作为独立外部验证图。
- 只有完成最终冻结包后，才可从上述 Type 2 图中选择并升级正式 Type 3 论文图。
