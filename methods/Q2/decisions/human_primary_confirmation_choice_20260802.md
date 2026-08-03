# Q2-B Primary 受限确认决定（原话转录）

schema_version: 1  
scope: Q2  
decision_id: q2b_primary_confirmation_choice  
decision_point: method_choice  
status: DECIDED  
decided_by: human  
decided_at: 2026-08-02  
captured_in_mode: learning  
ai_suggestion: USER_REQUESTED_ADVICE_BEFORE_CONFIRMATION  
supersedes: —

- options_considered: `冻结 P3、特征和评价规则后进行一次 Primary 受限确认` / `继续仅在 Train 内迭代并推迟确认`。
- evidence_refs: `results/Q2/experiments/q2b_proxy_round1/tables/q2b_model_comparison_and_selection.csv`; `robustness/Q2/q2_robustness_report.md`; `paper/data_processing_and_split_details.md`。
- choice: `不推迟外部验证：冻结 P3、特征和评价规则后，直接做一次受限的 Primary 确认。`
- rejected_alternatives: `不在 Primary 结果出现后更换 P3、特征、评价规则或候选池；不把 C1 由 challenger 升级为确认模型。`
- confidence: `未声明；Q2 结果与稳定性置信等级仍由 Gate G4.5 单独裁决。`

## Modeler's rationale

建模者原话：“不推迟外部验证：冻结 P3、特征和评价规则后，直接做一次受限的 Primary 确认。”

> 本文件只转录人工选择；P3 仍是 Train-only 规则选出的条件性确认代理，不因此被写成已证明最优模型。
