# Q1 表格使用说明

| 文件 | 主要内容 | 用途 |
|---|---|---|
| `q1_cell_level_summary.csv` | 每枚电池的策略、C1、Q1、C2、寿命、早期实测充电时间、SOH 第2圈、理论时间 | 回溯单枚电池、制作附录明细表 |
| `q1_dataset_lifetime_summary.csv` | Train/Primary/Secondary 的样本数、均值、中位数、标准差、最小值、最大值 | 回答第1项基础整理和第2项分区统计 |
| `q1_policy_summary.csv` | 按策略汇总的电池数、寿命均值/标准差和分区构成 | 策略级初步统计 |
| `q1_strategy_lifetime_summary_enhanced.csv` | 在上述基础上增加策略内最小–最大寿命、实测充电时间、理论时间及二者差值 | 图07、图08和论文正文的策略比较 |
| `q1_long_short_strategy_comparison.csv` | 典型长寿命策略与短寿命策略的完整参数对照 | 直接支撑第3、4项，可复制到论文表格 |
| `q1_train_primary_repeated_policy.csv` | Train/Primary 重复策略的均值和差异 | 图05及跨分区一致性说明 |
| `q1_representative_soh_cases.csv` | 图06所用的两个代表性电池 | 复现单电池 SOH 示例 |

建议正文使用 `q1_long_short_strategy_comparison.csv` 的两行汇总，附录保留 `q1_cell_level_summary.csv`。
