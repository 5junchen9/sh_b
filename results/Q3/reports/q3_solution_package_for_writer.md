# Q3 论文写作材料包

> **状态**：已完成人工签核；数字冻结见 `frozen_numbers.json`。  
> **来源**：`methods/Q3/q3_final_method_explanation.md`、`results/Q3/reports/q3_final_result_analysis.md`、`robustness/Q3/q3_robustness_report.md`、Q3 决策日志。

## 0. 快速引用

- **问题目标**：只用截止循环 k 及以前信息预测寿命，并生成后续 SOH 校正轨迹。
- **冻结流程**：早期特征 Ridge 给出寿命时间尺度，训练折非增 SOH 模板给出退化形状。<!-- from Q3-D01 -->
- **窗口边界**：k=5 为最早筛查记录，k=100 为冻结前预先指定的较充分校正窗口；不根据 Secondary 重选。<!-- from Q3-D02, Q3-D07 -->
- **核心外部事实**：Secondary 中 M3R-k=5 的未来 SOH RMSE 为 0.072023，高于 M2-k=5 的 0.062007；其差值区间 `[0.002531,0.017078]`。
- **置信边界**：needs_caution。<!-- from Q3-D05, Q3-D07 -->
- **写作篇幅**：约 2–2.5 页（含 2 图、2 表）。

## 1. 可直接写入的建模内容

### 模型构造

在窗口 `k` 前，提取容量、内阻、温度和充电时间的均值、斜率与变化量，拟合

`\hat z_{ik}=β_{0k}+β_k^T h_{ik}`。

再在每个训练折上按照 `u=n/L_i` 对齐训练电芯的 `SOH_nom=QDischarge/1.1`，通过非增 isotonic 回归获得 `G_f(u)`。验证电芯仅以 `\hat L_{ik}` 和截止点实测 SOH 进入预测，真实终止寿命不参与模板拟合。

### 外部验证的意义

这套流程对 40 枚 Secondary 电芯均可评价、模板失败为 0，说明字段—循环掩码下的计算链条可运行；但“可运行”不等于“模型优胜”。M3R-k=5 的开发期 SOH 改善在 Secondary 未复现，且 k=100 没有显示优于比较器，因而论文必须保留这个不确定性边界。

## 2. 图表与表格分配

| 文件 | 论文位置 | 支持的主张 | 建议图题/表题 | 状态 |
|---|---|---|---|---|
| `results/Q3/experiments/round2_joint/figures/q3_joint_window_comparison.png` | 模型比较/附录 | 开发期内不同窗口和候选的误差权衡 | 图：不同早期观察窗口下的寿命与 SOH 误差 | 可用，但图注须注明开发期 |
| `results/Secondary_final_pressure_test/figures/secondary_final_observed_predicted.png` | 外部压力测试 | 冻结模型的实测—预测偏离及外部差异 | 图：Secondary 上冻结寿命与 SOH 预测的实测—预测比较 | 主图候选 |
| `results/Secondary_final_pressure_test/tables/q3_external_metrics.csv` | 外部结果 | 三个冻结模型/窗口的误差与 40 枚可评价曲线 | 表：Secondary 外部压力测试的 Q3 误差 | 主表候选 |
| `results/Secondary_final_pressure_test/tables/bootstrap_intervals.csv` | 稳健性 | M3R-k=5 相对 M2-k=5 的差异不支持外部升级 | 表：关键模型差值的策略组 bootstrap 区间 | 主表或附录 |
| `robustness/Q3/figures/q3_raw_curve_bootstrap.png` | 附录 | 开发期 RAW challenger 的不确定性 | 图：开发期原始曲线 challenger 的策略组 bootstrap | 仅作开发期补充 |

## 3. 主张清单

### 可保留

| 主张 | 证据 | 当前状态 |
|---|---|---|
| 截止窗口严格不使用未来循环信息，联合流程可输出寿命与未来 SOH | 方法说明、40/40 可评价、零模板失败 | 保留；needs_caution |
| 原始曲线增强的开发期 SOH 改善未在 Secondary 复现 | Secondary SOH 差值区间完全为正 | 保留完整的负向外部结果；needs_caution |
| k=100 为预先冻结的较充分校正窗口，外部结果仅作报告 | Q3-D02、Q3-D07 | 保留；needs_caution |

### 必须限定

| 候选过度主张 | 原因 | 更安全的表达 |
|---|---|---|
| M3R-k=5 已经是外部验证的早筛模型 | Secondary 外部结果更差 | 开发期探索性 challenger，未获外部支持 |
| k=100 是经 Secondary 证明的最佳窗口 | 未显示优于 M2-k=5；不允许事后重选 | 预先指定窗口的外部表现 |
| 可从观察关联推断充电机制因果 | 当前为预测设计 | 预测关系与可信域边界 |

## 4. 建议写作顺序

1. 用时间线说明“截至 k 的信息边界”。
2. 写出寿命 Ridge 与 SOH 模板的组合公式，以及按电芯等权的轨迹指标。
3. 用开发期窗口图解释 k=5/k=100 的原始角色。
4. 用 Secondary 主图和 bootstrap 表报告不复现结果，不删除负向证据。
5. 在结论中把 Q3 传给 Q4 的内容限定为真实 pilot 的确认步骤，而非窗口优胜结论。

## 5. 冻结前检查

- [x] 最终方法说明存在。
- [x] 最终结果分析存在。
- [x] 已列出的图表均在磁盘上。
- [x] 主张范围及置信等级已签核（Q3 选 A）。
- [x] `frozen_numbers.json` 已生成。
