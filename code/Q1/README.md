# Q1 首轮描述性基线

本目录的 `q1_baseline.py` 实现 V2.1 第5节规定的描述性分析：寿命分布、官方分区比较、策略参数散点、理论 `tau_0_80`、Train–Primary 重复策略一致性和代表性 SOH 轨迹。

它只读取 P0 冻结数据，不写入原始文件，不选择 Q2/Q3 最终模型，也不将相关性解释为因果。

运行：

```powershell
.\.venv\Scripts\python.exe -W error l1\code\Q1\q1_baseline.py
```

预期输出：

- `results/Q1/experiments/round1/tables/`
- `results/Q1/experiments/round1/figures/`
- `results/Q1/experiments/round1/metrics/q1_key_metrics.json`
- `results/Q1/experiments/round1/logs/q1_baseline.log`
- `results/Q1/experiments/round1/run_summary.json`

## 初稿补充图表

为回答题目中“典型长寿命/短寿命策略”和“实测充电时间”的要求，另运行：

```powershell
.\.venv\Scripts\python.exe -W error l1\code\Q1\q1_enhanced.py
```

该脚本只读取 P0 冻结后的汇总表和循环视图，新增策略级寿命排名、实测充电时间–寿命散点、策略内 SOH 中位轨迹及两张对照表。输出说明见 `results/Q1/q1_paper_draft_notes.md`。
