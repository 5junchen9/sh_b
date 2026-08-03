# Q2-B P3 的 Primary 受限确认协议

> **状态**：FROZEN FOR ONE-TIME EXECUTION  
> **人工来源**：`methods/Q2/decisions/human_primary_confirmation_choice_20260802.md`（Q2-D03）  
> **目的**：在不再选模型、调参或修改评价规则的前提下，报告 P3 在 Primary 的一次受限确认结果。

## 1. 冻结对象

| 项目 | 冻结内容 | 来源 |
|---|---|---|
| 模型 | P3 低自由度加性样条 GAM | Q2-B Train-only 规则选择 |
| 特征 | `C1`、`Q1_percent`、`C2` | 设计前可知策略参数 |
| 目标 | `ln(cycle_life_table9)`；反变换为 `exp` | Q2 统一口径 |
| 参数 | `n_knots=4`、`alpha=0.03` | `q4_p3_full_train_tuning.csv` 的 Train-only 最优行 |
| 拟合集 | 仅 `dataset_table9 == Train` 的 41 枚电芯 | 数据分区政策 |
| 确认集 | 仅 `dataset_table9 == Prim. Test` 的 43 枚电芯 | 数据分区政策 |
| 禁止项 | 不读早期循环特征；不重调参数；不更换 P3；不扩充候选池；不以 Primary 结果反向修改规则 | A3、Q2-D03 |

## 2. 一次性评价

报告 Primary 上的 `RMSE_log`、`MAE_log`、`RMSE_cycle`、`MAE_cycle`、过预测比例、平均正向对数误差及平均正向循环寿命误差，并保存逐电芯预测表和中文观察—预测图。

本协议**不设事后自动通过阈值**：该确认只增加固定模型在 Primary 上的观察证据，不把一次 43 枚电芯的结果包装成无条件泛化或最终最优结论。Primary 已有探索暴露，正式独立压力测试仍留给 Secondary。

## 3. 结果使用边界

1. 不论确认结果如何，P3 都不能因此被称为已证明最优；C1 仍保持 challenger 身份。
2. Q4 的 1775 条仅继续称 `Q2_provisional`；本协议不产生寿命下界、正式 Pareto 或推荐点。
3. Q3 的 `k=5` 筛查与 `k=100` 正式窗口角色不改变；新策略仍须真实运行至 k=100 才能进入 Q3 确认。
4. 确认运行后，只能由建模者填写结果/稳定性置信及 claim scope；不得回到 Train 与 Primary 混合选模型。

## 4. 可复现入口

```powershell
.\.venv\Scripts\python.exe -W error l1\code\Q2\q2b_primary_confirmation.py
```

输出固定在 `results/Q2/experiments/q2b_primary_confirmation_round1/`，运行摘要记录协议、脚本、P0、标签、P3 选择 JSON 与冻结参数表的 SHA-256。
