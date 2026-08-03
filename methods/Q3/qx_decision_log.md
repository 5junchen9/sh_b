# Q3 决策日志

> 此文件为追加式决策记录；下游论文仅转述有来源的人工决定。

---

### Q3-D05 · confidence · 2026-08-03T00:00:00+08:00 · mode: learning

- **options_considered**: high / medium / needs_caution
- **evidence**: `robustness/Q3/round3_raw_curve_challenger/tables/q3_raw_curve_policy_bootstrap.csv` 中 M3R-k5 对 M2-k5 的 SOH RMSE 差值 95% 区间为 [-0.009075, -0.001605]；寿命 RMSE、MAE 差值区间分别为 [-0.091519, 0.021773]、[-0.071340, 0.004273]。
- **ai_suggestion**: 已在学习模式下先由建模者独立作出判断；本条仅转录人工确认。
- **modeler_decision**: needs_caution（CHOSEN）
- **modeler_rationale**: M3R-k5 仅作最早曲线增强筛查候选，SOH 改善有 bootstrap 支持，但寿命改善并不稳定；M2-k100 的结论限于开发期且待 Secondary 确认。
- **confidence**: needs_caution
- **supersedes**: —

### Q3-D07 · result_verdict · 2026-08-03T08:47:56.8242740+08:00 · mode: learning

- **options_considered**: 将 M3R-k=5 升格为外部支持的早筛/寿命模型，或保留为开发期探索性 challenger；将 k=100 或 k=5 据 Secondary 重选为最终窗口，或仅报告冻结窗口的外部表现；输出最优策略，或仅交付候选、风险边界和 pilot 接口。
- **evidence**: `results/Secondary_final_pressure_test/secondary_external_experiment_report.md`、`results/Secondary_final_pressure_test/tables/q3_external_metrics.csv`、`results/Secondary_final_pressure_test/tables/bootstrap_intervals.csv`、`results/Secondary_final_pressure_test/verification.md`。Secondary 的 M3R-k=5 相对 M2-k=5 的 SOH RMSE 差值 bootstrap 区间为 [0.002531, 0.017078]；k=100 未显示优于 M2-k=5；Q4 仅有 8 个既有策略组。
- **ai_suggestion**: 学习模式下不代替建模者裁决；本条仅逐字转录建模者对外部结果的范围约束。
- **modeler_decision**: M3R-k=5 作为开发期原始曲线增强的探索性 challenger 保留记录；其开发期 SOH 改善未在 Secondary 复现，因此不作为外部支持的早筛模型或寿命预测模型。k=100 是冻结前预先指定的较充分校正窗口；本次 Secondary 中未显示其优于 M2-k=5，因此仅报告其外部表现，不声称其更优、也不据此重选 k=5 为最终窗口。Q4 仅交付候选策略集合、风险边界与 pilot 试验接口；由于最终外部观察未支持代理模型升级，且 Secondary 仅含 8 个已有策略组，本文不输出最优新充电策略或可直接执行的推荐。
- **modeler_rationale**: 关闭冻结的 Secondary 一次性压力测试；按上述边界写入最终结果，不重跑、不调参、不重选。
- **confidence**: needs_caution
- **supersedes**: Q3-D06（仅替代其 Secondary 后的外部主张范围；不改变既定的冻结协议和一次性运行约束）

### Q3-D06 · result_verdict · 2026-08-03T00:00:00+08:00 · mode: learning

- **options_considered**: M3R-k5 作为正式寿命模型 / M3R-k5 作为筛查候选；单窗口 / 双窗口；继续调参 / 冻结后一次性 Secondary。
- **evidence**: M2-k100 的开发期指标为 RMSE_log=0.231737、MAE_log=0.170084、SOH RMSE=0.034753；M3R-k5 的 SOH 差值区间不跨 0，而寿命差值区间跨 0。
- **ai_suggestion**: 已在学习模式下先由建模者独立作出判断；本条仅转录人工确认。
- **modeler_decision**: 保留 M3R-k5 为最早筛查候选；保留 M2-k100 为开发期较充分校正候选；冻结后一次性运行 Secondary；Q4 仅交付候选与 pilot 接口。
- **modeler_rationale**: 冻结模型角色、窗口、特征、指标和 bootstrap 设置，不再调参；Secondary 按预注册协议一次性运行，不得因结果回调模型。
- **confidence**: k=5 needs_caution；k=100 limited_development_only_pending_secondary
- **supersedes**: —
