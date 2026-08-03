schema_version: 1
skill: final-method-explainer
scope: Q2
decision_id: q2_method_explanation
decision_point: assumption_necessity
status: DECIDED
decided_by: human
decided_at: 2026-08-03T09:05:00+08:00
captured_in_mode: learning
ai_suggestion: WITHHELD_IN_LEARNING_MODE; TRANSCRIBES_PRIOR_HUMAN_DECISIONS_ONLY
evidence_refs:
  - planning/model_assumptions.md
  - methods/Q2/q2_decision_log.md
  - methods/Q2/decisions/result-report-generator_modeler_decision.md
  - methods/Q2/decisions/robustness-checker_modeler_decision.md
choice:
  - assumption: Q2-A1
    necessity: simplifying
    rationale: "已确认：在 Train 支持域内，以低自由度线性、交互或加性平滑模型近似策略—ln(寿命)条件关系；若存在强阈值或更高阶结构，只能用受限 challenger 检查。"
  - assumption: Q2-A2
    necessity: simplifying
    rationale: "已确认：ln(寿命)尺度用于相对偏差评价，并同时报告 cycle 尺度指标。"
  - assumption: Q2-A3
    necessity: simplifying
    rationale: "已确认：策略组折外误差与策略组块 bootstrap 是支持域内不确定性的近似，且区间可能低估批次和电芯异质性。"
  - result_good_threshold: "M2 只有在 ΔMAE_log 的 95% 置信区间上界小于 0、相对改善不少于 5%、主要交互项符号稳定率不少于 80% 时，才可作为正式解释模型；否则 M1 为正文主模型、M2 仅作敏感性。"
rejected_alternatives:
  - alternative: "把 M2 写成正式主模型或因果机制"
    reason: "M2 的 MAE 点估计改善 8.91%，但策略组 bootstrap 差值区间跨 0；人工裁决保留 M1 正文、M2 敏感性。"
  - alternative: "把 P3 写成最终最优或正式寿命排序模型"
    reason: "P3 只作 Q4 provisional 候选代理，最终 Secondary 外部观察也未支持代理模型升级。"

## Modeler's rationale

Q2 正文主线：以 M1 主效应 Ridge 作为保守基线；M2 保留为“不同 SOC 阶段倍率交互的探索性关联/敏感性分析”；Q4 不使用这两个当前 PoC 模型直接优化，而进入 Q2-B 的 Train-only 代理比较。相同可信域、同样的分组验证和 bootstrap 下，选择误差不劣、过预测风险不更高、且最简单的模型。

限定范围内中等可信：M2 的 MAE 点估计改善 8.91%，但差值区间跨 0，因此保留 M1 正文、M2 敏感性；P3 仅作 Q4 provisional，不能说已验证为最优。
