# Q1 首轮描述性分析报告

> 状态：`complete_descriptive_baseline_not_a_final_model`  
> 数据版本：P0 passed；脚本与输入 SHA-256 见 `run_summary.json`。  
> 范围：本报告只描述已观察到的分布与重复策略一致性，不给出因果效应、最终预测模型或最优策略。

## 1. 输入与可复现性

- 官方电芯：124 枚；`cell_labels.csv` 中条码唯一。
- P0 循环长表：99,279 行；仅保留官方寿命端点前循环。
- 脚本：`code/Q1/q1_baseline.py`、`code/Q1/q1_enhanced.py`。
- 随机种子：20260802（图形抖动与结果不依赖随机抽样）。
- 运行状态：成功；合计生成 9 张 PNG 图和 7 张 CSV 表。

## 2. 寿命分布与官方分区

全体 124 枚电芯的循环寿命均值为 801.64 cycles，中位数为 736.5 cycles，四分位数为 498.75 和 946.5 cycles，范围为 148–2237 cycles，显示出明显右偏和长寿命尾部。

| 分区 | 电芯数 | 平均寿命 | 中位数 | 标准差 | 范围 |
|---|---:|---:|---:|---:|---:|
| Train | 41 | 673.76 | 527.0 | 327.14 | 300–2160 |
| Primary | 43 | 709.28 | 561.0 | 395.81 | 148–2237 |
| Secondary | 40 | 1032.00 | 964.5 | 308.60 | 541–1935 |

Secondary 的观测寿命整体更高，但分区同时伴随策略集合与实验批次的差异；该现象只能作为跨批次分布偏移的描述，不能解释为“分区/批次导致寿命变化”。

## 3. 策略参数与理论时间

已绘制 C1、切换 SOC（Q1）和 C2 与寿命的散点图，以及理论 `tau_0_80` 与寿命的散点图。`tau_0_80` 按两阶段恒流公式计算，范围仅反映 0–80% SOC 的理论 CC 时间，不等同于循环汇总中的 `chargetime`。

这些图说明三个策略参数受实验设计约束，不能把单变量散点趋势或后续多元系数直接解释为相互独立的物理贡献。Q2 必须使用策略分组验证和低自由度解释。

## 4. Train–Primary 重复策略

Train 与 Primary 条码不重叠，但共有 19 种完全相同的 Table 9 策略；Primary 中 23 枚电芯属于这些 seen-policy。按分区内同策略寿命均值比较：

| 指标 | 数值 |
|---|---:|
| Pearson 相关 | 0.902856 |
| Spearman 相关 | 0.551361 |
| 绝对差中位数 | 97.0 cycles |
| 绝对差均值 | 119.5 cycles |
| 最大绝对差 | 349.0 cycles |

策略均值在两组之间具有较高线性相关，但 Spearman 相关较低且存在最高 349 cycles 的差异。这说明策略携带稳定统计信息，但不能充分决定个体寿命；后续必须同时保留 Q2 的设计前策略模型和 Q3 的运行后个体化校正。

## 5. 代表性 SOH 案例

为避免仅挑选单一极端电芯，图中从至少有两枚电芯支持的策略组中自动选择寿命均值最高与最低的组，再取最接近组均寿命的电芯：

| 案例 | 策略 | 条码 | 官方寿命 |
|---|---|---|---:|
| 重复策略长寿命案例 | `3.6C(80%)-3.6C` | `EL150800460486` | 2160 |
| 重复策略短寿命案例 | `5.4C(60%)-3.6C` | `EL150800463871` | 559 |

曲线使用 `SOH_nom=QDischarge/1.1`，横坐标为 `global_cycle_index/cycle_life_table9`。该图仅为轨迹形状对照，不代表所有同策略电芯的确定性退化规律。

## 6. 产物

图表：

- `figures/q1_01_lifetime_distribution.png`
- `figures/q1_02_lifetime_by_dataset.png`
- `figures/q1_03_strategy_parameters_vs_lifetime.png`
- `figures/q1_04_theory_time_vs_lifetime.png`
- `figures/q1_05_train_primary_repeated_policy_agreement.png`
- `figures/q1_06_representative_soh_trajectories.png`

表格：

- `tables/q1_cell_level_summary.csv`
- `tables/q1_dataset_lifetime_summary.csv`
- `tables/q1_policy_summary.csv`
- `tables/q1_train_primary_repeated_policy.csv`
- `tables/q1_representative_soh_cases.csv`

## 7. 不能越过的结论边界

1. 不将策略参数、理论时间或分区与寿命的相关性表述为因果效应。
2. 不把 Primary 写成完全独立测试集；其只能用于后续冻结候选的一次受限确认。
3. `chargetime` 单位已确认是 min，`IR` 单位已确认是 Ω；但 `chargetime` 的起止点及 CV 覆盖尚未有字段说明，故不把它与理论 `tau_0_80` 混为同一时间变量，也不作题外安全阈值解释。
4. 本轮不选择 Q2/Q3 最终模型；下一步仅允许建立 Train-only 候选 PoC。

## 8. 初稿补充输出（2026-08-02）

为直接回答题目中的“典型长短策略”和“实测充电时间”两项，新增了三张策略层图和两张汇总表。它们仍属于描述性基线，不改变本报告的非因果解释范围：

- `figures/q1_07_policy_lifetime_top_bottom.png`：只对策略内 `n≥2` 的重复策略排序，并给出策略内最小–最大寿命范围；用于选择典型长寿命和短寿命策略。
- `figures/q1_08_observed_charge_time_vs_lifetime.png`：使用第 2–20 圈实测充电时间中位数，而不是只使用理论 `tau_0_80`；用于回答“充电时间角度”的初步解释。
- `figures/q1_09_long_short_soh_band.png`：对典型长短策略分别计算策略内 SOH 中位曲线和 10–90% 区间；比单电池轨迹更适合作为正文图，但样本量仍需在图注中说明。
- `tables/q1_strategy_lifetime_summary_enhanced.csv`：策略级寿命、C1、Q1、C2、实测充电时间和理论时间汇总。
- `tables/q1_long_short_strategy_comparison.csv`：典型长寿命策略 `3.6C(80%)-3.6C` 与典型短寿命策略 `5.4C(60%)-3.6C` 的两行对照表。

完整的逐图阅读说明和初稿可直接使用的结果段落见 `results/Q1/experiments/round1/figures/README.md` 与 `results/Q1/q1_paper_draft_notes.md`。

## 9. 运行核验清单

1. ✅ P0 门禁为 `pass`，输入规模为 124 枚电芯、99,279 行循环视图。
2. ✅ 基线与增强脚本的 SHA-256 均与各自运行摘要一致。
3. ✅ 9 张 PNG 与 7 张 CSV 全部存在且非空，增强摘要列出的 5 个新增产物均可解析。
4. ✅ 代表性策略由 `n≥2` 的策略自动选择，不是人工挑选单枚极端电芯。
5. ✅ 实测充电时间图使用第 2–20 圈中位数，单位为 min；理论时间另列。
6. ✅ Primary/Secondary 只参与 Q1 描述性汇总，没有进入 Q2/Q3 的训练与调参。
7. ✅ 所有新增图均为中文标题、坐标、图例和单位。
8. ✅ 已按 baseline→enhanced 顺序在 `-W error` 下完整复跑。
