# Q2 人工方法角色修订（原话转录）

schema_version: 1  
scope: Q2  
decision_id: q2_method_choice_revision  
decision_point: method_choice  
status: DECIDED  
decided_by: human  
decided_at: 2026-08-02  
captured_at: 2026-08-02T22:02:43+08:00  
captured_in_mode: learning  
ai_suggestion: WITHHELD_IN_LEARNING_MODE_UNTIL_HUMAN_RATIONALE  
supersedes: Q2-D01

- options_considered: `Q2-A M1 正文主线 + M2 敏感性` / `Q2-A M2 正文主线`；Q4 是否直接使用 Q2-A，或另做 Q2-B 设计前代理比较。
- evidence_refs: `robustness/Q2/q2_robustness_report.md`; `results/Q2/experiments/round1/metrics/comparison_metrics.json`; `results/Q2/experiments/q2b_proxy_round1/tables/q2b_model_comparison_and_selection.csv`; `paper/model_selection_early_warning_and_q4_details.md`
- choice: `Q2-A 以 M1 主效应 Ridge 作为正文保守主线；M2 仅作不同 SOC 阶段倍率交互的探索性关联/敏感性分析；Q4 不直接使用 Q2-A，而进入 Q2-B 比较。`
- rejected_alternatives: `不再将 Q2-M2 作为 Q2 正文正式主模型；不把当前 Q2-A PoC 直接用于 Q4 优化。`
- confidence: `未声明；结果与稳定性置信等级由后续 Gate G4.5 单独裁决。`

## Modeler's rationale

建模者原话：“Q2 正文主线：以 M1 主效应 Ridge 作为保守基线；M2：保留为‘不同 SOC 阶段倍率交互的探索性关联/敏感性分析’；Q4：不要使用这两个当前 PoC 模型直接优化，而是进入 Q2-B 的 Train-only 代理模型比较：Ridge、ElasticNet、低自由度 GAM；受限提升树只作 challenger。”

建模者原话：“相同可信域、同样的分组验证和 bootstrap 下，选择误差不劣、过预测风险不更高、且最简单的模型。”

> 本文件只转录上述人工选择；没有把 AI 建议改写成人工理由。
