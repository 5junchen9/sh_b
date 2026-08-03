# Secondary 最终压力测试独立复核

> 状态：**pass**。

## 通过项

1. ✅ `frozen_manifest_has_no_retuning_rule`：实际 `True`；预期 `True`。
2. ✅ `run_marks_primary_unused`：实际 `False`；预期 `False`。
3. ✅ `secondary_partition_is_40_unique_cells`：实际 `{'unique': 40, 'm1_rows': 40}`；预期 `{'unique': 40, 'm1_rows': 40}`。
4. ✅ `q2_M1_rmse_recomputed`：实际 `0.5472460445065896`；预期 `0.5472460445065898`。
5. ✅ `q2_M1_mae_recomputed`：实际 `0.4980708837204658`；预期 `0.4980708837204659`。
6. ✅ `q2_M2_rmse_recomputed`：实际 `0.5427978926458085`；预期 `0.5427978926458085`。
7. ✅ `q2_M2_mae_recomputed`：实际 `0.5079624762646341`；预期 `0.5079624762646342`。
8. ✅ `q2_P3_rmse_recomputed`：实际 `0.6778120740894927`；预期 `0.6778120740894927`。
9. ✅ `q2_P3_mae_recomputed`：实际 `0.6307695727312699`；预期 `0.63076957273127`。
10. ✅ `q3_M2_k5_rmse_recomputed`：实际 `0.4193015943867422`；预期 `0.4193015943867422`。
11. ✅ `q3_M2_k5_soh_recomputed`：实际 `0.06200724073551071`；预期 `0.062007240735511`。
12. ✅ `q3_M2_k5_all_cells_curve_evaluable`：实际 `{'curve_cells': 40, 'failures': 0}`；预期 `{'curve_cells': 40, 'failures': 0}`。
13. ✅ `q3_M3R_k5_rmse_recomputed`：实际 `0.4924530692800105`；预期 `0.4924530692800106`。
14. ✅ `q3_M3R_k5_soh_recomputed`：实际 `0.07202307657009045`；预期 `0.0720230765700907`。
15. ✅ `q3_M3R_k5_all_cells_curve_evaluable`：实际 `{'curve_cells': 40, 'failures': 0}`；预期 `{'curve_cells': 40, 'failures': 0}`。
16. ✅ `q3_M2_k100_rmse_recomputed`：实际 `0.4695040546243606`；预期 `0.4695040546243608`。
17. ✅ `q3_M2_k100_soh_recomputed`：实际 `0.06908360848236537`；预期 `0.0690836084823657`。
18. ✅ `q3_M2_k100_all_cells_curve_evaluable`：实际 `{'curve_cells': 40, 'failures': 0}`；预期 `{'curve_cells': 40, 'failures': 0}`。
19. ✅ `raw_feature_gate_k5`：实际 `{'cells': 40, 'min_valid_ratio': 1, 'cells_below_80pct_valid': 0}`；预期 `40 cells and valid ratio >= 0.8`。
20. ✅ `raw_feature_gate_k100`：实际 `{'cells': 40, 'min_valid_ratio': 1, 'cells_below_80pct_valid': 0}`；预期 `40 cells and valid ratio >= 0.8`。
21. ✅ `bootstrap_has_fixed_2000_repeats`：实际 `{'q2': 2000, 'q3': 2000}`；预期 `2000`。
22. ✅ `bootstrap_has_no_pareto_or_recommendation`：实际 `no new-strategy Pareto file`；预期 `no new-strategy Pareto file`。
23. ✅ `result_files_hashable`：实际 `SHA-256 computed`；预期 `nonempty files`。
