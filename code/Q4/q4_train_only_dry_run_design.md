# Q4 Train-only dry-run：代码设计

实施 `methods/Q4/q4_train_only_dry_run_protocol.md`：仅读取 P0 通过标记、`cell_labels.csv` 的
Train 行，以及 Q2-B 已冻结的候选定义；不读取 Primary/Secondary，不虚构 Q3 早期特征。

脚本在 Train 上重新以冻结 P3 的搜索网格做策略分组 CV 选取超参数并 refit；随后生成 3,822
个离散观测水平组合，检查理论时间、原始/SOC 双空间 5-NN、1,000 次 barcode bootstrap 支持率。
输出只含 `Q2_provisional` / `rejected` 的内部候选清单和诊断图，不生成正式 Pareto。

输出目录：`results/Q4/experiments/train_dry_run_round1/`。
