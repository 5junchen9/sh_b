# Q4：Train-only 候选流量 dry-run

运行：

```powershell
.\.venv\Scripts\python.exe -W error l1\code\Q4\q4_train_only_dry_run.py
```

输入只包括 P0 通过标记和 `data/processed/cell_labels.csv` 中的 Train 行。脚本绝不读取
Primary/Secondary，不创建新策略的 Q3 特征，不产生正式 Pareto 或最终充电策略。

固定协议见 `methods/Q4/q4_train_only_dry_run_protocol.md`：使用 Train 观测水平格点、raw/SOC
双空间 5-NN、95% 留一距离阈值和 1,000 次 barcode bootstrap 的 80% 支持率门槛。

输出位于 `results/Q4/experiments/train_dry_run_round1/`：

- `tables/q4_train_only_all_candidates.csv`：全部候选及支持状态；
- `tables/q4_q2_provisional_candidates.csv`：仅供后续 pilot 筛查的 `Q2_provisional` 候选；
- `metrics/q4_train_only_dry_run_summary.json`：阈值、流量与配置；
- `figures/q4_train_only_candidate_flow.svg/png`：内部诊断图；
- `q4_train_only_dry_run_report.md`：面向交接的结果与边界。

`Q2_provisional` 只表示 Train 支持域通过，仍需要至少 3 枚物理电芯运行到 Q3 的 `k=100` 后才可能升级；不要将其与正式 Q2+Q3 Pareto 或最终推荐混用。

## k=100 pilot 排程

```powershell
.\.venv\Scripts\python.exe -W error l1\code\Q4\q4_pilot_batch_design.py
```

该脚本在冻结的 1,775 条 `Q2_provisional` 记录中，先列出时间—P3 点预测非支配候选，再选快速端、中间权衡和寿命端各一条代表策略，构成最小 `3 策略 × 3 物理电芯 = 9 电芯` 的 pilot 排程。它不产生正式 Pareto 或最终最优点。

输入、登记与升级规则见 `methods/Q4/q4_k100_pilot_protocol.md`；代表点及中文图见 `results/Q4/experiments/pilot_design_round1/`，独立复审见 `code/Q4/reviews/q4_pilot_batch_design_python_review.md`。

## Pilot 登记表门禁

```powershell
.\.venv\Scripts\python.exe -W error l1\code\Q4\q4_validate_pilot_registry.py
```

默认检查已生成的 9 个空条码槽位；在实际分配条码后，用 `--registry` 指向填写后的登记表。它检查策略、复现数、条码唯一性以及 k=5/k=100 状态前后关系，但不替代 P0 或 Q3。
