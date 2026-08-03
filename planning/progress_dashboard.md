# L1 建模工作流面板

> 更新时间：2026-08-03（Asia/Shanghai）  
> 执行模式：`manual`；交互模式：`learning`  
> 当前全局阶段：**Q2、Q3、Q4 已完成最终方法说明、写作材料包与数字冻结；Q4 固定为候选、风险边界与 pilot 接口。Q1 的主线选择与材料包仍待完成，四问齐备后再进入正式论文写作。**

## 1. 环境与全局门禁

| 项目 | 状态 | 说明 |
|---|---|---|
| Python/科学计算依赖 | ✅ | Python 3.12.13；numpy/pandas/matplotlib/scikit-learn/scipy 可用 |
| Git 工作树 | ✅ | `l1` 已建立 Git 历史，基线提交 `1952d65` 已推送至 `5junchen9/sh_b`；原始 MAT/XLSX 由 SHA-256 清单追溯 |
| P0 数据门禁 | ✅ | 124 枚电芯、99,279 行；字段—循环掩码；原始源文件哈希不变 |
| G1 问题解析/分类 | ✅ | 人工确认：Q2 机制关联，Q3 精度与解释兼顾，Q4 Pareto |
| 全局符号表 | ✅ | `planning/symbol_table.md`；已统一为 `ln(L)`/`exp` |
| 统一模型假设 | ✅ | `planning/model_assumptions.md` 已人工确认；研究命题与评价/输出规则已分离 |
| G3 代码复审 | ✅（当前轮） | 已新增 Q1 bootstrap、Q3 Round2 联合、RAW MAT 提取/M3R 和 Q4 Round2 复审；每项均有≥5项具体检查 |
| G4.5 结果人工判断 | ✅（Q2/Q3/Q4） | Q2、Q3 已裁决；Q4 已签核保留 C1–C3、删除 F1–F3 |
| G4 结果冻结 | ⚠️ 部分完成 | Q2/Q3/Q4 已完成人工 package sign-off 并生成 frozen_numbers；Q1 尚未进入冻结 |
| G5 论文分节 | 未进入 | Q2/Q3/Q4 已具备 writer package；仍需 Q1 选型、结果包与四问统一写作 |
| G6 独立审计层 | ❌（最终组装仍阻断） | consistency 已 PASS；completeness 因人工门禁 FAIL；QA 为 BLOCKED BEFORE FINAL QA |
| 最终组装 | **禁止** | `final_assembly_allowed=false` |

## 2. 分问题状态

| 问题 | 当前状态 | 已完成证据 | 当前边界/阻断 | 下一动作 |
|---|---|---|---|---|
| Q1 | [01] 候选方法池与 PoC 已补齐 | 9 张中文图、7 张表；寿命分布与重复策略 2,000 次 bootstrap；M1–M3 PoC 均通过 | 仅描述性；最终主线待模型者记录 | 完成方法选择裁决，再生成最终方法/结果材料 |
| Q2-A | [06] 数字已冻结（限定范围） | M1 `0.37169/0.27557`；M2 `0.36854/0.25102`；Secondary 未形成 M2 稳定优势 | M1 正文、M2 敏感性；不称 M2 显著优于 | 可进入论文分节写作 |
| Q2-B | [06] 数字已冻结（provisional） | P3 Train `0.34892/0.23383`；Primary `0.28927/0.22572`；Secondary `0.67781/0.63077` | P3 未获外部升级，只保留候选与 pilot 接口 | 可作为 Q2/Q4 边界写入论文 |
| Q3 | [06] 数字已冻结（needs_caution） | Secondary：M2-k5 `0.41930/0.06201`，M3R-k5 `0.49245/0.07202`，M2-k100 `0.46950/0.06908` | M3R-k5 未外部复现；k=100 只报告外部表现，不重选 k=5 | 可进入论文分节写作 |
| Q4 | [06] 数字已冻结（中等可信） | 1,775 条 provisional；3 个 pilot 排程代表点；M1/M2 PoC 均通过 | 只交付候选、风险边界和 pilot 接口；F1–F3 已删除 | 可进入论文分节写作 |

注：上述 `0.x/0.x` 对 Q2 为 `RMSE_log/MAE_log`，对 Q3 为“电芯等权寿命 RMSE_log / 电芯等权未来 SOH RMSE”；`log` 均指自然对数。

## 3. 当前有效关键产物

- 数据：`data/p0_audit_report.md`、`data/processed/p0_summary.json`、`workspace/data_clean/data_report.md`
- 方案：`B题_最新完整建模方案_V2.md`
- 符号/假设：`planning/symbol_table.md`、`planning/model_assumptions.md`
- Q1：`results/Q1/experiments/round1/q1_experiment_report_round1.md`、`robustness/Q1/q1_robustness_report.md`
- Q2：`results/Q2/experiments/round1/q2_experiment_report_round1.md`、`robustness/Q2/q2_robustness_report.md`、`results/Q2/experiments/q2b_primary_confirmation_round1/q2b_primary_confirmation_report.md`
- Q2 最终分析：`results/Q2/reports/q2_final_result_analysis.md`
- Q3：`results/Q3/experiments/round2_joint/run_summary.json`、`results/Q3/experiments/round3_raw_curve_challenger/run_summary.json`、`robustness/Q3/q3_robustness_report.md`、`results/Q3/reports/q3_final_result_analysis.md`
- Q4：`results/Q4/experiments/train_dry_run_round1/q4_train_only_dry_run_report.md`、`results/Q4/experiments/existing_policy_round2_m2k100/q4_existing_policy_report.md`、`methods/Q4/q4_pilot_protocol_round2_proposed.md`、`results/Q4/reports/q4_final_result_analysis.md`
- 细节交接：`paper/model_selection_early_warning_and_q4_details.md`

## 4. 人工门禁

| 文件 | 状态 | 必填内容 |
|---|---|---|
| `methods/Q2/decisions/robustness-checker_modeler_decision.md` | DECIDED | 限定范围内中等可信 |
| `methods/Q2/decisions/result-report-generator_modeler_decision.md` | DECIDED | M1 正文、M2 敏感性、P3 provisional、结束本轮 |
| `methods/Q3/decisions/robustness-checker_modeler_decision.md` | DECIDED | needs_caution；开发期 M3R-k5 只保留为早筛候选 |
| `methods/Q3/decisions/result-report-generator_modeler_decision.md` | DECIDED | 冻结后一次性运行 Secondary；不得回调 |
| `methods/Q3/decisions/secondary_external_result_modeler_decision.md` | DECIDED | M3R-k5 不获外部支持；k=100 仅报告外部表现；Q4 仅 pilot 接口 |
| `methods/Q2/decisions/solution-package-builder_modeler_decision.md` | DECIDED | 选 A：M1 正文、M2 敏感性、P3 pilot 接口 |
| `methods/Q3/decisions/solution-package-builder_modeler_decision.md` | DECIDED | 选 A：无泄漏联合流程与 M3R 外部未复现的完整结论 |
| `methods/Q1/decisions/method-selector_modeler_decision.md` | PENDING | 选择 Q1 的正文主线与辅助模块 |
| `methods/Q4/decisions/method-selector_modeler_decision.md` | DECIDED | M2 支持域筛选 + k=100 pilot；M1 baseline |
| `methods/Q4/decisions/final-method-explainer_modeler_decision.md` | DECIDED | Q4-A1/A3 必要；候选经真实 k=100 后方可升级 |
| `methods/Q4/decisions/solution-package-builder_modeler_decision.md` | DECIDED | 删除 F1–F3；保留 C1–C3；中等可信 |

已经生效的人工作用决定：`Q2-D02`（M1 正文、M2 敏感性、Q4 走 Q2-B）、`Q2-D03`（P3 冻结后一次 Primary 受限确认）、`Q2-D04`（P3 仅用于 Q4 provisional）、`Q2-D05/D06`（结束 Q2 本轮、限定中等可信）与 `Q3-D02/D03/D04`（k=5 筛查、k=100 正式校正、结束迭代并冻结）。Q3 Primary 结果只作为受限观察，不回调模型。

## 5. 三条论文交接规则

| 规则 | Q1 | Q2 | Q3 | Q4 |
|---|---|---|---|---|
| 最终方法解释存在 | ❌ | ❌ | ❌ | ❌ |
| 最终结果分析存在 | ❌ | ✅ | ✅ | ✅ |
| writer solution package 存在 | ❌ | ✅ | ✅ | ❌ |
| Ready for Writer | **否** | **否** | **否** | **否** |

## 6. 审计修复记录

1. 已把方案的 `log10(L)`/`10^z` 全部统一为实际代码口径 `ln(L)`/`exp(z)`。
2. 已修复 P0 逐行温度顺序检查与布尔字段解析，并完整重建依赖链。
3. 已为 Q1 增强脚本补哈希/门禁/日志，为 Q2/Q3 补 outer fold，为 Q3 补逐电芯 SOH 误差和失败原因。
4. 已把 Q2/Q3 稳健性摘要拆为独立对象，并为 Q3 补五套早期特征哈希。
5. 已新增 Q2/Q3 标准实验报告与人工结果裁决入口；Q2 已在 Q2-D05/D06 完成人工裁决，Q3 的双窗口冻结范围已追加至 Q3-D04。
6. P0 最终重建后已追溯重跑 Q2-B 与 Q4；二者当前输入/脚本哈希重新匹配，目标字段统一为 `ln(...)`，数值未变化。Q2-B 已内置 Windows joblib 核心探测的兼容处理，严格复跑无需额外环境变量。
7. 已按 Q2-D03 新建并执行 P3 Primary 一次受限确认：模型、特征、参数和评价规则均冻结；43 枚 Primary 电芯的观察结果已保存，但未被升级为最终通过。
8. 已按 Q3-D02/D03 新建并执行 M3 Primary 一次受限确认：k=5/100 的 alpha 和单调 SOH 模板均仅由 Train 构建；Primary 结果显示 k=5 的寿命误差更低、k=100 的未来 SOH 误差更低，未据此重选窗口。
9. 已按 Q2-D05/D06 与 Q3-D04 建立 Q4 k=100 pilot 冻结协议和登记表模板：新策略每条至少 3 枚不同物理电芯，完成 cycle 2–100 的 P0 兼容记录后才可产生冻结 Q3 证据。
10. 已从 1,775 条 provisional 中得到 15 条时间—P3 点预测非支配排程候选，并冻结快速端 `(6.0,65%,4.5)`、中间权衡 `(5.2,71%,3.5)`、寿命端 `(4.4,71%,3.5)` 三条代表策略；它们只供最小 9 枚电芯 pilot，不是最终推荐。
11. 已为 9 槽位生成登记表预检门禁：合法空计划通过；重复条码和“完成 k=100 但未完成 k=5”等状态矛盾会阻断。当前为 `all_slots_unassigned`，尚无 pilot 观察数据。
12. 已完成一次冻结 Secondary 压力测试：40 枚电芯、8 个策略组、2,000 次策略组块 bootstrap，独立复核 23/23 项通过。Q3-D07 已记录外部主张边界，Q2/Q3/Q4 最终结果分析已写入 `results/*/reports/`。
13. 建模者选择 Q2-A、Q3-A 的论文主张范围；Q2/Q3 writer package 已签核并冻结数值，分别见 `results/Q2/reports/frozen_numbers.json` 与 `results/Q3/reports/frozen_numbers.json`。

## 7. 推荐下一技能

- **当前动作**：Q1 完成方法选择与材料包；Q2/Q3/Q4 可在不改数字的前提下准备论文分节材料。
- **仍需人工门禁**：Q1 的 `method-selector_modeler_decision.md` 仍为 PENDING；完成对应方法、结果和材料包前，不生成其 `frozen_numbers`。
- **禁止项**：若需新增模型，只允许回到 Train 重开轮次，不得利用 Primary 或 Secondary 改选。
