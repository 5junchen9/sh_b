# Primary 确认配置账本 Python 复审

> **状态**：passed_with_warnings  
> **复审者**：python-code-reviewer  
> **日期**：2026-08-02  
> **脚本**：`code/audit/build_primary_confirmation_manifest.py`

## 通过项

1. ✓ `build_primary_confirmation_manifest.py:18-19` 从项目相对根目录定位输入和输出，不包含用户机器的绝对数据路径。
2. ✓ `:22-28` 以分块读取计算 SHA-256；账本记录协议、决策、脚本、运行摘要和指标文件的哈希，避免把未追溯的文本当作证据。
3. ✓ `:31, 39-52` 只读取既有 UTF-8 协议和 JSON 摘要，不读取或写入 `data/raw/`，也不读取 Secondary。
4. ✓ `:64` 明确将 Secondary 标记为“未读取并保留给最终压力测试”，与项目数据隔离规则一致。
5. ✓ `:70-97` 从已保存的 Q2-B / Q3 Primary 运行摘要提取候选、参数、窗口、指标和变换，并由 `q3_round2_scope_update.md` 将 Primary 的历史 M3 标签准确重标为 Round 2 M2；不会重新拟合或在 Primary 上选择模型。
6. ✓ `:100-105` 显式记录“确认配置未在 Primary 暴露前建立”“没有自动通过阈值”及 M3/M4/M3R 未获 Primary 确认，未用账本掩盖设计局限。
7. ✓ `:103-104` 创建输出目录并写入可移植 JSON；实际运行和 `py_compile` 已通过，产物为 `outputs/experiments/primary_confirmation_manifest_post_exposure.json`。

## 失败或修复项

无代码失败项。本轮新增的是审计账本，不改变任何模型、特征、窗口、阈值或数据分区。

## 剩余风险

- 账本在 Primary 已暴露之后生成，因而只能作为可追溯性索引，不能替代前瞻预注册。
- Q3 M3、M4 与 M3R 的联合/RAW challenger 仅做了 Train-only 验证；不得由该账本延伸出“经 Primary 确认”的主张。
- JSON 中的 `created_at_utc` 会随重建时间变化；源文件哈希和已保存运行摘要才是证据锚点。

## 运行方法

```powershell
.\.venv\Scripts\python.exe -W error l1\code\audit\build_primary_confirmation_manifest.py
```

## 预期产物

- `outputs/experiments/primary_confirmation_manifest_post_exposure.json`

## 下一环节

- `consistency-auditor`：把账本与 Q2/Q3/Q4 报告交叉核对；正式论文写作前仍须完成外部 Secondary 压力测试。
