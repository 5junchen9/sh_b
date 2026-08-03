schema_version: 1
skill: result-report-generator
scope: Q2
decision_id: q2_result_verdict
decision_point: result_verdict
status: DECIDED
decided_by: human
decided_at: 2026-08-02T23:26:53+08:00
captured_in_mode: learning
ai_suggestion: WITHHELD_IN_LEARNING_MODE_UNTIL_HUMAN_RATIONALE
evidence_refs:
  - results/Q2/experiments/round1/q2_experiment_report_round1.md
  - results/Q2/experiments/round1/metrics/comparison_metrics.json
  - results/Q2/experiments/q2b_proxy_round1/tables/q2b_model_comparison_and_selection.csv
  - robustness/Q2/q2_robustness_report.md
method_choices:
  - method_id: Q2-A-M1
    choice: CHOSEN_AS_PAPER_MAINLINE
    rationale: M2 的 MAE 点估计改善 8.91%，但差值区间跨 0；建模者选择保守的 M1 主文口径。
  - method_id: Q2-A-M2
    choice: RETAINED_AS_SENSITIVITY_ONLY
    rationale: 仅用于不同 SOC 阶段倍率交互的探索性关联，不写成显著优于 M1 或因果机制。
  - method_id: Q2-B-P3
    choice: FROZEN_Q4_PROVISIONAL_PROXY
    rationale: P3 仅作 Q4 provisional 候选代理，不作为最终最优或正式寿命排序模型。
  - method_id: Q2-B-C1
    choice: RETAINED_AS_CHALLENGER_NOT_REPLACEMENT
    rationale: 不以一次点估计较低替换 P3；其相对 P3 的 bootstrap 差值区间仍跨 0。
round_decision: END_ITERATION_AND_FREEZE_CURRENT_Q2_ROUTE
confidence:
  - claim: Q2-A mechanism-association conclusion
    level: limited_medium
    rationale: M1 正文和 M2 敏感性的分工保留了 M2 的 8.91% MAE 改善信号，同时不忽略其差值区间跨 0 的不确定性。
  - claim: Q2-B design-before-use proxy
    level: limited_medium_provisional_only
    rationale: P3 已完成 Train 验证、bootstrap 与一次冻结 Primary 确认，但只能支持 Q4 provisional 候选，不能支持最终最优主张。
rejected_alternatives:
  - alternative: any method marked REJECTED above
    reason: 不扩大候选池，也不使用 Primary 结果重新选择模型；若需新模型，只能回到 Train 新开轮次。

## Modeler's rationale

建模者决定结束当前 Q2 模型迭代并冻结 P3、特征和评价指标。冻结的理由是 Train 验证、bootstrap 和一次 Primary 受限确认均已完成；继续利用 Primary 调整模型会造成验证集泄漏，Secondary 应保留作最终独立压力测试。
