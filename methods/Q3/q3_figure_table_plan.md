# Q3 图表与表格计划（开发期）

> **状态**：开发期可用。M3R-k=5 是早期筛查候选；M2-k=100 是开发集内较充分校正候选。Primary 的历史 M3 标签已重标为 M2，M3R 未获 Primary 确认。

## 1. 图形清单

### Type 2：窗口与候选比较图

| ID | 图题 | 比较内容 | 来源 | 开发稿位置 | 状态 | 建议图注 |
|---|---|---|---|---|---|---|
| Q3-F1 | 四类 Q3 候选的窗口误差 | M1–M4 在 k=5/10/20/50/100 的寿命和 SOH 误差 | `results/Q3/experiments/round2_joint/figures/q3_joint_window_comparison.png` | Q3 方法选择 | 存在 | “严格 Train-only 分组验证的候选与窗口比较；不将 Primary 用于重选。” |
| Q3-F2 | RAW 曲线增强筛查候选 | M3（策略＋早期）与 M3R（M3＋RAW 电压）五窗口点估计比较 | `results/Q3/experiments/round3_raw_curve_challenger/figures/q3_raw_curve_challenger.png` | Q3 结果 | 存在 | “经六字段审计的低维电压特征相对 M3 的点估计比较；与 M2 的 bootstrap 结论另见 Q3-T3。” |
| Q3-F3 | 双窗口 Primary 受限确认 | k=5 与 k=100 的历史 M2 观察 | `results/Q3/experiments/primary_confirmation_round1/figures/q3_primary_confirmation.png` | 附录/验证边界 | 存在 | “一次固定 M2 确认的观察结果；Primary 已有探索暴露，不是独立外部验证。” |

### Type 4：附录图

| ID | 图题 | 附录用途 | 来源 | 状态 |
|---|---|---|---|---|
| Q3-A1 | 策略组 bootstrap 与窗口 Pareto | 展示等权误差、区间和支配关系 | `robustness/Q3/figures/q3_window_cell_equal_pareto.png` | 存在 |
| Q3-A2 | SOH 模板与逐电芯曲线误差 | 核验模板失败和误差构成 | `results/Q3/experiments/round2_joint/tables/joint_cell_curve_errors.csv` | 表格存在；图待冻结后生成 |

## 2. 表格清单

| ID | 表题 | 类型 | 来源 | 状态 |
|---|---|---|---|---|
| Q3-T1 | M1–M4 五窗口误差表 | comparison_table | `results/Q3/experiments/round2_joint/tables/joint_window_metrics.csv` | 存在 |
| Q3-T2 | M3R 五窗口误差与 M2 对照 | comparison_table | `results/Q3/experiments/round3_raw_curve_challenger/tables/m3r_raw_curve_window_metrics.csv` | 存在 |
| Q3-T3 | M3R-k=5 相对 M2-k=5 的 bootstrap | sensitivity_table | `robustness/Q3/round3_raw_curve_challenger/metrics/q3_raw_curve_bootstrap_summary.json` | 存在 |
| Q3-T4 | Primary 双窗口受限确认指标 | validation_table | `results/Q3/experiments/primary_confirmation_round1/metrics/q3_primary_metrics.json` | 存在 |

## 3. 风险与冻结条件

- M3R-k=5 的 SOH 改善区间不跨 0，但寿命误差差值区间跨 0；图注必须保留这一限制。
- k=5 与 k=100 服务不同用途，不能用单一图或单一误差宣布其中一个“全面胜出”。
- Type 3 正式论文图须在 Q3 稳定性/结果裁决和 Secondary 压力测试后另行确认。
