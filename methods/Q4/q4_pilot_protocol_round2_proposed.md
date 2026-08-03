# Q4 两层 Pilot 协议（Round 2/3 证据后的操作性提案）

> **状态：operational_proposal_not_human_gate_decision。** 本文件不修改既有人工冻结记录；它把最新 Q3 实验的可执行输入写清，以便收到新策略数据时不临时改口径。

## 1. 上游候选与角色

| 阶段 | 当前候选 | 依据 | 允许的输出 |
|---|---|---|---|
| k=5 | M3R：策略＋12 项早期特征＋3 项审计 RAW 充电电压特征的 Ridge | SOH RMSE 对 M2-k5 的策略等权差值 `-0.00528`，95% 区间 `[-0.00908,-0.00161]` | 风险筛查、检测优先级与字段可用率；不升级 Pareto |
| k=100 | M2：12 项早期运行特征 Ridge | Train 内寿命 `RMSE_log=0.23174`、SOH RMSE=`0.03475`，为当前最低误差组合 | 运行后寿命/SOH 校正候选；仍非独立外部最终结论 |

M3R-k5 的寿命差值区间仍跨 0，故不将其解释为寿命的稳定优胜；M2-k100 也尚待冻结后的 Secondary 压力测试。二者是时间—精度的两层候选，并非同一任务的单一冠军。

## 2. Pilot 数据的新增要求

在原 `q4_k100_pilot_protocol.md` 的 cycle 2–100 P0 字段之外，k=5 筛查还必须保留每循环原始：

- `t/Qc/I/V/T/Qd` 六字段；
- `(source_file,batch_index,cycle_index)` 或等价可追溯键；
- 不得排序 `t`，并继承同一六字段深层审计和字段—循环掩码；
- 仅对 `I>0.1 A` 的充电点计算 `raw_charge_v_mean_mean`、`raw_charge_v_p95_mean`、`raw_charge_v_p95_slope`。

若 RAW 曲线无法满足该审计/连接条件，k=5 状态记为 `incomplete_raw_screen`，但仍可继续收集到 k=100；不得用插补 RAW 特征假装完成 M3R。

## 3. 固定处理顺序

```text
Q2 provisional 新策略（≥3 枚新物理电芯）
  → P0 长表 + 六字段 RAW 审计
  → cycle 2–5：M3R-k5 筛查（仅预警/调度）
  → cycle 2–100：M2-k100 校正候选
  → 每电芯和策略级归档掩码、预测、样本量
  → 真实寿命/SOH 到达后按电芯等权评价
  → 仅在模型与评价规则正式冻结后实施一次 Secondary 压力测试
```

任何阶段都不能：用 pilot/Primary 重新选择特征、窗口、Ridge alpha、P3、5-NN 阈值，或将 Q2-only 候选写为正式 Pareto。

## 4. 对 Q4 输出的影响

- 既有策略：可使用 `existing_policy_round2_m2k100` 作为开发池案例，标注 `development_pool_non_dominated_not_external`。
- 新策略：没有真实 pilot 时维持 `Q2_provisional`；有 k=5 只得到筛查状态；到 k=100 才能获得完整 Q3 预测记录。
- 正式新策略 Pareto 仍需要：至少 3 枚电芯的真实 early data、冻结 Q2/Q3 流水线、保守下界定义和 Secondary 一次性压力测试；本提案不越过这些门槛。
