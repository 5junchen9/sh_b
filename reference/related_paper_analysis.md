# 已提供文献的可迁移性分析

分析日期：2026-08-02  
输入目录：`papers/`（项目内指向 `reference/` 的目录链接）  
前置工件：`planning/parse/problem_parse.json`、`planning/classification/problem_classification.json`（G1 已确认）  
范围：只分析用户已放入项目的原始 PDF；不联网检索、不补造文献信息、不替代后续方法选型。

## 1. 已审阅文件

| 文件 | 可确认的可迁移线索 | 适合支持 | 不应直接照搬 |
|---|---|---|---|
| `1710560890-r2I8.pdf` | 原始数据研究及补充材料；包含 Table 9、两段式快充协议、早期寿命预测与多类特征讨论 | 124 条码/寿命/策略标签、80%后1C至3.6 V再恒压的参考研究协议、早期预测的研究动机 | 原文完整特征库或模型不能替代本题的 P0 掩码、分组验证与 V2 规则 |
| `s41560-019-0356-8.pdf` | 与上项同一原始研究的主文/片段版本 | 原文正文交叉核对 | 不作为独立参考文献重复引用 |
| `Ageing mechanisms in lithium-ion batteries.pdf` | 老化机制综述 | Q1/Q2 的谨慎机理背景 | 不可把背景机制转写成本数据已识别的因果效应 |
| `Differential voltage analysis as a tool for analyzing inhomogeneous aging A case study for LiFePO4Graphite cylindrical cells.pdf` | 差分电压与非均匀老化分析 | Q3 低维 RAW/DVA challenger 的动机 | 不可绕过 RAW 逐循环掩码，也不可直接搬用高维特征集 |
| `End-of-life prediction of a lithium-ion battery cell based on mechanistic aging models of the graphite electrode.pdf` | 机理化 EOL 预测 | Q3 轨迹/EOL写作中的边界和比较视角 | 当前缺少该类材料参数与实验条件，不能改造成主模型 |
| `EIS study on the formation of solid electrolyte interface in Li-ion battery.pdf` | EIS/SEI 背景 | `IR` 解释的背景提示 | 本项目 `IR` 不可等同于 EIS 谱参数 |
| 两篇 `Calendar Aging...pdf` | 日历老化、材料/工况影响 | 老化机制与外推风险背景 | 不可迁移其数值阈值至循环快充数据 |
| `Understanding solid electrolyte interface film formation on graphite electrodes.pdf` | SEI 形成背景 | 初始循环现象的定性讨论 | 不可推出本项目 cycle 1/2 的定量因果结论 |
| `Variation_of_coulombic_efficiency_versus.pdf` | 库仑效率与协议/电压关系背景 | 快充风险的背景线索 | 库仑效率不是本项目正式主特征，不能引入外部阈值 |

## 2. 已核验的协议来源

- `B.docx` 题面给出两段倍率、80% SOC 分界，以及80%后统一1C CC-CV/C/50截止。
- **3.6 V 不在题面中。** `1710560890-r2I8.pdf` 第 4 页补充图 2 说明该原始研究的数据集在80% SOC 后以1C充至3.6 V、再于3.6 V恒压充电，并将该上限表述为制造商限制。
- 因而 3.6 V 只能在论文中作为“参考研究的数据采集协议/可信范围背景”，不能伪装成赛题给定的优化硬约束。

## 3. 按子问题的可迁移线索

### Q1：整理与初步差异

- 使用原始研究的 Table 9 和协议说明核对正式标签与策略含义。
- 用老化综述解释“同一策略的寿命仍可能不同”，但正文只报告本地描述统计和重复策略证据。

### Q2：机制导向的统计解释

- 题面与建模者确认要求分析不同 SOC 区间倍率、切换 SOC、充电时间及交互作用。
- 文献可支撑“这些因素值得研究”的背景，**不能**把观察性分区比较升级为已识别因果机制。
- 可迁移的是低自由度、可解释的参数化和严谨验证思想；最终系数、显著性与排序只能来自本项目 Train-only PoC。

### Q3：预测精度与可解释性兼顾

- 原始研究支持早期循环数据预测寿命这一任务动机。
- DVA 文献只支持保留一个受掩码控制的低维 RAW challenger；它不支持把 1000 点 RAW 序列整体塞入小样本主模型。
- 机理 EOL 文献用于比较预测边界：本项目应优先使用已经具备的双 SOH、五个早期窗口和可重现误差，而非虚构材料参数。

### Q4：Pareto 权衡方案集

- 原始研究协议可约束解释范围，例如0--80%两段倍率与80%后统一尾段；它不是唯一最优或安全阈值的依据。
- 当前文献没有提供可直接迁移的本题最低寿命、最低SOH或最大时间硬门槛；按 V2 保留可信域内 Pareto 与 SOH 风险叠加，不借文献捏造阈值。

## 4. 必须随方法选择带走的限制

1. `IR=Ω`、`chargetime=min` 已确认，但 IR 测量时点与实际充电时间的起止/CV覆盖尚不清楚。
2. Q2 的“影响机制”是可解释统计关联；数据不足以排除批次、初始状态与未观测条件的混杂。
3. Primary 已有探索暴露，只能确认冻结候选；Secondary 不得参与选型或调参。
4. 文献中的模型和参数不应自动进入代码；所有特征、验证和超参数仍需由 Train-only PoC 决定。

## 5. 建议后续技能

`method-selector`：在 V2 的既定候选路线内，为 Q2 形成“机制解释模型 + Q4代理模型”的比较表，为 Q3 形成“预测精度 + 特征可解释性”的候选比较表；不锁定最终模型。
