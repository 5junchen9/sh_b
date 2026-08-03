# Q1 写作解决方案包：电芯差异与策略级观察性对照

> **状态**：主张范围已签核；数字已冻结，可供论文写作。

## 0. 快速索引

- **主线**：M2 策略级聚合；M1 解释电芯差异；M3 仅作跨分区核对。<!-- from Q1-D02 -->
- **关键结果**：124 枚电芯寿命中位数为 736.50 cycle；68 个策略中有 27 个重复策略；19 对跨分区重复策略的 Spearman 区间跨 0。
- **可信度**：中等。<!-- from Q1-D03 -->
- **结论边界**：可做本数据集内观察性策略对照，不做因果解释或稳定全排序。

## 1. 论文写作内容

### 1.1 电芯级差异（M1）

报告寿命均值 801.64 cycle、中位数 736.50 cycle、IQR [498.75, 946.50] cycle、范围 [148, 2237] cycle。2,000 次 bootstrap 下中位数 95% 区间为 [651.00, 825.00] cycle。结论是：数据有明显右偏和个体异质性。

### 1.2 策略级对照（M2）

将清洗后的记录按 `policy_table9` 聚合。只有策略内 \(n\ge2\) 的组进入正文比较，并同时报告 \(n_p\)、平均寿命和范围。68 个策略中有 27 个重复策略；其平均寿命从 546.5 到 2083.0 cycle。这里的“较好”只表示已观测策略组的描述性整体表现。

长、短寿命典型案例可使用 `3.6C(80%)-3.6C`（代表电芯 2160 cycle）与 `5.4C(60%)-3.6C`（代表电芯 559 cycle），并在图注注明它们是重复策略组案例，不是因果或最优策略结论。

### 1.3 重复策略核对（M3）

19 对 Train–Primary 重复策略的 Pearson 为 0.9029，而 Spearman 为 0.5514、95% 区间 [-0.0231, 0.8791]；平均绝对差为 119.50 cycle。可写“线性一致性迹象伴随明显差异”，不可写“策略排序稳定”或“策略可以完全迁移”。<!-- from Q1-D04 -->

## 2. 图表与表格安排

| 图表 | 文件 | 论文位置 | 作用 |
|---|---|---|---|
| Q1-F1 | `results/Q1/experiments/round1/figures/q1_01_lifetime_distribution.png` | Q1.1 | 寿命右偏与个体差异。 |
| Q1-F2 | `results/Q1/experiments/round1/figures/q1_07_policy_lifetime_top_bottom.png` | Q1.2 | 重复策略组的长短寿命与组内范围；M2 主图。 |
| Q1-F3 | `results/Q1/experiments/round1/figures/q1_09_long_short_soh_band.png` | Q1.2 | 典型策略组的 SOH 中位轨迹和区间。 |
| Q1-F4 | `results/Q1/experiments/round1/figures/q1_05_train_primary_repeated_policy_agreement.png` | 附录/稳健性 | M3 一致性核对及其限制。 |

| 表格 | 文件 | 论文位置 | 作用 |
|---|---|---|---|
| Q1-T1 | `results/Q1/experiments/round1/tables/q1_cell_level_summary.csv` | Q1.1 | 电芯级寿命统计。 |
| Q1-T2 | `results/Q1/experiments/round1/tables/q1_strategy_lifetime_summary_enhanced.csv` | Q1.2 | 策略参数、寿命与时间摘要。 |
| Q1-T3 | `results/Q1/experiments/round1/tables/q1_long_short_strategy_comparison.csv` | Q1.2 | 典型长短寿命策略对照。 |

## 3. 主张清单

| 编号 | 可保留主张 | 证据 |
|---|---|---|
| C1 | 124 枚电芯存在明显个体寿命异质性和右偏长尾。 | M1 分布与 2,000 次 bootstrap。 |
| C2 | 具备重复电芯支撑的策略可作本数据集内观察性整体对照。 | 27 个重复策略组及 M2 聚合表。 |
| C3 | 跨分区重复策略有线性一致性迹象，但不支持稳定排序。 | Pearson、Spearman 区间和绝对差。 |

| 编号 | 必须删除的过度表述 | 原因 | 人工裁决 |
|---|---|---|---|
| F1 | “某一充电倍率或 SOC 切换点导致寿命更长。” | 观察性数据无法消除组合、批次与未观测混杂。 | drop <!-- from Q1-D05 --> |
| F2 | “M3 给出稳定的策略排序。” | Spearman 95% 区间跨 0。 | drop <!-- from Q1-D05 --> |
| F3 | “单枚电芯策略代表策略总体。” | 缺乏组内重复。 | drop <!-- from Q1-D05 --> |

## 4. 写作顺序

1. 用 M1 分布图回答“是否存在个体差异”；
2. 用 M2 重复策略图和对照表回答“哪些已观测策略整体更优”；
3. 用 M3 附录图说明跨分区核对和边界；
4. 以非因果、非全排序的限制结束 Q1。

## 5. 来源

- 最终结果：`results/Q1/reports/q1_final_result_analysis.md`
- 最终方法：`methods/Q1/q1_final_method_explanation.md`
- 稳健性：`robustness/Q1/q1_robustness_report.md`
- 决策：`methods/Q1/q1_decision_log.md`（Q1-D01 至 D04）

## 6. 完整性

- [x] 方法、结果、稳健性与图表可追溯
- [x] 所有正文策略案例限定为 `n≥2`
- [x] 主张范围已签核；数值见 `results/Q1/reports/frozen_numbers.json`
