# 原始材料版本清单

> 更新日期：2026-08-03。原始文件保持只读；Git 跟踪本清单、处理脚本、审计报告、处理数据和结果，而不直接提交大体积二进制源文件。

## 版本策略

- 原始 MAT 文件合计约 7.70 GiB，不提交至普通 Git，以免超过远程仓库的可用容量。
- 每次重新获取或替换源文件，先比对下表 SHA-256；若校验值不同，须新增一条版本记录、重新运行数据审计，且不得覆盖既有结果。
- 可再生的清洗数据、特征、脚本、报告、图表和论文草稿进入 Git；结果必须能追溯到本清单中的源数据版本。
- 若未来确有远程保存原始 MAT 的需求，须先确认 Git LFS 容量与费用，并把新的 LFS 对象版本号写入本文件；在此之前不上传。

## 当前源文件指纹

| 文件 | 大小（字节） | SHA-256 | 角色 |
|---|---:|---|---|
| `data_1.mat` | 3,025,320,241 | `9D928AB978F0E3C70B31CB833A749FEDD35094D01AF76475D69B40AA3497F5BA` | 官方原始数据批次 1 |
| `data_2.mat` | 2,007,331,155 | `63AB200D09ECB237FEE5EF3A5C5DB76E3212E3206A0BD92F769E1427FED338B8` | 官方原始数据批次 2 |
| `data_3.mat` | 3,236,690,412 | `62C30E413B63E6144720E016DEED3661FAC8468641794A5807B123FE84717998` | 官方原始数据批次 3 |
| `data_1.xlsx` | 3,676,722 | `C38A29814E6EF450A9D76ED3F806A8138532C37465A2D6B16DB777C7133FDA09` | 官方表格数据批次 1 |
| `data_2.xlsx` | 2,710,709 | `7FD0878C958A1F472DB87C3C7300BE5D9605A19ABEBB7C3C0F5B9F252DF5661C` | 官方表格数据批次 2 |
| `data_3.xlsx` | 4,834,463 | `66D9650DC7F72ACA0671ADF8C7E8055644B1D7586F4B8604E441F04838B53096` | 官方表格数据批次 3 |
| `1710560890-r2I8.pdf` | 4,627,397 | `5BD1E59D57DAAF7778E42841C6AA0FFEE6D286285D6968768DDB062FBE718A3C` | 论文原文 |
| `B.docx` | 276,894 | `95B630857FC5798E027EE98C501FED81A4CC03F39746AEE387B21CD0E6C07F26` | 赛题材料 |
| `论文.docx` | 346,524 | `F510FFE58F1C2C8A3CF4A9481038B777770DAAF302C6B4F691A367B0858B6256` | 论文模板 |

## 可复现入口

- 数据审计：`code/phase2_data_audit.m`、`code/phase2_nested_cycle_audit.m`
- 清洗与特征：`code/phase2_prepare_analysis.py`、`code/phase3_prepare_q3_features.py`
- 冻结结果：`results/Q2/reports/frozen_numbers.json`、`results/Q3/reports/frozen_numbers.json`
- 工作状态：`planning/progress_dashboard.md`
