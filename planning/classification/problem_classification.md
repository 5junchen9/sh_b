# L1 B题问题分类（G1已确认）

状态：`G1_confirmed_by_modeler_2026-08-02`。问题框架已由建模者确认；这不是 Q2/Q3 最终模型的自动锁定。

| 问题 | AI建议主类型 | 次类型 | 由输出决定的理由 | 主要风险 |
|---|---|---|---|---|
| Q1 | `data-analysis` | `evaluation` | 输出是分布、比较、规律和典型案例 | 相关性不可写成因果性 |
| Q2 | `data-analysis` | `prediction` | 以不同SOC区间倍率的影响机制、因素排序和交互作用为主，同时保留服务Q4的设计前预测代理 | 仅41枚Train电芯，必须分组验证，相关性不可写成因果性 |
| Q3 | `prediction` | `mechanism` | 输出是早期寿命估计与未来SOH轨迹 | 不能用截止点之后的信息或破坏掩码 |
| Q4 | `optimization` | `prediction` | 输出是可信域内的快充—寿命—SOH权衡策略 | 不能用参数范围代替可信域 |

## 已确认的分类字段

### Q1

- `modeler_chosen_type`: `data-analysis`
- `framing_rationale`: 题目要求数据整理、策略寿命差异和典型案例；建模者明确此类可从题意直接判定，无需额外询问。

### Q2

- `modeler_chosen_type`: `data-analysis`（机制导向的统计解释）
- `framing_rationale`: 建模者确认：“题目里要求重点分析不同SOC区间内充电电流倍率对电池寿命的影响，我觉得是充电策略影响机制。”

### Q3

- `modeler_chosen_type`: `prediction`
- `framing_rationale`: 建模者确认寿命/SOH预测精度与早期指标可解释性“二者兼顾”。

### Q4

- `modeler_chosen_type`: `optimization`
- `framing_rationale`: 建模者确认交付为“Pareto 权衡方案集”。

## 候选方法族（未选型）

- Q1：稳健描述统计、分组比较、相关/秩相关、低复杂度可解释分割。
- Q2：正则化回归、可解释策略参数重编码、policy-group CV、低自由度交互。
- Q3：正则化寿命预测、残差校正、SOH模板/函数轨迹、低维RAW challenger。
- Q4：可信域约束、多目标Pareto、邻域支持和保守决策。

## 不适合直接采用的方向

- 在 Primary 上反复挑模型或超参数；
- 使用高维 RAW 特征自动筛选；
- 将Q2的策略相关解释写成严格因果结论；
- 在未经Q3确认时把连续新策略写成已验证最优策略。

下一技能为 `related-paper-analyzer`；G1 已通过。Q2/Q3 的候选方法仍须完成 PoC、受限确认和后续人工锁定。
