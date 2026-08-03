# Q3 方法选择：待建模者填写

status: DECIDED  
decided_by: human  
decision_id: q3_method_choice  
captured_in_mode: learning

- options_considered: `Q3-M1` 早期汇总特征 Ridge / `Q3-M3` 寿命锚定单调 SOH 模板
- evidence_refs: `methods/Q3/q3_method_candidates.md`; `methods/Q3/poc/m1_early_feature_ridge_poc.py`; `methods/Q3/poc/m3_life_anchored_soh_template_poc.py`
- ai_suggestion: `WITHHELD_IN_LEARNING_MODE_UNTIL_HUMAN_RATIONALE`
- choice: `Q3-M3 寿命预测 + 单调 SOH 模板联合主线`
- rejected_alternatives: `Q3-M1 不单独作为主线；其寿命 Ridge 组件保留在 Q3-M3 内。`

## Modeler's rationale

建模者原话：“直接 SOH 斜率外推失败，不是能直接说明电池的衰减与与时间相关度很大吗，所以采用联合主线目前数据能验证吗”“先做个联合主线看看”。
