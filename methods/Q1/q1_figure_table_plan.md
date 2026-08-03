# Q1 图表与表格计划（开发期）

> **状态**：开发期可用；正式论文冻结后需重新确认图型和主张。以下不把描述性图表升级为因果证据。

## 1. 图形清单

### Type 2：比较/描述图

| ID | 图题 | 用途 | 来源 | 开发稿位置 | 状态 | 建议图注 |
|---|---|---|---|---|---|---|
| Q1-F1 | 124 枚电芯的循环寿命分布 | 展示长尾与寿命尺度 | `results/Q1/experiments/round1/figures/q1_01_lifetime_distribution.png` | 数据审计后 | 存在 | “124 枚正式电芯的 Table 9 循环寿命分布；用于说明为何同时报告对数尺度误差与 MAE。” |
| Q1-F2 | Train–Primary 重复策略一致性 | 展示相同策略跨分区的描述性一致性和个体差异 | `results/Q1/experiments/round1/figures/q1_05_train_primary_repeated_policy_agreement.png` | Q1 结果 | 存在 | “重复策略按策略聚合后的寿命比较；仅为描述性重复证据。” |
| Q1-F3 | 代表性 SOH 轨迹 | 解释 Q3 需要运行后校正 | `results/Q1/experiments/round1/figures/q1_06_representative_soh_trajectories.png` | Q1→Q3 过渡 | 存在 | “不同寿命样本的 SOH 轨迹案例；不作为对全部电芯的一般化曲线。” |

### Type 1：诊断图（不进入正式正文）

| ID | 图题 | 诊断目的 | 来源 | 状态 |
|---|---|---|---|---|
| Q1-D1 | 理论充电时间与寿命 | 检查理论时间与实测/寿命关系的离散程度 | `results/Q1/experiments/round1/figures/q1_04_theory_time_vs_lifetime.png` | 存在 |
| Q1-D2 | 实测充电时间与寿命 | 检查 `chargetime` 字段是否可直接解释 | `results/Q1/experiments/round1/figures/q1_08_observed_charge_time_vs_lifetime.png` | 存在 |

### Type 4：附录图

| ID | 图题 | 附录用途 | 来源 | 状态 |
|---|---|---|---|---|
| Q1-A1 | 按分区寿命分布 | 展示分区差异，避免将其归为批次因果 | `results/Q1/experiments/round1/figures/q1_02_lifetime_by_dataset.png` | 存在 |
| Q1-A2 | 策略参数与寿命散点 | 补充策略覆盖范围 | `results/Q1/experiments/round1/figures/q1_03_strategy_parameters_vs_lifetime.png` | 存在 |

## 2. 表格清单

| ID | 表题 | 类型 | 来源 | 开发稿位置 | 状态 |
|---|---|---|---|---|---|
| Q1-T1 | 电芯级数据与寿命摘要 | data_summary_table | `tables/q1_cell_level_summary.csv` | 数据审计 | 存在 |
| Q1-T2 | 分区寿命汇总 | data_summary_table | `tables/q1_dataset_lifetime_summary.csv` | Q1 结果 | 存在 |
| Q1-T3 | Train–Primary 重复策略统计 | comparison_table | `tables/q1_train_primary_repeated_policy.csv` | Q1 结果 | 存在 |

## 3. 风险与冻结条件

- 寿命散点与分区图仅支持描述性比较，不能作为“倍率导致寿命变化”的图证。
- 正式 Type 3 论文图、图型及单一核心主张必须在全题方法和结果冻结后由模型负责人确认。
- 现有图均为中文输出；正式排版前仍须检查字号、图注和色盲可读性。
