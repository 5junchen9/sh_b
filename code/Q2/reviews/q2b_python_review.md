# Q2-B Python Code Review

> **状态**：passed_with_warnings  
> **审查者**：python-code-reviewer  
> **日期**：2026-08-02  
> **审查脚本**：`code/Q2/q2b_train_proxy_comparison.py`
> **当前脚本 SHA-256**：`34a0bda986e3ebca6b101ea3c375adf9c2b040c29c4eeb7e59955e71d822f461`

## 通过项

1. `code/Q2/q2b_train_proxy_comparison.py:48` 将设计前输入显式冻结为 `C1`、`Q1_percent`、`C2`；脚本未载入 `early_features_k*.csv`，与 Q2-B“新策略运行前可知”的定义一致。
2. `code/Q2/q2b_train_proxy_comparison.py:127-145` 在外层 5 折 `GroupKFold(policy_table9)` 的训练折内才构造内层 4 折和拟合模型；标准化、样条基函数与调参都没有接触对应外层测试策略，检查为无该类预处理泄漏。
3. `code/Q2/q2b_train_proxy_comparison.py:53-104` 实现并区分了冻结候选池：Ridge、ElasticNet、低自由度加性样条 GAM，以及叶节点数最多为 3、每叶至少 8 个样本的受限提升树挑战者；未引入重型第三方依赖。
4. `code/Q2/q2b_train_proxy_comparison.py:194-207` 固定 `BOOTSTRAP_REPLICATES=2000`，按 `policy_table9` 整组重抽样 OOF 误差；实际输出 `q2b_policy_block_bootstrap.csv` 为 8,000 行（2,000 次 × 4 模型）。
5. `code/Q2/q2b_train_proxy_comparison.py:253-303` 将参数模型的一标准误简约选择和提升树的“RMSE/MAE 差值上界均小于 0、过预测风险不升高”准入条件写成可执行判断；本次运行中 C1 未被自动升级。
6. `code/Q2/q2b_train_proxy_comparison.py:420-431` 要求 P0 为 pass、所需字段完整且无缺失，并断言 Train 名册必须为 41 枚电芯、40 个策略组；未静默删除任何行。
7. `code/Q2/q2b_train_proxy_comparison.py:447-476` 将 OOF 预测、嵌套调参、bootstrap、比较表、选择 JSON、中文 PNG/SVG、日志和 `run_summary.json` 全部保存到 `results/Q2/experiments/q2b_proxy_round1/`，而非仅打印至控制台。
8. 在项目根目录执行 `python -m py_compile` 及 `python -W error l1/code/Q2/q2b_train_proxy_comparison.py` 均返回 0；另行检查确认 OOF 表恰有 41 行、四列预测均非空，且条码集合与 Train 名册完全一致。
9. 2026-08-02 最终追溯重跑后，`run_summary.json` 中 P0 输入哈希与当前 `data/processed/p0_summary.json` 一致，目标字段也显式记为 `ln(cycle_life_table9)`；四模型指标和 P3 条件性选择均未变化。

## 失败／已修复项

| # | 文件:位置 | 问题 | 处理 | 状态 |
|---|---|---|---|---|
| 1 | 独立核对命令 | 首次使用 PowerShell 内嵌 Python 字符串时引号不闭合；这是检查命令问题，不是建模脚本异常。 | 改为不嵌套 `query` 字符串的集合比较，核对通过。 | 已修复 |
| 2 | `code/Q2/README.md` | 原 README 只描述 Q2-A，缺少 Q2-B 的运行入口和输出位置。 | 已补充 Q2-B 的 Train-only 输入限制、运行命令和输出目录。 | 已修复 |
| 3 | `code/Q2/q2b_train_proxy_comparison.py` | 部分 Windows 环境的 joblib 无法探测物理核心数，严格 `-W error` 会将该环境警告升级为异常。 | 在导入 scikit-learn 前设置不覆盖用户配置的 `LOKY_MAX_CPU_COUNT` 默认值；最终已无需额外环境变量重跑通过。 | 已修复 |

## 约束方向审查

本脚本没有资源分配或不等式约束；模型选择中的数值门槛由 `choose_proxy` 的布尔判断实现，已在第 5 项核对。无须人工核对物理不等式方向。

## 剩余风险

- 41 枚 Train 电芯、40 个策略组仍是小样本；bootstrap 只衡量 Train 内 OOF 的重抽样稳定性，不能代替 Primary 的一次受限确认。
- P3 GAM 只允许加性平滑关系，不表示已证明物理因果关系；Q2-A 的 M1/M2 解释结论与 Q2-B 的预测代理必须分开写。
- 过预测比例为 48.8%，不能单独解释为“偏差很小”；应连同平均正向对数误差、区间和 Q3 k=100 受限验证一起使用。
- 受限提升树虽有更低点误差，但差值区间仍跨 0，不能以本轮结果替换 P3。

## 运行说明

```powershell
.\.venv\Scripts\python.exe -W error l1\code\Q2\q2b_train_proxy_comparison.py
```

## 预期输出

- `results/Q2/experiments/q2b_proxy_round1/tables/q2b_oof_predictions.csv`
- `results/Q2/experiments/q2b_proxy_round1/tables/q2b_model_comparison_and_selection.csv`
- `results/Q2/experiments/q2b_proxy_round1/tables/q2b_policy_block_bootstrap.csv`
- `results/Q2/experiments/q2b_proxy_round1/metrics/q2b_proxy_selection.json`
- `results/Q2/experiments/q2b_proxy_round1/figures/q2b_proxy_error_comparison.png`
- `results/Q2/experiments/q2b_proxy_round1/figures/q2b_proxy_overprediction_risk.png`
- `results/Q2/experiments/q2b_proxy_round1/run_summary.json`

## 建议下一步

在 Q4 代码开始前，使用冻结的 P3 加性样条 GAM 仅在 Train 支持域内生成 `Q2_provisional` Pareto 候选；候选策略须运行并经 Q3 的 `k=100` 规则受限确认，之后才形成正式 Q2+Q3 Pareto 集。
