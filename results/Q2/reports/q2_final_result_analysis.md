# Q2 最终结果分析：充电策略关联与设计前代理的限定使用

> Q2-A 的模型角色、置信等级和轮次结论均转录自 `methods/Q2/decisions/result-report-generator_modeler_decision.md` 与 `methods/Q2/decisions/robustness-checker_modeler_decision.md`；Q2-B 的外部升级边界与 Q3-D07 后的 Q4 裁决一致。

## 1. 方法角色与人工裁决

| 模块 | 方法 | 最终角色 | 裁决依据 |
|---|---|---|---|
| Q2-A | M1 主效应 Ridge | 正文保守主线 | M2 的典型误差点估计虽改善，但 bootstrap 区间跨 0；选择最简单的主效应口径。 |
| Q2-A | M2 二阶交互 Ridge | 不同 SOC 阶段倍率交互的探索性关联/敏感性分析 | 不写成显著优于 M1 或因果机制。 |
| Q2-B | P3 低自由度加性 GAM | 已冻结的 Q4 `provisional` 候选代理 | 不作为最终最优或正式寿命排序模型。 |
| Q2-B | C1 受限提升树 | challenger，未替代 P3 | 其相对 P3 的 bootstrap 差值区间跨 0。 |

Q2-A 的人工置信等级为 **limited_medium（限定范围内中等可信）**；Q2-B 只具有 `limited_medium_provisional_only` 的设计前候选含义。

## 2. Train-only 结果

所有模型开发、调参和 2,000 次策略组块 bootstrap 仅使用 41 枚 Train 电芯、40 个 `policy_table9` 策略组；目标为 `ln(cycle_life_table9)`。

| 模块/方法 | RMSE_log | MAE_log | 关键读法 |
|---|---:|---:|---|
| Q2-A M1 主效应 Ridge | 0.37169 | 0.27557 | 简单、透明的正文关联基线 |
| Q2-A M2 二阶交互 Ridge | 0.36854 | 0.25102 | MAE 点估计较 M1 改善 8.91%，但不构成稳定优胜 |
| Q2-B P3 加性 GAM | 0.34892 | 0.23383 | 由预注册简单性/风险规则选作 provisional 候选代理 |
| Q2-B C1 受限提升树 | 0.33168 | 0.22735 | 点误差最低，但未通过替代 P3 的不确定性门槛 |

M2 相对 M1 的 `ΔMAE_log` 95% 区间为 `[-0.07245, 0.02620]`，跨越 0。因此其 8.91% 的点估计改善只能作为敏感性信号，而非“交互模型显著更好”的结论。

## 3. 冻结外部观察及其边界

P3 在 Primary 的一次受限确认（43 枚电芯）为 `RMSE_log=0.289268`、`MAE_log=0.225722`；该确认不重调参数，也未设置事后自动通过门槛。

在最终一次 Secondary 压力测试（40 枚电芯、8 个既有策略组）中：

| 模型 | RMSE_log | MAE_log | 过预测比例 |
|---|---:|---:|---:|
| M1 | 0.547246 | 0.498071 | 2.50% |
| M2 | 0.542798 | 0.507962 | 0.00% |
| P3 | 0.677812 | 0.630770 | 2.50% |

M2 相对 M1 的 Secondary 策略组 bootstrap `ΔMAE_log` 中位数为 `0.012848`，95% 区间 `[-0.089695, 0.083228]`，未形成稳定外部优势。P3 的外部误差也不支持将其升级为正式寿命排序或最优策略代理。因此，Secondary 只能作为已冻结角色的压力测试，不可反向改写 M1/M2/P3 的选择。

## 4. 图表、可写结论与限制

- `results/Q2/experiments/round1/figures/m1_m2_oof_comparison.png`：折外预测散点，说明 M1/M2 的点估计接近；用于“主效应基线与交互敏感性”比较。
- `results/Q2/experiments/q2b_proxy_round1/figures/q2b_proxy_error_comparison.png`：四个设计前候选的折外误差与不确定性，说明不能仅凭受限提升树的最低点误差替换更简单的 P3。
- `results/Secondary_final_pressure_test/figures/secondary_final_observed_predicted.png`：最终外部实测—预测散点，显示 P3 不能据此升级。

### 可写

1. 在给定策略空间内，`C1`、SOC 分界和 `C2` 与寿命存在可用于预测的条件关联；正文以主效应 Ridge 呈现保守关联。
2. 二阶交互仅作为不同 SOC 阶段倍率联合作用的探索性敏感性分析。
3. P3 的作用是设计前候选筛查；任何候选必须经真实 pilot 与 Q3 `k=100` 评价后才能升级。

### 必须避免

1. 不把任一回归系数解释为因果效应。
2. 不称 M2 在外部稳定优于 M1。
3. 不称 P3 为最终最优模型、正式寿命排序模型或可直接推荐策略的依据。

## 5. 写作交接

Q2 正文应先呈现主效应模型的可解释关联，再以交互 Ridge 的敏感性结果说明阶段倍率可能存在联合作用，随后明确其不确定性。Q4 只可继承 P3 的候选生成接口，不得继承“最优策略”结论。

**可交接给**：`final-method-explainer`、`solution-package-builder`。  
**不再执行**：使用 Primary 或 Secondary 回调 Q2 的模型、特征或参数。
