# Q4 已有策略 Pareto 敏感性报告

## 1. 计算事实

- 基线口径（至少 2 枚电芯、Q2/Q3 经验 P10 寿命摘要）得到 4 个开发池内非支配策略。
- 所有 4 个基线 Pareto 策略均为 `n=2`，且各由 1 枚 Train OOF 与 1 枚 Primary 冻结确认电芯组成。
- 将最小策略样本数从 2 收紧为 3 后，基线 Pareto 点保留率为 0%；对每个基线点留出任一电芯后，策略均降为单电芯案例，资格保持率亦为 0%。
- 使用中位数寿命摘要及要求每个策略同时含 Train 与 Primary 证据时，结果见 `tables/q4_existing_policy_sensitivity.csv`；这些都是开发池内部敏感性而非外部验证。

## 2. 结论边界

当前 4 个点可作为“已有策略中的开发池内权衡案例”，但其 Pareto 身份高度依赖最小样本阈值。论文不得把它们称为稳健的最终推荐、工程最优或独立外部验证；应同时报告每个策略仅有 2 枚电芯及其来源构成。

## 3. 产物

- `tables/q4_existing_policy_sensitivity.csv`
- `tables/q4_existing_policy_pareto_leave_one_cell.csv`
- `figures/q4_existing_policy_sensitivity.png/svg`
