# Q4 已有策略聚合评价代码复审

> **状态：passed_with_warnings**  
> **复审脚本：** `code/Q4/q4_existing_policy_evaluation.py`  
> **实现目标：** 已有 Train/Primary 策略的 Q2+Q3 证据聚合；不生成新策略结果，不读取 Secondary。

## 通过项

1. ✅ `q4_existing_policy_evaluation.py:25-34` 的输入清单只包含标签、Q2/Q3 的 Train OOF 和 Primary 冻结确认工件；没有 Secondary 路径。
2. ✅ `q4_existing_policy_evaluation.py:83-86` 强制开发池为 41 枚 Train + 43 枚 Primary = 84 个唯一条码；实际运行断言通过，输出 84 行电芯证据且条码无重复。
3. ✅ `q4_existing_policy_evaluation.py:88-104` 保留预测来源：Train 使用 `Train_policy_group_OOF`，Primary 使用 `Primary_frozen_confirmation`；两个来源没有被合并为“独立测试”。
4. ✅ `q4_existing_policy_evaluation.py:62-80` 的 bootstrap 以同一策略内的条码为单位重抽样 Q2/Q3 成对预测，样本量为 2,000；表头和报告明确将结果称为经验 P10 摘要，未冒充经重拟合的置信下界。
5. ✅ `q4_existing_policy_evaluation.py:46-56` 的非支配判断方向为“理论时间更小、经验 P10 寿命更大”，且要求至少一项严格改善；这与 Q4 的双目标定义一致。
6. ✅ `q4_existing_policy_evaluation.py:181-184` 将单电芯策略标记为 `observed_single_cell_case` 并排除 Pareto；实际汇总为 60 个策略、19 个多电芯策略、4 个开发池内非支配策略。
7. ✅ `q4_existing_policy_evaluation.py:191-194` 将 CSV、PNG、SVG、Markdown 报告、JSON 摘要和日志全部写入 `results/Q4/experiments/existing_policy_round1/`，运行工件可复现且不覆盖原始数据。
8. ✅ 脚本通过 `python -m py_compile`，随后以项目 `.venv` 实跑；独立断言复核了 84 个条码、60 个策略、19 个多电芯策略、4 个 Pareto 点、41/43 两类来源和 Secondary 未读取。

## 约束方向复核

| 位置 | 方向 | 左侧 | 右侧 | 物理/统计含义 |
|---|---|---|---|---|
| 第 46–56 行 | $\le$ / $\ge$ | 候选时间 / 寿命 | 当前点时间 / 寿命 | 时间不更慢且寿命不更低、至少一项严格改善时构成支配；方向与“快充时间最小、寿命最大”一致。 |
| 第 182 行 | $\ge$ | `cell_count` | 2 | 只有至少两枚物理电芯支持的已有策略才能进入开发池内 Pareto。 |
| 第 183 行 | 非缺失 | `SOH(120)` 经验摘要 | 可评价条件 | 没有 k=100 轨迹预测的策略不得以 SOH 风险齐全的形式进入 Pareto。 |

## 已修复问题

首次运行发现 Train 的 Q3 寿命预测列名为 `pred_log_life`，Primary 为 `predicted_log_life`。已在第 108 行按各自源表映射到统一的 `q3_pred_log_life_k100`，未改变任何模型或数据值；复跑通过。

## 剩余风险

- 4 个非支配点只在开发池中成立，Primary 已有探索暴露，不能写成独立外部泛化或最终推荐。
- 经验 P10 仅重抽样已有电芯预测，未包含代理模型重拟合不确定性；不能叫严格 LCB。
- 新策略仍缺少真实 k=100 early features，不能由本脚本升级为 `Q3_confirmed`；9 槽 pilot 协议仍是唯一合规路径。

## 运行方式

```powershell
.\.venv\Scripts\python.exe l1\code\Q4\q4_existing_policy_evaluation.py
```

## 关键输出

- `results/Q4/experiments/existing_policy_round1/tables/q4_existing_policy_cell_evidence.csv`
- `results/Q4/experiments/existing_policy_round1/tables/q4_existing_policy_summary.csv`
- `results/Q4/experiments/existing_policy_round1/tables/q4_existing_policy_development_pareto.csv`
- `results/Q4/experiments/existing_policy_round1/figures/q4_existing_policy_pareto.png`
- `results/Q4/experiments/existing_policy_round1/q4_existing_policy_report.md`

## 下一步

对 Q4 进行边界/机制审计：检查开发池 Pareto 是否只受单一确认来源驱动、生成 Pareto 留一敏感性摘要，并将已有策略分支与新策略 k=100 pilot 分支写入统一的 Q4 结果报告。
