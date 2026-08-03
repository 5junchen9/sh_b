# Q2-B P3 Primary 一次受限确认

> 状态：**observed_not_adjudicated**。本报告只给出冻结模型的确认观察，不自动决定通过、换模型或写入最终 Q4。

- 训练：41 枚 Train 电芯；确认：43 枚 Primary 电芯。
- 冻结模型：P3 低自由度加性 GAM，`n_knots=4`、`alpha=0.03`。
- 特征：`C1`、`Q1_percent`、`C2`；目标：`ln(cycle_life_table9)`。
- 禁止：不重调参数、不比较 C1、不读取早期循环特征、不用 Primary 结果反向修改模型。

| 指标 | Primary 结果 |
|---|---:|
| RMSE_log（ln 尺度） | 0.289268 |
| MAE_log（ln 尺度） | 0.225722 |
| RMSE_cycle | 179.39 |
| MAE_cycle | 146.79 |
| 过预测比例 | 39.53% |
| 平均正向 ln 误差 | 0.120652 |
| 平均正向 cycle 误差 | 63.31 |

图 `figures/q2b_primary_observed_vs_predicted.png` 为中文观察—预测图；逐电芯结果见 `tables/q2b_primary_predictions.csv`。

限制：Primary 已有探索暴露，因此只能称受限确认；Secondary 才是最终压力测试集。本次没有预注册自动通过阈值，结果置信与论文主张范围仍由建模者在 Gate G4.5 记录。
