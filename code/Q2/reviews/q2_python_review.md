# Q2-A Python 代码复审

> **状态**：passed_with_warnings  
> **对象**：`code/Q2/q2_run_all.py`  
> **脚本 SHA-256**：`478eb3faa1ecb0caf653136bb2c6d6ede067704c7f2480e3d872d3012248131e`

## 明确通过项

1. ✅ `q2_run_all.py:42-44` 要求 P0 通过，并只保留 `dataset_table9 == 'Train'` 的 41 枚电芯、40 个策略组。
2. ✅ `:29-39` 外层和内层都按 `policy_table9` 使用 GroupKFold；标准化、二阶展开和 Ridge 均在折内流水线拟合。
3. ✅ OOF 表新增 `outer_fold`，M1/M2 均为 41 行、折规模 9/8/8/8/8，同一策略只属于一个外层折，且两模型折分配完全一致。
4. ✅ `:47` 同时保存 OOF 预测与折内 alpha；从 OOF 表重算的四项误差与 `comparison_metrics.json` 一致。
5. ✅ `:53` 明确记录目标为自然对数 `ln(L)`、逆变换为 `exp`；总方案已同步为同一口径。
6. ✅ 当前脚本哈希及 `cell_labels.csv`、`p0_summary.json` 输入哈希与 `run_summary.json` 全部匹配。
7. ✅ 图表标题、坐标和图例均为中文；日志、JSON、4 个 CSV 和 PNG 均存在且非空。
8. ✅ 已执行 `py_compile` 与完整 `-W error` 运行；M1/M2 指标分别复现为 `RMSE_log=0.37169/0.36854`、`MAE_log=0.27557/0.25102`。

## 剩余边界

- 41 枚电芯对应 40 个策略组，39 个策略仅一枚电芯；估计方差是数据限制，不能靠模型复杂度消除。
- 本脚本是 Q2-A 解释层：按人工记录 `Q2-D02`，M1 为正文保守主线，M2 只作交互探索/敏感性。
- Q4 不能直接使用 Q2-A；设计前代理须引用 Q2-B 的独立比较和后续人工结果裁决。

## 复现命令

```powershell
.\.venv\Scripts\python.exe -W error l1\code\Q2\q2_run_all.py
```

