# Q3 双窗口 Primary 受限确认协议

> **状态**：FROZEN FOR ONE-TIME EXECUTION  
> **人工来源**：Q3-D02/D03（k=5 筛查；k=100 正式窗口且待外部确认）

| 项目 | 冻结内容 |
|---|---|
| 窗口 | 仅 k=5、k=100；不在 Primary 上增删窗口 |
| 训练集 | 仅 41 枚 Train 电芯；每个窗口只用 Train 的 4 折策略分组 CV 选择 Ridge alpha，再以全 Train refit |
| 特征 | P0 正式 12 列早期特征；不读 k 之后的特征 |
| SOH 模板 | 仅用 Train 的真实寿命按 `u=n/L` 对齐并构造非增 isotonic 模板；Primary 不参与拟合 |
| 确认集 | 仅 43 枚 `Prim. Test` 电芯；真实寿命和未来 SOH 只用于事后评分 |
| 正式 SOH 指标 | 电芯等权 `cell_equal_soh_rmse`；观测点合并仅作诊断 |
| 禁止项 | 不在 Primary 选择 alpha、窗口、特征、模板或阈值；不以 Primary 结果回调 Q3；Secondary 不读取 |

## 结果边界

1. k=5 只写为最早筛查结果；不与 k=100 宣称同精度。
2. k=100 保持正式预测窗口，但 Primary 已有探索暴露，结果只能称受限确认，不能称最终独立泛化。
3. 不设事后自动通过阈值；稳定性置信和论文主张范围仍由建模者在 Gate G4.5 裁决。
4. 本协议不为 Q4 新策略制造 Q3 证据；新策略仍须真实运行至 k=100。

## 可复现入口

```powershell
.\.venv\Scripts\python.exe -W error l1\code\Q3\q3_primary_confirmation.py
```

输出固定于 `results/Q3/experiments/primary_confirmation_round1/`，并保存输入、协议与脚本 SHA-256。
