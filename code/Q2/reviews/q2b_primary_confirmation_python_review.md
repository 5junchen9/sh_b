# Q2-B P3 Primary 受限确认：Python 代码复审

> **状态**：passed_with_warnings  
> **审查者**：python-code-reviewer  
> **日期**：2026-08-02  
> **审查脚本**：`code/Q2/q2b_primary_confirmation.py`  
> **当前脚本 SHA-256**：`42a3b8f4100d8ca60f54562300046cdc1d1e7b43df4b5b785d93a34ec601b4bf`  
> **对应协议**：`methods/Q2/q2b_primary_confirmation_protocol.md`

## 通过项

1. ✅ `code/Q2/q2b_primary_confirmation.py:57, 109–114` 将 P3、`n_knots=4`、`alpha=0.03` 写为冻结常量，并验证 Q2-B 的选择 JSON 仍为 P3、冻结参数仍存在于 Train-only 参数表；Primary 不能触发重新选模型或参数。
2. ✅ `:106–107` 强制 P0 状态为 `pass`；`:116–130` 检查所有字段、Train=41、Primary=43、条码唯一和无缺失，异常时显式阻断，没有静默删行。
3. ✅ `:122–123, 136–141` 先只以 Train 的 41 枚电芯拟合，再一次性对 `Prim. Test` 的 43 枚电芯预测；`SplineTransformer`、标准化和 Ridge 均只在 Train `fit`，不存在 Primary 参与拟合或调参的泄漏。
4. ✅ `:65–77, 142` 使用实际代码一致的 `ln` 寿命尺度计算 RMSE/MAE、反变换为 `exp` 后计算 cycle 指标，并单列过预测比例和正向误差，符合冻结协议的评价口径。
5. ✅ `:143–151` 保存逐电芯预测、实际/预测对数寿命、cycle 预测与残差；独立复算确认 43 行、43 个唯一条码、无非有限值，且 RMSE/MAE 与 JSON 完全一致。
6. ✅ `:81–101` 保存全中文标题、坐标、图例的观察—预测 PNG/SVG；不把图写入论文目录，也不把它标为最终推荐图。
7. ✅ `:154–202` 保存 JSON 指标、Markdown 确认报告、日志和 `run_summary.json`，并记录 P0、标签、P3 选择 JSON、参数表、协议与脚本 SHA-256，结果可追溯。
8. ✅ 使用项目 `.venv` 实际执行 `python -m py_compile` 与 `python -W error code/Q2/q2b_primary_confirmation.py` 均返回 0；运行结果状态为 `observed_not_adjudicated`，未伪造自动通过结论。

## 失败／已修复项

无。本轮没有为复审改变模型、数据或协议。

## 约束方向复核

本脚本没有资源分配或物理不等式约束。仅有冻结条件和数据门禁（P0 必须通过、选择必须为 P3、分区规模必须为 41/43），均是相等性/状态检查，不存在需要人工确认方向的优化约束。

## 剩余风险

- Primary 已有探索暴露，因此此次只能称“受限确认”，不能作为最终独立泛化证据；Secondary 仍保留给最终压力测试。
- 协议没有预注册自动通过阈值，输出只能增加观察证据；Q2 的结果标签、稳定性置信和论文主张范围仍需建模者填写 Gate G4.5 决定文件。
- P3 在 Primary 的本次表现不会授权切换到 C1、修改参数或重新生成 Q4 候选；任何此类修改都必须回到 Train-only 新轮次。

## 运行入口

```powershell
.\.venv\Scripts\python.exe -W error l1\code\Q2\q2b_primary_confirmation.py
```

## 预期输出

- `results/Q2/experiments/q2b_primary_confirmation_round1/tables/q2b_primary_predictions.csv`
- `results/Q2/experiments/q2b_primary_confirmation_round1/metrics/q2b_primary_metrics.json`
- `results/Q2/experiments/q2b_primary_confirmation_round1/figures/q2b_primary_observed_vs_predicted.png`
- `results/Q2/experiments/q2b_primary_confirmation_round1/run_summary.json`
- `results/Q2/experiments/q2b_primary_confirmation_round1/q2b_primary_confirmation_report.md`

## 下一步

使用 `result-report-generator` 的人工 Gate G4.5 裁决 Q2 的结果标签、置信等级和可写主张；在此之前不生成最终 Q4 推荐。
