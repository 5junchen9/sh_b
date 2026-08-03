# Q3 Round 2 联合模型 Python 代码复审

> **状态**：passed_with_warnings  
> **复审者**：python-code-reviewer  
> **日期**：2026-08-02  
> **脚本**：`code/Q3/q3_run_joint_comparison.py`  
> **对应设计**：`code/Q3/q3_round2_joint_code_design.md`

## 通过项

1. ✅ `code/Q3/q3_run_joint_comparison.py:245-256` 只读 P0 处理后的标签与长表，明确筛选 `dataset_table9 == "Train"`，并检查为 41 个唯一条码；没有读取 Primary 或 Secondary。
2. ✅ `:91-100` 对每一个 Ridge 候选都在外层训练折内部以 `GroupKFold(policy_table9)` 选择 alpha；`SimpleImputer` 和 `StandardScaler` 均封装在拟合管线中（`:78-79`），未在验证电芯上预拟合。
3. ✅ `:190-207` 将 M1、M2、M3、M4 四条路线明确分开；M3 使用策略加早期特征，而 M4 先交叉拟合策略先验、再拟合残差，符合 Round 2 设计而非旧 Round 1 的早期特征单模型。
4. ✅ `:168-177, 201-207` 的 M4 在每个 Q3 外层训练折内重新生成 P3 内层 OOF 先验；代码检查 `prior` 无缺失后才拟合残差，避免把同一电芯标签泄漏给其先验。
5. ✅ `:278-287` 建立外层 `GroupKFold`，并显式检查训练与留出策略组没有交集；实跑后的 `joint_oof_life_predictions.csv` 有 820 行（4 模型×5 窗口×41 电芯），每个模型—窗口覆盖 41 枚电芯、无重复。
6. ✅ `:103-126, 300-306` 每个留出电芯的 SOH 模板只由同一外层训练折的真实寿命和曲线建立；留出电芯只使用截止点实测 `SOH_nom(k)` 作锚定，未使用其真实寿命拟合模板。
7. ✅ `:345-360` 同时保存寿命折外预测、逐电芯曲线误差、SOH120 预测、调参记录和指标；正式 `cell_equal_soh_rmse` 按逐电芯 MSE 等权聚合，未让长寿命电芯因曲线点多而加权更高。
8. ✅ 已用 `.\.venv\Scripts\python.exe -m py_compile` 和实际运行复核；输出 20 行模型×窗口指标，数值列无 NaN/Inf、20 个模型—窗口组合均无模板失败，图和 CSV/JSON 日志均生成。

## 失败或修复项

| # | 文件:行 | 问题 | 处理 | 状态 |
|---:|---|---|---|---|
| 1 | `q3_run_joint_comparison.py:84-88` | 初版 P3 管线额外放入了 `SimpleImputer`，与冻结 Q2 P3 的确认脚本不完全一致。 | 已删除该步骤，保持二次 B 样条（4 结点）+ 标准化 + `Ridge(0.03)`。 | 已修复并复跑 |

## 约束方向复核

本脚本是回归和单调模板模型，不含资源分配、不等式约束或优化可行域，因此没有需要人工复核方向的 `≤/≥` 约束。

## 剩余风险

- `code/Q3/q3_run_joint_comparison.py:91-100`：41 枚 Train 电芯、约 40 个策略组使每折训练样本很小；应以策略组 bootstrap 检验模型和窗口差异，不把点估计直接写成最终胜负。
- `:82-88`：P3 是 Q2 的冻结 provisional 代理，M4 不应因本轮表现被解释为“Q2 最优模型”或进入 Q4 正式寿命排序。
- `:300-342`：SOH 的双端锚定使用实际的截止点 SOH；这符合“运行到 k 后校正”的情境，但不属于策略设计前可得到的信息。
- Round 1 已暴露的 Primary 不能继续充作本 Round 2 的独立确认；需在锁定候选后按新的受限协议处理，或仅保留 Train-only 结论。

## 运行方法

```powershell
.\.venv\Scripts\python.exe -W error l1\code\Q3\q3_run_joint_comparison.py
```

## 预期产物

- `results/Q3/experiments/round2_joint/tables/joint_window_metrics.csv`
- `results/Q3/experiments/round2_joint/tables/joint_oof_life_predictions.csv`
- `results/Q3/experiments/round2_joint/tables/joint_cell_curve_errors.csv`
- `results/Q3/experiments/round2_joint/tables/joint_oof_soh120_predictions.csv`
- `results/Q3/experiments/round2_joint/figures/q3_joint_window_comparison.png`
- `results/Q3/experiments/round2_joint/run_summary.json`

## 下一环节

`robustness-checker`：对模型差异和 k=5/k=100 的双窗口表述进行策略组等权 bootstrap 与 Pareto 检验。
