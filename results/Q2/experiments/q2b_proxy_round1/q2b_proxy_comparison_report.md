# Q2-B：设计前寿命预测代理比较报告

## 结论

按冻结规则，本轮供 Q4 使用的设计前寿命代理为 **P3 低自由度加性样条 GAM**。
其 Train 策略分组折外指标为 `RMSE_log=0.3489`、
`MAE_log=0.2338`，预测寿命高于真实寿命的比例为
`48.8%`。

参数模型选择说明：在误差一标准误范围且过预测风险不高于误差锚点的参数模型中，选择复杂度最低者。
受限提升树：未同时满足对参数代理的明确增益门槛，因此只保留为挑战者。

## 评价范围

- 数据：仅 `dataset_table9 == 'Train'` 的 41 枚电芯、40 个 `policy_table9` 组。
- 输入：设计前可知的 `C1`、`Q1_percent`、`C2`；不读取早期曲线、Primary 或 Secondary。
- 验证：外层 5 折策略分组 OOF，内层 4 折策略分组调参。
- 稳健性：对 OOF 误差做 2000 次策略组块 bootstrap；区间反映 Train 内重抽样稳定性，不等于外部泛化保证。

## 候选模型结果

| 模型 | RMSE_log | MAE_log | 过预测比例 | 平均正向对数误差 | 角色 |
|---|---:|---:|---:|---:|---|
| P1 主效应 Ridge | 0.3676 | 0.2668 | 56.1% | 0.1361 | parameter_baseline |
| P2 ElasticNet | 0.3770 | 0.2727 | 51.2% | 0.1406 | parameter_candidate |
| P3 低自由度加性样条 GAM | 0.3489 | 0.2338 | 48.8% | 0.1093 | parameter_candidate |
| C1 严格受限提升树（挑战者） | 0.3317 | 0.2274 | 48.8% | 0.1096 | challenger |

## 对 Q4 的使用规则

1. 仅在 Train 的原始/SOC 双空间支持域内调用本代理，不做域外外推。
2. 优化结果只能标记为 `Q2_provisional`，直到按 Q3 冻结窗口 `k=100` 完成受限确认。
3. 本报告不替代 Q2-A 的机制解释：M1 仍是正文保守基线，M2 仍仅为交互敏感性分析。
4. 不能用 Primary 或 Secondary 重新调模型、改阈值或扩充候选池。

## 可复现入口

- 脚本：`code/Q2/q2b_train_proxy_comparison.py`
- 全部数表：`results/Q2/experiments/q2b_proxy_round1/tables/`
- 指标与选择记录：`results/Q2/experiments/q2b_proxy_round1/metrics/`
- 图：`results/Q2/experiments/q2b_proxy_round1/figures/`
