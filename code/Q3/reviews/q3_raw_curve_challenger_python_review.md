# Q3 RAW challenger Python 代码复审

> **状态**：passed_with_warnings  
> **复审者**：python-code-reviewer  
> **日期**：2026-08-03  
> **脚本**：`code/Q3/q3_run_raw_curve_challenger.py`、`code/Q3/q3_raw_curve_challenger_robustness.py`

## 通过项

1. ✅ `q3_run_raw_curve_challenger.py:65-72` 检查 P0 通过，并只筛选 41 枚 `Train` 电芯；Primary/Secondary 没有进入模型、调参或曲线模板。
2. ✅ `:76-82` 对每个窗口以一对一条码合并已冻结早期特征和 Train-only RAW 表，同时检查 RAW 三列存在、合并后仍为 41 枚电芯。
3. ✅ `:80-81` 将 `raw_valid_ratio<0.8` 视为阻断错误而非静默填补；实际五个窗口全通过该门禁。
4. ✅ `:88-93` 以 `GroupKFold(policy_table9)` 生成外层折、显式检查策略组不相交，并只在外层训练折内选择 Ridge alpha。
5. ✅ `:94-103` 复用 Round 2 的外层训练 SOH 模板与截止点锚定逻辑；残差按电芯先算 MSE，再生成正式等权 SOH 指标。
6. ✅ `:105-111` 保存 OOF 寿命预测、逐电芯曲线误差、调参记录、指标和中文 PNG/SVG；实际输出为 205 行寿命预测和 205 行曲线误差（5 窗口×41 电芯），所有数值有限。
7. ✅ `q3_raw_curve_challenger_robustness.py:43-49` 对 M3R 与 Round 2 对照模型进行配对策略组 bootstrap；没有重拟合、也没有读取 Primary/Secondary。

## 失败或修复项

无待修复的代码错误。首次运行与 `py_compile` 均成功。

## 约束方向复核

脚本不含优化不等式。唯一硬门禁是 `raw_valid_ratio≥0.8`，其含义为“至少 80% 早期循环通过 RAW 审计并成功形成特征”，并不代表电芯安全阈值。

## 剩余风险

- M3R-k5 的寿命 `RMSE_log` 和 `MAE_log` bootstrap 区间仍跨 0；不要把其点估计提升写成稳健寿命优势。
- RAW 特征仅在 Train 计算，尚没有为 Primary/Secondary 提取；在锁定前不应拿它进行外部确认或 Q4 正式输入。
- 3 个 RAW 特征来源于 `I>0.1 A` 充电点；这是操作性定义，需在论文方法部分说明。

## 运行方法

```powershell
.\.venv\Scripts\python.exe l1\code\Q3\q3_run_raw_curve_challenger.py
.\.venv\Scripts\python.exe l1\code\Q3\q3_raw_curve_challenger_robustness.py
```

## 预期产物

- `results/Q3/experiments/round3_raw_curve_challenger/tables/m3r_raw_curve_window_metrics.csv`
- `results/Q3/experiments/round3_raw_curve_challenger/tables/m3r_vs_m3_point_comparison.csv`
- `robustness/Q3/round3_raw_curve_challenger/tables/q3_raw_curve_policy_bootstrap.csv`
- `robustness/Q3/round3_raw_curve_challenger/figures/q3_raw_curve_bootstrap.png`

## 下一环节

将 M3R-k5 的 bootstrap 证据合并进 Q3 Round 2 稳健性报告；候选是否保留及稳定性等级仍由 Gate G4.5 决定。
