# Q2 M1 因素排序与条件关联补充报告

> **定位：** 仅补充冻结 Q2-A M1 主效应 Ridge 的解释证据；所有结果只用 Train，不能解释为因果贡献，也不会改变 M1 主线、M2 敏感性或 P3 provisional 的既有角色。

## 1. 方法

- 样本：41 枚 Train 电芯、40 个 `policy_table9` 组；目标为 `ln(cycle_life_table9)`。
- 完整 M1 与删一变量模型均使用相同的外层策略分组折和内层 alpha 选择；完整 M1 的 OOF 预测与既有 Round 1 表逐元素一致。
- 系数是在 Train 全量、内层选定 `alpha=3` 后得到的标准化 Ridge 系数；系数区间来自 2,000 次策略组块重抽样、固定 alpha 重拟合。
- 变量重要性以 `ΔMAE_log=MAE_删除后−MAE_完整` 表示。正值说明删去该变量后典型折外误差上升；它仍只是相关结构下的条件预测信息，不能称为物理因果贡献。

## 2. 删一变量结果

| 模型 | 删除变量 | RMSE_log | MAE_log | ΔMAE_log |
|---|---|---:|---:|---:|
| full_M1 | — | 0.37169 | 0.27557 | +0.00000 |
| drop_C1 | C1 | 0.35659 | 0.25995 | -0.01561 |
| drop_Q1_percent | Q1_percent | 0.39233 | 0.29455 | +0.01898 |
| drop_C2 | C2 | 0.38566 | 0.29801 | +0.02244 |

## 3. 使用边界

1. 三个策略变量受两段式协议约束，彼此并非充分独立；删一变量差值不等于独立贡献百分比。
2. 任何 bootstrap 区间跨 0 的删一差值只能称“证据不足以稳定排序”，不应在论文中强行排出唯一第一因素。
3. 系数、删一误差与 M2 交互均在 `ln(L)` 尺度计算；反变换为 cycle 时只使用 `exp`。

## 4. 产物

- `tables/q2_m1_standardized_coefficients.csv`
- `tables/q2_m1_feature_ablation_summary.csv`
- `tables/q2_m1_feature_ablation_bootstrap.csv`
- `figures/q2_m1_factor_explainability.png/svg`
