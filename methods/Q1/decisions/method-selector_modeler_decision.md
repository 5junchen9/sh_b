---
schema_version: 1
skill: method-selector
scope: Q1
decision_id: q1_method_choice
decision_point: method_choice
status: DECIDED
decided_by: human
decided_at: 2026-08-03T13:40:00+08:00
ai_suggestion: "[WITHHELD — learning mode; revealed only after the modeler records a rationale.]"
choice: "Q1 采用 M2 策略级聚合为正文主线，M1 电芯级分析作为基础描述；M3仅作跨分区一致性核对。"
rejected_alternatives:
  - method: M1 / M3 not selected as main line
    reason: "M1电芯级分析作为基础描述；M2为正文主线，M3仅作跨分区一致性核对。"
confidence: "中等"
evidence_refs:
  - methods/Q1/q1_method_candidates.md
  - results/Q1/experiments/round1/q1_experiment_report_round1.md
  - robustness/Q1/q1_robustness_report.md
---

## 模型者理由

Q1 采用 M2 策略级聚合为正文主线，M1 电芯级分析作为基础描述；理由：27 个重复策略组和 19 对跨分区重复策略支持策略级对照，但仅作观察性比较；可信度：中等。
