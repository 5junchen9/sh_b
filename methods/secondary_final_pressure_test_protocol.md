# Secondary 最终压力测试协议（仅在冻结后执行）

> 状态：**预注册协议，未执行**。本文件不读取 Secondary，也不包含任何 Secondary 数值。  
> 目的：在不再改变模型、特征、窗口、指标或阈值的前提下，对已冻结的 Q2/Q3/Q4 开发路线做一次独立压力测试。

## 1. 执行前门槛

只有同时满足以下条件，才允许打开 `dataset_table9 == "Secondary"` 的标签或曲线：

1. `methods/Q3/decisions/robustness-checker_modeler_decision.md` 与 `result-report-generator_modeler_decision.md` 均由建模者完成并记录为 `DECIDED`；
2. 生成带 SHA-256 的冻结清单，固定 Q2 的 M1 主线、M2 敏感性定位、P3 仅作 Q4 暂定候选的定位；
3. 固定 Q3 的 M3R-k=5 早筛角色与 M2-k=100 正式预测角色，并明确两者都不得在 Secondary 后重新选择；
4. 固定 Q4 只报告已有策略开发池比较与暂定候选，不将未实测新策略写为结论；
5. 为所有执行脚本设置新输出目录，禁止覆盖 Train/Primary 的表、图、日志。

任一条件不满足时，测试不得启动。Primary 已暴露，不能替代本协议中的独立测试。

## 2. 固定输入与禁止事项

| 项目 | 冻结规则 |
|---|---|
| 数据 | 只读取 P0 已处理的 Secondary 电芯；原始 MAT 继续只读，局部异常仍只执行字段—循环掩码 |
| Q2 | 使用已冻结的 Train 拟合管线；不在 Secondary 重选 alpha、交互项、GAM 自由度或特征 |
| Q3 | k=5 和 k=100 都使用截止循环以前的信息；SOH 模板、缩放器和超参数只从 Train 取得 |
| Q4 | 不用 Secondary 改候选格点、支持域阈值或 Pareto 规则；如报告已有策略，只作外部对照，不作重新寻优 |
| 随机性 | 使用已冻结的种子与 bootstrap 次数；输出执行环境、输入/脚本 SHA-256 |
| 禁止 | 不在 Secondary 上调参、选窗口、补特征、删整枚电芯、改阈值或反复测试 |

## 3. 固定评价表

所有指标同时按电芯等权与策略等权（按 `policy_table9` 聚类）报告；策略组 bootstrap 次数固定为 2,000。

| 问题 | 主指标 | 必报诊断 | 通过后的表述上限 |
|---|---|---|---|
| Q2 | `RMSE_log`、`MAE_log`、过预测率 | M1 与 M2 的差值区间 | 只报告外部误差；M2 仍非正式解释主模型，除非已有冻结规则已允许其升级 |
| Q3 k=5 | 寿命 `RMSE_log/MAE_log`、电芯等权未来 SOH RMSE | 模板失败数、SOH 有效电芯数、相对 M2-k=5 差值区间 | “早筛候选的外部表现”，不等同正式寿命排序 |
| Q3 k=100 | 寿命 `RMSE_log/MAE_log`、电芯等权未来 SOH RMSE | 模板失败数、SOH 有效电芯数、相对开发集差异 | “较充分校正窗口的外部表现”，不得由此回调 k |
| Q4 | 已有策略的样本数、经验寿命摘要、Q2/Q3 输出范围 | n≥2/n≥3 与留一资格敏感性 | 仅可保留或否定开发期描述，不能生成未经 pilot 的最优新策略 |

## 4. 预先解释规则

1. **一致**：若主要误差量级与 Train/Primary 开发期相近，且没有明显扩大过预测风险，则称“开发期结果在 Secondary 上得到有限支持”。
2. **部分一致**：若 k=5、k=100 或 Q2 的不同指标给出不同信号，则分开报告，不以某一个指标覆盖其余指标。
3. **不一致**：若误差明显恶化、模板失败增加或策略等权区间显示方向不稳，则停止将相应路线用于任何推荐；回到 Train 新开一轮开发，Secondary 不参与调参。
4. 所有结论都写出 Secondary 的一次性、冻结后性质，不称因果效应，也不宣称跨所有充电方案泛化。

## 5. 交付物与审计

执行时在新目录 `results/Secondary_final_pressure_test/` 生成：

- `manifest.json`：输入、脚本、冻结清单和环境哈希；
- `q2_external_metrics.csv`、`q3_external_metrics.csv`、`q4_existing_policy_external_summary.csv`；
- `bootstrap_intervals.csv` 和中文 PNG/SVG；
- `secondary_final_pressure_test_report.md`：按上表逐项说明，不产生“最优新策略”；
- `audit.md`：确认未用 Secondary 选择模型或修改 Train 产物。

执行后再运行跨媒体一致性、完整性和最终质量审计；只有三者均通过，才允许把开发证据稿升级为最终论文。
