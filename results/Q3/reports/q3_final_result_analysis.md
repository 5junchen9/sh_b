# Q3 最终结果分析：冻结双窗口与原始曲线 Challenger

> 本文档的模型角色、外部主张范围和置信等级均转录自已人工裁决的 `methods/Q3/decisions/secondary_external_result_modeler_decision.md`；不依据 Secondary 的一次性结果重选窗口或调参。

## 1. 方法角色与裁决来源

| 对象 | 论文中的最终角色 | 人工裁决来源 |
|---|---|---|
| M3R-k=5（原始曲线增强 Ridge） | 开发期探索性 challenger 的保留记录 | 其开发期 SOH 改善未在 Secondary 复现，不作为外部支持的早筛模型或寿命预测模型。 |
| M2-k=100（早期特征 Ridge） | 冻结前预先指定的较充分校正窗口；仅报告本次外部表现 | Secondary 未显示其优于 M2-k=5，不声称更优。 |
| M2-k=5（早期特征 Ridge） | Secondary 上的比较器观察 | 不因其本次误差较低而反向重选为最终窗口。 |

本题 Q3 的最终置信等级为 **needs_caution（需谨慎）**：这不是模型失效，而是外部结果不支持把开发期的差异升级为稳定优势。决定记录见 `methods/Q3/qx_decision_log.md` 的 Q3-D07。

## 2. 冻结 Secondary 一次性压力测试

- 训练仅使用 41 枚 Train 电芯；最终测试为 40 枚 Secondary 电芯、8 个 `policy_table9` 组。
- 比较前已冻结特征、Ridge 正则化参数、`k=5/k=100`、2,000 次策略组块 bootstrap 与评价指标；运行后不调参、不重选。
- 对每枚 Secondary 电芯，`k=5` 和 `k=100` 的原始充电曲线均满足深层审计后的字段—循环掩码规则，`raw_valid_ratio=1.0`；40 枚均可形成未来 SOH 模板，模板失败数为 0。
- 独立复核共 23 项均通过，见 `results/Secondary_final_pressure_test/verification.md`。

## 3. 外部结果

| 模型 | 截止窗口 | 寿命 RMSE_log | 寿命 MAE_log | 电芯等权未来 SOH RMSE | 可评价曲线 |
|---|---:|---:|---:|---:|---:|
| M2 早期特征 Ridge | k=5 | 0.419302 | 0.360166 | 0.062007 | 40 |
| M3R 原始曲线增强 Ridge | k=5 | 0.492453 | 0.453799 | 0.072023 | 40 |
| M2 早期特征 Ridge | k=100 | 0.469504 | 0.399460 | 0.069084 | 40 |

相对 M2-k=5，M3R-k=5 的 2,000 次策略组块 bootstrap 差值（M3R 减 M2）为：

- 寿命 `ΔRMSE_log=0.071037`，95% 区间 `[0.005447, 0.140498]`；
- 寿命 `ΔMAE_log=0.093379`，95% 区间 `[-0.000436, 0.170258]`；
- 未来 `ΔSOH_RMSE=0.009872`，95% 区间 `[0.002531, 0.017078]`。

两个主要 RMSE 差值区间均在 0 的上方，表明 M3R-k=5 的开发期 SOH 改善未在 Secondary 复现；而 k=100 的三项外部点估计也未显示优于该冻结比较器。这里的“未显示优于”只描述本次冻结外部观察，**不构成事后选择 k=5 的依据**。

## 4. 图表及其论文含义

- `results/Secondary_final_pressure_test/figures/secondary_final_observed_predicted.png`：中文实测—预测散点图，同时展示 Q2 和 Q3 的外部误差范围。Q3 面板中，M3R-k=5 的散点偏离与表中较高误差一致，适合放在“外部压力测试与局限性”小节，而非作为模型优越性的证据。
- `results/Secondary_final_pressure_test/tables/q3_external_metrics.csv`：逐模型的寿命和未来 SOH 误差、模板失败诊断。它支持“40 枚均可评价、但不同模型的泛化表现不同”的结论。
- `results/Secondary_final_pressure_test/tables/bootstrap_intervals.csv`：策略组块 bootstrap 区间。它是“不将 M3R-k=5 升级为外部支持模型”的主要统计证据。

## 5. 论文可写与不可写

### 可写

1. 在严格的 Train-only 开发和冻结 Secondary 压力测试下，原始曲线特征在开发期呈现的 SOH 改善没有得到 Secondary 复现。
2. `k=100` 是预先指定的较充分校正窗口；其本次外部误差应如实报告，但不能被称为更优窗口。
3. 截止窗口必须只使用 k 及以前的信息；原始曲线异常采用字段—循环掩码，而不是静默剔除整枚电芯。

### 必须限定或避免

1. 不称 M3R-k=5 为“外部验证的早筛模型”或“寿命预测优胜模型”。
2. 不用 Secondary 上 M2-k=5 的较低误差重新选定最终窗口。
3. 不把本题的预测关联解释为充电策略对寿命的因果机制。

## 6. 写作交接

Q3 的贡献应表述为：建立了无泄漏的早期预测与未来 SOH 校正流程，并通过最终外部压力测试识别出原始曲线增强在当前样本下的不可复现性。该负向验证结果是可信域边界的一部分，不应被省略。

**可交接给**：`final-method-explainer`、`solution-package-builder`。  
**不再执行**：针对 Q3 的窗口、特征或正则化参数重选。
