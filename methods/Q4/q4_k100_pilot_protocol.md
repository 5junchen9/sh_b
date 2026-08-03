# Q4：`k=100` 新策略 Pilot 冻结协议

> **版本**：1.0（2026-08-02）  
> **状态**：可执行设计；尚无新策略 pilot 数据，不能产生正式 Pareto 或最优策略。  
> **上游冻结来源**：`Q2-D05/D06`、`Q3-D04`、`results/Q4/experiments/train_dry_run_round1/`。

## 1. 目的和边界

本协议把 Q4 的 `Q2_provisional` 策略转为可审计的物理试验候选：每个被选策略至少由 **3 枚不同物理电芯**运行至第 100 循环。运行至第 5 循环时先按冻结 Q3 `k=5` 输出早期筛查信息；第 100 循环时再用冻结 Q3 `k=100` 形成正式运行后寿命/SOH 校正证据。

它的目的不是从 1,775 条候选中直接寻找“预测寿命最高”的策略。P3 的寿命预测只用于候选提名和试验排程；pilot 的真实早期数据才可进入 Q3 确认。未运行或未通过本协议的候选始终保持 `Q2_provisional`。

## 2. 不得改变的输入和规则

| 项目 | 冻结口径 |
|---|---|
| 候选池 | `tables/q4_q2_provisional_candidates.csv` 的 1,775 条 `Q2_provisional` 记录 |
| 策略变量 | `C1`（C）、`Q1_percent`（% SOC）、`C2`（C）；`Q1=80%` 时采用 `C2=C1` 的单阶段分支 |
| 快充时间 | `tau_0_80_min`，单位 min；仅为 0–80% 恒流理论时间，不等同完整实测 CC-CV 时间 |
| 可信域 | raw/SOC 双空间 5-NN；`c_raw=1.2182`、`c_soc=2.8286`；Train barcode bootstrap 支持率不少于 80% |
| Q2 代理 | 冻结 P3，只作 `Q2_provisional` 候选提名；不做最终寿命排序 |
| Q3 窗口 | `k=5` 为早期筛查窗口；`k=100` 为正式校正窗口和策略升级的唯一 Q3 门槛 |
| 数据处理 | 继续使用 P0 的 EOL 截断、cycle 2 起算和字段—循环掩码；不得因单字段/单循环异常删整枚电芯 |

禁止：使用 Primary/Secondary 或 pilot 结果重新选 P3、`k`、特征、5-NN 阈值、80% 支持率门槛、候选网格或策略排序规则。

## 3. Pilot 的最小试验单元

对每一条拟试策略 `s`：

\[
r_s \ge 3,
\]

其中 `r_s` 为彼此不同的物理电芯数。条码不可复用；每枚电芯应有唯一 `pilot_id`、`barcode` 和策略三元组。

每枚电芯至少保存 cycle 2–100 的 `QDischarge`、`QCharge`、`IR`、`Tmax/Tavg/Tmin`、`chargetime` 以及相应原始/处理元数据。`IR` 单位为 Ω，`chargetime` 单位为 min。若任一字段在某循环异常，只标该字段—循环的掩码与原因，保留同循环其他字段和该电芯。

## 4. 收集、质控与晋级顺序

```text
Q2_provisional 候选
  → 冻结策略参数 + 至少 3 枚新物理电芯
  → 运行至 k=5：冻结 Q3 早期风险筛查（只作预警/调度）
  → 运行至 k=100，并形成 P0 兼容长表
  → 字段—循环掩码与特征生成
  → 冻结 M3(k=100) 输出寿命/SOH 校正
  → 记录为 Q3_confirmed / Q3_not_confirmed / incomplete
  → 只有 Q3_confirmed 才有资格进入后续正式 Pareto
```

`k=5` 的筛查输出包括冻结 k=5 的寿命预测、风险提示、字段有效比例和逐电芯掩码统计。它可用于安排后续检测优先级、预警异常或决定额外观察资源，但**不得**单独把策略升级为正式 Pareto、宣布寿命优劣或取代第 100 循环的实测记录；本项目尚未为 k=5 预注册安全停机阈值。

`Q3_confirmed` 的**数据资格**定义为：每个策略至少 3 枚不同电芯均拥有 cycle 2–100 记录；冻结的 k=100 特征可生成；没有未说明的数据缺失；每枚电芯的 Q3 输出与掩码统计都已归档。它只表示“已获得 Q3 确认证据”，不表示策略安全、最优或外部泛化已经通过。

如果电芯未到第 100 循环、字段无法按 P0 规则审计或策略参数与登记表不一致，状态为 `incomplete`，不得以预测填补替代实测早期信息。

## 5. Pilot 登记表

创建并维护 `data/pilot/q4_k100_pilot_registry.csv`。必须包含：

```text
pilot_id,barcode,C1,Q1_percent,C2,q,single_stage_0_80,
tau_0_80_min,candidate_source,status,cycle_5_complete,k5_screen_status,
cycle_100_complete,raw_data_path,p0_compatible_view_path,notes
```

- `candidate_source` 必须能回溯到冻结候选表中的唯一策略三元组。
- `status` 仅允许：`planned`、`running`、`incomplete`、`Q3_confirmed`、`Q3_not_confirmed`。
- `k5_screen_status` 仅允许：`not_due`、`complete_no_alert`、`complete_alert`、`incomplete`；它记录筛查，不构成最终淘汰或升级。
- `Q3_confirmed` 仅在第 4 节的数据资格与冻结 Q3 输出均完成后写入。
- `notes` 记录试验偏差、仪器中断等事实，不能用来修改已冻结规则。

## 6. 冻结 Q3 的评价输出

对每枚 pilot 电芯，保存：

1. 截止 k=5 的冻结特征、筛查寿命预测、风险提示及字段有效比例；
2. 截止 k=100 的冻结 12 项早期特征及字段有效比例；
3. k=100 的 `predicted_log_life`、`predicted_cycle_life`，并明确其是运行后校正预测；
4. 从第 100 循环实测 `SOH_nom` 锚定的未来 SOH 轨迹预测；
5. 若后续真实寿命/SOH 可获得，再按电芯等权汇总 `RMSE_log`、`MAE_log`、未来 SOH RMSE 和失败原因；
6. 每策略的 3 枚电芯逐枚结果及策略等权汇总，严禁按曲线行数加权。

在未达到寿命终点前，第 4 项中的寿命/SOH 误差应标为“未观测”，不能伪造为通过或不通过；此时仅有“Q3 已产生冻结预测”的证据。

## 7. Q4 后续输出门槛

只有同时满足下列条件，策略才可从 `Q2_provisional` 进入**后续正式 Pareto 的候选层**：

1. Pilot 数据资格完成，且每策略至少 3 枚不同电芯运行至 k=5（筛查记录）和 k=100（正式确认）；
2. 冻结 Q3 k=100 预测、掩码统计和逐电芯记录均已归档；
3. 后续一旦寿命/SOH 真值可观测，使用预先定义的电芯等权指标报告表现，而不是重选规则；
4. 不越过 raw/SOC 双空间支持域，且不引入 Secondary 的结果回调开发；
5. 明确标注 P3 的限定中等可信范围及 Secondary 尚未完成的事实。

最终正式 Pareto 仍需要冻结的保守寿命下界、可追溯的 Q3 结果和一次 Secondary 压力测试；本协议不解除这些要求。

## 8. 当前可执行事项

当前没有新增 pilot 原始数据，因此本轮只完成协议和登记规范。收到新策略试验数据后，下一步是：P0 兼容性审计 → 生成 k=100 特征 → 冻结 Q3 预测/评估 → 写入登记表，不允许跳过中间步骤。
