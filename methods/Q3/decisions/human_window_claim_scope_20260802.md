# Q3 双窗口主张范围决定（原话转录）

schema_version: 1  
scope: Q3  
decision_id: q3_window_claim_scope  
decision_point: claim_scope  
status: DECIDED  
decided_by: human  
decided_at: 2026-08-02  
captured_in_mode: learning  
ai_suggestion: USER_REQUESTED_ADVICE_BEFORE_CONFIRMATION  
supersedes: —

- options_considered: `k=5 筛查 + k=100 正式窗口（注明待外部确认）` / `两者均只称开发窗口`。
- evidence_refs: `results/Q3/experiments/round1/q3_experiment_report_round1.md`; `robustness/Q3/q3_robustness_report.md`; `paper/model_selection_early_warning_and_q4_details.md`。
- choice: `k=5 为最早筛查窗口；k=100 为正式预测窗口，相关结论仍注明待外部确认。`
- rejected_alternatives: `不把 k=5 写成与 k=100 同等精度；不把 k=100 写成无条件外部泛化结论。`
- confidence: `未声明；稳定性置信等级仍由 Gate G4.5 单独裁决。`

## Modeler's rationale

建模者原话：“Q3：k=5 为最早筛查窗口；k=100 为正式预测窗口，相关结论仍注明待外部确认。”

> 本文件只转录人工选择；它补充 Q3-D02 的窗口角色，不替代稳定性裁决。
