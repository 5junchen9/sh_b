# Q3 Decision Log

> Canonical, append-only record of modeler decisions. Downstream narrative must trace to these records.

---

### Q3-D01 | method_choice | 2026-08-02T19:41:51+08:00 | mode: learning

- **options_considered**: `Q3-M1` 早期汇总特征 Ridge / `Q3-M3` 寿命预测 + 单调 SOH 模板
- **evidence**: `methods/Q3/q3_method_candidates.md`；`Q3-M3` 五窗口 SOH RMSE 为 0.0387--0.0417。
- **ai_suggestion**: WITHHELD_IN_LEARNING_MODE_UNTIL_HUMAN_RATIONALE
- **modeler_decision**: `Q3-M3 寿命预测 + 单调 SOH 模板联合主线`（CHOSEN）
- **modeler_rationale**: 建模者原话：“直接 SOH 斜率外推失败，不是能直接说明电池的衰减与与时间相关度很大吗，所以采用联合主线目前数据能验证吗”“先做个联合主线看看”。
- **confidence**: 未声明
- **supersedes**: —

---

### Q3-D02 | hyperparameter | 2026-08-02T22:02:43+08:00 | mode: learning

- **options_considered**: 单一早期窗口 / `k=5` 与 `k=100` 两层输出。
- **evidence**: `robustness/Q3/q3_robustness_report.md`；`robustness/Q3/tables/q3_window_cell_equal_bootstrap_summary.csv`。
- **ai_suggestion**: WITHHELD_IN_LEARNING_MODE_UNTIL_HUMAN_RATIONALE
- **modeler_decision**: `k=5` 为最早筛查窗口；`k=100` 为当前 V2 one-standard-error 规则下的正式预测窗口。
- **modeler_rationale**: 建模者原话：“给出两层结果：k=5：最早筛查窗口，可用于早期风险预警或策略初筛；k=100：当前 V2 one-standard-error 规则下的正式预测窗口，用于较可信的寿命与未来 SOH 结论。”
- **confidence**: 未声明
- **supersedes**: —

---

### Q3-D03 | claim_scope | 2026-08-02 | mode: learning

- **options_considered**: k=5 筛查 + k=100 正式窗口（注明待外部确认）/ 两者均只称开发窗口。
- **evidence**: `results/Q3/experiments/round1/q3_experiment_report_round1.md`；`robustness/Q3/q3_robustness_report.md`；`paper/model_selection_early_warning_and_q4_details.md`。
- **ai_suggestion**: USER_REQUESTED_ADVICE_BEFORE_CONFIRMATION
- **modeler_decision**: `k=5 为最早筛查窗口；k=100 为正式预测窗口，相关结论仍注明待外部确认。`（CHOSEN）
- **modeler_rationale**: 建模者原话：“Q3：k=5 为最早筛查窗口；k=100 为正式预测窗口，相关结论仍注明待外部确认。”
- **confidence**: 未声明；稳定性置信仍待 Gate G4.5。
- **supersedes**: —

---

### Q3-D04 | claim_scope | 2026-08-02T23:26:53+08:00 | mode: learning

- **options_considered**: 继续本轮模型/窗口迭代 / 结束本轮并保留 k=5 与 k=100 的双窗口；Primary 回调窗口/冻结并保留 Secondary 压力测试。
- **evidence**: `results/Q3/experiments/primary_confirmation_round1/q3_primary_confirmation_report.md`；k=5 Primary 寿命 `RMSE_log=0.30305`、k=100 为 `0.39702`；k=100 Primary 电芯等权未来 SOH RMSE `0.03843`、k=5 为 `0.04259`。
- **ai_suggestion**: WITHHELD_IN_LEARNING_MODE_UNTIL_HUMAN_RATIONALE
- **modeler_decision**: `结束本轮迭代，保留 k=5 筛查和 k=100 正式校正的双窗口；冻结窗口、特征和指标，Secondary 留作最终压力测试。`（CHOSEN）
- **modeler_rationale**: 建模者确认：k=5 与 k=100 分别在 Primary 的寿命和未来 SOH 指标上更低，说明两者服务不同用途；Train 验证、bootstrap 与一次冻结 Primary 确认完成后，不能再利用 Primary 重选窗口，否则会造成验证集泄漏。
- **confidence**: 未单独裁决；Q3 的稳定性置信门禁保持 PENDING。
- **supersedes**: —

---

### Q3-D08 | assumption_necessity | 2026-08-03T09:05:00+08:00 | mode: learning

- **options_considered**: 将 Q3-A1/A2/A3 分类为必要或简化；按 Secondary 单次比较事后选择窗口，或只报告已冻结窗口的外部表现。
- **evidence**: `planning/model_assumptions.md`；`methods/Q3/qx_decision_log.md`（Q3-D07）；`methods/Q3/decisions/final-method-explainer_modeler_decision.md`。
- **ai_suggestion**: WITHHELD_IN_LEARNING_MODE; TRANSCRIBES_PRIOR_HUMAN_DECISIONS_ONLY
- **modeler_decision**: Q3-A1 为必要假设，Q3-A2/Q3-A3 为简化假设。M3R-k=5 未获得 Secondary 外部支持；k=100 仅报告冻结前预先指定窗口的外部表现，不据此重选 k=5。
- **modeler_rationale**: 冻结模型角色、窗口、特征、指标和 bootstrap 设置，不再调参。M3R-k=5 仅作为开发期原始曲线增强的探索性 challenger 保留记录；其开发期 SOH 改善未在 Secondary 复现，因此不作为外部支持的早筛模型或寿命预测模型。
- **confidence**: needs_caution
- **supersedes**: Q3-D04（仅更新 Secondary 后的外部主张范围；不改变冻结协议）

---

### Q3-D09 | claim_scope | 2026-08-03T09:18:56.0741029+08:00 | mode: learning

- **options_considered**: A. 保留无泄漏联合预测流程可运行和 M3R 外部未复现优势的完整结论，均标注需谨慎；B. 只保留流程与数据审计，不讨论模型比较。
- **evidence**: `results/Q3/reports/q3_solution_package_for_writer.md`；`results/Q3/reports/frozen_numbers.json`；`methods/Q3/decisions/solution-package-builder_modeler_decision.md`。
- **ai_suggestion**: WITHHELD_IN_LEARNING_MODE_UNTIL_HUMAN_RATIONALE
- **modeler_decision**: 选 A（CHOSEN）。
- **modeler_rationale**: 建模者原话：“Q3选A”。即保留无泄漏联合预测流程可运行与 M3R 外部未复现优势的完整结论，均标注需谨慎；不把模型比较改写为优胜结论。
- **confidence**: needs_caution
- **supersedes**: —
