# Q3/Q4 图表中文化重跑核验

> 状态：passed_with_warnings  
> 核验日期：2026-08-03  
> 范围：仅更新图表文字，不改变数据、模型、分组、随机种子或选择结论。

## 通过项

1. `code/Q3/q3_run_joint_comparison.py` 将第二轮总标题和 SOH 纵轴改为中文；以 `-W error` 重跑成功，五个窗口的 M1–M4 数值与重跑前一致。
2. `code/Q3/q3_round2_robustness.py` 将图的轮次标题改为“Q3 第二轮”；以 `-W error` 重跑成功，策略组 bootstrap 仍为 2,000 次。
3. `code/Q3/q3_run_raw_curve_challenger.py` 将“RAW/Train-only/challenger”图中文字改为“原始电压/仅训练集/候选模型”；以 `-W error` 重跑成功。目视核验 `results/Q3/experiments/round3_raw_curve_challenger/figures/q3_raw_curve_challenger.png`，标题、图例、坐标和单位清晰可读。
4. `code/Q3/q3_raw_curve_challenger_robustness.py` 将 bootstrap 图标题、纵轴改为中文；以 `-W error` 重跑成功，未改变比较对象或置信区间计算。
5. `code/Q4/q4_train_only_dry_run.py` 将候选流量图的“Train、raw、Pareto”等普通文字改为中文；以 `-W error` 重跑成功。目视核验 `results/Q4/experiments/train_dry_run_round1/figures/q4_train_only_candidate_flow.png`，图仍明确写有“非正式推荐”和“并非帕累托解”。
6. Q4 候选流量计数仍为 3,653→2,858→2,398→2,329→1,775；这些数值只说明支持域筛选，未被改写为正式优化结论。
7. `code/Q4/q4_existing_policy_round2_m2k100.py` 和敏感性脚本已以 `-W error` 重跑；目视核验已有策略图，普通文字中的“Pareto、Train、Primary”已改为“帕累托比较、训练集、主确认集”，60 个策略、4 个开发池非支配案例及 n≥3/留一保留率均未改变。

## 保留警示

- `M3R-k5` 的寿命误差 bootstrap 区间仍跨 0；图表中文化不改变其“仅候选、待 Gate G4.5”的地位。
- Q4 图中的 Q2、P3、SOC 与单位 min 是变量/指标缩写，保留以便与方法和表格一一对应；其余叙述性文字均使用中文。
- 本次没有读取 Primary 或 Secondary，也没有生成新策略的实测结果。

## 复现命令

```powershell
.\.venv\Scripts\python.exe -W error l1\code\Q3\q3_run_joint_comparison.py
.\.venv\Scripts\python.exe -W error l1\code\Q3\q3_round2_robustness.py
.\.venv\Scripts\python.exe -W error l1\code\Q3\q3_run_raw_curve_challenger.py
.\.venv\Scripts\python.exe -W error l1\code\Q3\q3_raw_curve_challenger_robustness.py
.\.venv\Scripts\python.exe -W error l1\code\Q4\q4_train_only_dry_run.py
```
