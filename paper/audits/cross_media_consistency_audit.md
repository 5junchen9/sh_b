# 跨介质一致性审计报告

> **状态**：FAILED（当前不允许最终组装）  
> **审计时间**：2026-08-03（含中文图表重跑与开发证据稿重建复核）  
> **范围**：Q1–Q4 的当前开发产物，以及现有 `论文初稿_冻结结果版.md`。  
> **权威来源层级**：Q1=Round 1 原始表与稳健性报告；Q2=Round 1 指标表与 bootstrap；Q3=Round 2/3 原始指标表与 Round 3 稳健性报告；Q4=Round 2 已有策略汇总表。四问均**尚无** `frozen_numbers.json` 或 writer solution package。

本审计不修改模型、数据或论文正文。`论文初稿_冻结结果版.md` 是早期开发稿，不是可交付论文；其名称中的“冻结结果版”已不反映当前 Q3 Round 3 状态。

## 已通过的核对项（本审计已实质运行）

1. ✓ Q2 的 M1 `RMSE_log=0.37169、MAE_log=0.27557` 与 M2 `0.36854、0.25102` 在开发稿第 112–115 行、Round 1 输出及 Q2 细节文档之间一致。
2. ✓ Q2 的 `ΔMAE_log=[-0.07245,0.02620]` 与 `ΔRMSE_log=[-0.04887,0.04018]` 在开发稿第 115 行和 Q2 bootstrap 结论之间一致；正文没有把跨零区间写成显著优于。
3. ✓ 开发稿引用的 Q1 两张图、Q2 比较图和旧 Q3 M2 窗口图均存在于磁盘；四个已解析的 `results/...png` 链接无断链。
4. ✓ 开发稿第 11、175、187、202 行均将 1,775 条网格候选限定为待验证的 `Q2_provisional`，未误写成已验证最优策略。
5. ✓ 当前 Q3 的 M2-k100 数值在开发稿第 11、152、156 行与 `results/Q3/experiments/round2_joint/tables/joint_window_metrics.csv:19` 一致：寿命 `RMSE_log=0.23174`、电芯等权未来 SOH RMSE=`0.03475`。
6. ✓ 当前 Q3 的 M3R-k5 原始输出与 Round 3 稳健性报告一致：`RMSE_log=0.24070`、`MAE_log=0.15714`、SOH RMSE=`0.03299`，见 `m3r_raw_curve_window_metrics.csv:2` 与 `robustness/Q3/q3_robustness_report.md:40–46`。
7. ✓ 当前 Q4 已有策略重算报告明确只使用 Train+Primary 的 84 枚电芯、60 个已有策略，并将 4 个开发池非支配点限定为非最终推荐；未读取 Secondary。
8. ✓ `outputs/experiments/primary_confirmation_manifest_post_exposure.json` 已将 Q2-B P3 与 Q3 Primary 的脚本、协议、输入和指标哈希汇总；它显式把 Primary 定义为受限确认，并将历史 Q3 标签重标为 Round 2 M2。
9. ✓ 新建 `paper/开发证据稿_全篇_非最终.md` 的 Q1、Q2、Q3 与 Q4 数字已逐项回查 P0、Q2 bootstrap、Q3 Round 3 和 Q4 Round 2 产物；重建后的 DOCX 结构检查为 81 段、5 张表、6 张内嵌中文图，并带有开发期参考文献，且首页明确“非最终”。
10. ✓ Q3/Q4 的更新图已用 `-W error` 重跑并目视检查；叙述性图题、图例与坐标使用中文，详见 `code/audit/reviews/q3_q4_chinese_figure_rerun_verification.md`。重跑未读取 Primary 或 Secondary，且未改变任一模型选择结论。
11. ✓ `code/audit/verify_development_draft.py` 已对开发证据稿的 P0/Q1/Q2/Q3/Q4 关键片段做 13 项只读回查，结果为 PASS；对应 JSON/Markdown 回查记录已保存，且脚本显式不读取 Secondary。
8. ✓ Q3 当前稳健性决策仍为 `PENDING`，且证据引用已更新到 Round 3 RAW challenger；没有伪造人工 `DECIDED` 结论。

## 不一致与阻断项

| # | 严重度 | 维度 | 开发稿位置 | 当前权威来源 | 开发稿值/说法 | 当前值/说法 | 修复技能 |
|---|---|---|---|---|---|---|---|
| 1 | BLOCKING | 数值与模型角色 | `paper/论文初稿_冻结结果版.md:148–160` | `results/Q3/experiments/round3_raw_curve_challenger/tables/m3r_raw_curve_window_metrics.csv:2`; `robustness/Q3/q3_robustness_report.md:40–57` | k=5 使用旧 M2 的 `0.27936/0.03817`，并称其为当前筛查结果 | 当前曲线增强筛查候选为 M3R-k5：`0.24070/0.03299`；其寿命改善区间仍跨 0 | paper-section-writer |
| 2 | BLOCKING | 图文件 | `paper/论文初稿_冻结结果版.md:21` | 文件系统 | `paper/figures/总体建模与确认流程.png` | 目标文件不存在 | math-figure-generator |
| 3 | BLOCKING | 结论溯源 | `paper/论文初稿_冻结结果版.md:154、156、201` | `methods/Q3/decisions/robustness-checker_modeler_decision.md`（PENDING） | k=5/k=100 的正式角色与置信措辞已写入正文，但没有可解析的 `decision_id` 且 Round 3 稳定性裁决尚未完成 | 只能写为“当前开发候选/待外部压力测试”，不能作为已冻结的最终结论 | paper-section-writer + modeler-decision-logger |
| 4 | BLOCKING | 范围漂移 | `paper/论文初稿_冻结结果版.md:11、175、191、202` | `results/Q4/experiments/existing_policy_round2_m2k100/q4_existing_policy_report.md:1–4` | Q4 以历史网格 1,775 条候选为主要结果 | 当前可写的实证结果是 60 个已有策略、4 个开发池非支配点；1,775 条仅保留为 Q2 provisional 网格产物 | paper-section-writer |
| 5 | BLOCKING | 正式来源缺失 | 全部正式数值段 | `results/Q1–Q4/reports/` | 开发稿被命名为“冻结结果版” | 没有 Q1–Q4 的 final result analysis、solution package 或 frozen numbers | solution-package-builder |
| 6 | WARNING | 交叉验证标签 | `paper/论文初稿_冻结结果版.md:156、170` | `methods/Q3/q3_round2_scope_update.md:1–15` | Primary 的旧 M2 观察仍被称为“冻结 M3”确认 | Round 1/Primary 与当前 M2 对应；不得称为 M3/M3R 验证 | paper-section-writer |

## 暂不可审计项

| # | 原因 | 影响范围 | 需要的后续产物 |
|---|---|---|---|
| 1 | Q1–Q4 均没有 canonical `frozen_numbers.json` | 正式论文中所有数字的逐项冻结核验 | 在人工结果闸门完成后运行 solution-package-builder |
| 2 | `paper/sections/` 与 `paper/main.tex` 尚不存在 | 无法对正式章节、符号、图表清单和决策标记做最终核验 | 先形成开发版章节，再在最终组装前复审 |
| 3 | Q3 Round 3 稳定性/结果裁决仍 PENDING，Secondary 未进行最终压力测试 | k=5 M3R 与 k=100 M2 的最终置信等级和外部泛化表述 | 人工裁决后固定规则，再一次性运行 Secondary 压力测试 |

## 跨问题核对

- 对数寿命口径：当前 Q2/Q3 代码与报告均为自然对数 `ln(L)`；开发稿没有使用 `log10(L)` 作为计算口径。
- 原始曲线边界：M3R 只读取通过 `t/Qc/I/V/T/Qd` 六字段掩码的充电点，局部异常按字段—循环掩码处理；当前资料没有声称删整枚电芯。
- 外部数据边界：现有开发模型比较与 bootstrap 只使用 Train；Primary 仅可作为已暴露的一次受限观察，Secondary 未被读取。

## 结论

- **最终组装允许**：否。
- **阻断项**：5 项（新增账本不消除旧稿漂移、Q3 人工裁决或 Secondary 压力测试的缺口）。
- **警告项**：1 项。
- **下一步**：先以当前 Round 3/Q4 Round 2 证据重写开发版章节和图表；待人工作出 Q3 稳定性裁决并完成冻结后，再生成 writer package、冻结数字和最终论文。
