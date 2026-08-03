schema_version: 1
skill: robustness-checker
scope: Q3
decision_id: q3_stability_verdict
decision_point: confidence
status: DECIDED
decided_by: human
decided_at: 2026-08-03T00:00:00+08:00
ai_suggestion: WITHHELD_IN_LEARNING_MODE_UNTIL_HUMAN_RATIONALE
evidence_refs:
  - robustness/Q3/q3_robustness_report.md
  - robustness/Q3/round3_raw_curve_challenger/metrics/q3_raw_curve_bootstrap_summary.json
  - robustness/Q3/round3_raw_curve_challenger/tables/q3_raw_curve_policy_bootstrap.csv
  - robustness/Q3/round3_raw_curve_challenger/tables/q3_round3_combined_window_pareto.csv
  - results/Q3/experiments/round2_joint/tables/joint_window_metrics.csv
  - results/Q3/experiments/round3_raw_curve_challenger/tables/m3r_raw_curve_window_metrics.csv
  - results/Q3/experiments/round2_joint/tables/joint_oof_life_predictions.csv
choice: needs_caution
rejected_alternatives:
  - alternative: high
    reason: 建模者不接受高可信表述：寿命误差改善的策略组 bootstrap 区间仍跨越 0，不能据此宣称稳定优于基线。
  - alternative: medium
    reason: 建模者不以中等可信替代限制性表述；k=5 的稳定支持仅覆盖未来 SOH 误差改善，而未覆盖寿命预测优势。
  - alternative: needs_caution
    reason: 建模者选择 needs_caution，并保留 k=5 的早筛用途与 k=100 的较充分校正用途，均待 Secondary 确认。

## Modeler's rationale

建模者原话：“Q3 稳定性：needs_caution。M3R-k5：保留为‘最早曲线增强筛查候选’；仅表述其 SOH 误差改善有 bootstrap 支持，不称寿命预测稳定优于基线。M2-k100：保留为‘开发期较充分寿命/SOH 校正窗口’，结论限定为开发期内有限可信，待 Secondary 确认。”

上述判断对应 `robustness/Q3/round3_raw_curve_challenger/tables/q3_raw_curve_policy_bootstrap.csv`：M3R-k5 相对 M2-k5 的未来 SOH RMSE 差值为 -0.005279，95% 区间为 [-0.009075, -0.001605]；但寿命 RMSE 差值区间为 [-0.091519, 0.021773]、MAE 差值区间为 [-0.071340, 0.004273]，均跨越 0。
