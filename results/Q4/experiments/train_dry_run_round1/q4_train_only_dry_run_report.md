# Q4 Train-only 候选流量 dry-run

## 状态

本次只完成候选格点、双空间支持域与 barcode bootstrap 支持率审计。通过者均为
`Q2_provisional`，**不是最终推荐，也不进入正式 Q2+Q3 Pareto**。

## 冻结配置

- 格点：Train 离散水平组合；`Q1<80%` 的完整组合加上 `Q1=80%` 时 `C2=C1` 的单阶段分支。
- 距离：Train 中位数/IQR 标准化的 raw `(C1,q,C2_effective)` 与 SOC
  `(E0-20,E20-40,E40-60,E60-80,tau0-80)` 双空间欧氏 5-NN。
- 阈值：留一第 5 邻居距离的 95% 分位，`c_raw=1.2182`，`c_soc=2.8286`。
- 支持率：1000 次 Train barcode bootstrap，门槛 80%。
- Q2 点预测：Train 全量 refit 的 P3 加性样条 GAM，分组 CV 选择 `n_knots=4`、`alpha=0.03`；仅供候选审计，不提供寿命下界。

## 候选流量

| 阶段 | 数量 |
|---|---:|
| 候选格点总数 | 3653 |
| 数学可行 | 3653 |
| 参数边界通过 | 3653 |
| raw 5-NN 通过 | 2858 |
| SOC 5-NN 通过 | 2398 |
| 双空间通过 | 2329 |
| 双空间且支持率≥80%（Q2 暂定候选） | 1775 |

## 使用边界

- 候选表含有点预测只是为了发现明显异常；不把它作为最终寿命或保守寿命下界。
- 新策略必须至少有 3 枚不同物理电芯运行到 Q3 冻结窗口 `k=100`，方可升级为 `Q3_confirmed`。
- Primary/Secondary 均未读取；不得用之后的结果修改本格点、距离阈值或 80% 支持率。
- 单模型下模型分歧统一记录为 `N/A`，不是 0。

## 文件

- 全部候选：`tables/q4_train_only_all_candidates.csv`
- 可供 pilot 的暂定候选：`tables/q4_q2_provisional_candidates.csv`
- 流量和阈值：`metrics/q4_train_only_dry_run_summary.json`
- 图：`figures/q4_train_only_candidate_flow.svg`（内部诊断图）
