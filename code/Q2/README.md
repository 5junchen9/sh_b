# Q2

## Q2-A：机制关联 PoC

运行：`.\.venv\Scripts\python.exe -W error l1\code\Q2\q2_run_all.py`

输入为冻结 P0 与 `cell_labels.csv`；只使用 Train，并以 `policy_table9` 做外层和内层分组。输出写入 `results/Q2/experiments/round1/`。M1 是主效应基线，M2 是二阶交互 Ridge 敏感性分析。

## Q2-B：设计前寿命预测代理比较

运行：`.\.venv\Scripts\python.exe -W error l1\code\Q2\q2b_train_proxy_comparison.py`

仅使用 Train 的 `C1`、`Q1_percent`、`C2` 预测 `ln(cycle_life_table9)`，禁止读取早期循环特征、Primary 或 Secondary。脚本以嵌套策略分组验证比较 Ridge、ElasticNet、低自由度加性样条 GAM 与严格受限提升树，并进行 2000 次策略组块 bootstrap。

输出写入 `results/Q2/experiments/q2b_proxy_round1/`：包括 OOF 预测、调参记录、模型比较表、选择 JSON、中文 PNG/SVG 图和面向论文的报告。候选池与冻结选择规则见 `methods/Q2/q2b_proxy_method_candidates.md`。

## Q2-B：P3 Primary 一次受限确认

运行：`.\.venv\Scripts\python.exe -W error l1\code\Q2\q2b_primary_confirmation.py`

仅在 `methods/Q2/q2b_primary_confirmation_protocol.md` 冻结的条件下执行：P3（`n_knots=4`、`alpha=0.03`）只以 Train 的 41 枚电芯拟合一次，再对 43 枚 `Prim. Test` 电芯评分。禁止调参、替换 P3、读取早期循环特征或将 Primary 反馈给模型选择。输出写入 `results/Q2/experiments/q2b_primary_confirmation_round1/`，状态仅为受限确认观察，不自动产生最终通过或 Q4 推荐。
