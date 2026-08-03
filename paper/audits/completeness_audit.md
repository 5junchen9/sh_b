# 完整性审计报告

> **状态**：FAILED（开发产物充分，但人工作业闸门与正式交付链未完成）  
> **审计时间**：2026-08-03（补充中文图表重跑核验）  
> **范围**：Q1–Q4、跨介质审计和论文开发链。  
> **判定原则**：只把已经进入当前轮次的产物列为“应有”；最终 method explanation、writer package 和 frozen numbers 在人工结果裁决前为 `NOT_YET_DUE`，不伪称已完成。

## 汇总

| 产物/技能 | 当前文件 | 状态 | 明确通过项 | 说明/修复技能 |
|---|---|---:|---:|---|
| P0 Python/Matlab 代码复审 | `src/reviews/l1_deep_mat_audit_review.md` 等 | OK | ≥5 | 当前深层掩码审计有复审证据 |
| Q1 Python 代码复审 | `code/Q1/reviews/q1_python_review.md` | OK | ≥5 | 基线与描述性运行已复审 |
| Q1 稳健性报告 | `robustness/Q1/q1_robustness_report.md` | OK | 6 | 已补入与真实 bootstrap 产物对应的六项明确检查清单 |
| Q2 Python 代码复审与 Round 1 报告 | `code/Q2/reviews/q2_python_review.md`、`results/Q2/experiments/round1/q2_experiment_report_round1.md` | OK | ≥5 | 当前 M1/M2 证据完整 |
| Q2 稳健性报告 | `robustness/Q2/q2_robustness_report.md` | OK | ≥5 | 2,000 次策略组 bootstrap 已留档 |
| Q3 Round 2/RAW 代码复审 | `code/Q3/reviews/q3_round2_joint_python_review.md`、`q3_raw_curve_challenger_python_review.md`、`src/reviews/q3_raw_curve_feature_matlab_review.md` | OK | ≥5 | 联合、MAT 特征与 RAW challenger 均有独立复审 |
| Q3 稳健性报告 | `robustness/Q3/q3_robustness_report.md` | OK | ≥5 | 2,000 次策略等权 bootstrap、RAW 掩码与 Pareto 均留档 |
| Q4 Round 2 已有策略重算复审 | `code/Q4/reviews/q4_existing_policy_round2_m2k100_python_review.md` | OK | ≥5 | 60 个已有策略的重算与范围限制已复审 |
| Q4 开发池敏感性报告 | `robustness/Q4/q4_robustness_report.md` | OK | 7 | 样本量、寿命摘要、来源平衡、留一与外部数据边界已逐项核对 |
| Q3/Q4 中文图表重跑核验 | `code/audit/reviews/q3_q4_chinese_figure_rerun_verification.md` | OK | 6 | 图中文字已更新并以 `-W error` 重跑；未改变模型与数据范围 |
| 开发稿核心数字回查与复审 | `code/audit/verify_development_draft.py`、`code/audit/reviews/development_draft_numeric_verification_python_review.md` | OK | 9 | 13 项只读回查已通过，P0/Q1/Q2/Q3/Q4 数字与文稿片段可追溯 |
| Primary 确认配置账本复审 | `code/audit/reviews/primary_confirmation_manifest_python_review.md` | OK（带限制） | 7 | 已运行、哈希可复算，并明确账本为事后重建而非前瞻预注册 |
| 跨介质一致性审计 | `paper/audits/cross_media_consistency_audit.md` | FAILED | 8 | 本轮已实质运行，但发现开发稿陈旧、缺图与正式来源缺失 |
| Q3 人工稳定性裁决 | `methods/Q3/decisions/robustness-checker_modeler_decision.md` | BLOCKING | — | `status: PENDING`，不得由 AI 代填；`modeler-decision-logger` |
| Q3 人工结果裁决 | `methods/Q3/decisions/result-report-generator_modeler_decision.md` | BLOCKING | — | `status: PENDING`，不得由 AI 代填；`modeler-decision-logger` |
| Q1–Q4 最终方法/结果/冻结包 | `methods/Qx/*final*`、`results/Qx/reports/*` | NOT_YET_DUE | — | 需先完成 Q3 人工裁决和当前开发稿修复 |
| 参考文献本地核验 | `paper/reference_audit.md`、`paper/refs.bib` | OK（当前本地引用） | 7 | 两条实际使用的本地来源均已追溯；正式章节冻结后仍须逐条复审引用 |
| 润色与最终 QA | `paper/qa_report.md` 等 | NOT_YET_DUE | — | 正式章节尚未生成，不能提前宣称完成 |

## 已通过的核对项（本审计已实质运行）

1. ✓ P0 的深层 MAT 审计有独立复审文件，且复审文件包含超过 5 项具体通过核对。
2. ✓ Q1 的 Python 基线分析有独立复审，且数据描述性图表与 Round 1 实验报告均存在。
3. ✓ Q1 稳健性报告现在逐项核对电芯 bootstrap、策略 bootstrap、分布统计、双相关、数据边界和结论边界，共六项可复现检查。
4. ✓ Q2 当前 M1/M2 代码复审、实验报告、稳健性报告和两个已 `DECIDED` 的人工记录均在磁盘上。
5. ✓ Q3 当前 Round 2 联合模型、Round 3 RAW challenger 与 Matlab 原始特征提取各自具有独立复审文件。
6. ✓ Q3 Round 3 稳健性报告包含策略 bootstrap、失败率、Pareto、RAW 掩码和结论边界等五类具体检查。
7. ✓ Q4 当前 Round 2 已有策略重算具有可复现脚本、CSV/JSON/中文图及独立 Python 复审。
8. ✓ Q4 开发池敏感性报告逐项核对样本资格、n≥3 收紧、中位数摘要、来源平衡、留一资格和 Secondary 隔离，共七项可复现检查。
9. ✓ 本轮跨介质审计文件存在且列出 8 项可验证的通过核对及每项阻断修复路由。
10. ✓ `paper/reference_audit.md` 已独立核验当前两条本地引用及 3.6 V 的来源边界；`paper/refs.bib` 未加入未经核验的条目。
10. ✓ 已检测到 Q3 人工裁决仍为 PENDING，系统未把用户的窗口意图伪写成 `DECIDED` 或最终外部验证。
11. ✓ Primary 确认账本已核对 Q2-B P3 与 Q3 M2 的历史标签、脚本、协议和输入哈希；账本不读取 Secondary，也不改变任何模型或模型选择。
12. ✓ Q3/Q4 新图均有独立中文化重跑核验，且该核验保留复现命令、数值不变检查和模型边界警示。

## 不足、缺失与陈旧项

| # | 类型 | 文件/范围 | 问题 | 严重度 | 修复技能 |
|---|---|---|---|---|---|
| 1 | STALE | `paper/论文初稿_冻结结果版.md` | Q3 仍以旧 M2-k5 写作，未纳入 M3R-k5；流程图文件也不存在 | BLOCKING | paper-section-writer、math-figure-generator |
| 2 | PENDING_GATE | `methods/Q3/decisions/robustness-checker_modeler_decision.md` | 置信等级、替代项理由和建模者理由为 `<<<HUMAN>>>` | BLOCKING | modeler-decision-logger |
| 3 | PENDING_GATE | `methods/Q3/decisions/result-report-generator_modeler_decision.md` | 结果标签与置信理由未由建模者填写 | BLOCKING | modeler-decision-logger |
| 4 | NOT_YET_DUE | Q1–Q4 final result analysis / solution package / frozen numbers | 依赖上述 Q3 人工闸门与当前开发稿修复 | 未到期，最终交付前必需 | final-method-explainer、solution-package-builder |

## 结论

- **审计层可进入最终 QA**：否。
- **最终论文组装允许**：否；但允许继续形成清楚标注边界的开发版论文与图表。
- **优先修复顺序**：①修复开发稿与缺失流程图；②等待并记录 Q3 人工稳定性/结果裁决；③再冻结数值、组装正式论文、做参考文献与最终 QA。
