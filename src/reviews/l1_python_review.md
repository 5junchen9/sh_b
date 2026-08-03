# L1 Python Code Review

> **Status**: failed
> **Reviewer**: python-code-reviewer
> **Date**: 2026-08-02
> **Scripts reviewed**: `src/audit_l1_data.py`, `src/compare_xlsx_to_table9.py`, `src/prepare_cycle_data.py`
> **Scope note**: 当前目录没有已冻结的方法方案或论文正文；本报告仅审查数据审计/整理代码和对应操作，不批准后续建模。

## 结论

名册冻结、文件保护和基础对账总体可靠，但 `early_cycle_features.csv` 当前不可用于建模。5 个续测电芯的片段顺序与原始 `batch_date` 相反；同时 41 个全零占位循环和 14 个极端充电时间循环未被异常规则识别，其中分别有 36 个和 3 个进入前 100 循环窗口。

## Pass Items

1. ✅ `src/audit_l1_data.py:29-34` 以流式 SHA-256 固定源文件版本；复核三份 MAT 哈希均与审计报告一致。
2. ✅ `src/audit_l1_data.py:31`、`src/compare_xlsx_to_table9.py:30`、`src/prepare_cycle_data.py:25` 均以只读方式打开源附件；代码中不存在对 MAT/XLSX 源文件的写入。
3. ✅ `src/compare_xlsx_to_table9.py:67-69` 强制要求 PDF 文本解析得到 124 个唯一 Table 9 条码；独立复核正式名册为 124 行且条码唯一。
4. ✅ `src/compare_xlsx_to_table9.py:112-123` 使用“源文件—批次—循环”复合键检查循环重复，并对汇总长度、Vdlin 长度与元数据声明进行对账。
5. ✅ `src/compare_xlsx_to_table9.py:147-168` 只把论文 Table 9 的寿命、分区、C1/Q1/C2 写入冻结名册；本地冲突标签未进入正式字段。
6. ✅ `src/prepare_cycle_data.py:59-62` 通过已对账的“源文件—批次”映射排除 11 个论文名册外条码；独立复核派生数据只含 124 个正式条码。
7. ✅ `src/prepare_cycle_data.py:80-90` 在不重排源记录的前提下检查片段内循环索引；100,501 行派生记录中未发现重复或逆序索引。
8. ✅ `src/prepare_cycle_data.py:115-160` 将结果保存为 CSV/JSON，路径均位于 `l1/data/processed/`；输出行数独立复核为标签 124、循环汇总 100,501、候选特征 124。
9. ✅ 三个 Python 文件均为普通脚本、无随机过程、无网络调用、无硬编码到工作区外的写入路径。

## Failed / Blocking Items

| # | 严重性 | 位置 | 问题 | 证据 | 状态/建议 |
|---|---|---|---|---|---|
| 1 | BLOCKING | `src/prepare_cycle_data.py:92-103` | 续测片段顺序写反。代码固定 `data_2 → data_1`，而原始 MAT 的 `batch_date` 为 `data_1=2017-05-12`、`data_2=2017-06-30`。 | 5 个重复条码的候选特征当前都标记来源为 `data_2.xlsx`，即把后续批次当作前 100 循环。 | 应改为按 MAT `batch_date` 排序，而非硬编码文件名；重新生成循环全局索引和早期特征。修复前禁止建模。 |
| 2 | BLOCKING | `src/prepare_cycle_data.py:34-35,74-75,128-135` | “非负”不是充分的有效性规则，零占位和极端异常被纳入特征。 | 100,501 行中有 41 行七个核心字段全为 0，其中 36 行进入当前前 100 循环；另有 14 行 `chargetime>100`，而中位数约 10.335、P99=20，其中 3 行进入早期窗口。脚本却报告 `core_invalid_row_count=0`。 | 增加全零占位掩码及基于字段定义/稳健统计的异常标记；不得静默删除，特征聚合只使用明确有效循环并报告窗口样本数。 |
| 3 | BLOCKING | `src/prepare_cycle_data.py:56-58,143-158` | 当前代码读取的是 Excel 的“循环汇总”，没有从 MAT 扫描 `cycles.t/Qc/I/V/T/Qd`；却把总体状态写成 `ready_with_warnings`。 | `data/data_report.md` 同时承认原始数组尚未全量扫描。因此这只是汇总级整理，不是已完成的曲线级清洗。 | 在原始数组审计完成前，状态应为“汇总基线可用、原始曲线特征阻塞”；不要把当前产物交给电压曲线/增量容量模型。 |
| 4 | WARNING | `src/audit_l1_data.py:60-69,115-119` | Excel 工作簿缺少维度缓存时 `ws.max_row=None`，库存脚本把行数打印为 0。 | 当前 `inventory.json` 三个工作簿的所有 sheet `rows` 均为 `null`，控制台汇总为 0，与实际 114,738 行汇总数据不符。 | 通过迭代计数或读取工作表 XML 维度，不应把未知值折算成 0。 |
| 5 | WARNING | `src/audit_l1_data.py:77-79` 与 `outputs/data_audit/data_audit_report.md:25` | 当前环境没有 `h5py` 时脚本只写 `pending_matlab_h5info`；报告中的 MAT 顶层结构来自人工 MATLAB 命令，没有保存为可复现脚本或日志。 | 重新运行 `audit_l1_data.py` 无法独立重建报告中的 MAT 结构结论。 | 增加轻量 MATLAB 审计脚本并保存 JSON/日志，或在报告中明确人工命令及输出路径。 |
| 6 | WARNING | `src/prepare_cycle_data.py:129-135` | `early_cycle_features.csv` 同时含数值目标 `cycle_life_table9`、批次索引和候选特征，但没有特征白名单。 | 下游若按数值列自动建模，会把寿命标签或批次编号当输入，造成直接泄漏或批次混杂。 | 输出单独的特征列清单，或把标签与特征物理分表并在建模脚本显式指定 `X` 与 `y`。 |

## Cross-Artifact Consistency

- ✅ 报告中的 124 个正式条码、135 个本地唯一条码、140 条原始记录与 JSON/CSV 一致。
- ✅ 报告中的 5 个重复条码和 11 个名册外条码与对账 JSON 一致。
- ✅ 三份 MAT 合计 8,269,341,808 bytes，哈希与当前源文件一致。
- ✅ `cycle_summary_clean.csv` 为 100,501 行，`early_cycle_features.csv` 为 124 行，与准备摘要一致。
- ❌ `data/data_report.md` 的 `data_2 → data_1` 拼接顺序与原始批次日期冲突。
- ❌ `data_preparation_summary.json` 的 `core_invalid_row_count=0` 与 41 个全零占位循环冲突。

## Constraint Direction Review

这些脚本只执行审计、对齐和特征聚合，不含优化不等式约束；本项不适用。

## Operation Review

- 原始 MAT 文件未被覆盖，当前 SHA-256 与审计锚点一致。
- 所有生成物均位于 `l1/outputs/`、`l1/data/processed/` 或 `l1/src/`，未写入工作区外部。
- 未使用网络或外部赛题数据；论文来源为用户提供的本地 PDF。
- MATLAB 深层 `h5disp/h5info` 因耗时过长被终止，没有破坏源文件，但也没有形成可复现审计产物。
- Python 编译检查留下了 `l1/src/__pycache__/`，属于可清理的临时产物，不影响结果正确性。

## Run Instructions After Repair

```powershell
python l1/src/audit_l1_data.py
python l1/src/compare_xlsx_to_table9.py
python l1/src/prepare_cycle_data.py
```

## Expected Outputs

- `l1/outputs/data_audit/inventory.json`
- `l1/outputs/data_audit/clean_cell_roster.csv`
- `l1/outputs/data_audit/table9_reconciliation.json`
- `l1/data/processed/cell_labels.csv`
- `l1/data/processed/cycle_summary_clean.csv`
- `l1/data/processed/early_cycle_features.csv`
- `l1/data/processed/data_preparation_summary.json`

## Recommended Next Skill

先返回 `data-auditor-cleaner` 修复片段顺序与异常掩码，并完成原始数组审计；修复后再重新运行 `python-code-reviewer`。当前不应进入模型分析或论文写作。
