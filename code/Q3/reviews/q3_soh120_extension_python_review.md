# Q3 第 120 循环 SOH 输出扩展代码复审

> **状态：passed_with_warnings**  
> **复审对象：** `code/Q3/q3_run_all.py`、`code/Q3/q3_primary_confirmation.py`  
> **范围：** 在不改变既有 M3、窗口、特征、交叉验证或评价规则的前提下，增加 Q4 已有策略聚合所需的第 120 循环 SOH 预测表。

## 通过项

1. ✅ `q3_run_all.py:56-58` 仍以 `policy_table9` 进行外层 GroupKFold，并且每一外层测试电芯的 Ridge、正则化参数和 SOH 模板均仅由该外层训练条码构造；新增输出没有把测试电芯或同策略电芯回灌训练。
2. ✅ `q3_run_all.py:44-49` 的 `predict_soh` 只使用已冻结的单调模板、预测寿命和 k 时刻真实锚点；第 120 循环预测未读取 120 循环的真实 SOH 作为特征。
3. ✅ `q3_run_all.py:68` 将真实第 120 循环 SOH 仅作为独立的 `actual_soh_nom_120` 审计列输出，模型输入未增加该列；这保持了预测目标与特征的分离。
4. ✅ `q3_run_all.py:72` 将新增结果保存为 UTF-8 CSV `m3_oof_soh120_predictions.csv`，原有寿命、SOH 误差与图表输出仍保留，未以控制台输出代替可复现工件。
5. ✅ `q3_primary_confirmation.py:70-74` 继续保持 Primary 的冻结确认边界：模型和模板只由 41 枚 Train 电芯构建，Primary 43 枚电芯不参与参数选择。
6. ✅ `q3_primary_confirmation.py:82-86` 对预测寿命不超过 k、缺锚点、无未来曲线和模板分母异常保持原有显式失败分支；新增第 120 循环输出仅在 k<120 且曲线可评价时写入。
7. ✅ 两个脚本均通过 `python -m py_compile`，并以项目 `.venv` 实际运行完成；原有五窗口与 Primary 指标逐项复核后与扩展前一致，说明本扩展没有改变既有结论。
8. ✅ `q3_run_all.py:18` 与 `q3_primary_confirmation.py:24` 保持固定种子 `20260802`，运行摘要重新记录脚本哈希和输入哈希。

## 约束方向复核

本次为预测输出扩展，无线性/整数优化约束。唯一条件判断为 `n<L_i` 的正式长表上游门禁、`predicted_life>k` 的可评价条件以及 `k<120` 的预测输出条件；三者均不是需要改变方向的资源约束。

## 修复与复跑

初次扩展发现 `curve_error` 的异常返回分支仍返回两个值、而调用方已解包三个值；已在 `q3_primary_confirmation.py:49-54` 统一为 `(residual, predicted_soh120, reason)` 三元返回，并重新编译、复跑通过。

## 剩余风险

- 第 120 循环 SOH 是由 Q3 模板给出的预测；它是 Q4 已有策略的辅助风险维度，不是新的寿命终点或安全阈值。
- Primary 预测仍是一次受限确认，不能与 Train OOF 混写为独立外部测试；后续策略聚合必须保留来源列。
- 该扩展未改变 Q3 的正式电芯等权 SOH RMSE。正式窗口选择仍以既有 bootstrap 表和 `Q3-D02/D04` 为准。

## 运行方式

```powershell
.\.venv\Scripts\python.exe l1\code\Q3\q3_run_all.py
.\.venv\Scripts\python.exe l1\code\Q3\q3_primary_confirmation.py
```

## 关键输出

- `results/Q3/experiments/round1/tables/m3_oof_soh120_predictions.csv`
- `results/Q3/experiments/primary_confirmation_round1/tables/q3_primary_soh120_predictions.csv`
- `results/Q3/experiments/round1/run_summary.json`
- `results/Q3/experiments/primary_confirmation_round1/run_summary.json`

## 下一步

在 Q4 的已有策略分支中，按条码将 Q2 的 P3 预测、Q3 的 k=100 预测和第 120 循环 SOH 预测合并；保留 `Train_OOF` 与 `Primary_restricted_confirmation` 两种来源，按策略电芯数区分正式比较与单电芯案例。
