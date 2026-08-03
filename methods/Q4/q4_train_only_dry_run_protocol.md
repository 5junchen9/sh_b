# Q4 Train-only 候选流量 dry-run 协议

## 目的

本协议只在 Primary 受限确认前回答：哪些新策略组合同时接近 Train 的原始参数和 SOC 暴露，
从而值得标为 `Q2_provisional` 并进入后续 pilot。它**不**产生正式 Pareto、最终最优策略、
寿命下界或 Q3 确认结论。

## 冻结候选格点

V2 未指定统一数值步长。为避免人为插值密度改变结果，本轮固定使用 Train 中已经出现的
离散水平的笛卡尔组合：对 `Q1_percent<80`，取 13 个 `C1` × 20 个 `Q1_percent` × 14 个
`C2`；对 `Q1_percent=80`，第二阶段没有物理长度，固定 `C2=C1` 并仅保留每个 `C1` 一条。
合计 3,653 个策略格点。该规则比在 min/max 长方体内任意细分更保守；后续不得查看结果后
增删水平或改用更细网格。

`Q1_percent=80` 按单阶段分支计算理论时间与 SOC 暴露，不假设不存在的第二阶段运行。

## 支持域门槛

1. 仅 Train 的 41 个 barcode 冻结原始空间 `(C1,q,C2)` 与 SOC 空间
   `(E0-20,E20-40,E40-60,E60-80,tau0-80)` 的中位数/IQR 标准化。
2. 以 Train 留一第 5 近邻距离的 95% 分位，分别得到 `c_raw` 与 `c_soc`。
3. 候选须同时满足 `d5_raw <= c_raw`、`d5_soc <= c_soc`；相邻电芯按 barcode 计数。
4. 做 1,000 次 Train barcode bootstrap，只改变本次出现的不同 barcode；候选在至少 80%
   的重采样中仍有至少 5 个不同邻居且双空间通过，才标为 `Q2_provisional`。

## 预测与状态

- 对所有格点使用 Q2-B 按 Train-only 预注册规则选出的 P3 加性 GAM（已冻结为限定中等可信的 provisional 用途）给出全 Train refit 的设计前寿命点预测，仅作
  审计列；不计算或声称正式寿命下界。
- 既有 Train 策略与新增组合分开标记；新增且支持通过者为 `Q2_provisional`，新增但支持不足者为
  `rejected/no_support`。
- 单模型状态下 `model_disagreement_log` 记为 `N/A`，不得写为 0。

## 允许的结论

只报告格点流量、支持率、距离和待试验候选数。任何通过候选仍须至少 3 枚新物理电芯运行至
冻结窗口 `k=100` 并经 Q3 确认，之后才可进入正式 Q2+Q3 Pareto。
