# Q1 Python 代码复审

> **状态**：passed_with_warnings  
> **对象**：`code/Q1/q1_baseline.py`、`code/Q1/q1_enhanced.py`  
> **用途**：描述性基线与论文候选图，不是因果模型或最终预测模型。

## 明确通过项

1. ✅ 两个脚本均要求 `p0_status=pass`；增强脚本还校验基线表必需字段、124 行及 124 个唯一条码。
2. ✅ 两个脚本只读取 `data/processed/` 和当前 Q1 基线表，所有写入均位于 `results/Q1/experiments/round1/`。
3. ✅ 基线脚本保存脚本及三个输入 SHA-256；增强脚本保存生成时间、脚本哈希、三个输入哈希和独立日志。
4. ✅ 当前哈希均匹配：基线 `ef66b264...9750a2e`，增强 `d7398f64...11ab4c3`。
5. ✅ 完整运行生成 9 张中文 PNG 与 7 张 CSV；标题、坐标、单位、图例及样本范围均可追溯。
6. ✅ 重复策略比较只作 Train–Primary 描述，报告明确 Primary 已有探索暴露，不能当独立未见测试集。
7. ✅ 实测 `chargetime` 与理论 `tau_0_80` 分开绘制和解释，没有把两者混成同一物理量。
8. ✅ 典型长短寿命策略仅从 `n≥2` 的重复策略中选择，并同时给策略内范围和 SOH 区间，避免只挑单枚极端电芯。
9. ✅ 已依次执行 baseline→enhanced 的 `-W error` 全流程，摘要列出的全部产物均存在且非空。

## 剩余边界

- Q1 图只能支持相关和分布描述，不能写成倍率导致寿命变化的因果结论。
- Secondary 的寿命分布差异同时混有批次与策略设计差异。
- 论文若引用增强图，必须连同样本量和“描述性”限定一起引用。

## 复现命令

```powershell
.\.venv\Scripts\python.exe -W error l1\code\Q1\q1_baseline.py
.\.venv\Scripts\python.exe -W error l1\code\Q1\q1_enhanced.py
```

