# Q2 Decision Log

> Canonical, append-only record of modeler decisions. Downstream narrative must trace to these records.

---

### Q2-D01 | method_choice | 2026-08-02T19:41:51+08:00 | mode: learning

- **options_considered**: `Q2-M1` 主效应 Ridge / `Q2-M2` 二阶交互 Ridge
- **evidence**: `methods/Q2/q2_method_candidates.md`；PoC 的 `RMSE_log` 分别为 0.3842 与 0.3620。
- **ai_suggestion**: WITHHELD_IN_LEARNING_MODE_UNTIL_HUMAN_RATIONALE
- **modeler_decision**: `Q2-M2 二阶交互 Ridge`（CHOSEN）
- **modeler_rationale**: 建模者原话：“二阶交互 Ridge是不是更贴近我们的建模需求”“二阶交互 Ridge”。
- **confidence**: 未声明
- **supersedes**: —

---

### Q2-D02 | method_choice | 2026-08-02T22:02:43+08:00 | mode: learning

- **options_considered**: `Q2-A M1 正文主线 + M2 敏感性` / `Q2-A M2 正文主线`；Q4 使用 Q2-A / 另做 Q2-B。
- **evidence**: `robustness/Q2/q2_robustness_report.md`；`results/Q2/experiments/round1/metrics/comparison_metrics.json`；`results/Q2/experiments/q2b_proxy_round1/tables/q2b_model_comparison_and_selection.csv`。
- **ai_suggestion**: WITHHELD_IN_LEARNING_MODE_UNTIL_HUMAN_RATIONALE
- **modeler_decision**: `Q2-A 以 M1 主效应 Ridge 作为正文保守主线；M2 仅作交互探索/敏感性；Q4 改走 Q2-B 代理比较。`（CHOSEN）
- **modeler_rationale**: 建模者原话：“Q2 正文主线：以 M1 主效应 Ridge 作为保守基线；M2：保留为‘不同 SOC 阶段倍率交互的探索性关联/敏感性分析’；Q4：不要使用这两个当前 PoC 模型直接优化，而是进入 Q2-B 的 Train-only 代理模型比较……”以及“相同可信域、同样的分组验证和 bootstrap 下，选择误差不劣、过预测风险不更高、且最简单的模型。”
- **confidence**: 未声明
- **supersedes**: Q2-D01

---

### Q2-D03 | method_choice | 2026-08-02 | mode: learning

- **options_considered**: 冻结 P3、特征和评价规则后进行一次 Primary 受限确认 / 继续仅在 Train 内迭代并推迟确认。
- **evidence**: `results/Q2/experiments/q2b_proxy_round1/tables/q2b_model_comparison_and_selection.csv`；`robustness/Q2/q2_robustness_report.md`；`paper/data_processing_and_split_details.md`。
- **ai_suggestion**: USER_REQUESTED_ADVICE_BEFORE_CONFIRMATION
- **modeler_decision**: `冻结 P3、特征和评价规则后，直接做一次受限的 Primary 确认。`（CHOSEN）
- **modeler_rationale**: 建模者原话：“不推迟外部验证：冻结 P3、特征和评价规则后，直接做一次受限的 Primary 确认。”
- **confidence**: 未声明；Q2 的结果与稳定性置信等级仍待 Gate G4.5。
- **supersedes**: —

---

### Q2-D04 | claim_scope | 2026-08-02 | mode: learning

- **options_considered**: P3 作为 Q4 provisional 候选的冻结代理 / P3 仅保留为内部观察且不进入 Q4 叙述。
- **evidence**: `results/Q2/experiments/q2b_proxy_round1/q2b_proxy_comparison_report.md`；`results/Q2/experiments/q2b_primary_confirmation_round1/q2b_primary_confirmation_report.md`；`robustness/Q2/q2_robustness_report.md`。
- **ai_suggestion**: USER_REQUESTED_ADVICE_BEFORE_CONFIRMATION
- **modeler_decision**: `P3 为可用于 Q4 provisional 候选的冻结代理；不作为最终最优或正式寿命排序模型。`（CHOSEN）
- **modeler_rationale**: 建模者原话：“Q2-B：P3 为可用于 Q4 provisional 候选的冻结代理；不作为最终最优或正式寿命排序模型。”
- **confidence**: 未声明；稳定性置信仍待 Gate G4.5。
- **supersedes**: —

---

### Q2-D05 | result_verdict | 2026-08-02T23:26:53+08:00 | mode: learning

- **options_considered**: M1 正文 / M2 正文；P3 provisional / P3 最终排序；继续调参 / 冻结当前路线。
- **evidence**: `results/Q2/experiments/round1/q2_experiment_report_round1.md`；`robustness/Q2/q2_robustness_report.md`；`results/Q2/experiments/q2b_primary_confirmation_round1/q2b_primary_confirmation_report.md`。
- **ai_suggestion**: WITHHELD_IN_LEARNING_MODE_UNTIL_HUMAN_RATIONALE
- **modeler_decision**: `M1 正文、M2 敏感性；P3 仅作 Q4 provisional；结束本轮并冻结当前 Q2 路线。`（CHOSEN）
- **modeler_rationale**: 建模者确认：M2 的 MAE 点估计改善 8.91%，但差值区间跨 0；因此不将其升格为正文主模型。P3 不称已验证最优；Train 验证、bootstrap 与一次冻结 Primary 确认完成后不再用 Primary 回调模型。
- **confidence**: limited_medium
- **supersedes**: —

---

### Q2-D06 | confidence | 2026-08-02T23:26:53+08:00 | mode: learning

- **options_considered**: high / limited medium / needs caution
- **evidence**: `robustness/Q2/q2_robustness_report.md`；M2 `MAE_log` 点估计改善 8.91%，`ΔMAE_log` 95% 区间跨 0；P3 Primary 受限确认报告。
- **ai_suggestion**: WITHHELD_IN_LEARNING_MODE_UNTIL_HUMAN_RATIONALE
- **modeler_decision**: `限定范围内中等可信。`（CHOSEN）
- **modeler_rationale**: 建模者只将该置信度赋予 M1 正文、M2 敏感性和 P3 provisional 范围，不延伸到最终最优策略或独立外部泛化。
- **confidence**: limited_medium
- **supersedes**: —

---

### Q2-D07 | assumption_necessity | 2026-08-03T09:05:00+08:00 | mode: learning

- **options_considered**: 将 Q2-A1/A2/A3 作为必要前提或简化近似；以 M2 三项联合门槛约束正式解释模型，或按单一有利指标升级。
- **evidence**: `planning/model_assumptions.md`；`robustness/Q2/q2_robustness_report.md`；`methods/Q2/decisions/final-method-explainer_modeler_decision.md`。
- **ai_suggestion**: WITHHELD_IN_LEARNING_MODE; TRANSCRIBES_PRIOR_HUMAN_DECISIONS_ONLY
- **modeler_decision**: Q2-A1、Q2-A2、Q2-A3 均为简化假设；M2 只有同时满足 `ΔMAE_log` 95% 区间上界小于 0、相对改善不少于 5%、主要交互项符号稳定率不少于 80% 时，才可作为正式解释模型；否则 M1 为正文主模型、M2 仅作敏感性。
- **modeler_rationale**: Q2 正文主线采用 M1 主效应 Ridge；M2 保留为不同 SOC 阶段倍率交互的探索性关联/敏感性分析。在相同可信域、同样的分组验证和 bootstrap 下，选择误差不劣、过预测风险不更高、且最简单的模型。
- **confidence**: limited_medium
- **supersedes**: —

---

### Q2-D08 | claim_scope | 2026-08-03T09:18:56.0741029+08:00 | mode: learning

- **options_considered**: A. 保留 M1 的限定范围条件关联为正文、M2 为敏感性、P3 为 pilot 候选接口；B. 进一步弱化为只报告描述性规律。
- **evidence**: `results/Q2/reports/q2_solution_package_for_writer.md`；`results/Q2/reports/frozen_numbers.json`；`methods/Q2/decisions/solution-package-builder_modeler_decision.md`。
- **ai_suggestion**: WITHHELD_IN_LEARNING_MODE_UNTIL_HUMAN_RATIONALE
- **modeler_decision**: 选 A（CHOSEN）。
- **modeler_rationale**: 建模者原话：“Q2选A”。即保留 M1 的限定范围条件关联为正文，M2 仅作敏感性，P3 仅作 pilot 候选接口；不扩大为因果、最优策略或正式寿命排序结论。
- **confidence**: limited_medium；P3 为 limited_medium_provisional_only
- **supersedes**: —
