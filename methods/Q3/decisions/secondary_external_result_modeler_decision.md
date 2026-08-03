schema_version: 1
skill: result-report-generator
scope: Q3_Q4_after_secondary
decision_id: q3_secondary_external_result_verdict
decision_point: result_verdict
status: DECIDED
decided_by: human
decided_at: 2026-08-03T08:47:56.8242740+08:00
captured_in_mode: learning
ai_suggestion: WITHHELD_IN_LEARNING_MODE; RECORDS_HUMAN_DECISION_ONLY
evidence_refs:
  - results/Secondary_final_pressure_test/secondary_external_experiment_report.md
  - results/Secondary_final_pressure_test/tables/q3_external_metrics.csv
  - results/Secondary_final_pressure_test/tables/bootstrap_intervals.csv
  - results/Secondary_final_pressure_test/verification.md
choices:
  - claim: M3R-k5 external role
    choice: RETAIN_AS_DEVELOPMENT_RAW_CURVE_EXPLORATORY_CHALLENGER_ONLY
    rationale: "M3R-k=5 作为开发期原始曲线增强的探索性 challenger 保留记录；其开发期 SOH 改善未在 Secondary 复现，因此不作为外部支持的早筛模型或寿命预测模型。"
  - claim: M2-k100 external role
    choice: REPORT_AS_PRE_SPECIFIED_CALIBRATION_WINDOW_EXTERNAL_OBSERVATION_ONLY
    rationale: "k=100 是冻结前预先指定的较充分校正窗口；本次 Secondary 中未显示其优于 M2-k=5，因此仅报告其外部表现，不声称其更优、也不据此重选 k=5 为最终窗口。"
  - claim: M2-k5 external observation
    choice: REPORT_AS_POST_HOC_COMPARATOR_OBSERVATION_NOT_FINAL_SELECTION
    rationale: "不因 Secondary 中的比较结果重选 k=5 为最终窗口。"
  - claim: Q4 delivery scope
    choice: CANDIDATE_SET_RISK_BOUNDARIES_AND_PILOT_INTERFACE_ONLY
    rationale: "Q4 仅交付候选策略集合、风险边界与 pilot 试验接口；由于最终外部观察未支持代理模型升级，且 Secondary 仅含 8 个已有策略组，本文不输出最优新充电策略或可直接执行的推荐。"
round_decision: "关闭冻结的 Secondary 一次性压力测试；按上述边界写入最终结果，不重跑、不调参、不重选。"
confidence:
  - claim: Q3 frozen dual-window conclusion
    level: needs_caution
    rationale: "外部观察未支持 M3R-k=5 的开发期 SOH 改善，也未支持 k=100 优于 M2-k=5；两者均只保留限定角色和外部结果报告。"
rejected_alternatives:
  - alternative: "将 M3R-k=5 表述为外部支持的早筛模型或寿命预测模型"
    reason: "其开发期 SOH 改善未在 Secondary 复现。"
  - alternative: "根据本次 Secondary 比较结果将 k=5 重选为最终窗口"
    reason: "测试在冻结后一次性执行，不得据此重选。"
  - alternative: "输出最优新充电策略或可直接执行的推荐"
    reason: "最终外部观察未支持代理模型升级，且 Secondary 仅含 8 个已有策略组。"

## Modeler's rationale

M3R-k=5 作为开发期原始曲线增强的探索性 challenger 保留记录；其开发期 SOH 改善未在 Secondary 复现，因此不作为外部支持的早筛模型或寿命预测模型。

k=100 是冻结前预先指定的较充分校正窗口；本次 Secondary 中未显示其优于 M2-k=5，因此仅报告其外部表现，不声称其更优、也不据此重选 k=5 为最终窗口。

Q4 仅交付候选策略集合、风险边界与 pilot 试验接口；由于最终外部观察未支持代理模型升级，且 Secondary 仅含 8 个已有策略组，本文不输出最优新充电策略或可直接执行的推荐。
