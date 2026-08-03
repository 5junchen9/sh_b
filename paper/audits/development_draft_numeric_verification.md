# 开发证据稿核心数字自动回查

> 状态：**PASS**。脚本只读现有结果，不读取 Secondary、不重新拟合模型。

| 文稿片段/数值 | 机器可读来源 | 状态 |
|---|---|---|
| 124 枚电芯和 99,279 行 | `data/processed/p0_summary.json` | PASS |
| 字段—循环掩码 | `data/processed/p0_summary.json` | PASS |
| 801.64 cycle | `data/processed/cell_labels.csv` | PASS |
| 498.75 / 946.50 | `data/processed/cell_labels.csv` | PASS |
| 0.37169 | `results/Q2/experiments/round1/metrics/comparison_metrics.json` | PASS |
| 0.25102 | `results/Q2/experiments/round1/metrics/comparison_metrics.json` | PASS |
| [−0.07245, 0.02620] | `robustness/Q2/metrics/q2_bootstrap_summary.json` | PASS |
| RMSE_log=0.24070 | `results/Q3/experiments/round3_raw_curve_challenger/tables/m3r_raw_curve_window_metrics.csv` | PASS |
| RMSE_log=0.23174 | `results/Q3/experiments/round2_joint/tables/joint_window_metrics.csv` | PASS |
| 3,653 | `results/Q4/experiments/train_dry_run_round1/tables/q4_candidate_flow.csv` | PASS |
| 1,775 | `results/Q4/experiments/train_dry_run_round1/tables/q4_candidate_flow.csv` | PASS |
| 60 个已有策略 | `results/Q4/experiments/existing_policy_round2_m2k100/metrics/q4_existing_policy_summary.json` | PASS |
| 4 个开发池非支配案例 | `results/Q4/experiments/existing_policy_round2_m2k100/metrics/q4_existing_policy_summary.json` | PASS |

所有检查通过后，文稿中的数值仍仅代表开发期证据；本审计不替代 Q3 人工裁决或 Secondary 最终压力测试。
