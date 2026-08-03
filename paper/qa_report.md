# 当前阶段质量保证审计

## 总体状态

- **QA 状态**：FAILED / BLOCKED BEFORE FINAL QA
- **最终组装允许**：false
- **审计时间**：2026-08-03（开发证据稿与中文图表重跑后）
- **说明**：这是对当前开发阶段的独立 QA，不把开发稿、已暴露 Primary 或计划中的 pilot 误当为已冻结论文证据。

## 三审计器状态（G6 前置条件）

| 审计器 | 报告路径 | 结论 |
|---|---|---|
| consistency-auditor | `paper/audits/cross_media_consistency_audit.md` | FAILED：旧开发稿与 Round 3/Q4 Round 2 口径不一致，且缺正式冻结来源 |
| completeness-auditor | `paper/audits/completeness_audit.md` | FAILED：Q3 两份人工结果裁决仍 PENDING，正式交付链未到期 |
| quality-assurance-auditor | 本报告 | FAILED / BLOCKED |

**跨审计结论**：ONE_OR_MORE_FAILED，禁止最终组装。

## 已通过的核对项

1. ✓ P0 深层审计以 124 个物理条码为主体，并保留字段—循环掩码；Q3 RAW 特征只从通过 `t/Qc/I/V/T/Qd` 六字段审计的充电点提取。
2. ✓ Q2 代码、Round 1 结果、策略组 bootstrap 和人工 M1 主线/M2 敏感性决定均存在；M2 的区间跨 0 没有被升格为显著优于。
3. ✓ Q3 已完成 Round 2 的 M1–M4 比较、Round 3 的 M3R RAW challenger 和 2,000 次策略组 bootstrap；两个当前非支配候选均可追溯到 CSV/JSON/中文图。
4. ✓ Q4 已有策略重算输出 60 个策略与 4 个开发池非支配案例，并完成样本量、寿命摘要、来源平衡和留一资格敏感性；Secondary 仍为未读取状态。
5. ✓ Q4 轮次标签漂移已修复：`q4_existing_policy_evaluation.py` 由输出目录动态写入 `round`，重跑结果为 `existing_policy_round2_m2k100`。
6. ✓ 模板开发稿由 `论文.docx` 的校验副本生成；原模板 SHA-256 未变化，开发稿明确为非最终，并包含假设与符号、可追溯的 Q1–Q4 开发期结果、5 张核心数值表和 6 张中文图。
7. ✓ 中文开发流程图已通过脚本级 render check，且保存 SVG、300 dpi PNG 和 JSON 检查记录；它明确标注“开发版、非最终推荐”。
8. ✓ 当前本地引用已由 `paper/reference_audit.md` 和 `paper/refs.bib` 核验：仅保留题面与 Severson 原始研究两条可追溯来源，且已区分 3.6 V 协议背景与题面硬约束。
9. ✓ Primary 确认配置账本已重建并经 Python 复审；它把 Q3 Primary 的历史 M3 标签校正为 Round 2 M2，同时明确 Primary 不能重新标成独立外部验证。
10. ✓ Q3/Q4 图表已经中文化并以 `-W error` 重跑，图形目视核验记录在 `code/audit/reviews/q3_q4_chinese_figure_rerun_verification.md`；重跑不读取 Primary/Secondary。
11. ✓ 开发证据稿已补充经本地资料核验的 `[1]`、`[2]` 引用与参考文献节；引用边界和 BibTeX 条目复核见 `paper/reference_audit.md`。
12. ✓ 开发证据稿 DOCX 的可访问性审计为 high=0、medium=0、low=0；图替代文本与表头标记均已写入生成文件。
13. ✓ 开发证据稿的 P0/Q1/Q2/Q3/Q4 核心数字已由只读 Python 脚本自动回查，13 项检查均通过，且脚本显式不读取 Secondary。
8. ✓ Q1、Q3、Q4 稳健性报告均含不少于五项具体检查；所有可复现脚本、表和图保留在相应结果目录。

## 工作流完整性检查

| 交付链 | Q1 | Q2 | Q3 | Q4 |
|---|---|---|---|---|
| 候选方法池 | 缺独立方法池文件 | 有 | 有 | 缺独立方法池文件 |
| 实验结果 | 有 | 有 | 有（Round 2/3） | 有（已有策略 Round 2） |
| 方法迭代日志 | 缺 | 缺独立迭代日志 | 缺独立迭代日志 | 缺 |
| 最终方法说明 | 缺 | 缺 | 缺 | 缺 |
| 最终结果分析 | 缺 | 缺 | 缺 | 缺 |
| writer solution package / frozen numbers | 缺 | 缺 | 缺 | 缺 |
| 稳健性报告 | 有 | 有 | 有 | 有（开发池范围） |
| 图表计划 | 缺 | 缺 | 缺 | 缺 |

## 三条写作关键规则

| 规则 | 当前判定 | 原因 |
|---|---|---|
| 规则 1：论文模型必须来自 final method explanation | FAIL | Q1–Q4 均尚无 final method explanation。 |
| 规则 2：论文结果必须来自 final result analysis | FAIL | 当前仅有实验/稳健性报告，尚无按人工裁决转录的最终结果分析。 |
| 规则 3：写作者必须以 solution package 为主来源 | FAIL | Q1–Q4 均无 solution package 与 `frozen_numbers.json`。 |

## 阻断项

| # | 阻断项 | 影响 | 为什么重要 | 修复路线 |
|---|---|---|---|---|
| 1 | Q3 `robustness-checker_modeler_decision.md` 与 `result-report-generator_modeler_decision.md` 为 PENDING | Q3、Q4 与最终写作 | 置信等级、候选角色和轮次结论不能由 AI 代填；未裁决时不能冻结数字 | 建模者填写后由 modeler-decision-logger 记录 |
| 2 | Secondary 最终压力测试尚未执行 | Q3/Q4 泛化与最终推荐 | Primary 已有探索暴露，不能替代独立测试 | 所有规则冻结后一次性运行 Secondary |
| 3 | 正式方法说明、结果分析、solution package、冻结数字均缺失 | Q1–Q4 写作链 | 纸面数字无法获得可审计的唯一来源 | 先通过 Q3 人工闸门，再运行 final-method-explainer、result-report-generator、solution-package-builder |
| 4 | 旧 `论文初稿_冻结结果版.md` 仍使用旧 Q3 k=5 口径，且流程图链接缺失 | 旧开发稿 | 若继续引用将把 M2-k5 误作当前 M3R-k5 候选 | 停用旧稿；以本次开发稿和 Round 3 scope update 为后续底稿 |
| 5 | `paper/sections/` 尚未生成正式章节 | 最终论文 | 开发前置 DOCX 不是可提交论文 | 上游冻结完成后使用 paper-section-writer 生成章节 |

## 反捏造检查

- 没有把 4 个开发池案例写成最终最优策略。
- 没有把 M3R-k=5 的寿命点估计改善写成已稳定改善寿命；其 RMSE/MAE bootstrap 区间仍跨 0。
- 没有把 k=100 的开发集最低误差写成外部泛化保证。
- 没有把 3.6 V 的参考文献实验协议写成题面硬约束。
- 没有读取或使用 Secondary 参与当前模型选择、调参或策略重排。

## 修复与交付顺序

1. 保持当前 M3R-k=5（筛查候选）与 M2-k=100（正式校正候选）的模型、特征和指标不再回调。
2. 由建模者完成 Q3 两份 PENDING 决策的真实理由和置信等级；此项不能自动化。
3. 生成 Q1–Q4 的 final method explanation、final result analysis 与 solution package，冻结所有论文数字。
4. 冻结后一次性运行 Secondary，记录任何降级或适用范围变化。
5. 基于冻结包再写正式章节、参考文献审计、语言润色和最终三审计器复核。

## 推荐下一步

当前不应再改变模型或用 Primary 调参。下一步是等待/记录 Q3 人工裁决；完成后按上述顺序冻结并写正式论文。开发稿可继续用于团队交接与模板排版，但不得作为最终提交版本。
