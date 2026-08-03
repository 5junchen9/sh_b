# Q2 论文写作材料包

> **状态**：已完成人工签核；数字冻结见 `frozen_numbers.json`。  
> **来源**：`methods/Q2/q2_final_method_explanation.md`、`results/Q2/reports/q2_final_result_analysis.md`、`robustness/Q2/q2_robustness_report.md`、Q2 决策日志。

## 0. 快速引用

- **问题目标**：分析两段式充电参数与循环寿命的条件关联，并提供受限的设计前候选筛查接口。
- **正文模型**：M1 主效应 Ridge；M2 二阶交互 Ridge 只作敏感性分析。<!-- from Q2-D02, Q2-D05 -->
- **核心结果**：Train 中 M2 的 MAE_log 点估计较 M1 改善 8.91%，但 `ΔMAE_log` 95% 区间 `[-0.07245,0.02620]` 跨 0；故正文采用 M1。
- **置信边界**：`limited_medium`，且不延伸到因果、最终最优策略或独立泛化。<!-- from Q2-D06 -->
- **写作篇幅**：约 1.5–2 页（含 1 图、2 表）。

## 1. 可直接写入的建模内容

### 模型构造

令 `x_i=(C_{1i},q_i,C_{2i})`，`z_i=ln(L_i)`。对折内标准化变量，M1 拟合

`\hat z_i=β_0+β_1\tilde C_{1i}+β_2\tilde q_i+β_3\tilde C_{2i}`，

以 `Σ(z_i-\hat z_i)^2+α||β||_2^2` 最小化。M2 在此基础上加入三项二次项和三项两两交互，并以相同分组交叉验证比较；所有系数均只解释为条件关联。

### 结果分析

M1 的 Train OOF `RMSE_log/MAE_log=0.37169/0.27557`，M2 为 `0.36854/0.25102`。M2 的典型误差点估计改善存在，但区间不排除无改善；因此用 M1 呈现保守主关系，用 M2 展示阶段倍率之间可能的联合作用和其不确定性。

### Q4 的传递边界

P3 加性 GAM 在开发期只产生 `Q2_provisional` 候选。最终 Secondary 中 P3 的 `RMSE_log/MAE_log=0.677812/0.630770`，未获升级；它不能承担最终寿命排序或新策略推荐。

## 2. 图表与表格分配

| 文件 | 论文位置 | 支持的主张 | 建议图题/表题 | 状态 |
|---|---|---|---|---|
| `results/Q2/experiments/round1/figures/m1_m2_oof_comparison.png` | 结果分析 | M1/M2 的折外点估计接近，不能仅凭点误差升级 M2 | 图：主效应与交互 Ridge 的分组折外预测比较 | 可用 |
| `robustness/Q2/figures/q2_policy_block_bootstrap.png` | 稳健性/附录 | M2−M1 误差差值区间跨 0 | 图：策略组块 bootstrap 下的交互模型误差差异 | 可用 |
| `results/Q2/experiments/m1_explainability_round1/tables/q2_m1_standardized_coefficients.csv` | 结果分析 | M1 的标准化关联方向和相对强度 | 表：主效应 Ridge 的标准化系数 | 需从表中挑 3 项排版 |
| `robustness/Q2/tables/q2_interaction_sign_stability.csv` | 敏感性分析 | 交互符号的稳定性与不稳定项 | 表：主要 SOC 阶段交互项的重抽样符号稳定率 | 可用 |

不要将 P3 的 Primary 或 Secondary 散点图作为“模型成功”主图；它们只用于局限性或 Q4 接口说明。

## 3. 主张清单

### 可保留

| 主张 | 证据 | 当前状态 |
|---|---|---|
| 在本数据支持域内，策略参数与寿命存在可预测的条件关联 | M1 分组 OOF、系数表 | 保留；限定范围内中等可信 |
| M2 提供阶段倍率交互的探索性信号，而非稳定优胜 | M2 8.91% 点估计改善与跨 0 的 bootstrap 区间 | 保留为敏感性；限定范围内中等可信 |
| 设计前候选须经真实 pilot 和 Q3 评价 | P3 外部误差、Q4 协议 | 保留为 pilot 接口；provisional only |

### 必须限定

| 候选过度主张 | 原因 | 更安全的表达 |
|---|---|---|
| M2 显著优于 M1 | `ΔMAE_log` 区间跨 0 | M2 仅显示探索性改善信号 |
| 交互系数是因果机制 | 观察性设计且存在未观测混杂 | 条件关联/敏感性结果 |
| P3 给出最优策略 | Secondary 未支持升级 | P3 只生成 pilot 候选 |

## 4. 建议写作顺序

1. 先交代分区、按策略组验证和 `ln(L)` 口径。
2. 给出 M1 公式及其可解释关联。
3. 用 M2 的对照表解释“为何保留敏感性而不升级正文”。
4. 用 bootstrap 图收束不确定性与因果边界。
5. 最后衔接 Q4：P3 只作候选生成，真实试验为必要闭环。

## 5. 冻结前检查

- [x] 最终方法说明存在。
- [x] 最终结果分析存在。
- [x] 已列出的图表均在磁盘上。
- [x] 主张范围及置信等级已签核（Q2 选 A）。
- [x] `frozen_numbers.json` 已生成。
