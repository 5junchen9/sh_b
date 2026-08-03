# Q2 主效应 Ridge 的因素排序与解释性补充设计

## 目的

本补充不重新选模型、不使用 Primary/Secondary，也不把系数解释为因果贡献。它仅为已冻结的 Q2-A 正文基线 M1 生成两类可追溯解释证据：

1. 在 Train 全量上按既有内层 `policy_table9` 分组规则选择正则化强度后，报告标准化系数及其策略组重抽样符号稳定率；
2. 对 `C1`、`Q1_percent`、`C2` 分别做删一变量的策略分组嵌套 OOF 比较，报告相对完整 M1 的 $\Delta MAE_{log}$ 与 bootstrap 区间。

## 冻结条件

- 标签：`ln(cycle_life_table9)`；反变换仅用 `exp`。
- 输入：只读 `data/processed/cell_labels.csv` 与 `p0_summary.json`；只筛选 41 枚 Train 电芯和 40 个策略组。
- 验证：完整 M1 与每个删一变量模型共用 policy-group 外层折；每个外层训练折再以最多 4 折 group CV 选 alpha。
- 重抽样：2,000 次以策略组为单位的 paired bootstrap，负的 $\Delta MAE_{log}=MAE_{ablated}-MAE_{full}$ 不应被解释为“删除变量更好”，而需结合区间谨慎说明。
- 输出：CSV、JSON、中文 PNG/SVG、日志与输入/脚本 SHA-256；不改动现有 Q2 round1 数字。

## 非目标

- 不计算因果效应、显著性或“贡献百分比”。
- 不将 M2 重新升格为正文模型。
- 不将本补充作为 Q4 的最终寿命代理。
