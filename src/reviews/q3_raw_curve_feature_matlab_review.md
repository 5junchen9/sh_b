# Q3 RAW 曲线特征 MATLAB 代码复审

> **状态**：passed_with_warnings  
> **复审者**：matlab-code-reviewer  
> **日期**：2026-08-03  
> **脚本**：`src/extract_q3_raw_curve_features.m`  
> **兼容性目标**：MATLAB（北太天元需另测 `matfile`、`jsonencode` 与 `prctile`）

## 通过项

1. ✅ `src/extract_q3_raw_curve_features.m:7-13` 使用相对项目根目录读取 P0 处理表和深层审计表，未以写入方式打开任何 `.mat` 原始文件。
2. ✅ `:19` 严格选择 `dataset_table9 == "Train"`、cycle 2–100；脚本没有把 Primary 或 Secondary 电芯写入 RAW challenger 特征表。
3. ✅ `:22-28` 以 `source_file|batch_index|cycle_index` 将 P0 曲线行与 `mat_deep_cycle_flags.csv` 一对一匹配，并在两处 raw 可用掩码不一致时中止，而非静默采用未审计曲线。
4. ✅ `:46-63` 仅在 `raw_usable_for_curve_features` 为真时读取 `V/I`；`I>0.1 A` 明确限定充电点，空充电段或非有限电压保留为缺失，不删除整枚电芯。
5. ✅ `:31-36,52-58` 对每个源文件—batch 缓存 MATLAB record，修复了逐循环反复读取嵌套记录导致的超时风险；重跑成功并生成五个 CSV 与 JSON 摘要。
6. ✅ `:79-102` 每个窗口均显式保存期望循环数、有效数、有效比例及 3 个低维特征；实际结果为 41 枚 Train 电芯全覆盖，k=5–50 最低有效比例 1.0，k=100 为 0.9899，均未触发低于 80% 的门禁。
7. ✅ `:103-112` 产物采用 UTF-8 CSV/JSON，可被 Python Q3 challenger 读取；没有 GUI、Live Script、Simulink、并行/深度学习工具箱依赖。

## 修复项

| # | 文件:行 | 问题 | 处理 | 状态 |
|---:|---|---|---|---|
| 1 | `extract_q3_raw_curve_features.m:26,48` | `readtable(..., TextType='string')` 在当前 MATLAB 会把布尔列导入为字符串，直接 `logical(...)` 报错。 | 增加 `as_logical` 本地函数，兼容逻辑型和字符串型 `true/1`。 | 已修复并完整运行 |
| 2 | `:52-58` | 初版每循环从 `matfile` 取整条 record，运行超过前台超时。 | 加入按 source/batch 的 record 缓存；随后完整产物已写出。 | 已修复并完整运行 |

## 约束方向复核

本脚本不含优化不等式约束。唯一筛选是深层审计掩码与 `I>0.1 A` 的充电点定义，均作为特征提取范围而非物理安全约束。

## 剩余风险

- `:54` 的 `I>0.1 A` 是可解释的充电段操作定义，而不是题目提供的物理阈值；论文应说明这是 RAW challenger 的特征提取规则。
- `:59-60` 的 95% 分位充电电压接近 3.6 V 上限，方差很小；后续模型必须以 Train 分组 bootstrap 而非点估计判断其是否带来实质增益。
- `matfile` 对大型 v7.3 文件速度较慢；当前缓存方式在本机可运行，但北太天元兼容性与大文件读取性能未验证。

## 运行方法

```powershell
D:\13470\matlab\bin\matlab.exe -batch "addpath(fullfile(pwd,'l1','src')); extract_q3_raw_curve_features"
```

## 预期产物

- `data/processed/raw_curve_features_train_k5.csv` 至 `raw_curve_features_train_k100.csv`
- `data/processed/raw_curve_features_train_summary.json`

## 下一环节

`python-code-reviewer`/`robustness-checker`：在相同策略分组 OOF 下审查 M3R challenger，并以 bootstrap 决定是否保留为早期筛查候选。
