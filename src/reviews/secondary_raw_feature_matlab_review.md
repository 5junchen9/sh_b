# Secondary RAW 曲线特征 MATLAB 代码复审

> **状态**：passed_with_warnings  
> **复审对象**：`src/extract_q3_raw_curve_features_secondary.m`  
> **兼容目标**：MATLAB；本次已在本机 MATLAB batch 实跑。

## 通过项

1. ✅ `extract_q3_raw_curve_features_secondary.m:1,105` 的主函数与文件同名，采用普通 `.m` 函数和局部函数，不依赖 Live Script、GUI、Simulink 或并行工具箱。
2. ✅ `:8-11` 使用项目相对根目录定位输入与输出，并将新文件限定写入 `results/Secondary_final_pressure_test/inputs`；未覆盖 Train-only 特征或 `.mat` 原始数据。
3. ✅ `:19-30` 逐行对齐 `(source_file,batch_index,cycle_index)` 深层审计键，并检查 P0 复制的 RAW 掩码与原审计表一致。
4. ✅ `:49-58` 仅对 `raw_usable_for_curve_features` 为真且 `I>0.1 A` 的充电点提取电压统计量；空段或非有限值不被填补。
5. ✅ `:76-86` 只生成 k=5、100 两个冻结窗口；任一 `raw_valid_ratio<0.8` 或三项特征缺失都会报错，而不会删整枚电芯。
6. ✅ `:89-100` 以 UTF-8 CSV/JSON 输出特征与摘要；实跑生成 40 枚 Secondary 电芯，k=5/k=100 的最小有效比例均为 1.0。

## 约束方向复核

本脚本不含资源分配或优化不等式；唯一数值门禁为 `valid_ratio < 0.8`（`:85`），其含义是“RAW 特征构造可用性下限”，不是电池安全阈值。

## 剩余风险

- `matfile` 读取嵌套记录耗时较长；本次约 12 分钟，但这是换取逐循环审计映射的计算代价。
- 代码使用 `matfile`、`readtable` 和 `jsonencode`；如改在其他 MATLAB 兼容环境运行，应先做 API 兼容性检查。

## 复现命令

```powershell
D:\13470\matlab\bin\matlab.exe -batch "addpath(fullfile(pwd,'l1','src')); extract_q3_raw_curve_features_secondary"
```

## 后续

该特征提取已服务于唯一一次 Secondary 评分；不得重新提取后选择不同特征或窗口。
