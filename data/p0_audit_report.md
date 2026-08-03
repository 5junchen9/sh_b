# P0 数据审计报告

## 审计结论

**通过。** 正式建模长表已按官方寿命端点截断，七个汇总字段采用字段—循环级掩码；任何异常都没有导致整行或整枚电芯被静默删除。五个早期窗口由同一脚本生成且通过机器校验。

## 冻结规则

- EOL：仅保留 `global_cycle_index < cycle_life_table9`，共 99,279 行、124 枚电芯。
- 早期窗口：统一使用 `2 <= global_cycle_index <= k`，`k = 5,10,20,50,100`。
- 确定性掩码：非有限值、非负字段的负值、全零占位、温度次序冲突。
- 统计掩码：只对 `chargetime` 使用 Train 拟合的 `Q99 × 5`；`Q99=18.0101474`，冻结上界 `90.050737`。
- 其他字段未设置统计阈值，因为现有资料不足以支持单位相关的物理边界；保留真实跨批次分布差异。
- 缺失处理：P0 不填补、不标准化；两点变化特征严格要求 cycle 2 与 cycle k 均有效。
- RAW 曲线审计按 `(barcode, source_file, batch_index, cycle_index)` 四字段键连接，仅提供未来 challenger 的可用性标志。

## 字段掩码汇总

| 字段 | 无效字段—循环数 | 原因 |
|---|---:|---|
| QDischarge | 41 | all_zero_placeholder: 41 |
| QCharge | 41 | all_zero_placeholder: 41 |
| IR | 41 | all_zero_placeholder: 41 |
| Tmax | 41 | all_zero_placeholder: 41 |
| Tavg | 41 | all_zero_placeholder: 41 |
| Tmin | 41 | all_zero_placeholder: 41 |
| chargetime | 55 | all_zero_placeholder: 41; train_q99_x5_upper: 14 |

## 输出与校验和

| 文件 | 行数 | SHA-256 |
|---|---:|---|
| `data/processed/cycle_model_view.csv` | 99,279 | `c8cef3e86a2472e92f37253333e9b853c43164a1bc6a976bff8977b150f45e75` |
| `data/processed/early_features_k5.csv` | 124 | `d26e8149ca236ff514d6a711b78905c64635c41bccc3837fc1790ad9c6419400` |
| `data/processed/early_features_k10.csv` | 124 | `e5c97421bbe0618e1efdc5161440644866ba168f2f2a15d9c3e16ff844d2068f` |
| `data/processed/early_features_k20.csv` | 124 | `0bc6d996eaeff3588a4dad2bd9bf3a65dc361a4c12c111b7d0442a00f65ff2dd` |
| `data/processed/early_features_k50.csv` | 124 | `d253860ee796a6c96830124d1eb4a3e28c13a3b43e87f5c6e67d43bb69f04460` |
| `data/processed/early_features_k100.csv` | 124 | `607b789e1a37ce582087f882c05d329b5635d16bfd08cd4bd69758156b7b159e` |

`p0_summary.json` 另记录输入 SHA-256、脚本 SHA-256、随机种子 20260802、阈值来源及全部机器检查。

## 通过项

- [x] `official_cell_count_124`
- [x] `retained_row_count_99279`
- [x] `unique_barcode_global_cycle`
- [x] `every_cell_has_L_minus_1_rows`
- [x] `all_cycles_before_eol`
- [x] `raw_audit_join_complete`
- [x] `cycle2_capacity_reference_complete`
- [x] `anomaly_does_not_remove_cells`
- [x] `threshold_fit_uses_train_only`
- [x] `window_k5_has_124_rows`
- [x] `window_k5_one_row_per_cell`
- [x] `window_k5_expected_cycle_denominator`
- [x] `window_k5_QDischarge_counts_traceable`
- [x] `window_k5_QCharge_counts_traceable`
- [x] `window_k5_IR_counts_traceable`
- [x] `window_k5_Tmax_counts_traceable`
- [x] `window_k5_Tavg_counts_traceable`
- [x] `window_k5_Tmin_counts_traceable`
- [x] `window_k5_chargetime_counts_traceable`
- [x] `window_k10_has_124_rows`
- [x] `window_k10_one_row_per_cell`
- [x] `window_k10_expected_cycle_denominator`
- [x] `window_k10_QDischarge_counts_traceable`
- [x] `window_k10_QCharge_counts_traceable`
- [x] `window_k10_IR_counts_traceable`
- [x] `window_k10_Tmax_counts_traceable`
- [x] `window_k10_Tavg_counts_traceable`
- [x] `window_k10_Tmin_counts_traceable`
- [x] `window_k10_chargetime_counts_traceable`
- [x] `window_k20_has_124_rows`
- [x] `window_k20_one_row_per_cell`
- [x] `window_k20_expected_cycle_denominator`
- [x] `window_k20_QDischarge_counts_traceable`
- [x] `window_k20_QCharge_counts_traceable`
- [x] `window_k20_IR_counts_traceable`
- [x] `window_k20_Tmax_counts_traceable`
- [x] `window_k20_Tavg_counts_traceable`
- [x] `window_k20_Tmin_counts_traceable`
- [x] `window_k20_chargetime_counts_traceable`
- [x] `window_k50_has_124_rows`
- [x] `window_k50_one_row_per_cell`
- [x] `window_k50_expected_cycle_denominator`
- [x] `window_k50_QDischarge_counts_traceable`
- [x] `window_k50_QCharge_counts_traceable`
- [x] `window_k50_IR_counts_traceable`
- [x] `window_k50_Tmax_counts_traceable`
- [x] `window_k50_Tavg_counts_traceable`
- [x] `window_k50_Tmin_counts_traceable`
- [x] `window_k50_chargetime_counts_traceable`
- [x] `window_k100_has_124_rows`
- [x] `window_k100_one_row_per_cell`
- [x] `window_k100_expected_cycle_denominator`
- [x] `window_k100_QDischarge_counts_traceable`
- [x] `window_k100_QCharge_counts_traceable`
- [x] `window_k100_IR_counts_traceable`
- [x] `window_k100_Tmax_counts_traceable`
- [x] `window_k100_Tavg_counts_traceable`
- [x] `window_k100_Tmin_counts_traceable`
- [x] `window_k100_chargetime_counts_traceable`
- [x] `raw_source_hashes_unchanged`
- [x] `all_p0_checks_pass`

## 仍需在后续显式处理的限制

1. `IR` 单位已确认是 Ω，`chargetime` 单位已确认是 min；但前者的测量时点、后者的起止点与 CV 覆盖尚无字段元数据。论文中仍须保守表述，不能据此设置题外安全阈值或将实测时间等同于理论 `tau_0-80`。
2. P0 没有执行模型填补、标准化或特征选择；这些参数须在后续 Train 内层折中重新拟合。
3. RAW 曲线字段有独立深层掩码；若启用 RAW challenger，必须继续沿用长表中的连接标志，不能回退到整枚电芯删除。
