# L1 代码逻辑说明（当前仅 Q1 描述性基线）

实现目标：执行 V2.1 第5节的可复现 Q1 基线统计，不承担 Q2/Q3 模型选型。

- 实现语言：Python 3.12。
- 输入：`data/processed/cell_labels.csv`、`data/processed/cycle_model_view.csv`、`data/processed/p0_summary.json`。
- 核心口径：124 枚官方电芯；P0=pass；理论 `tau_0_80` 与实测 `chargetime` 分开；同策略按分区内寿命均值比较。
- 输出：`results/Q1/experiments/round1/` 下的表、图、指标、日志和运行摘要。
- 非目标：不拟合或锁定 Q2/Q3 最终模型；不读取 Primary/Secondary 来选择模型；不修改数据。

后续 Q2/Q3 必须在 G1 与 G2/G2.5 门禁通过后另建独立代码逻辑说明。

## Q2/Q3 Round 1 实现计划（G2.5 已获建模者选择）

- 实现语言：Python 3.12；随机种子 `20260802`；仅依赖 numpy、pandas、scikit-learn、matplotlib。
- 冻结输入：`data/processed/p0_summary.json` 必须为 pass；`cell_labels.csv`、五套 `early_features_k*.csv` 与 `cycle_model_view.csv` 只读。
- 验证：外层仅 Train、按 `policy_table9` 分组；内层同样按策略分组选择 Ridge 正则化强度。Primary 与 Secondary 不得在本轮读取。

### Q2-M2：二阶交互 Ridge

1. 对 `C1/Q1_percent/C2` 构造主效应、平方项和两两交互；以 `ln(cycle_life_table9)` 为目标。
2. 外层 policy-group OOF；每一外层折内进行标准化、二阶展开和内层正则化选择。
3. 写出 OOF 预测、原尺度系数/交互项、折级指标和策略级误差；M1 主效应 Ridge 同步作为基线。

### Q3-M3：早期 Ridge + 单调 SOH 模板

1. 对每个 `k=5/10/20/50/100`，仅使用相应早期特征表，在每个外层训练折内选择 Ridge 正则化。
2. 用该折训练电芯的 `SOH_nom` 与真实训练寿命构建电芯等权、非增 isotonic 模板；验证电芯只使用预测寿命与截止点 SOH 双端锚定。
3. 输出寿命 OOF、未来 SOH 点级/电芯等权误差、可用率、模板失败率和端点一致性；M1寿命 Ridge为基线，M3为联合主线。

### 结果结构

```text
results/Q2/experiments/round1/{figures,tables,metrics,logs,run_summary.json}
results/Q3/experiments/round1/{figures,tables,metrics,logs,run_summary.json}
```

每个 `run_summary.json` 记录：问题、轮次、脚本 SHA-256、输入 SHA-256、种子、外/内层分组规则、方法状态、输出列表、核心指标、警告与失败计数。下一技能：`python-model-code-generator`。
