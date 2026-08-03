---
schema_version: 1
skill: method-selector
scope: Q4
decision_id: q4_method_choice
decision_point: method_choice
status: DECIDED
decided_by: human
decided_at: 2026-08-03T13:09:00+08:00
ai_suggestion: "[WITHHELD — learning mode; revealed only after the modeler records a rationale.]"
choice: "M2（支持域筛选 + k=100 pilot 闭环）；M1作为baseline，不要退回M1。"
rejected_alternatives:
  - method: M1 / M2 not selected as main line
    reason: "M1作为baseline，不要退回M1。"
confidence: "中等"
evidence_refs:
  - methods/Q4/q4_method_candidates.md
  - results/Q4/experiments/train_dry_run_round1/q4_train_only_dry_run_report.md
  - results/Q4/reports/q4_final_result_analysis.md
---

## 模型者理由

选 M2，因为 Train-only 筛出 1775 个候选且最低支持率为 0.800；M1不能生成受控候选策略，仅作为对照。置信度：中等。
