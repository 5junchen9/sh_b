schema_version: 1
skill: result-report-generator
scope: Q3
decision_id: q3_result_verdict
decision_point: result_verdict
status: DECIDED
decided_by: human
decided_at: 2026-08-03T00:00:00+08:00
captured_in_mode: learning
ai_suggestion: WITHHELD_IN_LEARNING_MODE_UNTIL_HUMAN_RATIONALE
evidence_refs:
  - results/Q3/experiments/round1/q3_experiment_report_round1.md
  - results/Q3/experiments/round1/tables/window_metrics.csv
  - robustness/Q3/tables/q3_window_cell_equal_bootstrap_summary.csv
  - robustness/Q3/q3_robustness_report.md
  - results/Q3/experiments/primary_confirmation_round1/q3_primary_confirmation_report.md
  - results/Q3/experiments/primary_confirmation_round1/metrics/q3_primary_metrics.json
method_choices:
  - method_id: Q3-M3R-k5-screening
    choice: RETAIN_AS_EARLIEST_CURVE_ENHANCED_SCREENING_CANDIDATE
    rationale: 仅将其用于最早筛查；未来 SOH 误差的策略组 bootstrap 改善有支持，但寿命 RMSE/MAE 差值区间跨 0，不能写成稳定的寿命优胜或正式寿命排序模型。
  - method_id: Q3-M2-k100-calibration
    choice: RETAIN_AS_DEVELOPMENT_CALIBRATION_CANDIDATE
    rationale: 在开发期五窗口中其寿命 RMSE 为 0.231737，作为较充分寿命/SOH 校正窗口；结论只限开发期内有限可信，必须待 Secondary 一次性确认。
round_decision: FREEZE_AND_ADVANCE_TO_ONE_TIME_SECONDARY_WITH_NO_RETUNING
confidence:
  - claim: k5 early-screening conclusion
    level: needs_caution
    rationale: k=5 的未来 SOH 改善区间为 [-0.009075, -0.001605]，但寿命 RMSE 与 MAE 改善区间跨 0；只保留早筛候选的限定主张。
  - claim: k100 formal life-and-SOH conclusion
    level: limited_development_only_pending_secondary
    rationale: k=100 的开发期指标为 RMSE_log=0.231737、MAE_log=0.170084、SOH RMSE=0.034753；Primary 仅是历史 M2 的受限观察，不能替代独立 Secondary。
rejected_alternatives:
  - alternative: M3R-k5 as a formal lifetime-ranking model
    reason: 寿命误差的策略组 bootstrap 区间跨 0，不满足稳定优于基线的证据要求。
  - alternative: one universal window for both early screening and fuller calibration
    reason: k=5 与 k=100 服务的时间—精度目标不同，强行合并会掩盖误差结构差异。
  - alternative: retune after Primary or Secondary
    reason: 建模者已冻结模型角色、特征、指标和 bootstrap 设置；利用已暴露或最终测试数据回调会造成验证泄漏。

## Modeler's rationale

建模者原话：“冻结：冻结模型角色、窗口、特征、指标和 bootstrap 设置，不再调参。Secondary：批准按预注册协议一次性运行；不得因结果回调模型。Q4：仅交付候选与 pilot 接口，不输出最佳策略。”

建模者同时确认：M3R-k5 保留为最早曲线增强筛查候选；M2-k100 保留为开发期较充分寿命/SOH 校正窗口，待 Secondary 确认。
