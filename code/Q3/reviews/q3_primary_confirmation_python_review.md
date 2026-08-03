# Q3 Primary 受限确认 Python 代码复审

> **状态**：passed_with_warnings  
> **复审者**：python-code-reviewer  
> **日期**：2026-08-02  
> **已审查脚本**：`code/Q3/q3_primary_confirmation.py`  
> **脚本 SHA-256**：`df253648605fa65735c80d0e9a53cfb1110aef9c64208344b649d785c4974fbf`

## 复审范围

该脚本实现已经冻结的 Q3 M3，在 `k=5` 和 `k=100` 上对 Primary 分区进行一次**受限确认**。它不是重新选窗口、重新挑 alpha 或独立的最终外部测试。方法边界来自 `methods/Q3/q3_primary_confirmation_protocol.md`。

## 通过项（具体检查）

1. ✅ `code/Q3/q3_primary_confirmation.py:21-25` 以项目相对根目录组织输入与输出，冻结窗口为 `[5, 100]`，并将本轮产物写入 `results/Q3/experiments/primary_confirmation_round1/`，没有硬编码本机绝对路径。
2. ✅ `code/Q3/q3_primary_confirmation.py:29-32,78` 中位数填补、标准化和 Ridge 均封装在 pipeline 内；每个 `alpha` 只在 41 枚 Train 电芯的 `policy_table9` 分组折中选择，Primary 没有参与参数选择。
3. ✅ `code/Q3/q3_primary_confirmation.py:34-44,72` 单调 SOH 模板只由 Train 条码及其循环记录构建；Primary 的未来 SOH 仅在 `curve_error` 中用于评分，未流入模板或模型拟合。
4. ✅ `code/Q3/q3_primary_confirmation.py:69-71,75-77` 对 P0 通过状态、固定 Train/Primary `41/43` 条码、特征字段以及一对一合并均设置阻断检查，避免分区漂移、缺列或合并重复被静默接受。
5. ✅ `code/Q3/q3_primary_confirmation.py:45-56,79-84` 指标在自然对数寿命尺度计算，并以 `exp` 还原循环寿命；SOH 失败原因按字段记录，`predicted_life_not_after_k` 等异常不会静默删除整枚电芯。
6. ✅ `code/Q3/q3_primary_confirmation.py:84-86` 明确区分正式电芯等权 `cell_equal_soh_rmse` 与未来点合并诊断指标，保存逐电芯预测、逐电芯曲线误差、调参和机器可读 JSON，结果不只打印到控制台。
7. ✅ `code/Q3/q3_primary_confirmation.py:57-65` 的作图字体、标题、坐标和图例均为中文，并同时导出 PNG/SVG；已人工查看 `figures/q3_primary_confirmation.png`，标注可读。
8. ✅ 以 `..\\.venv\\Scripts\\python.exe -W error code\\Q3\\q3_primary_confirmation.py` 从 `l1/` 实际运行通过；输出表格与 JSON 存在，且独立重算 43 条寿命预测得到的两窗口 RMSE 与报告一致，k=5 有 43 枚、k=100 有 41 枚可评价 SOH 曲线。

## 约束方向复核

本脚本是预测与评分流程，不含优化变量、可行域或不等式约束；因此无可供逐条核对的约束方向。

## 失败/修复项

| # | 文件:行 | 问题 | 处理 | 状态 |
|---|---|---|---|---|
| — | — | 未发现需要在不改变冻结建模路线前提下修复的实现错误 | 未改动模型或代码 | 通过 |

## 运行结果核验

| k | RMSE_log（ln） | MAE_log（ln） | 电芯等权 SOH RMSE | 可评价 SOH 电芯 | 模板失败 |
|---:|---:|---:|---:|---:|---:|
| 5 | 0.303054 | 0.203225 | 0.042589 | 43 | 0 |
| 100 | 0.397017 | 0.215347 | 0.038429 | 41 | 2 |

`k=100` 的 2 个失败均为 `predicted_life_not_after_k`；其余三类失败均为 0。失败被记录于 `tables/q3_primary_window_metrics.csv`，不能被解释成不存在。

## 剩余风险

- Primary 在前期开发中已有探索暴露，本轮只能称“冻结模型的一次受限确认”，不能当作最终独立外部泛化结论。
- k=100 在 Primary 上的寿命误差高于 k=5，尽管其电芯等权未来 SOH RMSE 更低；双窗口的不同用途应保留，不能据此改写为单一窗口全面更优。
- `SEED` 已写入运行摘要，但本脚本本身没有随机抽样；可复现性主要来自固定分区、特征、alpha 候选和输入 SHA-256。

## 运行命令

从 `l1/` 目录运行：

```powershell
..\.venv\Scripts\python.exe -W error code\Q3\q3_primary_confirmation.py
```

## 预期产物

- `results/Q3/experiments/primary_confirmation_round1/tables/q3_primary_window_metrics.csv`
- `results/Q3/experiments/primary_confirmation_round1/tables/q3_primary_life_predictions.csv`
- `results/Q3/experiments/primary_confirmation_round1/tables/q3_primary_cell_curve_errors.csv`
- `results/Q3/experiments/primary_confirmation_round1/metrics/q3_primary_metrics.json`
- `results/Q3/experiments/primary_confirmation_round1/figures/q3_primary_confirmation.png`
- `results/Q3/experiments/primary_confirmation_round1/run_summary.json`

## 建议下一步

将这次受限确认观察同步至 Q3 报告和交接材料；之后由建模者在不利用 Primary 回调模型的前提下填写 Q3 的结果与稳定性裁决，并保留 Secondary 作为真正独立的最终压力测试。
