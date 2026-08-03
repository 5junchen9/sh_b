# L1 曲线级数据整理报告

> **状态说明（2026-08-02）**：本文记录的是 P0 前的探索性整理。正式建模请使用 `processed/cycle_model_view.csv`、五套 `processed/early_features_k*.csv` 和 `processed/p0_summary.json`；下文全体样本 P99×5=100 的 `chargetime` 标记已被 Train-only 冻结上界 90.050737 取代，`early_cycle_features.csv` 仅保留为历史探索产物。论文写作细节统一见 `../paper/data_processing_and_split_details.md`。

## 结果

已从冻结的 124 条论文 Table 9 名册生成可复现的派生数据，原始 MAT 与 Excel 导出件均未改动。

| 输出 | 粒度 | 行数 | 用途 |
|---|---|---:|---|
| `processed/cell_labels.csv` | 物理电芯 | 124 | 唯一条码、论文分区、寿命、C1/Q1/C2 标签 |
| `processed/cycle_summary_clean.csv` | 片段—循环 | 100,501 | 已对齐的循环汇总；保留来源、片段和全局循环索引 |
| `processed/early_cycle_features.csv` | 物理电芯 | 124 | 前 100 个全局循环的均值与线性斜率候选特征 |
| `processed/data_preparation_summary.json` | 审计摘要 | 1 | 可机读的检查结果与风险 |

## 清洗与拼接规则

1. 仅保留论文 Table 9 中的 124 个条码；名册外 11 个条码不进入派生主表。
2. 寿命、分区和策略标签只使用论文 Table 9；本地同名字段仅作审计证据。
3. 保留 129 个本地片段。5 个重复条码按 MAT 中的真实批次日期排序，即 `data_1.xlsx（2017-05-12）→ data_2.xlsx（2017-06-30）`，并新增 `global_cycle_index`；不覆写原始 `cycle_index`。
4. 五个拼接电芯的片段汇总循环数均等于论文寿命减 1，拼接校验通过。
5. 对 `QDischarge`、`QCharge`、`IR`、`Tmax`、`Tavg`、`Tmin`、`chargetime` 增加字段级标记；不插补、不删除任何源值。七字段全零的结构性占位循环不进入特征聚合。
6. `chargetime` 采用不使用寿命标签的保守远端异常规则：剔除占位值后，以全体数据 P99 的 5 倍作为阈值。当前阈值为 100，异常值保留在循环表中并标记，但不进入候选特征。

## 检查结果

- 共 100,501 行正式名册内的循环汇总记录。
- 发现并标记 41 个七字段全零的结构性占位循环；其余核心字段未发现缺失或 NaN/Inf。
- 发现并标记 14 个 `chargetime` 远端异常循环；原值全部保留。
- 129 个片段均未发现本地 `cycle_index` 逆序。
- 5 个重复条码均已在特征表按物理电芯合并，最终特征表为 124 行。

## 仍需在特征扩展前完成的检查

当前状态为“原始曲线可按字段—循环掩码使用”。`cycles` 内的原始数组 `t/Qc/I/V/T/Qd` 已完成逐字段、逐循环全量扫描。因此：

- 当前 `early_cycle_features.csv` 仅使用已经审计的循环汇总字段，适合作为问题一基线与问题三的保守起点；
- 电压曲线、增量容量或时间积分特征必须同时使用 `outputs/data_audit/mat_deep_cycle_flags.csv` 的 `in_official_roster=1` 与 `usable_for_curve_features=1` 掩码；
- 寿命标签与分区只保存在 `cell_labels.csv`，候选特征列由 `processed/feature_columns.json` 明确列出，防止自动选列造成标签泄漏；
- `IR` 与 `chargetime` 的单位仍待由原始实验说明确认，暂不用于带单位的论文结论。
