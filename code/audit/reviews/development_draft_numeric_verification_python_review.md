# 开发证据稿数字回查 Python 代码复审

> **状态**：passed_with_warnings  
> **复审者**：python-code-reviewer  
> **日期**：2026-08-03  
> **脚本**：`code/audit/verify_development_draft.py`

## 通过项

1. ✅ `verify_development_draft.py:16-19` 以项目根目录派生相对路径，并把输出限制在 `paper/audits/`；没有硬编码用户机器路径。
2. ✅ `:22-31` 使用标准库 `csv` 与“唯一行”断言读取结果表；若模型/窗口选择条件不唯一或缺失会停止，不会任选一行。
3. ✅ `:44-47` 只读 P0 摘要，核对 P0 通过状态和 99,279 行正式视图，并将相应文稿片段加入回查记录。
4. ✅ `:49-57` 从 124 个 `cycle_life_table9` 标签重算均值、中位数和线性分位数；修复前的错误中点分位数已改为与标准线性分位定义一致的 498.75、736.5、946.5。
5. ✅ `:59-65` 分别核对 Q2 M1/M2 指标和 bootstrap 决策事实 `mae_ci_upper_lt_zero=False`；脚本未把 M2 提升为主模型。
6. ✅ `:67-72` 使用 `model_id,k` 的唯一条件分别读取 M3R-k=5 和 M2-k=100；检查寿命与 SOH 指标均与论文片段对应。
7. ✅ `:74-81` 核对 Q4 候选流量、已有策略数、非支配案例数以及 `secondary_read=False`；没有打开任何 Secondary 文件。
8. ✅ `:83-94` 将逐项结果保存为 JSON 和 Markdown，而非只在控制台打印；实际运行返回 `PASS`、13 项检查、`secondary_read=false`。
9. ✅ 已执行 `python -W error l1/code/audit/verify_development_draft.py` 与 `python -m py_compile`，均返回 0。

## 失败或已修复项

| # | 文件:行 | 问题 | 处理 | 状态 |
|---|---|---|---|---|
| 1 | `verify_development_draft.py:52,54` | 初版把 25%/75% 分位数误按相邻两个样本的中点计算，和文稿采用的线性分位口径不一致。 | 改为按位置 30.75、92.25 线性插值；重跑后通过。 | 已修复 |

## 约束方向复核

本脚本不含优化或物理不等式约束。Q4 的“支持率不低于 80%”只作为现有结果表的键值核对，不在脚本中重新计算或改变阈值。

## 剩余风险

- 当前仅回查最关键的 13 项文稿片段，不替代全文逐字数值抽取。
- 该脚本验证“文稿数值与当前结果文件一致”，不验证这些模型是否已取得最终外部泛化资格。
- 写作修改后应重新运行此脚本；若增加新的关键数值，应同步增加一条显式检查。

## 复现命令

```powershell
.\.venv\Scripts\python.exe -W error l1\code\audit\verify_development_draft.py
.\.venv\Scripts\python.exe -m py_compile l1\code\audit\verify_development_draft.py
```

## 预期输出

- `paper/audits/development_draft_numeric_verification.json`
- `paper/audits/development_draft_numeric_verification.md`

## 建议后续

冻结后运行 `secondary_final_pressure_test_protocol.md` 所述的一次性脚本，并以同一回查脚本扩充 Secondary 外部指标条目；当前不应使用 Secondary 反向调整模型或文稿结论。
