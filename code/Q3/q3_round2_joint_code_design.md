# Q3 Round 2 联合模型：代码设计

## 目的与范围

本轮纠正 `round1` 仅使用早期运行特征、却被误称为“联合模型”的口径偏差。Round 2 仅读取 P0 处理后的 `cell_labels.csv`、五套 `early_features_k*.csv` 和 `cycle_model_view.csv`；**只使用 Train**。不读取 Primary 或 Secondary，也不覆盖 Round 1 的历史输出。

目标是在五个截止窗口 `k∈{5,10,20,50,100}` 上，以相同的策略分组外层折，比较设计策略、早期运行信息及其严格交叉拟合残差校正对 `ln(L)` 和未来 `SOH_nom` 的预测价值。

## 模型与数据流

| ID | 角色 | 输入 | 对数寿命预测 |
|---|---|---|---|
| M1 | 策略基线 | `C1,Q1_percent,C2` | 分组嵌套调参的 Ridge |
| M2 | 运行后基线 | 12 个已冻结早期特征 | 分组嵌套调参的 Ridge |
| M3 | 直接联合候选 | 策略参数 + 12 个早期特征 | 分组嵌套调参的 Ridge |
| M4 | 残差校正候选 | 冻结 P3-GAM 策略先验 + 12 个早期特征 | 每个外层折内，P3 在外层训练集内交叉拟合先验，Ridge 拟合残差；测试预测为先验加残差 |

所有模型在每个外层策略组折中独立完成：填补、标准化、正则化选择；M4 的先验绝不复用全 Train OOF。每个测试电芯的 SOH 模板只由同一外层训练折的真实寿命和曲线拟合，再以该电芯截止点的实际 `SOH_nom(k)` 锚定，预测其后续轨迹。

## 目录与产物

```text
results/Q3/experiments/round2_joint/
├── tables/
│   ├── joint_window_metrics.csv
│   ├── joint_oof_life_predictions.csv
│   ├── joint_cell_curve_errors.csv
│   ├── joint_oof_soh120_predictions.csv
│   └── joint_tuning.csv
├── figures/
│   ├── q3_joint_window_comparison.png
│   └── q3_joint_window_comparison.svg
├── metrics/
│   └── q3_joint_metrics.json
├── logs/
│   └── run.log
└── run_summary.json
```

`joint_window_metrics.csv` 的正式 SOH 指标为“先逐电芯计算 MSE、再等权平均开方”的 `cell_equal_soh_rmse`；合并全部曲线点的误差只作诊断。寿命的主指标为 `RMSE_log`，同时保留 `MAE_log`、循环尺度误差和过预测比例。

## 可复现与检查

- 实现：Python，`numpy/pandas/scikit-learn/matplotlib`；固定种子 20260802。
- 外层：最多 5 折 `GroupKFold(policy_table9)`；内层：最多 4 折同样分组。
- P3-GAM 固定为 Q2 已冻结的二次 B 样条（4 个结点、二次）+ `Ridge(alpha=0.03)`；此处不因 Q3 表现调节其参数。
- 脚本在保存前检查：P0 已通过、输入字段齐全、每个 Train 电芯均有一个外层折、测试组不与该折训练组重叠。
- Round 2 是候选比较，不自动锁定模型、窗口或 Q4 正式推荐；随后必须进行稳健性审查和受限确认协议更新。

## 运行

```powershell
.\.venv\Scripts\python.exe l1\code\Q3\q3_run_joint_comparison.py
```

下一环节：`python-code-reviewer`，然后才可由稳健性检验与结果报告使用本轮产物。
