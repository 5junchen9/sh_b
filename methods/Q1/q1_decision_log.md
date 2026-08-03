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
