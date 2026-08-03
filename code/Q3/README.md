# Q3：早期运行数据的寿命与 SOH 校正

## Round 2（当前候选比较）

运行：

```powershell
.\.venv\Scripts\python.exe -W error l1\code\Q3\q3_run_joint_comparison.py
```

该脚本严格只读取 Train 的 P0 处理结果，并按 `policy_table9` 做嵌套分组验证。它在五个截止窗口 `k=5/10/20/50/100` 下比较：

- M1：策略参数 Ridge（设计前基线）；
- M2：早期运行特征 Ridge；
- M3：策略参数与早期运行特征的直接联合 Ridge；
- M4：每个外层折内重新交叉拟合冻结 P3 策略先验，再以早期特征校正残差。

每个外层训练折独立生成单调 SOH 模板；正式 SOH 指标按电芯等权。结果写入 `results/Q3/experiments/round2_joint/`。Round 2 为 Train-only 候选比较，**不会自动锁定模型、窗口或 Q4 推荐**。

## 历史 Round 1

`q3_run_all.py` 是仅使用早期特征的历史诊断脚本；它不能再被称为 V2.1 规定的“策略＋早期特征联合模型”。其旧 Primary 输出也不得作为 Round 2 候选的确认结果。
