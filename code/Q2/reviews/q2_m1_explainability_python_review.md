# Q2 M1 因素排序与解释性补充代码复审

> **状态：passed_with_warnings**  
> **复审脚本：** `code/Q2/q2_m1_explainability.py`  
> **范围：** 已冻结 M1 的 Train-only 条件关联解释；非新模型选型，非因果分析。

## 通过项

1. ✅ 第 26–28 行只读取 P0、`cell_labels.csv` 与既有 M1 OOF 表；主数据在第 128 行严格筛为 Train，Primary/Secondary 不参与拟合、调参或 bootstrap。
2. ✅ 第 43–49 行的 alpha 选择仅在内层 `policy_table9` GroupKFold 内进行；第 52–67 行的外层预测继续按策略组隔离。
3. ✅ 第 133–135 行以逐条码的 `np.allclose(..., atol=1e-12)` 重现并核对原 M1 OOF 预测；运行已通过，说明补充没有改变冻结 M1 数值。
4. ✅ 第 137–151 行的每个删一变量模型与完整 M1 共享外层折，并在第 146–147 行显式阻断折号不一致，保证配对误差差值公平。
5. ✅ 第 70–81 行以策略组为块重抽样完整与删一模型的成对绝对误差，2,000 次重复已保存；不会把同策略的重复记录错误地当作独立抽样单位。
6. ✅ 第 83–96 行以固定的全 Train 内层选择 alpha 对策略组重抽样重拟合标准化系数；输出含区间和主导符号率，未把单次系数直接作为稳定结论。
7. ✅ 第 170–176 行将 OOF、指标、bootstrap、调参表输出为 CSV，并在第 210–214 行保存脚本/输入哈希、随机种子、JSON 摘要和日志。
8. ✅ 脚本通过 `python -m py_compile` 和项目 `.venv` 实跑；完整 M1 MAE_log 为 0.27557，删 C2 后增至 0.29801，增量区间 [0.00662, 0.03781]。

## 约束方向复核

| 位置 | 条件/方向 | 含义 |
|---|---|---|
| 第 114–118 行 | `ΔMAE = MAE_删除后 − MAE_完整` | 正值仅表示删除后折外典型误差上升；不解释为因果贡献。 |
| 第 127 行 | `p0_status == pass` | P0 未通过即阻断解释性补充。 |
| 第 129 行 | `len=41` 且 `groups=40` | 冻结 Train 分区规模与策略组数检查。 |
| 第 146 行 | `fold_ids == ablation_folds` | 所有删一比较使用同一外层策略分组折。 |

## 剩余风险

- `C1`、q 和 `C2` 在两段式协议下相关，删一增量只能表达当前条件预测信息；不应在论文中改写为“独立贡献百分比”。
- q 的删一 ΔMAE 95% 区间 [−0.00032, 0.04050] 跨零，C1 的区间 [−0.03335, 0.00127] 也跨零；两者的稳定排序不足。
- 系数方向与删一预测信息回答的问题不同：前者是线性条件方向，后者是保留其余变量后的预测增量，不能互相替代。

## 运行方式

```powershell
.\.venv\Scripts\python.exe l1\code\Q2\q2_m1_explainability.py
```

## 关键输出

- `results/Q2/experiments/m1_explainability_round1/tables/q2_m1_standardized_coefficients.csv`
- `results/Q2/experiments/m1_explainability_round1/tables/q2_m1_feature_ablation_summary.csv`
- `results/Q2/experiments/m1_explainability_round1/figures/q2_m1_factor_explainability.png`
- `results/Q2/experiments/m1_explainability_round1/q2_m1_explainability_report.md`

## 下一步

将本解释性补充并入 Q2 最终结果分析：保留 M1 的低复杂度关联主线、M2 的交互敏感性，并用删一变量证据限制“因素排序”的措辞。
