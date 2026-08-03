# Q3 人工窗口角色决定（原话转录）

schema_version: 1  
scope: Q3  
decision_id: q3_window_role_choice  
decision_point: hyperparameter  
status: DECIDED  
decided_by: human  
decided_at: 2026-08-02  
captured_at: 2026-08-02T22:02:43+08:00  
captured_in_mode: learning  
ai_suggestion: WITHHELD_IN_LEARNING_MODE_UNTIL_HUMAN_RATIONALE  
supersedes: —

- options_considered: `只保留单一窗口` / `k=5 与 k=100 两层输出`
- evidence_refs: `robustness/Q3/q3_robustness_report.md`; `robustness/Q3/tables/q3_window_cell_equal_bootstrap_summary.csv`; `paper/model_selection_early_warning_and_q4_details.md`
- choice: `k=5 作为最早筛查窗口；k=100 作为当前 V2 one-standard-error 规则下的正式预测窗口。`
- rejected_alternatives: `不把 k=5 包装为与 k=100 同等精度的正式寿命窗口；不因单一亮点删除两层用途。`
- confidence: `未声明；稳定性置信等级由后续 Gate G4.5 单独裁决。`

## Modeler's rationale

建模者原话：“给出两层结果：k=5：最早筛查窗口，可用于早期风险预警或策略初筛；k=100：当前 V2 one-standard-error 规则下的正式预测窗口，用于较可信的寿命与未来 SOH 结论。”

> 本文件只转录上述人工选择；没有把 AI 建议改写成人工理由。
