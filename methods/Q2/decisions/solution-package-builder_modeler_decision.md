schema_version: 1
skill: solution-package-builder
scope: Q2
decision_id: q2_package_signoff
decision_point: claim_scope
status: DECIDED
decided_by: human
decided_at: 2026-08-03T09:18:56.0741029+08:00
captured_in_mode: learning
ai_suggestion: WITHHELD_IN_LEARNING_MODE_UNTIL_HUMAN_RATIONALE
evidence_refs:
  - results/Q2/reports/q2_solution_package_for_writer.md
  - results/Q2/reports/q2_final_result_analysis.md
  - robustness/Q2/q2_robustness_report.md
  - methods/Q2/q2_decision_log.md
choice:
  - claim: M1 主效应关联的正文范围
    approve: keep
    confidence: limited_medium
  - claim: M2 的交互敏感性范围
    approve: keep_as_sensitivity_only
    confidence: limited_medium
  - claim: P3/Q4 的候选接口范围
    approve: keep_as_pilot_candidate_interface_only
    confidence: limited_medium_provisional_only
rejected_alternatives:
  - alternative: "进一步弱化为只报告描述性规律（选项 B）"
    reason: "建模者选择选项 A；保留 M1 的限定范围条件关联、M2 的敏感性和 P3 的 pilot 候选接口。"

## Modeler's rationale

建模者原话：“Q2选A”。即保留 M1 的“限定范围内条件关联”为正文，M2 仅作敏感性，P3 仅作 pilot 候选接口；不扩大为因果、最优策略或正式寿命排序结论。
