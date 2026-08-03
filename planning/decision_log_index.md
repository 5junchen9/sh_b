# Decision Log Index

| id | Qx | decision_point | choice | confidence | supersedes |
|---|---|---|---|---|---|
| Q1-D01 | Q1 | method_choice | M2 策略级聚合正文；M1 基础描述；M3 一致性核对 | 中等 | — |
| Q4-D04 | Q4 | confidence | Q4 包整体可信度中等 | 中等 | — |
| Q4-D03 | Q4 | result_verdict | drop F1–F3；保留 C1–C3 | 中等 | — |
| Q4-D02 | Q4 | assumption_necessity | Q4-A1/A3 必要；双空间支持、≥0.800、每点≥3枚至k=100后方可升级 | 中等 | — |
| Q4-D01 | Q4 | method_choice | M2 支持域筛选 + k=100 pilot 闭环；M1 baseline | 中等 | — |
| Q3-D09 | Q3 | claim_scope | 选 A：保留无泄漏联合流程与 M3R 外部未复现的完整结论 | needs_caution | — |
| Q2-D08 | Q2 | claim_scope | 选 A：M1 正文、M2 敏感性、P3 pilot 接口 | limited_medium | — |
| Q3-D08 | Q3 | assumption_necessity | Q3-A1 必要；Q3-A2/A3 简化；不据 Secondary 重选窗口 | needs_caution | Q3-D04（外部主张范围） |
| Q2-D07 | Q2 | assumption_necessity | Q2-A1/A2/A3 简化；M2 联合准入门槛 | limited_medium | — |
| Q3-D07 | Q3 | result_verdict | M3R-k5 仅开发期探索性记录；k=100 仅报告外部表现，不重选 k=5；Q4 仅候选、风险边界和 pilot 接口 | needs_caution | Q3-D06（外部主张范围） |
| Q3-D05 | Q3 | confidence | needs_caution：k=5 仅 SOH 改善稳定，寿命改善需谨慎 | needs_caution | — |
| Q3-D06 | Q3 | result_verdict | M3R-k5 早筛；M2-k100 开发期校正；冻结后一次 Secondary | k=5 needs_caution；k=100 limited development | — |
| Q2-D01 | Q2 | method_choice | Q2-M2 二阶交互 Ridge | 未声明 | — |
| Q3-D01 | Q3 | method_choice | Q3-M3 寿命预测 + 单调 SOH 模板 | 未声明 | — |
| Q2-D02 | Q2 | method_choice | M1 正文主线；M2 敏感性；Q4 走 Q2-B | 未声明 | Q2-D01 |
| Q3-D02 | Q3 | hyperparameter | k=5 筛查；k=100 正式窗口 | 未声明 | — |
| Q2-D03 | Q2 | method_choice | P3 冻结后进行一次 Primary 受限确认 | 未声明 | — |
| Q2-D04 | Q2 | claim_scope | P3 仅用于 Q4 provisional，不作最终排序 | 未声明 | — |
| Q3-D03 | Q3 | claim_scope | k=5 筛查；k=100 正式且待外部确认 | 未声明 | — |
| Q2-D05 | Q2 | result_verdict | M1 正文、M2 敏感性；P3 provisional；结束本轮 | 限定中等可信 | — |
| Q2-D06 | Q2 | confidence | 限定范围内中等可信 | 限定中等可信 | — |
| Q3-D04 | Q3 | claim_scope | 结束迭代；保留双窗口；冻结并留 Secondary 压力测试 | 未单独裁决 | — |
