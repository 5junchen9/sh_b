# Secondary 最终压力测试 Python 代码复审

> **状态**：passed_with_warnings  
> **复审对象**：`code/audit/build_secondary_final_freeze_manifest.py`、`run_secondary_final_pressure_test.py`、`verify_secondary_final_pressure_test.py`  
> **运行验证**：2026-08-03，项目 `.venv`，`python -W error`。

## 通过项

1. ✅ `build_secondary_final_freeze_manifest.py:74-75` 要求 Q3 的稳定性与结果人工记录均为 `DECIDED`，未决状态或残留 sentinel 会阻止读取最终集。
2. ✅ `build_secondary_final_freeze_manifest.py:87,114-124` 将 RAW 有效比例门禁、模型参数、2,000 次策略组 bootstrap、脚本与输入 SHA-256 写入 `results/Secondary_final_pressure_test/manifest.json`；清单实测生成成功。
3. ✅ `run_secondary_final_pressure_test.py:216-219` 在评分前逐项核对冻结清单中的脚本/输入哈希；`metrics/run_summary.json` 记录 `inputs_and_scripts_verified=true`。
4. ✅ `run_secondary_final_pressure_test.py:116-130` 对 M3R-k=5 分别合并 Train 与 Secondary 的特征，采用 `validate='one_to_one'` 并阻止 `raw_valid_ratio<0.8`，没有静默删除电芯。
5. ✅ `run_secondary_final_pressure_test.py:156-177,246,252` 以 `policy_table9` 为块进行固定种子 2,000 次 bootstrap；两张原始重抽样表各有 2,000 行，独立复核通过。
6. ✅ `run_secondary_final_pressure_test.py:224-226,305` 仅在 RAW 特征文件齐备后运行，并在审计中记录 Train=41、Secondary=40、`primary_used=false` 与冻结参数。
7. ✅ `verify_secondary_final_pressure_test.py:33-60` 从输出预测表重新计算 Q2/Q3 的误差，检查 40 枚电芯、40 枚曲线可评价、RAW 门禁和无新策略 Pareto；实跑结果为 23/23 通过。

## 修复项

| 文件 | 问题 | 处理 |
|---|---|---|
| `verify_secondary_final_pressure_test.py` | 初版两处嵌套括号造成语法错误 | 仅拆分为中间计数变量；未改变模型或最终测试结果，随后通过 `py_compile` 与实际复核。 |

## 剩余风险

- `run_secondary_final_pressure_test.py` 已被写入冻结清单并完成一次性执行；不得再修改后重跑，也不得据此调参。
- Secondary 只有 8 个策略组，因此差值区间应配合样本结构保守解释，不能当作跨所有充电方案的泛化保证。

## 复现命令

```powershell
.\.venv\Scripts\python.exe -W error l1\code\audit\verify_secondary_final_pressure_test.py
```

## 关键产物

- `results/Secondary_final_pressure_test/manifest.json`
- `results/Secondary_final_pressure_test/tables/bootstrap_intervals.csv`
- `results/Secondary_final_pressure_test/verification.md`

## 后续

先形成外部结果报告并由建模者完成“结论是否升级/收缩”的裁决；不得再执行模型迭代。
