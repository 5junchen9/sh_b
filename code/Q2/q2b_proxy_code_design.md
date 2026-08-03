# Q2-B 代理模型比较：代码逻辑

对应 `methods/Q2/q2b_proxy_method_candidates.md`。实现语言为 Python 3.12，固定
随机种子 `20260802`，仅使用 `numpy`、`pandas`、`scikit-learn` 和 `matplotlib`。

- 输入：`data/processed/p0_summary.json`（必须为 pass）及
  `data/processed/cell_labels.csv`（仅 Train 行）。
- 特征：`C1`、`Q1_percent`、`C2`；目标：`ln(cycle_life_table9)`；分组：
  `policy_table9`。
- 模型：P1 Ridge、P2 ElasticNet、P3 低自由度加性样条 GAM、C1 严格受限
  HistGradientBoosting。P1/P2/P3 均输出连续、平滑的设计前响应；C1 不作默认主模型。
- 验证：外层 5 折策略分组 OOF，内层 4 折策略分组以 `RMSE_log` 调参。
- 稳健性：策略组块 bootstrap 2000 次，只对完成的 OOF 误差重抽样；不读 Primary 或
  Secondary。
- 输出：`results/Q2/experiments/q2b_proxy_round1/` 下的表、图、指标、日志及运行摘要。
  脚本同时生成面向论文的比较报告。

运行命令：

```powershell
.\.venv\Scripts\python.exe l1\code\Q2\q2b_train_proxy_comparison.py
```
