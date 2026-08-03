# 全局符号表

> 更新时间：2026-08-02  
> 依据：题目解析、P0 数据字典、Q2/Q3 候选与实验、Q4 Train-only 协议。  
> 统一口径：本文所有 `log`、`RMSE_log`、`MAE_log` 均指自然对数 `ln` 尺度，反变换为 `exp`。

## 1. 集合与索引

| 符号 | 含义 | 范围 | 使用问题 |
|---|---|---|---|
| (i\in\mathcal I) | 物理电芯索引，以 `barcode` 唯一标识 | 全部 124 枚；Train 41 枚 | Q1–Q4 |
| (p\in\mathcal P) | Table 9 充电策略组索引 | Train 中 40 组 | Q1–Q4 |
| (n) | 拼接后的全局循环序号 | (1,2,\ldots,L_i-1) | P0、Q1、Q3 |
| (k\in\mathcal K) | 早期观测截止循环 | ({5,10,20,50,100}) | Q3、Q4 |
| (f\in\mathcal F) | 外层策略分组交叉验证折 | (1,\ldots,5) | Q2、Q3 |
| (b) | bootstrap 重复索引 | Q2/Q3：1–2000；Q4：1–1000 | Q2–Q4 |
| (s\in\mathcal S) | SOC 分段索引 | 0–20%、20–40%、40–60%、60–80% | Q2、Q4 |

## 2. 已给定输入量

| 符号 | 数据字段 | 含义 | 单位 | 使用问题 |
|---|---|---|---|---|
| (C_{1i}) | `C1` | 第一阶段充电倍率 | C-rate | Q1、Q2、Q4 |
| (q_i) | `Q1_percent/100` | 两阶段倍率切换 SOC 比例 | 无量纲；表中以 % 存储 | Q1、Q2、Q4 |
| (C_{2i}) | `C2` | 第二阶段充电倍率 | C-rate | Q1、Q2、Q4 |
| (L_i) | `cycle_life_table9` | Table 9 官方循环寿命 | cycle | Q1–Q4 |
| (t_{in}) | RAW `t` | 单循环曲线时间坐标 | 原文数据定义 | P0、RAW challenger |
| (Q^{d}_{in}) | `QDischarge` / RAW `Qd` | 放电容量 | Ah | P0、Q1、Q3 |
| (Q^{c}_{in}) | `QCharge` / RAW `Qc` | 充电容量 | Ah | P0、Q3 |
| (I_{in}) | RAW `I` | 电流曲线 | 原文数据定义 | P0、RAW challenger |
| (V_{in}) | RAW `V` | 电压曲线 | V | P0、RAW challenger |
| (R_{in}) | `IR` | 内阻 | Ω | P0、Q1、Q3 |
| (T^{max}_{in},T^{avg}_{in},T^{min}_{in}) | `Tmax/Tavg/Tmin` | 单循环温度摘要 | °C（按数据说明） | P0、Q1、Q3 |
| (t^{chg}_{in}) | `chargetime` | 实测充电时间字段 | min | P0、Q1、Q3 |

## 3. 派生量与状态量

| 符号 | 定义 | 含义 | 单位 | 使用问题 |
|---|---|---|---|---|
| (z_i) | (z_i=\ln L_i) | 自然对数寿命目标 | 无量纲 | Q2、Q3 |
| (\widehat L_i) | (\exp(\widehat z_i)) | 预测循环寿命（条件中位数口径） | cycle | Q2、Q3 |
| (SOH^{nom}_{in}) | (Q^d_{in}/1.1) | 以 1.1 Ah 标称容量归一化的 SOH | 无量纲 | P0、Q1、Q3 |
| (SOH^{rel}_{in}) | (Q^d_{in}/Q^d_{i,2}) | 相对 cycle 2 的容量保持率 | 无量纲 | P0、敏感性 |
| (u_{in}) | (n/L_i) | 相对寿命进程 | 无量纲 | Q1、Q3 |
| (G_f(u)) | 外层训练折构建的非增 SOH 模板 | 共享退化形状 | 无量纲 | Q3 |
| (\tau_{0-80}(\mathbf x)) | 两阶段恒流公式计算 | 0–80% SOC 理论充电时间 | min | Q1、Q4 |
| (\mathbf x) | ((C_1,q,C_2)) | 设计前策略向量 | 混合单位 | Q2、Q4 |
| (\mathbf e_{soc}(\mathbf x)) | ((E_{0-20},E_{20-40},E_{40-60},E_{60-80},\tau_{0-80})) | SOC 分段暴露向量 | C-rate 与 min | Q2、Q4 |
| (d_{raw}(\mathbf x),d_{soc}(\mathbf x)) | Train 标准化后的第 5 近邻距离 | 双空间可信域距离 | 无量纲 | Q4 |
| (c_{raw},c_{soc}) | Train 留一第 5 近邻距离 95% 分位 | 可信域阈值 | 无量纲 | Q4 |
| (\pi_{supp}(\mathbf x)) | barcode bootstrap 中双空间通过比例 | 候选支持率 | 0–1 | Q4 |

## 4. 模型参数与指标

| 符号 | 含义 | 估计方式 | 使用问题 |
|---|---|---|---|
| (\boldsymbol\beta) | Ridge 主效应系数 | 每个训练折内估计 | Q2-A M1 |
| (\boldsymbol\gamma) | 二阶交互项系数 | 每个训练折内估计；bootstrap 检查符号 | Q2-A M2 |
| (\alpha) | Ridge/GAM 正则化强度 | 内层策略分组 CV | Q2、Q3、Q4 |
| (a_f) | 第 f 个外层折选出的正则化强度 | 内层折最小误差 | Q2、Q3 |
| (RMSE_{\ln L}) | (sqrt{N^{-1}\sum_i(\hat z_i-z_i)^2}) | 折外预测 | Q2、Q3 |
| (MAE_{\ln L}) | (N^{-1}\sum_i|\hat z_i-z_i|) | 折外预测 | Q2、Q3 |
| (RMSE_{SOH}^{cell}) | 先逐电芯算误差、再电芯等权汇总 | 折外未来点 | Q3 |
| (\Delta M) | (M_{complex}-M_{baseline}) | 配对 OOF/bootstrap；负值表示复杂模型较好 | Q2 |
| (\epsilon_z) | Train OOF 的预注册对数误差容忍量 | 冻结模型输出 | Q4 确认协议 |

## 5. Q4 决策输出

| 符号/状态 | 含义 | 当前使用边界 |
|---|---|---|
| (L_{Q2}(\mathbf x)) | 设计前代理寿命预测 | 当前 P3 仅为条件性、Train-only 点预测 |
| (L_{Q3}(\mathbf x)) | 新策略运行至窗口 k 后的个体化寿命校正 | 必须有真实早期数据 |
| (L_{rob}(\mathbf x)) | (min(L_{Q2},L_{Q3})) 的保守合并口径 | 仅在两条流水线均通过确认后使用 |
| (L_{m,LCB}(\mathbf x)) | bootstrap 低分位减过预测惩罚后的寿命下界 | 当前 dry-run 尚未计算 |
| `Q2_provisional` | 仅通过 Q2 与可信域候选审计 | 不等于正式推荐 |
| `Q3_confirmed` | 有真实早期数据并通过 Q3 协议 | 仍需报告样本数与不确定性 |
| (mathcal P_{Pareto}) | 在快充时间、寿命与 SOH 风险上不被严格支配的集合 | Q4 正式交付；当前尚未生成 |

## 6. 跨问题传递

| 输出→输入 | 统一符号 | 一致性检查 |
|---|---|---|
| Q1 数据边界→Q2/Q3 | (mathcal I,\mathcal P,L_i) 与字段掩码 | ✅ P0 为共同只读来源 |
| Q2→Q4 | (L_{Q2}(\mathbf x)) | ⚠ P3 已冻结为限定中等可信的 `Q2_provisional` 候选代理，不作最终寿命排序 |
| Q3→Q4 | (L_{Q3}(\mathbf x),SOH^{nom}) | ⚠ k=100 角色已决定，稳定性置信仍 PENDING |
| Q2+Q3→Q4 | (L_{rob},L_{m,LCB}) | ⏳ Q2/Q3 Primary 受限确认已完成；新策略 k=100 pilot、保守下界与 Secondary 压力测试尚未完成 |

## 7. 冲突处理记录

| 日期 | 原冲突 | 统一处理 |
|---|---|---|
| 2026-08-02 | 方案写 `log10(L)`，代码使用 `np.log/np.exp` | 统一为 (z=\ln L)、(hat L=\exp(\hat z))；现有指标无需重算 |
| 2026-08-02 | `Q1` 同时可指子问题一和 SOC 切换百分比字段 | 子问题写 Q1；数学变量用 (q=Q1\_percent/100) |
| 2026-08-02 | (C_1,C_2) 容易被误解为成本 | 明确只表示 C-rate；成本符号不使用 C |
| 2026-08-02 | (k) 既可能表示窗口又可能表示近邻数 | (k) 只表示窗口；近邻数固定写“第 5 近邻” |
| 2026-08-02 | Q3 `soh_rmse` 有点合并与电芯等权两种口径 | 基础诊断改名 `future_point_pooled_soh_rmse`；正式指标写 (RMSE_{SOH}^{cell}) |

## 8. 记号约定

- 带帽符号为预测量，星号只用于真正完成并通过约束的最优/代表解。
- `log` 字段名为历史兼容名称，数学公式统一写 `ln`。
- `cycle`、min、V、Ω、Ah 与 C-rate 不相互换算；理论时间与实测 `chargetime` 分列。
- 未进入正式 Pareto 的 1775 条候选不得使用“最优策略”符号。
