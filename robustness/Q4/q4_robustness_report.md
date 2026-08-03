# Q4 已有策略开发池敏感性报告（Round 2，M2-k=100）

> **范围**：仅为已有实验策略的开发池比较提供敏感性证据；不是新策略推荐，也不是最终 Pareto。  
> **数据边界**：Train 41 枚与已暴露的 Primary 43 枚，共 84 枚；Secondary 未读取。  
> **结论状态**：本报告不产生 Q4 最终裁决。新策略的正式 Q2+Q3 Pareto 仍需冻结规则、真实 early-run 数据与 Secondary 压力测试。

## 1. 计算事实

基线口径（策略至少两枚物理电芯、以策略内预测寿命的经验 P10 摘要比较）有 19 个可比较策略，得到 4 个开发池非支配点。四个点分别为 `5.4C(40%)-3.6C`、`5.4C(70%)-3C`、`5.4C(80%)-5.4C` 与 `6C(40%)-3C`。它们都只有 2 枚电芯，因此只能称为开发池案例。

## 2. 已完成的敏感性与边界检查

1. ✓ **样本资格核对**：60 个已有策略中只有 19 个满足 `n≥2`，基线 Pareto 只在这些策略内计算；单电芯策略保留为案例，不混入排名。见 `round2_m2k100/tables/q4_existing_policy_sensitivity.csv`。
2. ✓ **最小样本量收紧**：把资格从 `n≥2` 收紧为 `n≥3` 后，仅剩 3 个可比较策略、2 个新的非支配点，原基线 4 点保留率为 0%。这说明原 4 点的排序无法抵抗样本资格收紧。
3. ✓ **寿命摘要替换**：将经验 P10 摘要替换为策略内中位数时，得到 6 个非支配点，原基线 4 点中有 3 个保留（75%）；结论对寿命风险摘要有实质敏感性。
4. ✓ **来源平衡核对**：要求每个策略至少包含 1 枚 Train 与 1 枚 Primary 时，仍有 19 个可比较策略且 4 个基线点全部保留；该条件下来源构成没有改变基线 Pareto。
5. ✓ **留一电芯检查**：四个基线 Pareto 策略均只有 `n=2`；删去任一电芯后均降为 `n=1`，资格保留率为 0%。未将这种机械失去资格误表述为模型预测失败。
6. ✓ **外部数据隔离**：运行摘要 `q4_existing_policy_summary.json` 记录 `secondary_read=false`、随机种子 `20260802` 与 2,000 次策略内 barcode bootstrap；复现脚本没有读取 Secondary 标签。
7. ✓ **寿命下界口径核对**：报告只把 `empirical_p10` 写作策略内预测的经验低分位摘要，明确它不是重拟合后的置信下界、覆盖率保证或真实寿命 10% 分位。

## 3. 可支持与不可支持的表述

| 表述 | 是否可用 | 依据/限制 |
|---|---|---|
| “在当前开发池和基线资格下，有 4 个已有策略不被时间—经验 P10 摘要严格支配。” | 可用 | 仅描述 19 个 `n≥2` 策略的当前表内关系。 |
| “这 4 个点是稳健的最终最优策略。” | 不可用 | `n≥3` 与留一电芯资格下保留率均为 0%。 |
| “来源平衡不会改变这 4 个点。” | 有条件可用 | 仅在本次“每策略至少 1 Train + 1 Primary”的资格检查下成立。 |
| “新策略已完成 Q2+Q3 推荐。” | 不可用 | 没有新策略真实 k=5/k=100 运行记录，且 Q3/Secondary 仍未冻结。 |

## 4. 产物与复现

- 主结果：`results/Q4/experiments/existing_policy_round2_m2k100/q4_existing_policy_report.md`，含 60 个已有策略和 4 个开发池非支配点。
- 敏感性表：`robustness/Q4/round2_m2k100/tables/q4_existing_policy_sensitivity.csv`。
- 留一资格表：`robustness/Q4/round2_m2k100/tables/q4_existing_policy_pareto_leave_one_cell.csv`。
- 中文图：`robustness/Q4/round2_m2k100/figures/q4_existing_policy_sensitivity.png`。
- 命令：

```powershell
.\.venv\Scripts\python.exe l1\code\Q4\q4_existing_policy_round2_m2k100.py
.\.venv\Scripts\python.exe l1\code\Q4\q4_existing_policy_round2_m2k100_sensitivity.py
```

## 5. 后续边界

当前证据可用于说明“已有策略开发池内的比较对样本量与寿命摘要较敏感”，不能替代 Q4 的正式推荐。真正进入新策略比较的必要顺序仍是：冻结 Q2/Q3 规则 → 新策略真实运行至 k=5 作筛查并继续至 k=100 → 按冻结 Q3 校正 → 形成受约束 Pareto → 一次性 Secondary 压力测试。
