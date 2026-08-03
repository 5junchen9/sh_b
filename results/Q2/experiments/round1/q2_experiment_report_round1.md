# Q2 实验报告——Round 1（Train-only）

> **结果裁决**：`[PENDING-MODELER]`。本报告只整理计算证据；最终方法标签、轮次决定与置信等级由 `methods/Q2/decisions/result-report-generator_modeler_decision.md` 在 Gate G4.5 记录。  
> **既有人工作用决定**：`Q2-D02` 已确定 Q2-A 以 M1 为正文保守主线、M2 为交互敏感性；`Q2-D03` 已冻结 P3 后进行一次 Primary 受限确认。两项决定均不等于 Q2-B 最终结果裁决。

## 1. 执行摘要

- Train-only 比较：41 枚 Train 电芯、40 个 `policy_table9` 策略组；Primary、Secondary 未参与拟合、调参或 bootstrap。
- 目标：`ln(cycle_life_table9)`；历史字段 `RMSE_log/MAE_log` 均为自然对数尺度。
- Q2-A：M1 主效应 Ridge 与 M2 二阶交互 Ridge，5×4 策略分组嵌套验证。
- Q2-B：P1 Ridge、P2 ElasticNet、P3 低自由度加性样条 GAM 与 C1 严格受限提升树；2,000 次策略组块 bootstrap。`Q2-D04` 已限定 P3 仅用于 Q4 provisional 候选。
- Primary 确认：按冻结的 P3/特征/参数另行对 43 枚 `Prim. Test` 电芯一次评分，不参与任何选择；见 `../q2b_primary_confirmation_round1/run_summary.json`。

## 2. 各方法结果

### 2.1 Q2-A M1 主效应 Ridge `[PENDING-MODELER]`

- 指标：`RMSE_log=0.37169`，`MAE_log=0.27557`，`RMSE_cycle=329.91`，`MAE_cycle=198.72`。
- 图：`figures/m1_m2_oof_comparison.png` 中灰色散点为 M1；相对 45° 线的离散显示其只能作为低复杂度参考。
- 表：`tables/m1_oof_predictions.csv` 给出 41 条折外预测及 outer fold；`m1_folds.csv` 给出每折 alpha 和内层误差。
- 既有人工作用：正文保守主线（`Q2-D02`）；最终结果置信仍 `[PENDING-MODELER]`。

### 2.2 Q2-A M2 二阶交互 Ridge `[PENDING-MODELER]`

- 指标：`RMSE_log=0.36854`，`MAE_log=0.25102`，相对 M1 的 MAE 点估计改善 8.91%。
- 稳健性：`ΔMAE_log` 95% 区间 `[-0.07245,0.02620]` 跨 0；自动准入三门槛未同时通过。
- 图：同一 OOF 比较图中蓝色散点为 M2；点估计略好，但策略组重抽样下不能排除无改善。
- 表：`m2_oof_predictions.csv` 与 `m2_folds.csv` 保存配对折外结果和 alpha。
- 既有人工作用：不同 SOC 阶段倍率交互的探索性关联/敏感性（`Q2-D02`）；不直接用于 Q4。

### 2.3 Q2-B 设计前代理候选 `[PENDING-MODELER]`

| 方法 | RMSE_log | MAE_log | 过预测比例 | 规则状态 |
|---|---:|---:|---:|---|
| P1 主效应 Ridge | 0.36760 | 0.26676 | 56.10% | 线性基线 |
| P2 ElasticNet | 0.37705 | 0.27267 | 51.22% | 未进入双指标一标准误集合 |
| P3 加性 GAM | 0.34892 | 0.23383 | 48.78% | 预注册规则选出的条件性代理 |
| C1 受限提升树 | 0.33168 | 0.22735 | 48.78% | challenger；替代门槛未通过 |

- `q2b_proxy_error_comparison.png/svg`：C1 点误差最低，P3 次之，但误差条显示成对差值不确定性不能忽略。
- `q2b_proxy_overprediction_risk.png/svg`：P3 与 C1 点过预测比例相同；C1 相对 P3 的风险差上界仍为 0.1951。
- `q2b_model_metrics.csv`：逐模型点指标和区间；`q2b_model_comparison_and_selection.csv`：一标准误、风险及 challenger 门槛的机器判定。
- `q2b_oof_predictions.csv`：四模型配对 OOF 预测；`q2b_nested_cv_selected_params.csv`：各外折调参结果；`q2b_policy_block_bootstrap.csv`：2,000 次成对策略组块结果。

### 2.4 Q2-B P3 Primary 一次受限确认 `[PENDING-MODELER]`

- 冻结：P3 加性 GAM，`n_knots=4`、`alpha=0.03`；只用 Train 41 枚电芯拟合，以 `C1/Q1_percent/C2` 预测 Primary 43 枚电芯。
- Primary 观察：`RMSE_log=0.28927`，`MAE_log=0.22572`，`RMSE_cycle=179.39`，`MAE_cycle=146.79`，过预测比例 `39.53%`。
- 边界：没有重调参数、比较 C1 或读取早期循环特征；确认协议未设置事后自动通过阈值，因此此处是固定模型的受限确认观察，不是最终泛化判定。
- 证据：`../q2b_primary_confirmation_round1/q2b_primary_confirmation_report.md`、逐电芯表及中文观察—预测图。

## 3. 跨方法比较

| 评价问题 | 证据最强的当前结果 | 必须保留的限制 |
|---|---|---|
| Q2-A 正文解释 | M1 最简单且由 `Q2-D02` 指定为保守主线 | 系数是条件统计关联，不是因果贡献 |
| SOC 交互探索 | M2 三个主要交互符号主导率均≥80% | `ΔMAE_log` 区间跨 0；`C1×C2` 系数区间也跨 0 |
| Q4 设计前代理 | P3 被预注册简单性/风险规则选出，并由 `Q2-D04` 限定为 provisional 候选代理 | P3 相对 P1 的差值区间跨 0，不能称“显著优于”、最终最优或正式寿命排序 |
| P3 的受限确认 | Primary 上冻结模型的 `0.28927/0.22572` 观察结果 | Primary 已有探索暴露且无自动通过阈值；不能据此换模型或写最终泛化 |
| 非线性 challenger | C1 点误差最低 | 相对 P3 的 `ΔRMSE/ΔMAE` 区间跨 0，不能替代 |

## 4. 总体评估

- **AI 建议**：学习模式下暂不展示，避免在人工理由前锚定。
- **轮次决定**：`[PENDING-MODELER]`。
- 当前可确定的计算事实是：M2 未通过正式解释模型的自动准入门槛；P3 已完成一次冻结的 Primary 受限确认，但结果置信和论文主张仍待人工裁决。

## 5. 可用于论文的材料

- 可用：Q2-A 的 M1/M2 配对 OOF 指标；Q2 稳健性区间；Q2-B 四模型比较表、两张中文诊断图及 P3 的 Primary 受限确认表/图。
- 需限定：M2 交互只能称关联/敏感性；P3 只能称可用于 Q4 provisional 候选的冻结代理。
- 尚不支持：跨批次泛化、正式 Q4 寿命下界、任何“最优充电策略”结论。

## 6. 运行核验清单

1. ✅ Q2-A 与 Q2-B 均只使用 Train。
2. ✅ 所有外层/内层验证按 `policy_table9` 分组，预处理位于折内。
3. ✅ Q2-A 两张 OOF 表均为 41 行，outer fold 完整且配对一致。
4. ✅ Q2-A 脚本、输入哈希和运行摘要全部匹配。
5. ✅ Q2-B 保存四模型 OOF、调参、2,000 次 bootstrap、比较表、中文 PNG/SVG、日志和脚本哈希；P0 最终重建后已追溯重跑，当前 P0/脚本哈希匹配且目标显式记录为 `ln(cycle_life_table9)`。
6. ✅ M2 自动准入三项门槛按用户给定规则逐项计算，没有按有利指标改口径。
7. ✅ P3/C1 的差值区间与机器表、报告和论文细节文档一致。
8. ✅ Q2-A/Q2-B 比较阶段未读取 Primary/Secondary；Primary 仅由独立冻结脚本一次评分，未参与模型选择，Secondary 未读取。

## 7. 下一步

由建模者填写 Q2 结果裁决与稳定性置信等级；在此之前不生成最终结果分析或正式 Q4 推荐。
