# Q1 决策日志

> 模型者决策的规范、追加式记录；论文和交接材料中的裁决依据须可追溯至本文件。

---

### Q1-D01 | method_choice | 2026-08-03T13:40:00+08:00 | mode: learning

- **options_considered**: M1 电芯级描述统计 / M2 策略级聚合比较 / M3 Train–Primary 重复策略一致性核对。
- **evidence**: `methods/Q1/q1_method_candidates.md`：68 个策略中有 27 个重复策略；19 对 Train–Primary 重复策略，Pearson=0.903、绝对差中位数 97.0 cycles；`robustness/Q1/q1_robustness_report.md`。
- **ai_suggestion**: WITHHELD_IN_LEARNING_MODE_UNTIL_HUMAN_RATIONALE
- **modeler_decision**: Q1 采用 M2 策略级聚合为正文主线，M1 电芯级分析作为基础描述；M3仅作跨分区一致性核对。（CHOSEN）
- **modeler_rationale**: Q1 采用 M2 策略级聚合为正文主线，M1 电芯级分析作为基础描述；理由：27 个重复策略组和 19 对跨分区重复策略支持策略级对照，但仅作观察性比较；可信度：中等。
- **confidence**: 中等
- **supersedes**: —

---

### Q1-D04 | assumption_necessity | 2026-08-03T13:55:00+08:00 | mode: learning

- **options_considered**: Q1-A1 必要或简化；Q1-A2 必要或简化；将 M3 秩相关区间跨 0 作为限制或稳定排序证据。
- **evidence**: `planning/model_assumptions.md`（Q1-A1/Q1-A2）；`robustness/Q1/q1_robustness_report.md`（Spearman 95% 区间 [-0.0231, 0.8791]）。
- **ai_suggestion**: WITHHELD_IN_LEARNING_MODE
- **modeler_decision**: Q1-A1 为必要假设，Q1-A2 为简化假设；只比较 `n≥2` 策略组，同时报告样本数与寿命范围；M3 的 Spearman 区间跨 0 只写为限制。
- **modeler_rationale**: Q1-A1 为必要假设，Q1-A2 为简化假设；Q1 合格结果须仅比较 n≥2 的策略组、同时报告样本数与寿命范围，并把 M3 的 Spearman 区间跨0写为限制而非稳定排序证据；可信度中等。
- **confidence**: 中等
- **supersedes**: —

---

### Q1-D02 | result_verdict | 2026-08-03T13:48:00+08:00 | mode: learning

- **options_considered**: M2 正文主线 / M1 基础描述 / M3 稳定排序方法或仅一致性核对；结束本轮或继续迭代。
- **evidence**: `results/Q1/experiments/round1/q1_experiment_report_round1.md`；`robustness/Q1/q1_robustness_report.md`：M2 有 27 个重复策略组，M3 Pearson=0.9029，Spearman 95% 区间 [-0.0231, 0.8791]。
- **ai_suggestion**: WITHHELD_IN_LEARNING_MODE
- **modeler_decision**: M2 选为正文主线，M1保留为基础描述，M3仅保留为一致性核对、不作为稳定策略排序方法；本轮结束并进入写作材料整理。
- **modeler_rationale**: M2有27个重复策略组支撑，M3虽 Pearson=0.9029，但 Spearman 的95%区间跨0，不能支持稳定排序或因果结论。
- **confidence**: 中等
- **supersedes**: —

---

### Q1-D03 | confidence | 2026-08-03T13:48:00+08:00 | mode: learning

- **options_considered**: 高 / 中等 / 需谨慎。
- **evidence**: `robustness/Q1/q1_robustness_report.md`：寿命分布 2,000 次 bootstrap；19 对重复策略的 Spearman 95% 区间跨 0。
- **ai_suggestion**: WITHHELD_IN_LEARNING_MODE
- **modeler_decision**: Q1 可信度中等。
- **modeler_rationale**: M2 有重复策略组支撑，且个体分布和策略组对照可复核；但重复策略的秩相关区间跨 0，故不升级为高可信排序或因果结论。
- **confidence**: 中等
- **supersedes**: —
