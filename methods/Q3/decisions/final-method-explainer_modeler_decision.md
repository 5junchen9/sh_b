schema_version: 1
skill: final-method-explainer
scope: Q3
decision_id: q3_method_explanation
decision_point: assumption_necessity
status: DECIDED
decided_by: human
decided_at: 2026-08-03T09:05:00+08:00
captured_in_mode: learning
ai_suggestion: WITHHELD_IN_LEARNING_MODE; TRANSCRIBES_PRIOR_HUMAN_DECISIONS_ONLY
evidence_refs:
  - planning/model_assumptions.md
  - methods/Q3/q3_decision_log.md
  - methods/Q3/qx_decision_log.md
  - methods/Q3/decisions/secondary_external_result_modeler_decision.md
choice:
  - assumption: Q3-A1
    necessity: necessary
    rationale: "已确认：任一截止窗口只使用循环 k 及以前可获得的信息；k 之后的信息完全不可见。"
  - assumption: Q3-A2
    necessity: simplifying
    rationale: "已确认：外层训练电芯按相对寿命对齐后使用共同非增 SOH 形状，测试电芯以截止点实测 SOH 锚定模板；若存在多模态或恢复过程，应分层或换函数模型。"
  - assumption: Q3-A3
    necessity: simplifying
    rationale: "已确认：Table 9 寿命端点与 SOH=0.8 模板端点在本题口径下协调使用；若端点定义不一致，则取消该锚点。"
  - result_good_threshold: "不以 Secondary 的一次性点误差重选窗口。M3R-k=5 只有获得外部复现才可称外部支持的早筛/寿命模型；k=100 只报告预先冻结窗口的外部表现，不因本次比较重选 k=5。"
rejected_alternatives:
  - alternative: "仅用早期 SOH 局部斜率外推寿命"
    reason: "PoC 中仅 2/41 枚 Train 电芯形成可投影的有效递减斜率，RMSE_log=3.2081。"
  - alternative: "把 M3R-k=5 升级为外部支持的早筛或寿命预测模型"
    reason: "其开发期 SOH 改善未在 Secondary 复现。"
  - alternative: "依据 Secondary 将 k=5 重选为最终窗口"
    reason: "Secondary 为冻结后一次性压力测试，不得据此重选。"

## Modeler's rationale

冻结模型角色、窗口、特征、指标和 bootstrap 设置，不再调参。k=5 为最早筛查窗口；k=100 为当前 V2 one-standard-error 规则下的正式预测窗口。M3R-k=5 仅作为开发期原始曲线增强的探索性 challenger 保留记录，其开发期 SOH 改善未在 Secondary 复现，因此不作为外部支持的早筛模型或寿命预测模型。k=100 仅报告其外部表现，不声称更优、也不据此重选 k=5。
