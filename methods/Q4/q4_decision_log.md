# Q4 决策日志

> 模型者决策的规范、追加式记录；论文和交接材料中的裁决依据须可追溯至本文件。

---

### Q4-D01 | method_choice | 2026-08-03T13:09:00+08:00 | mode: learning

- **options_considered**: M1 已有策略的观察性多目标参照 / M2 Train-only 双空间支持域筛选与 k=100 pilot 闭环
- **evidence**: `methods/Q4/q4_method_candidates.md`：M2 的 Train-only 流程筛出 1775 个 `Q2_provisional` 候选，最低 bootstrap 支持率为 0.800；`results/Q4/experiments/train_dry_run_round1/q4_train_only_dry_run_report.md`
- **ai_suggestion**: WITHHELD_IN_LEARNING_MODE_UNTIL_HUMAN_RATIONALE
- **modeler_decision**: M2（支持域筛选 + k=100 pilot闭环）为 Q4 主线；M1 仅作为 baseline，不退回 M1。（CHOSEN）
- **modeler_rationale**: 选 M2，因为 Train-only 筛出 1775 个候选且最低支持率为 0.800；M1不能生成受控候选策略，仅作为对照。置信度：中等。
- **confidence**: 中等
- **supersedes**: —

---

### Q4-D02 | assumption_necessity | 2026-08-03T13:16:00+08:00 | mode: learning

- **options_considered**: 将 Q4-A1/Q4-A3 定为必要假设，或将其降为简化假设；候选仅筛选后升级，或须经真实 `k=100` 确认后升级。
- **evidence**: `planning/model_assumptions.md`（Q4-A1/Q4-A3）；`results/Q4/experiments/train_dry_run_round1/q4_train_only_dry_run_report.md`（支持率阈值 0.800）；`methods/Q4/q4_decision_log.md`（Q4-D01）。
- **ai_suggestion**: WITHHELD_IN_LEARNING_MODE
- **modeler_decision**: Q4-A1、Q4-A3均为必要假设；候选只在双空间支持通过、支持率≥0.800、且完成每点不少于 3 枚电芯至 `k=100` 的真实确认后升级；之前不称优或推荐。
- **modeler_rationale**: Q4-A1、Q4-A3均为必要假设；只有双空间支持通过、支持率≥0.800，并完成每点不少于3枚电芯至k=100的真实确认后，候选才可升级，之前不称优或推荐；最终可信度：中等。
- **confidence**: 中等
- **supersedes**: —
