# Q4 已有策略 Round 2（M2-k100）Python 代码复审

> **状态**：passed_with_warnings  
> **复审者**：python-code-reviewer  
> **日期**：2026-08-03  
> **脚本**：`code/Q4/q4_existing_policy_evaluation.py`、`code/Q4/q4_existing_policy_round2_m2k100.py`、`code/Q4/q4_existing_policy_round2_m2k100_sensitivity.py`

## 通过项

1. ✅ `q4_existing_policy_round2_m2k100.py:18-22` 只替换 Q3 Round 2 M2-k100 的 Train OOF 输入和输出目录，保留历史 Round 1 目录，避免把旧 M2 早期特征结果误写成联合 M3。
2. ✅ `q4_existing_policy_evaluation.py:99-100` 明确断言开发池为 84 个唯一的 Train/Primary 条码；不读取 `Sec. test`。
3. ✅ `:107-115` 在输入表含 `model_id` 时显式过滤 `M2` 且 `k=100`；历史表没有 `model_id` 时仍能兼容读取，避免把 Round 2 的四个候选混入同一策略。
4. ✅ `:125-130` 对 SOH120 表执行同样的 `M2/k=100` 过滤，再以条码一对一并入；脚本检查每枚电芯都有成对 Q2/Q3 寿命预测，防止无声缺失。
5. ✅ `:145-151` 将 Train 预测标记为交叉拟合开发证据、Primary 标记为冻结确认；输出文档明确不是独立外部验证。
6. ✅ `:54-62, 171-181` Pareto 只在至少两枚物理电芯且存在 SOH120 证据的已有策略中计算；单电芯策略保留为案例而不进入 Pareto。
7. ✅ 实际运行、`py_compile` 均成功：得到 84 枚电芯、60 个已有策略、4 个开发池内非支配案例；敏感性脚本确认四点均为 n=2，收紧到 n≥3 或留一电芯时保留率均为 0%。

8. ✓ `q4_existing_policy_evaluation.py:237` 使用 `OUT.name` 写入 JSON 的 `round` 字段；重跑后的 Round 2 摘要为 `existing_policy_round2_m2k100`，不再与输出目录发生轮次漂移。
9. ✓ `q4_existing_policy_evaluation.py:212` 将已生成的 Primary 确认配置账本写入报告，并明确其为事后重建、不能把 Primary 改称独立测试；主脚本和敏感性脚本已随此改动重跑。

## 失败或修复项

| # | 文件:行 | 问题 | 处理 | 状态 |
|---:|---|---|---|---|
| 1 | `q4_existing_policy_evaluation.py:107,125` | 初版只适配 Round 1 无 `model_id` 的表，直接读 Round 2 会混入四种模型。 | 已增加有 `model_id` 时的 M2/k=100 显式筛选，并以新入口输出 Round 2 目录。 | 已修复并运行 |
| 2 | `q4_existing_policy_evaluation.py:237` | JSON 的 `round` 曾写死为 `existing_policy_round1`。 | 改为 `OUT.name` 后重跑主脚本和敏感性脚本。 | 已修复并运行 |
| 3 | `q4_existing_policy_evaluation.py:212` | 输出报告未指向 Primary 确认的可追溯配置账本。 | 增加账本路径及“事后重建、非前瞻预注册”的限制说明后重跑。 | 已修复并运行 |

## 约束方向复核

脚本仅进行已有策略的 Pareto 过滤：`q4_existing_policy_evaluation.py:54-62` 正确使用“理论时间更小、经验寿命摘要更大”作为支配关系。没有资源分配或物理不等式约束。

## 剩余风险

- 每个非支配策略仅两枚电芯，且由一枚 Train OOF 与一枚已暴露 Primary 组成；只能称开发池案例，不能写为稳健最终推荐。
- `empirical_p10` 是策略内预测的经验下分位摘要，不是全流水线 bootstrap、预测区间或真实寿命 10% 分位数。
- Q2 P3 仍是 provisional 代理；Q3 M2-k100 尚待 Q3 Gate G4.5 与最终 Secondary 压力测试，因而本输出不得进入正式新策略 Pareto。

## 运行方法

```powershell
.\.venv\Scripts\python.exe l1\code\Q4\q4_existing_policy_round2_m2k100.py
.\.venv\Scripts\python.exe l1\code\Q4\q4_existing_policy_round2_m2k100_sensitivity.py
```

## 预期产物

- `results/Q4/experiments/existing_policy_round2_m2k100/tables/q4_existing_policy_summary.csv`
- `results/Q4/experiments/existing_policy_round2_m2k100/figures/q4_existing_policy_pareto.png`
- `robustness/Q4/round2_m2k100/tables/q4_existing_policy_sensitivity.csv`
- `robustness/Q4/round2_m2k100/figures/q4_existing_policy_sensitivity.png`

## 下一环节

等待 Q3 模型/窗口门禁后，才可把同一口径作为 Q4 已有策略背景案例；没有真实新策略 pilot 时不得生成 Q3-confirmed 新策略或正式推荐。
