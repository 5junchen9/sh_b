schema_version: 1
skill: robustness-checker
scope: Q2
decision_id: q2_stability_verdict
decision_point: confidence
status: DECIDED
decided_by: human
decided_at: 2026-08-02T23:26:53+08:00
ai_suggestion: WITHHELD_IN_LEARNING_MODE_UNTIL_HUMAN_RATIONALE
evidence_refs:
  - robustness/Q2/q2_robustness_report.md
  - robustness/Q2/metrics/q2_bootstrap_summary.json
  - robustness/Q2/tables/q2_policy_block_bootstrap.csv
  - robustness/Q2/tables/q2_interaction_sign_stability.csv
choice: limited_medium
rejected_alternatives:
  - alternative: high
    reason: M2 的 MAE 点估计虽改善 8.91%，但策略组 bootstrap 差值区间跨 0，不足以支持高可信或显著优于 M1。
  - alternative: medium
    reason: 建模者选择此项；其适用范围限定为 M1 正文、M2 敏感性和 P3 的 Q4 provisional 用途。
  - alternative: needs_caution
    reason: 不将 P3 升格为最终最优或正式寿命排序模型的前提下，现有 Train 验证、bootstrap 和一次冻结 Primary 确认足以保留限定范围内的中等可信。

## Modeler's rationale

建模者确认“限定范围内中等可信”：M2 的 MAE 点估计改善 8.91%，但差值区间跨 0，因此保留 M1 正文、M2 敏感性；P3 仅作 Q4 provisional，不能说已验证为最优。
