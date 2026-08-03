# B题：快充策略对锂离子电池寿命衰减的影响
## 最新完整建模方案（经审查修订的候选执行框架）

**版本：V2.1**  
**日期：2026-08-02**  
**适用范围：以循环汇总数据和官方 Table 9 标签为主线；原始 MAT 曲线仅作为已审计、受掩码约束的低维 challenger，不作为默认依赖。**

---

# 0. 文档定位

这份文档不是“模型名称清单”，而是一份可以直接指导后续建模、代码实现、论文写作和答辩准备的总方案。

它需要解决六件事：

1. 现在到底有哪些数据可以正式使用；
2. 正式建模前必须先做哪些过滤；
3. 四个问题分别应该回答什么；
4. 每一问用什么方法、为什么用、输出什么图；
5. 哪些结论可以说，哪些结论不能说；
6. 后续代码和论文按什么顺序推进。

当前最推荐的主线是：

\[
\boxed{
\text{数据过滤}
\rightarrow
\text{Q1 认识数据}
\rightarrow
\text{Q2 设计前寿命估计}
\rightarrow
\text{Q3 运行后寿命校正}
\rightarrow
\text{Q4 可信范围内的策略优化}
}
\]

这条主线保留。

相比 V2.0，本版有以下关键修正：

- **RAW 深层审计已经完成**；循环汇总特征仍是主线，但保留不超过 1–3 个预注册曲线特征作为 challenger；
- **Q2 必须分成“解释模型”和“预测模型”**，解释模型不一定能直接用于 Q4；
- **Primary 已有探索性结果暴露，只能用于少量预注册候选的受限确认，不能再称完全独立测试集**；大规模选型在 Train 内嵌套交叉验证完成；
- **Secondary 只作为模型锁定后的一次性跨批次压力测试**；
- **SOH 同时保留相对 SOH 和额定 SOH**，避免寿命终点定义错误；
- **bootstrap 输出只能称“保守预测下界/模型不确定性区间”**，不能冒充真实寿命概率分布；
- **Q3 的“运行后校正”比较直接联合和完整交叉拟合的对数残差校正，并同时验证未来 SOH 轨迹**；
- **Q4 改为 Q2 设计前提名 + Q3 早期运行后确认的两阶段闭环**；
- **Q4 的可信范围必须公式化**，同时检查最近策略距离、邻居数、模型分歧、参数边界与适用批次。

---

# 1. 当前数据基础与正式使用边界

## 1.1 正式分析对象

当前正式分析单位：

- 124 个唯一物理电芯；
- 官方寿命、数据分区、快充策略参数以论文 Supplementary Table 9 为准；
- 目标变量：`cycle_life_table9`；
- 分区变量：`dataset_table9`；
- 策略变量：`C1`、`Q1_percent`、`C2`；
- 主键：`barcode`。

当前主要数据文件：

- `data/processed/cell_labels.csv`
- `data/processed/cycle_summary_clean.csv`
- `data/processed/early_cycle_features.csv`
- `data/processed/feature_columns.json`
- `data/processed/data_preparation_summary.json`

其中，当前 `early_cycle_features.csv` 只能继续作为**探索性基线**，不能直接作为最终建模输入，因为新的正式过滤规则尚未全部作用到该特征表。

## 1.2 循环汇总字段为主，RAW 曲线为受控 challenger

本版正式主线不依赖原始 MAT 曲线。Q3 首轮先使用：

- 放电容量 `QDischarge`；
- 充电容量 `QCharge`；
- 内阻 `IR`；
- 温度 `Tmax/Tavg/Tmin`；
- 充电时间 `chargetime`。

以及由这些变量构造的：

- 当前状态；
- 相对 cycle 2 的变化量；
- 长窗口与最近窗口斜率；
- 波动性；
- 有效观测数和有效比例。

但不能再写“RAW 未审计或不可使用”。当前全量深层审计已经得到：

- 正式名册原始循环：100,501；
- 可用于曲线特征：100,243；
- 仅通过掩码排除：258；
- 前 20 个循环没有 RAW 掩码异常；截至 cycle 50 仅 2 个异常循环，截至 cycle 100 仅 22 个异常循环。

因此保留一个低维 RAW challenger：

1. 每个截止窗口最多预注册 1–3 个曲线特征，例如合格循环对的 `ln Var[ΔQ(V)]`、`min ΔQ(V)`；
2. 只允许使用截止循环及以前的数据；
3. 必须同时满足 `in_official_roster=1` 与 `usable_for_curve_features=1`；
4. 两条曲线构造差值时，两端循环均须合格；
5. 与循环汇总模型使用完全相同的 Train 嵌套 policy-group CV；
6. 只有先在 Train 折外结果中稳定入围，才允许进入已暴露 Primary 做一次受限确认；若增益不稳定，则用实验结果正式淘汰。

默认不采用：

- 大规模 dQ/dV、dV/dQ 特征库；
- 无约束逐点插值；
- 高维 RAW 特征自动筛选；
- 为了复现原论文而绕开本题验证体系。

换言之：**循环汇总特征是主模型输入，RAW 只承担“低维对照实验”角色。**

---

## 1.3 单位状态与写作边界

根据题面 `B.docx` 与已确认说明：`IR` 单位为 Ω，`chargetime` 单位为 min；`QDischarge/QCharge` 暂按 Ah 理解但仍待原始说明确认，温度暂按 °C 理解。正式处理遵循：

1. 单位确认前保留原始数值，不擅自换算；
2. 特征可使用训练折内标准化值、相对变化和趋势，但图表纵轴写“原始记录值”或“标准化值”；
3. 不基于未确认单位设置外部物理安全阈值，也不把系数量纲写进结论；
4. \(\tau_{0-80}\) 由 C-rate 公式得到，单位明确为 min，必须与 `chargetime` 分列；
5. 单位证据、来源页码和最终采用口径写入数据字典及 AI/实验日志，论文中保持一致。

---

# 2. P0：正式建模前必须完成的数据过滤

这是整个方案最优先的一步。

如果 P0 没有完成，后续模型结果最多只能叫“压力测试”或“探索性结果”，不能叫正式结果。

### 当前 P0 状态

已完成：

- 124 枚正式电芯的 Table 9 名册与标签冻结；
- 三份 MAT 只读校验和深层循环审计；
- 5 个跨片段条码合并；
- EOL 截断后的 99,279 行唯一正式长表；
- 七个汇总字段各自的字段—循环掩码及原因列；
- `k=5/10/20/50/100` 五套统一窗口特征，每套 124 行；
- 只在 Train 拟合并冻结到其他分区的 `chargetime` Q99×5 统计离群阈值；
- P0 机器摘要、数据审计报告和 Python 代码复核。

P0 已于 2026-08-02 通过。正式输入为 `cycle_model_view.csv` 和五套 `early_features_k*.csv`；旧的 `early_cycle_features.csv` 仍仅作探索性历史产物，不得作为正式 Q3 输入。具体阈值、掩码计数、输入/脚本/输出 SHA-256 见 `data/processed/p0_summary.json`，人工可读结论见 `data/p0_audit_report.md`。

## 2.1 过滤一：统一截断到官方寿命终点

对第 \(i\) 个电芯，官方寿命为：

\[
L_i
\]

只保留：

\[
\boxed{n < L_i}
\]

也就是：

```text
global_cycle_index < cycle_life_table9
```

### 为什么必须做

官方 `cycle_life_table9` 已经定义了寿命终点。

如果仍使用：

\[
n \ge L_i
\]

之后的测试记录，就会出现：

- 一边把 \(L_i\) 当成寿命终点；
- 一边又拿寿命终点之后的数据拟合 SOH、趋势或特征。

这会破坏目标定义的一致性。

当前复核结果表明：

- 原循环汇总表 100,501 行；
- 有 1,222 行位于官方寿命终点及以后；
- 截断后 99,279 行；
- 截断后每枚电芯应严格保留 `cycle_life - 1` 个寿命前循环记录。

### 必做校验

代码执行后必须自动检查：

```text
for each barcode:
    max(global_cycle_index) < cycle_life_table9
```

以及：

```text
retained_cycles == cycle_life_table9 - 1
```

如果不成立，程序必须报错，不能静默继续。

此外还要检查：

```text
official_cell_count == 124
retained_row_count == 99279
duplicate(barcode, global_cycle_index) == 0
```

## 2.2 过滤二：早期窗口统一从 cycle 2 开始

统一定义：

\[
\boxed{2 \le n \le k}
\]

其中：

\[
k\in\{5,10,20,50,100\}
\]

### 为什么不用 cycle 1

原因：

1. cycle 1 中存在较多结构性全零占位；
2. cycle 2 更适合作为统一初始状态参考；
3. 避免不同电芯实际有效起点不一致。

### 写作术语统一

不要写：

> “使用前5个循环”。

因为：

\[
2\le n\le5
\]

实际上只有 4 个循环。

以后统一写：

> **观测截至第 \(k\) 循环**

例如：

> “当观测截止循环从第 5 循环增加到第 100 循环时，比较寿命预测误差的变化。”

这样不会出现 off-by-one 表述问题。

## 2.3 过滤三：采用“字段—循环级掩码”

如果某个循环中：

- `QCharge` 异常；
- `QDischarge` 正常；
- `IR` 正常；
- 温度正常；

那么只把：

```text
valid_QCharge = False
```

其他字段仍保留。

### 禁止的做法

不要因为：

- 某一个字段；
- 某一个循环；

出现异常，就删除：

- 整行；
- 整枚电芯。

### 推荐字段

建模长表至少维护：

```text
valid_QDischarge
valid_QCharge
valid_IR
valid_Tmax
valid_Tavg
valid_Tmin
valid_chargetime
```

后续每个字段自己的：

- mean
- slope
- std
- min
- max

都只使用该字段 `valid=True` 的循环。

原始值必须保留；掩码列不能通过覆盖、截尾或回填来“修复”源值。每个掩码还要配套：

```text
mask_reason_QDischarge
mask_reason_QCharge
mask_reason_IR
mask_reason_Tmax
mask_reason_Tavg
mask_reason_Tmin
mask_reason_chargetime
```

涉及两个时点的变化特征，只有基准点和终点对应字段都有效时才有效。例如：

```text
valid_delta_QDischarge_k = valid_QDischarge_cycle2 AND valid_QDischarge_cycle_k
```

不得用未来循环替代无效的 cycle `k`。若派生特征缺失，只能在模型流水线内使用 Train 拟合的填补值，并同时保留缺失指示列。

## 2.4 异常规则分两类

### 第一类：确定性结构异常

这类可以全局固定规则处理：

- NaN；
- Inf；
- 全零占位；
- 明显非法索引；
- 已确认的数据结构错误。

这类规则不是模型超参数。

### 第二类：统计离群

例如：

- 极端充电时间；
- 容量异常高值；
- 极端斜率；
- 某些统计上非常偏离的点。

这类不能根据 Primary 或 Secondary 反复调整。

如果阈值由数据统计得到，例如：

\[
Median \pm k\cdot MAD
\]

或：

\[
Q_{0.995}
\]

那么必须：

\[
\boxed{\text{只在 Train 中确定阈值}}
\]

然后原样应用于 Primary、Secondary。

### 特别注意

当前快速检查中使用过：

\[
QCharge > 1.2Ah
\]

这只能作为**敏感性检查阈值**，除非能给出明确物理依据，否则不能直接固化成最终规则。

当前 `chargetime_far_outlier` 的全局 P99×5 阈值也只属于探索性标记；正式 P0 必须在 Train 内重新拟合，再冻结应用到 Primary 和 Secondary。

## 2.5 不要把跨批次差异当作异常数据删除

如果 Secondary 的：

- 温度平均值；
- 内阻平均值；
- 初始容量水平；

整体偏离 Train，这不自动代表“脏数据”。

这可能是：

- 日历老化；
- 批次差异；
- 实验条件差异；
- 初始状态变化；

造成的真实分布偏移。

因此必须坚持：

\[
\boxed{\text{错误数据要清理，真实分布差异要保留}}
\]

## 2.6 不维护五套独立清洗逻辑

推荐结构：

### 先生成一张正式建模长表

例如：

`cycle_model_view.csv`

包含：

```text
barcode
dataset
batch
global_cycle_index
cutoff_cycle
QDischarge
QCharge
IR
Tmax
Tavg
Tmin
chargetime
valid_QDischarge
valid_QCharge
valid_IR
valid_Tmax
valid_Tavg
valid_Tmin
valid_chargetime
```

然后由同一个特征生成程序根据：

\[
k=5,10,20,50,100
\]

生成五个窗口。

## 2.7 P0 固定输出与通过标准

必须生成：

```text
data/processed/cycle_model_view.csv
data/processed/early_features_k5.csv
data/processed/early_features_k10.csv
data/processed/early_features_k20.csv
data/processed/early_features_k50.csv
data/processed/early_features_k100.csv
data/processed/p0_summary.json
data/p0_audit_report.md
```

P0 只有同时满足以下条件才算通过：

1. 99,279 行、124 枚电芯、无重复 `(barcode, global_cycle_index)`；
2. 每个窗口输出 124 行，一枚电芯一行；
3. 每个字段的 `valid_count/valid_ratio` 可追溯到长表掩码；
4. 任何异常只影响对应字段特征，不导致整枚电芯消失；
5. 所有阈值、填补、标准化参数都有 Train-only 证据；
6. 五个窗口由同一程序和同一字段定义生成；
7. 运行日志记录输入 SHA-256、代码版本或脚本 SHA-256、随机种子和输出行数。

---

# 3. SOH：必须同时保留两个定义

## 3.1 相对 SOH

定义：

\[
\boxed{SOH_i^{rel}(n)=\frac{Q_{d,i}(n)}{Q_{d,i}(2)}}
\]

适合：

- 比较不同电芯的退化形状；
- 长短寿命轨迹对比；
- Q3 的运行后校正；
- 曲线形状建模。

## 3.2 额定 SOH

额定容量：

\[
Q_{nom}=1.1Ah
\]

定义：

\[
\boxed{SOH_i^{nom}(n)=\frac{Q_{d,i}(n)}{1.1}}
\]

它适合：

- 与官方 80% 容量寿命概念对齐；
- 判断寿命终点对应的绝对容量。

## 3.3 重要纠错：不能强制相对 SOH 在寿命终点等于 0.8

例如 cycle 2：

\[
Q_d(2)=1.07Ah
\]

寿命终点容量：

\[
Q_d(L)=0.88Ah
\]

则：

\[
SOH^{rel}(L)=\frac{0.88}{1.07}\approx0.822
\]

所以：

\[
SOH^{rel}(L)=0.8
\]

不是通用成立的。

以后如果使用寿命终点约束，只能写：

\[
SOH^{nom}(L)\approx0.8
\]

相对 SOH 的终点值由各电芯初始容量决定。

数据一致性核验：124 枚电芯的官方 \(L\) 均已知；其中 43 枚在本地汇总表保留了 `n=L` 的容量记录，其 \(SOH^{nom}(L)\) 范围为 0.7947–0.79993，中位数 0.79940，与 0.8 终点定义一致。其余 81 枚没有 `n=L` 容量行，但这只是曲线记录边界，不代表寿命标签右删失；正式寿命仍使用 Table 9 的 \(L\)，43 枚记录用于一致性验证而不是重新估计标签。

---

# 4. 数据集角色重新定义

## 4.1 Train：训练集

共有 41 枚电芯、40 种策略。

用途：

- 模型拟合；
- 标准化参数拟合；
- 异常统计阈值拟合；
- 交叉验证；
- 超参数选择；
- bootstrap。

## 4.2 Primary：受限确认集（已有探索暴露）

共有 43 枚电芯、39 种策略，其中：

- seen-policy：23 枚电芯、19 种与 Train 精确重复的策略；
- unseen-policy：20 枚电芯、20 种 Train 未见策略。

用途：

- 对 Train 内嵌套交叉验证筛出的少量预注册候选按冻结协议做一次受限确认；
- 检查 seen-policy 和 unseen-policy 泛化；
- 判断是否满足预先冻结的锁定条件。

本项目此前已经出现若干 Primary 快速诊断数字，因此它不再是“从未查看”的独立测试集。正式阶段必须如实记录这次暴露，只允许对 Train 内冻结的少量候选做一次受限确认，不允许把几十组窗口、特征和超参数送入后再挑最好者。Primary 的结果统一称验证/确认成绩；最终独立证据只能依赖 Secondary。

后文涉及 Primary 的“预注册/冻结”仅指 **V2.1 之后不可修改的前置分析协议**，不代表在数据暴露前完成的严格前瞻预注册，也不能恢复 Primary 已失去的独立测试地位。

## 4.3 Secondary：最终跨批次压力测试

共有 40 枚电芯、8 种策略；8 种策略均未在 Train 出现，并且同策略电芯存在组内相关。

流程必须是：

\[
\boxed{Train\rightarrow Primary\rightarrow\text{锁定/重拟合}\rightarrow\text{冻结 Q4 推荐}\rightarrow Secondary}
\]

禁止：

```text
看 Secondary
→ 改超参数
→ 再看 Secondary
→ 再改特征
```

Secondary 除了 cell-level 指标，还必须按 8 种策略等权汇总，并使用按策略聚类的 bootstrap 区间。

## 4.4 模型锁定后的最终重拟合

保留两套清晰口径：

1. **开发模型**：只用 Train 拟合，Primary 指标用于路线确认；
2. **最终代理模型**：模型族、特征定义、阈值规则、超参数搜索网格/选择规则和 one-standard-error 规则全部锁定后，可用 Train+Primary 共 84 枚电芯重新拟合；具体 `alpha` 等数值只在该训练数据内按冻结规则重选。先生成并冻结 Q4 候选与推荐，再对 Secondary 进行一次性外部压力测试。

最终重拟合不能改变已经锁定的特征定义、超参数搜索范围、可信域阈值规则或评价指标。Primary 的开发成绩仍按“验证成绩”报告，不包装成独立测试成绩。

---

# 5. Q1：数据整理与寿命差异初步分析

Q1 的任务不是追求预测精度。

它要回答：

1. 数据基本分布是什么；
2. 不同策略下寿命是否有明显差别；
3. 哪些策略/电芯典型长寿命或短寿命；
4. 策略是不是寿命的唯一决定因素；
5. 哪些规律值得 Q2 进一步建模。

## 5.1 Q1 第一层：基础统计

建立 cell-level 总表：

```text
barcode
dataset
batch
C1
Q1
C2
policy
cycle_life
tau_0_80_theory
early_measured_chargetime
Qd_cycle2
SOH_rel
SOH_nom
```

## 5.2 理论充电时间与实测充电时间必须分开

理论 0–80% SOC 恒流阶段时间：

\[
\tau_{0-80}=60\left[\frac{q}{C_1}+\frac{0.8-q}{C_2}\right]
\]

其中：

\[
q=Q_1/100
\]

而循环汇总中的 `chargetime` 是实际实验测量量。

两者不能混成一个变量。

必须进一步注明：

- `τ0-80` 只表示理想恒流阶段的理论 0–80% 快充时间，不是完整 0–100% CC-CV 时间；
- 80% 以后所有电芯采用相同的 1C 恒流—恒压协议，因此 `τ0-80` 可作为策略可控部分，但不能冒充总充电时间；
- `chargetime` 已确认单位为 min，但其起止点和是否覆盖完整 CV 阶段尚未见字段元数据；图表必须标明“实测每循环充电时间（min）”，不能默认其与理论时间定义相同；
- 在 Train 中检查理论时间与早期实测时间的一致性；若偏差随策略系统变化，再建立简单校准模型。

## 5.3 Q1 图表规划

### 图 Q1-1：循环寿命分布

推荐：

- Histogram；
- ECDF；
- 标注中位数和四分位数。

### 图 Q1-2：不同分区/批次的寿命箱线图

注意：

不能看到 batch 均值不同就直接写：

> “batch 导致寿命不同”。

只能说：

> “不同批次观察到明显寿命差异，但批次同时伴随策略集合变化，无法仅凭此归因。”

### 图 Q1-3：\(C_1,Q_1,C_2\) 与寿命散点

分别画：

\[
C_1-L,
\quad Q_1-L,
\quad C_2-L
\]

### 图 Q1-4：理论充电时间与寿命

横轴：

\[
\tau_{0-80}
\]

纵轴：

\[
L
\]

颜色：batch 或 dataset。

### 图 Q1-5：典型 SOH 曲线

至少包括：

- 典型长寿命电芯；
- 典型短寿命电芯；
- 优先选有重复策略支持的案例。

### 图 Q1-6：Train–Primary 重复策略一致性

推荐画：

- x：Train 同策略寿命；
- y：Primary 同策略寿命；
- 45° 参考线。

同时报告：

- Pearson 相关；
- Spearman 相关；
- 寿命绝对差的 median/mean/max。

当前可复现关键事实：

- Pearson 约 0.903；
- 绝对差中位数约 97 cycles；
- 平均约 119.5 cycles；
- 最大约 349 cycles。

## 5.4 “长寿命策略”必须谨慎定义

如果一个策略只有 1 个电芯：

\[
n=1
\]

不能因为这个电芯寿命高而直接叫“长寿命策略”。

### 可称策略结论

- 策略有重复电芯；
- 重复结果方向一致；
- 组内离散不过大。

### 只能称案例

- 只有一个电芯；
- 极端寿命；
- 无法验证重复性。

## 5.5 决策树在 Q1 中的定位

可以使用浅层决策树：

```text
max_depth = 2~3
min_samples_leaf = 5~8
```

输入：

\[
(C_1,Q_1,C_2)
\]

输出：

\[
L
\]

或：

\[
\ln L
\]

用途：辅助分层图。

严禁把树的切分点写成“物理临界 SOC”。

## 5.6 Q1 最终主结论

> **充电策略对寿命具有稳定的统计信息，但批次、初始状态和电芯个体差异同样不可忽略，因此后续既需要策略层面的设计前模型，也需要运行后的个体化校正。**

---

# 6. Q2：充电策略对寿命影响的量化

Q2 必须拆成：

\[
\boxed{\text{解释模型}}
\]

和：

\[
\boxed{\text{预测代理模型}}
\]

两条线。

---

# 7. Q2 前置认识：\(C_1,Q_1,C_2\) 不是三个充分独立变量

理论前 80% SOC 充电时间：

\[
\tau_{0-80}=60\left[\frac q{C_1}+\frac{0.8-q}{C_2}\right]
\]

多数实验策略本身接近约 10 min 快充设计。

所以：

\[
C_1,Q_1,C_2
\]

受到强约束。

### 不能再做的解释

不推荐高阶多项式后直接声称：

> “C2 独立贡献 34%”。

因为高共线条件下：

- 回归系数会不稳定；
- SHAP 会在相关变量之间重新分配；
- “独立贡献”并没有充分实验辨识基础。

---

# 8. Q2-A：解释模型——不同 SOC 区域是否对高倍率更敏感

## 8.1 把两段充电策略写成 SOC—倍率函数

\[
C(s)=
\begin{cases}
C_1,&0\le s<q\\
C_2,&q\le s<0.8
\end{cases}
\]

其中：

\[
q=Q_1/100
\]

`τ0-80` 是理论 0–80% 恒流快充时间，不是完整 0–100% CC-CV 时间。80–100% 协议虽然相同，但只有在实测验证支持时才能认为它不改变策略排序。

单位确认后，应在 Train 中校验 `τ0-80` 与早期实测 `chargetime`；若存在策略相关系统偏差，使用简单校准模型及其时间上界，而不是直接把理论值当实测总时间。

## 8.2 固定划分四个 SOC 区域

\[
0\%-20\%,
\quad20\%-40\%,
\quad40\%-60\%,
\quad60\%-80\%
\]

对第 \(j\) 个区域定义平均倍率：

\[
E_j=\frac{1}{\Delta s_j}\int_{\Omega_j}C(s)\,ds
\]

通俗解释：

> \(E_j\) 表示这个 SOC 区间平均经历了多大的充电倍率。

## 8.3 主解释模型

不能直接把 `τ0-80` 与四个原始 `E_j` 一起放入普通回归后解释系数。它们均由同一组 `C1/Q1/C2` 推导，仍会混合整体快充强度和倍率在 SOC 上的分配。

先定义：

\[
A_i=\frac14\sum_{j=1}^{4}E_{ij},
\qquad
D_{ij}=E_{ij}-A_i
\]

于是：

\[
\sum_{j=1}^{4}D_{ij}=0
\]

其中：

- `A` 描述整体充电强度；
- `D_j` 描述第 `j` 个 SOC 区域相对整体强度的偏离；
- \(\tau=\tau_{0-80}\) 描述理论快充时间。

为避免“分别标准化四个 \(D_j\) 后和为零约束失真”，固定使用 4→3 的正交 Helmert 对比矩阵：

\[
H=
\begin{bmatrix}
1/\sqrt2&1/\sqrt6&1/\sqrt{12}\\
-1/\sqrt2&1/\sqrt6&1/\sqrt{12}\\
0&-2/\sqrt6&1/\sqrt{12}\\
0&0&-3/\sqrt{12}
\end{bmatrix},
\quad H^TH=I,\quad H^T\mathbf1=0
\]

令 \(D_i=(D_{i1},\ldots,D_{i4})^T\)，三个独立坐标为：

\[
c_i=H^TD_i
\]

只在训练折内标准化 \(A\) 和三个 \(c\) 坐标。建模系数从标准化尺度还原到原始 \(c\) 尺度后记为 \(\eta\)，最终用于四个 SOC 区间作图的系数为：

\[
\gamma=H\eta,
\qquad \mathbf1^T\gamma=0
\]

采用两个嵌套模型：

\[
M_A:\quad z_i=\alpha+\theta_A A_i+\varepsilon_i
\]

\[
M_{SOC}:\quad
z_i=\alpha+\theta_A A_i+\eta^Tc_i+\varepsilon_i
\]

其中：

\[
z_i=\ln L_i
\]

`M_A` 回答整体倍率强度是否携带寿命信息；`M_SOC` 回答在相近整体倍率强度下，SOC 区域分配是否增加解释信息。

充电时间另设单变量敏感性模型：

\[
M_\tau:\quad z_i=\alpha+\theta_\tau\tau_i+\varepsilon_i
\]

由于 `τ` 与 `A/D` 都由同一策略推导，`M_tau` 用于回答理论时间与寿命的总体关联，不与 `M_SOC` 的系数拼成“独立贡献”。

为避免相邻 SOC 系数在小样本下剧烈跳动，对还原后的 \(\gamma=H\eta\) 使用 fused-ridge：

\[
\min_{\theta_A,\eta}
\sum_i(z_i-\hat z_i)^2
+\lambda\left(\theta_A^2+\sum_j\gamma_j^2\right)
+\lambda_s\sum_{j=1}^{3}(\gamma_{j+1}-\gamma_j)^2
\]

和为零约束由 \(H\) 自动保证。`λ` 与 `λ_s` 必须在 Train 内层交叉验证中选择；每个外层折都重新拟合标准化参数，并在作图前撤销尺度变换。

关键检验不是单个训练集系数，而是：

\[
\Delta RMSE_{SOC}
=RMSE_{CV}(M_A)-RMSE_{CV}(M_{SOC})
\]

只有当加入 SOC 对比后折外误差稳定降低，且 `γ_j` 的方向在 bootstrap 中稳定，才允许画 SOC 敏感度曲线。


## 8.4 输出 SOC 敏感度曲线

画：

\[
SOC\rightarrow\hat\gamma_j
\]

解释时只说：

> 在相近的整体快充程度下，高倍率暴露位于某一 SOC 区域时，与较短循环寿命的统计关联更强/更弱。

不能写成因果结论。

如果相邻区间的区间大量跨零、符号稳定率低或 `M_SOC` 未改善折外误差，则应写：

> “在当前近固定快充时间且策略高度相关的实验设计下，不同 SOC 区间的独立敏感度无法稳定辨识。”

## 8.5 解释模型必须做稳定性分析

至少做：

- 设计矩阵秩、条件数和相关矩阵；
- bootstrap 系数区间；
- 系数符号稳定率；
- Train 内按策略分组的重复交叉验证；
- 加/不加 batch 指示变量的敏感性。

推荐表：

```text
SOC区间
平均系数
bootstrap 95%区间
负号比例
折外增益
```

---

# 9. Q2-B：预测代理模型——用于 Q4

它回答：

> 如果只给一个新充电策略，能不能估计它的大致寿命？

## 9.0 Baseline：常数模型

在每个训练折中预测训练样本 `ln(L)` 的均值。任何候选模型都必须相对该基线报告折外改进，不能只报告自身 RMSE。本文中的 `log`、`RMSE_log` 和 `MAE_log` 均指自然对数尺度；反变换统一使用 `exp`。

## 9.1 主候选：Ridge

输入：

\[
C_1,Q_1,C_2,\tau_{0-80}
\]

目标：

\[
y=\ln(L)
\]

理由：

- 样本少；
- 参数相关；
- 需要稳定；
- 实现透明。

`τ` 是由 `C1/Q1/C2` 推导的变量，因此 Ridge 可把它用于预测，但不得把四个系数解释为彼此独立的物理贡献。

## 9.2 候选：ElasticNet

用途：

- 检查部分变量能否被稳定压缩；
- 对高相关特征做稀疏化。

不能把“被 ElasticNet 留下”直接解释为“物理上最重要”。

## 9.3 候选：低自由度 GAM

用于检验明显非线性。

限制：

- 平滑自由度低；
- 不堆复杂二维交互；
- 超参数只在 Train 内确定。

## 9.4 Challenger：极受限提升树

可选，不建议默认正文主模型。

只有 Train 嵌套交叉验证中稳定优于 Ridge/GAM，才允许作为极少量预注册候选进入 Primary；Primary 只按冻结协议负责一次受限确认。

“稳定入围”只按 Train 外层折的配对误差差、bootstrap 区间和 one-standard-error 规则判断。进入 Primary 后只检查预注册的确认门槛，例如总体不劣于 Ridge 的容忍界且 unseen-policy 不触发失败线；不得再按 Primary 排名反复挑模型。否则按简单性优先保留 Ridge，或判定当前代理尚不能锁定。

## 9.5 解释模型与预测模型允许不同

例如：

- SOC 暴露模型解释最清楚；
- 原始参数 Ridge 在 Train 折外预测中更稳，并通过 Primary 确认门槛。

那么：

- Q2 解释部分用 SOC 模型；
- Q4 用 Ridge。

完全合理。

所有方法在 PoC 和正式实验完成前都保持“候选”状态，不在本文档中预先写成最终模型。

## 9.6 对数寿命的反变换

若模型输出：

\[
\hat z=\widehat{\ln L}
\]

则：

\[
\hat L_{median}=\exp(\hat z)
\]

它更接近条件中位数。若论文需要条件均值预测，应使用只在训练折估计的 smearing 校正；不能用 Primary/Secondary 残差校正反变换偏差。

---

# 10. Q2 模型选择规则

先在 Train 内完成嵌套交叉验证，再把少量预注册候选送到已暴露 Primary 做一次受限确认。

### Train 内层与外层

- 外层：按 `policy_table9` 分组，优先 Leave-One-Policy-Out 或重复 GroupKFold；
- 内层：选择标准化、Ridge alpha、ElasticNet 参数或 GAM 平滑度；
- 同一策略的两枚 Train 电芯不得跨外层训练/验证折；
- 每次外层评估都必须从原始特征重新拟合完整流水线。

预先指定：

\[
\boxed{RMSE_{log}\text{ 为主选型指标}}
\]

其他指标用于解释：

- RMSE；
- MAE；
- 中位绝对误差；
- \(R^2\)；
- 相对常数模型的改进率。

如果模型差异落在 one-standard-error 范围内，选择更简单的模型。

Q2 锁定分成“Train 选型”和“Primary 确认”两道门：

1. Train 外层 CV 的主指标与稳定性；
2. Train 内 bootstrap 稳定性；
3. Train 支持域内是否出现异常极端预测；
4. 按下节上限冻结入围候选、确认门槛与失败处理；
5. Primary 总体、seen-policy、unseen-policy 是否一次性通过各自门槛；
6. unseen-policy 到最近 Train 策略距离与误差的关系是否符合预期。

Primary 每个子集只有约 20 枚电芯，所有指标必须同时报告样本量和不确定区间；负 `R²` 必须原样保留。

### Primary 确认配置必须先落盘

第一次正式确认前生成只读式 `outputs/experiments/primary_confirmation_config.json`，至少冻结：候选 ID、数据/脚本/配置哈希、随机种子、主指标、总体/seen/unseen 门槛和失败处理。Q2 最多进入 2 条预测流水线；Q3 最多进入 2 个“模型 × 截止窗口”主线组合，另允许 1 个与最佳主线配对的低维 RAW challenger。

常数基线固定为只用完整 Train 估计的 \(\bar z_{Train}=\operatorname{mean}_{Train}(\ln L)\)，并用同一个 \(\bar z_{Train}\) 预测所有 Primary 样本；禁止用 Primary 总体、seen 或 unseen 自身均值另造更有利的基线。令 \(\epsilon_{NI}\) 为 Train 外层折中“候选减常数基线”的 `RMSE_log` 差的一个标准误，并在配置中冻结。确认规则默认是：

1. Primary 总体、seen-policy 和 unseen-policy 的 `RMSE_log` 均不得比上述同一个 Train-fitted 常数基线差超过 \(\epsilon_{NI}\)；
2. 灾难线预注册为 Train OOF 绝对自然对数寿命误差的 99% 分位；总体/seen/unseen 每个集合中超线样本数均不得超过该集合样本量的 10%（向上取整）；
3. Q4 所用保守下界在 Primary unseen-policy 的覆盖计数至少为 16/20；
4. 任一硬门槛失败，则该候选不得用于新策略 Q4；若只在 unseen 失败，可降级为 `seen_only`，不能宣称新策略泛化；
5. 若两条候选均通过，沿用 Train one-standard-error 规则预先确定的简单模型，不再按 Primary 排名二次选择。

由于 Primary 已有探索暴露，这些门槛只能降低后续自由度，不能恢复其独立测试地位；最终独立证据仍来自一次性 Secondary。

---

# 11. Q2 因素排序：不能写因果贡献百分比

题目要求讨论因素及交互作用。为避免在 41 个 Train 样本上使用无约束高阶多项式，另建一个低自由度层级 Ridge：

\[
z=\alpha+
\beta_1C_1+
\beta_2q+
\beta_3C_2+
\beta_{12}C_1q+
\beta_{13}C_1C_2+
\beta_{23}qC_2+
\varepsilon
\]

所有变量先在训练折标准化；含某个交互项时必须同时保留对应主效应。这个模型用于回答“当前数据中是否存在稳定交互信息”，不用于宣布物理机理。

## 方法一：分组消融

先比较“仅三个主效应”与“主效应 + 三个两两交互”的同折折外误差，判断交互整体是否提供增益；再逐一删除 `C1×q`、`C1×C2`、`q×C2`，检查单个交互的方向和稳定性。

因素级敏感性可计算：

\[
\Delta RMSE_g
=
RMSE(M_{-g})-RMSE(M_{full})
\]

解释：

> 删除该类信息后，预测误差上升越多，说明该类信息对当前模型的条件预测更重要。

删除某个因素时，应同时删除该因素参与的交互项。例如删除 `C1` 时，同时删除 `C1×q` 和 `C1×C2`。所有 `ΔRMSE_g` 必须由同一外层折的折外预测计算。

但三个因素组会共享交互项，因此这些 \(\Delta RMSE_g\) **相互重叠、不可相加**，也不能直接据此声称互斥的第 1–3 名。若题目必须给严格因素排序，则对 \(\{C_1,q,C_2\}\) 枚举全部 \(2^3=8\) 个子模型，以同一外层折的负 `RMSE_log` 为价值函数计算三因素分组 Shapley；子模型只在两个主效应都存在时加入对应交互，并对排名做 bootstrap。该 Shapley 仍只称“条件预测重要性”，不归一化为物理贡献百分比。

## 方法二：系数/部分效应稳定性

看方向、bootstrap 区间和不同折中是否稳定。

若执行严格因素排序，对每次 bootstrap 记录上述三因素 Shapley 排名，给出：

```text
median_rank
rank_IQR
top1_probability
sign_stability
```

只有排序稳定时才给严格名次；否则合并为“第一层/第二层/无法区分”。

## 方法三：响应面

用于展示：

\[
(C_1,Q_1)\rightarrow\hat L
\]

但只能画在实验支持较充分的区域。

最终至少提供两张互补表：

1. 原始策略因素及交互的条件预测重要性；
2. 整体快充时间与四个 SOC 对比的稳定性。

这两张表均不得写成因果贡献百分比。

---

# 12. Batch 在 Q2 中的正确处理方式

可以做：

\[
M_A:\text{不加入 batch}
\]

\[
M_B:\text{加入 batch 指示}
\]

但只能叫：

> **批次敏感性分析**

不能写：

> “加入 batch 后已经控制了所有批次混杂”。

如果加入 batch 后 SOC 敏感度方向稳定，说明结论更稳；如果明显翻转，应承认当前实验设计无法充分区分策略与批次。

---

# 13. Q2 待核验项

目前对话中出现过若干快速诊断数字，例如：

- 某些 Ridge 在 Primary 上的 \(R^2\)；
- SOC 暴露 Ridge 的对比结果；
- 过滤前后的性能变化。

如果没有代码、配置、输出 CSV、random seed、超参数记录，就统一标记为：

\[
\boxed{\text{待核验探索性结果}}
\]

不能直接进入最终论文摘要或结论。

每次正式 PoC 至少记录：

```text
experiment_id
date
input_file_hash
script_sha256
config_sha256
feature_schema_id
split
scaler
model
hyperparameters
random_seed
cv_method
metrics
predictions.csv
```

---

# 14. Q3：利用早期运行数据修正寿命预测

核心叙事：

> Q2 只知道“这个策略一般能活多久”；Q3 看到了这枚具体电池前几十个循环的真实表现，因此可以对 Q2 的预测进行个体化修正。

---

# 15. Q3 五个观察截止点

\[
k\in\{5,10,20,50,100\}
\]

窗口：

\[
2\le n\le k
\]

每个 \(k\) 都必须重新聚合特征。

---

# 16. Q3 特征体系

循环汇总字段是主线，分五类。另保留第 1.2 节定义的 1–3 个预注册 RAW 曲线特征作为独立 challenger；不得把大规模 RAW 特征与汇总特征一起自动筛选。RAW 路线必须用 `(barcode, source_file, batch_index, cycle_index)` 与 `outputs/data_audit/mat_deep_cycle_flags.csv` 一对一连接，并要求构造差值的两端循环均为 `usable_for_curve_features=1`。`global_cycle_index` 只存在于续测片段拼接后的汇总长表，不是 RAW flags 的连接键；连接完成后才把 flags 映射到全局循环号。电压网格、插值范围、平滑参数和缺失处理全部只在 Train 内冻结。

## 16.1 当前状态

例如：

- `QDischarge_mean`
- `QCharge_mean`
- `IR_mean`
- `Tavg_mean`
- `Tmax_mean`
- `Tmin_mean`
- `chargetime_mean`

## 16.2 相对 cycle 2 的变化量

\[
\Delta Q(k)=Q(k)-Q(2)
\]

\[
\Delta Q^{rel}(k)=\frac{Q(k)-Q(2)}{Q(2)}
\]

同理构造：

- \(\Delta IR\)
- \(\Delta T\)
- \(\Delta T_{charge}\)

## 16.3 全窗口趋势

对：

\[
2\sim k
\]

拟合斜率。

推荐：

- 普通线性斜率 baseline；
- Theil–Sen 稳健斜率作为候选。

## 16.4 最近窗口趋势

用于观察是否出现加速退化。

建议规则：

```text
recent_window = min(available_window, max(5, floor(0.2 * available_window)))
```

或在 Train 内固定。对于 `k=5`，窗口内实际只有 cycle 2–5 共 4 个点，因此不生成独立 recent slope，只保留全窗口 slope；不能把同一个四点斜率重复成两列。

不能为了 recent slope 只用 2～3 个点。

## 16.5 波动性与数据质量

加入：

- standard deviation；
- min/max；
- IQR；
- valid count；
- valid ratio。

## 16.6 特征预算与冻结

Train 只有 41 枚电芯，七个字段乘以全部统计量会轻易超过 50 个变量。首轮每个窗口应预先冻结约 12–18 个核心特征，优先覆盖：

- 容量的初始水平、相对变化、全窗口斜率；
- 内阻的初始水平、相对变化、全窗口斜率；
- 温度的均值/峰值与趋势；
- 充电时间的均值、变化与趋势；
- 最低有效比例或关键字段有效数。

RAW challenger 另成一组，不占主线 12–18 个汇总特征的自动筛选空间。

正式规则：

1. 特征定义只可在 Train 内调整；
2. Primary 之前冻结 `feature_schema_id`；
3. Ridge 为主候选，PLS 成分数限制为 3–5；
4. 特征筛选、填补和标准化全部置于交叉验证流水线内部；
5. 每个 `k` 独立生成流水线，不能复用更晚窗口的统计量。

---

# 17. Q3 四组核心实验

寿命模型统一在：

\[
z=\ln L
\]

尺度上训练，最终再反变换到 cycle。

## M1：只用策略

\[
strategy\rightarrow z
\]

代表“电池尚未运行”的基准。

## M2：只用早期数据

\[
early\ features\rightarrow z
\]

## M3：策略 + 早期数据直接联合

\[
strategy+early\rightarrow z
\]

## M4：Q2 先验 + Q3 残差校正

第一步：

\[
\hat z_0=f_{Q2}(strategy)
\]

第二步：

\[
r_i=z_i-\hat z_{0,i}
\]

训练：

\[
early\ features\rightarrow r
\]

最终：

\[
\boxed{\hat L_k=\exp(\hat z_0+\hat r_k)}
\]

解释：

> Q2 给出该策略下的对数寿命先验，Q3 根据具体电芯的早期表现学习乘法尺度上的个体偏离，再反变换为循环寿命。

---

# 18. M4 的关键防泄漏要求

Train 中的：

\[
\hat z_{0,i}
\]

必须使用：

\[
\boxed{\text{折外预测 OOF}}
\]

即每个样本的 Q2 预测来自“不包含该样本”的模型。

然后：

\[
r_i=z_i-\hat z_{0,i}^{OOF}
\]

再训练 Q3 残差模型。

否则会产生数据泄漏。

仅生成一次全 Train OOF 后再做外层评估仍不充分。比较 M4 时必须执行完整交叉拟合：

```text
外层训练折
  └─ 在该外层训练折内部再次分折
       └─ 生成 Q2 内层 OOF 先验与残差
  └─ 用这些残差训练 Q3
外层验证折
  └─ 只由外层训练数据拟合的 Q2/Q3 预测
```

任何标准化、缺失填补、特征筛选和反变换校正都必须在相应训练折内重新拟合。

---

# 19. Q3 模型候选

正文优先：

1. 均值/常数 baseline；
2. Ridge；
3. ElasticNet；
4. PLS。

低自由度 GAM 作为备选。

暂不推荐：

- LSTM；
- Transformer；
- 大规模 boosting 调参。

原因：

\[
n_{train}=41
\]

---

# 20. Q3 验证不只看一个 RMSE

M1–M4、五个截止窗口和模型超参数的主要比较必须先在 Train 内完成嵌套交叉验证。Primary 只接收已预注册的少量组合，并拆成：

## 20.1 seen-policy

策略在 Train 中出现过。

回答：

> 已知策略换一枚新电芯还能不能预测？

## 20.2 unseen-policy

策略在 Train 中没出现过。

回答：

> 新策略附近是否具有泛化能力？

精确“未见”还要按到最近 Train 策略的标准化距离拆成：

- 未见但近；
- 未见且远。

同时画预测误差随最近策略距离的变化，避免把所有 unseen-policy 当成同一种难度。

## 20.3 Secondary

回答：

> 换批次、换策略、初始状态整体变化以后还能不能泛化？

## 20.4 最终 Q3 主表

| 观测截止循环 | Primary 已见策略 | Primary 新策略 | Secondary 跨批次 |
|---:|---:|---:|---:|
| 5 | RMSE/MAE/R² | RMSE/MAE/R² | RMSE/MAE/R² |
| 10 | … | … | … |
| 20 | … | … | … |
| 50 | … | … | … |
| 100 | … | … | … |

每个单元格至少包括：

```text
n
RMSE_log（主指标；历史字段名，指 ln 寿命尺度）
MAE_cycle
RMSE_cycle
median_AE_cycle
R2
95% interval
```

小样本子集的 `R²` 必须带样本量和区间，负值原样报告。

---

# 21. Secondary 同时报 cell-level 与 policy-level

## Cell-level

\[
RMSE_{cell}
\]

## Policy-level

先对同策略的实际和预测寿命分别取均值，再计算：

\[
RMSE_{policy}
\]

这样可以区分：

- 模型对策略本身判断错；
- 同策略个体离散很大。

Secondary 只有 8 种策略，必须使用按策略聚类 bootstrap，并在 policy-level 让 8 种策略等权；不能把 40 枚电芯当成 40 个完全独立样本来计算过窄区间。由于簇数仅为 8，还要逐策略列出误差并做 leave-one-policy-out 汇总敏感性；bootstrap 区间只能称探索性不确定度，不能包装成高精度覆盖保证。

---

# 22. Q3 的 SOH 轨迹：优先简单模板

## 22.1 第一优先：寿命 + 标准化退化模板

在每个训练折内，对训练电芯把横轴缩放为：

\[
u=\frac{n}{L}
\]

研究：

\[
SOH^{nom}(u)
\]

或：

\[
SOH^{rel}(u)
\]

得到训练折内的单调归一化退化模板：

\[
g(u)
\]

主分析在训练折内把官方额定终点作为边界条件 \(g(1)=0.8\)，其余形状只由该训练折中 `valid_QDischarge=1` 的 \(n<L\) 记录估计。不能用验证/测试电芯的 \(L\) 或未来容量修正 \(g\)。

为防止长寿命电芯因循环行数更多而主导模板，固定以下电芯等权估计法：

1. 使用 \(u_r=r/1000,\ r=1,\ldots,1000\) 的 1000 点公共网格；预测所需位置在该模板上做单调线性插值；
2. 每枚训练电芯至少有 10 个有效容量点才参与模板形状估计，只在其有效 \(u\) 范围内插值，不向范围外外推；
3. 每个网格点每枚电芯最多贡献一个插值值，再对至少 5 枚不同 `barcode` 的值取中位数；
4. 对网格中位曲线做非增 isotonic regression，并强制终点 \(g(1)=0.8\)；
5. 网格、插值方法、10 点/5 电芯门槛和失败处理均写入特征配置，在每个训练折内重新估计曲线，不在 Primary 后修改。

`L` 只能用于训练折中学习模板，不能在验证/测试电芯上参与特征或模板拟合。

新电芯得到：

\[
\hat L
\]

后，不能简单把模板从 0 拉伸到 `L_hat`。主分析使用与官方寿命定义一致的 `SOH_nom`，令终点 \(s_E=0.8\)，构造双端锚定比例：

\[
h_i(n)=
\frac{g(n/\hat L_i)-g(k/\hat L_i)}
{g(1)-g(k/\hat L_i)}
\]

\[
\boxed{
\widehat{SOH}^{nom}_i(n)
=SOH^{nom}_i(k)
+\left[s_E-SOH^{nom}_i(k)\right]h_i(n),
\quad k<n<\hat L_i
}
\]

于是 \(\widehat{SOH}_i(k)=SOH_i(k)\)，且 \(\widehat{SOH}^{nom}_i(\hat L_i)=0.8\)。对 \(n\ge\hat L_i\) 不再把 \(g\) 外推到 \(u>1\)，曲线记为到达预测终点并保持在 \(s_E\)，同时由寿命误差单独惩罚“过早终止”。

`SOH_rel` 只作为形状敏感性分析，其终点不能固定为 0.8，而应使用：

\[
s^{rel}_{E,i}=\frac{0.8Q_{nom}}{Q_{d,i}(2)}
\]

所有预测曲线约束为非增；若保留小幅测量波动，其容许范围必须在 Train 中预先确定。若分母 \(g(1)-g(k/\hat L_i)\) 过小，或在 \(k<L_i\) 时已观测到 \(SOH^{nom}_i(k)\le0.8\)，按 Train 预注册规则标为模板失败/早阈值不一致；只把该电芯—窗口的曲线指标记为不可用，寿命指标仍保留，不能静默换公式或删除整枚电芯。

如果出现：

\[
\hat L_i\le k
\]

必须标记为预测失败并计入错误率，不能静默裁成 `k+1`。

解释仍然是：

> 寿命模型决定时间尺度，退化模板决定曲线形状。

但只有曲线级验证通过后，模板才能进入正文主模型。

## 22.2 未来 SOH 的评价指标

对每枚验证电芯先在 `k<n<L_i` 且 `valid_QDischarge=1` 的实际可观测未来点计算：

\[
MAE_{SOH,i},\quad RMSE_{SOH,i},\quad IAE_i
\]

其中 IAE 应除以该电芯实际可评价的未来区间长度，或另报固定共同区间的积分误差，避免不同寿命导致积分量纲不可比。每枚电芯同时报告 `future_valid_count/future_valid_ratio`；若没有有效未来容量点，曲线指标记 `unavailable`，但该电芯仍保留在寿命指标中。随后对电芯等权平均，避免长寿命电芯因为未来行数更多而主导指标。

官方 \(L_i\) 对 124 枚电芯均已给定，不是右删失标签。双端锚定后，预测曲线的 0.8 穿越时刻就是 \(\hat L_i\)，因此 `|L_hat-L_Table9|` 是寿命终点主误差；0.8 穿越只作曲线—寿命一致性检查，不再重复包装成独立成绩。同时报告：

- 固定共同未来点 `n*=120` 的 SOH 误差；
- 预测曲线在 `k` 和 \(\hat L\) 两端的连续性/终点一致性；
- `k=5/10/20/50/100` 下寿命误差与曲线误差的共同变化；
- 模板失败率和 \(\hat L\le k\) 的预测失败率。

不确定性带按每个外层训练折中的 `barcode` bootstrap 生成：每次完整重拟合寿命模型和模板 \(g\)，形成未来逐点轨迹集合；5%/95% 分位作为 90% **模型稳定性带**，并定义：

\[
SOH^{nom}_{LCB}(120)=Q_{0.10,b}\left(\widehat{SOH}^{nom}_{b}(120)\right)
\]

稳定性带的包含率先在每枚电芯的有效未来点上计算，再按电芯等权汇总。没有额外 OOF 残差校准时，只能称“稳定性带包含率和宽度”，不能称严格预测区间覆盖率。

图中必须同时显示截止点、截止点后的真实曲线、预测曲线和不确定区间，不能只挑选预测较好的案例。

## 22.3 第二优先：简单分段线性

如果模板明显不足，再比较单段线性和连续分段线性。

## 22.4 Knee 模型不是默认模型

只有 knee 模型先在 Train 嵌套 CV 中入围，并在 Primary 的一次受限检查中通过预注册确认门槛时才启用。

不能为了“高级”预设所有电芯都有清晰 knee。

---

# 23. Q4：可信范围内的保守快充优化

Q4 必须同时使用 Q2 和 Q3，但两者可获得信息的时点不同：

\[
\boxed{
\text{Q2 设计前提名}
\rightarrow
\text{小规模早期试验}
\rightarrow
\text{Q3 校正确认}
}
\]

## 23.1 已有实验策略：正式 Q2+Q3 评价

模型锁定后，Q4 的开发候选池限定为：

\[
\mathcal D_{dev}=Train\cup Primary
\]

Secondary 不参与候选生成、策略聚合、阈值调整或 Pareto 选择，只在推荐完全冻结后作外部压力测试。原先 Train→Primary 的受限确认成绩仍单独保留，不能因后续合并重拟合而覆盖。

对开发池已有真实早期循环的电芯，使用**冻结流水线、按策略分组的交叉拟合预测**作为 Q4 证据；不能用包含该电芯或同策略电芯的模型给它生成训练内预测。另在全部 \(\mathcal D_{dev}\) 上拟合最终代理，专门用于新候选提名。

对于策略 \(x\)，令 \(\mathcal I_x\) 为其不同 `barcode` 集合，先得到每枚电芯的诚实 Q3 预测，再在对数尺度按电芯等权聚合：

\[
\hat z_{Q3}(x)=\operatorname{median}_{i\in\mathcal I_x}\hat z^{CF}_{Q3,i},
\qquad n_x=|\mathcal I_x|
\]

在第 \(b\) 次 bootstrap 中同样先按电芯得到交叉拟合预测，再计算 \(\hat z_{Q3,b}(x)=\operatorname{median}_{i\in\mathcal I_x}\hat z^{CF}_{Q3,i,b}\)；策略级 \(L_{Q3,LCB}(x)\) 按第 29 节对这组策略级对数预测取分位并施加冻结惩罚。不能先把所有循环行混在一起取分位。

Q2、未来 \(SOH^{nom}(120)\) 和 bootstrap 也使用相同策略集合、相同电芯等权口径。只有 \(n_x\ge2\) 的策略才具备策略级比较资格，可标为 `observed_Q2Q3_confirmed` 并进入正式 Pareto，但仍必须报告 \(n_x\) 和宽区间，不称“大样本稳定策略”；\(n_x=1\) 必须标为 `observed_single_cell_case`，只作案例和敏感性对照。

正式评价步骤为：

1. Q2 给出设计前寿命先验与保守下界；
2. Q3 使用截止 `k*` 的真实早期循环，给出个体校正寿命、未来 SOH 和下界；
3. 按上述规则聚合为策略级结果，形成正式 Q2+Q3 Pareto 集；
4. 与 Q1 的典型长寿命、短寿命策略在同表比较。

可定义：

\[
L_{rob}(x)=\min\left\{L_{Q2,LCB}(x),L_{Q3,LCB}(x;k^*)\right\}
\]

这里 \(L_{rob}\) 只是把两个保守估计合并后的**启发式保守寿命评分**，单位为 cycle；它不是经过覆盖率校准的真实寿命置信下界。两个组成下界、策略样本量和实际寿命分布必须同时报告，不能只报一个 \(L_{rob}\)。

并同时报告共同未来点：

\[
SOH^{nom}_{LCB}(n^*=120)
\]

这里的 120 小于当前最短官方寿命 148，并晚于最大观察截止 100，适合作为所有电芯共同可评价的未来点。

## 23.2 邻域新策略：Q2 暂定 + Q3 晋级

新策略在没有真实 early features 时，只能由 Q2 给出：

> **设计前暂定候选（`Q2_provisional`）**

不得为新策略虚构容量、内阻、温度或充电时间特征。当前提供的数据没有新增策略的早期试验，因此本次新点最高只能到 `Q2_provisional`，不能产出 `Q3_confirmed` 新策略。

若未来具备补充实验条件，采用以下预注册 pilot 流程：

1. Q2 在严格可信邻域内提名；
2. 默认每个候选至少使用 3 枚不同物理电芯运行至预先冻结的 `k*`；若资源不足，结果只能称单电芯/双电芯案例；
3. Q3 用真实早期数据进行寿命与 SOH 校正；
4. 令 \(\epsilon_z\) 为冻结模型在 Train 外层 policy-group OOF 上的 `MAE_log`。若全部数学/邻域检查通过、无 \(\hat L\le k^*\) 预测失败，且 pilot 的 \(Q3-Q2\) 自然对数寿命差 bootstrap 10% 分位不低于 \(-\epsilon_z\)，标为 `Q3_confirmed`；
5. 若仍具邻域支持但低于 \(-\epsilon_z\)，标为 `downgraded` 并以 Q3 保守结果重新排序；若失去支持、出现结构性无效或违反预注册的外部硬约束，则标为 `rejected`。

三枚 pilot 只能提供初筛证据，不应写成大样本工程验证。若没有外部寿命/SOH 硬阈值，第 5 步不得临时编造阈值，SOH 只作为风险诊断和并列裁决。

`k*` 使用确定的 Train-only 规则选择：先保留外层 OOF 中模板失败率不超过 10%、\(\hat L\le k\) 失败率不超过 10%，且至少 90% 电芯可评价 \(SOH^{nom}(120)\) 的窗口；在这些窗口中，选择 `RMSE_log` 不超过最优窗口“均值 + 一个标准误”的最小 \(k\)。若没有窗口通过，Q3 不锁定，Q4 不能声称完成正式 Q2+Q3 推荐。该规则和数值写入 `primary_confirmation_config.json`，在 V2.1 的 Primary 受限确认运行前冻结。

## 23.3 候选状态必须显式记录

```text
observed_Q2Q3_confirmed   # 已有实验策略，Q2/Q3均可验证
observed_single_cell_case # 只有一枚电芯，只作案例
Q2_provisional            # 新邻域策略，仅设计前提名
Q3_confirmed              # 新策略完成早期试验后通过
downgraded
rejected
```

未经 Q3 确认的新策略不能与正式 Q2+Q3 Pareto 候选混在同一推荐表中。

---

# 24. Q4 充电时间模型：理论时间与实测时间分开

定义理论 0–80% 恒流快充时间：

\[
\tau_{0-80}(x)
=
60\left[\frac q{C_1}+\frac{0.8-q}{C_2}\right],
\qquad q=Q_1/100
\]

它**不是完整的 0–100% CC-CV 充电时间**。题面确认 80–100% 对所有电芯采用 1C CC-CV（电流降至 C/50 结束）；**3.6 V 上限来自题目所引 Severson 等原始研究的补充图 2，而非题面本身**。但只有 Train 中的实测结果支持时，才能认为该阶段不改变策略的时间排序。`chargetime` 单位已确认是 min，仍不能因同量纲就直接与定义不同的 \(\tau_{0-80}\) 混用。

现有 68 种策略的 \(\tau_{0-80}\) 约为 8.8889–13.3333 min，中位数约为 10.0004 min，时间变化范围较窄。单位确认后，应只用 Train 拟合一个简单校准关系：

\[
\tau_{meas}=a+b\tau_{0-80}+\varepsilon
\]

校准不能把约 10 万个循环行当作独立样本。单位确认后，默认先在冻结早期窗口 `cycle 2–20` 内，按 `barcode` 聚合未被 `chargetime` 掩码的中位数，并保留 `valid_count/valid_ratio`；再以电芯为单位、按 policy-group CV 拟合和验证上式。只有校准相对直接使用 \(\tau_{0-80}\) 的折外误差有稳定改善、斜率方向稳定时，Q4 才同时报告校准后的实测时间预测及其上界；否则正式优化目标只能称“理论 0–80% 快充时间”。早期窗口如需改变，必须在 Primary 受限确认运行前冻结新版本。

---

# 25. Q4 主目标

不一开始人工设：

\[
\alpha \tau-\beta L
\]

而做：

\[
\boxed{\max_x L_{rob}(x)}
\]

满足：

\[
\boxed{\tau_{0-80}(x)\le \tau_{max}}
\]

若题目、工程方或安全规范提供了可追溯阈值，可额外施加预先冻结的未来 SOH 风险约束，例如：

\[
SOH^{nom}_{LCB}(120\mid x)\ge s_{min}
\]

其中 \(s_{min}\) 只由外部要求或有依据的预注册规则确定，不能查看 Primary/Secondary 后倒推。若没有可信来源，则不设置该硬约束，改为强制报告 \(SOH^{nom}_{LCB}(120)\) 并作为风险诊断/并列裁决，避免虚构“安全阈值”。

含义：

> 在满足快充速度要求的前提下，寻找寿命尽可能长且预测较稳妥的策略。

---

# 26. 通过改变 \(\tau_{max}\) 得到正式 Pareto 前沿

逐渐改变：

\[
\tau_{max}
\]

得到：

\[
L^*(\tau_{max})
\]

即每一个允许的最大充电时间下，最好的保守寿命。

正式主 Pareto 使用题目最直接的两个方向：

\[
\left(\tau_{0-80}\downarrow,\quad L_{rob}\uparrow\right)
\]

\(SOH^{nom}_{LCB}(120)\) 必须叠加在图表和结果表中；只有存在可追溯 \(s_{min}\) 时才先作硬过滤。默认不把它与寿命再次等权放进三维欧氏距离，以免同一退化信息被重复计权。

只允许以下候选进入正式 Pareto 集：

- 开发池中至少有两枚物理电芯、已经完成交叉拟合 Q2+Q3 评价的已有策略；
- 新提出、至少三枚 pilot 运行到 \(k^*\) 且通过 Q3 确认的策略。

仅有 Q2 的 `Q2_provisional` 新策略另列“待试验候选”，不得与正式 Pareto 前沿混画为同一等级的推荐。

---

# 27. 不要在没有数据支持的时间范围硬优化

如果某个 \(\tau_{max}\) 附近几乎没有真实实验策略，就不能因为模型能给数值而正式推荐。

建议同时报告：

```text
支持候选点数量
最近真实策略距离
是否超出可信范围
```

支持不足时直接标：

\[
\boxed{\text{实验支持不足，不给正式推荐}}
\]

当前数据只有 124 枚电芯、68 种策略；Train/Primary/Secondary 分别为 41/43/40 枚电芯和 40/39/8 种策略。参数总范围虽为 \(C_1\in[1,8]\)、\(Q_1\in[2,80]\%\)、\(C_2\in[3,6]\)，但该长方体内部绝大多数组合没有实验支持。因此参数 min/max 只能作必要边界，不能单独定义可优化区域。

---

# 28. Q4 可信范围：双空间支持域 + 数学可行性

## 28.1 参数边界

检查：

- \(C_1\)；
- \(C_2\)；
- \(Q_1\)；

是否超出上述实验范围。边界检查只是第一道门，不能代替邻域支持检查。

## 28.2 与真实策略的最近距离

只用 Train 冻结标准化参数。定义：

\[
u_{raw}=(C_1,q,C_2),
\qquad
u_{soc}=(E_1,E_2,E_3,E_4,\tau_{0-80})
\]

每一维按 Train 的中位数和 IQR 标准化：

\[
\tilde u_j=\frac{u_j-\operatorname{median}_{Train}(u_j)}{IQR_{Train}(u_j)}
\]

若某维 IQR 为 0，则该维不进入距离，且在审计表中显式记录。对每个候选同时计算到 Train 的第 5 近邻距离：

- 原始参数距离 \(d^{(5)}_{raw}\)；
- SOC 暴露距离 \(d^{(5)}_{soc}\)。

SOC 暴露空间：

\[
(E_{0-20},E_{20-40},E_{40-60},E_{60-80},\tau_{0-80})
\]

两个阈值分别取 Train 留一计算的第 5 近邻距离的预注册分位数，默认 \(q_{dist}=0.95\)：

\[
d^{(5)}_{raw}(x)\le c_{raw},
\qquad
d^{(5)}_{soc}(x)\le c_{soc}
\]

候选必须同时通过双空间阈值，并至少拥有 5 个有效 Train 邻居。`k=5`、`q_dist=0.95`、距离度量和网格步长在 V2.1 的 Primary 受限确认运行前冻结；若 PoC 要改变，必须生成新版本并重新走完整验证，不能在 Q4 看结果后微调。

在 V2.1 的 Primary 受限确认运行前必须做一次 **Train-only 候选流量 dry-run**，只统计网格总数、数学可行数、参数边界通过数、raw 5-NN 通过数、SOC 5-NN 通过数、双空间通过数，以及在 Train barcode bootstrap 中支持率达到 80% 的最终数量，不再使用 Primary 寿命结果。若规则导致候选为空，应如实冻结为“无可推荐新策略”，不能在看到 Q4 结果后放宽 5-NN、0.95 分位或 80% bootstrap 支持率。

## 28.3 模型分歧

如果 Train 嵌套 CV 后有两个合格代理模型，例如 Ridge 与 GAM，则在自然对数寿命尺度计算：

\[
D_z(x)=|\hat z_{Ridge}(x)-\hat z_{GAM}(x)|
\]

阈值冻结为同一 Train 外层折 OOF 预测分歧的 95% 分位：

\[
c_{model}=Q_{0.95}\left(|\hat z^{OOF}_{Ridge,i}-\hat z^{OOF}_{GAM,i}|\right)
\]

候选若 \(D_z(x)>c_{model}\)，标记为模型分歧超界，不进入正式推荐；该阈值不在 Primary 或 Q4 结果出来后修改。使用自然对数尺度可避免同样的相对分歧仅因寿命数值较大而被放大。

如果最终只保留一个代理模型，`D_z` 必须记为 `N/A`，不能用 0 或人为增加一个弱模型制造“模型一致”。此时主要依靠双空间邻域、Train OOF 过预测惩罚、bootstrap、Primary 受限确认和批次压力测试控制风险。

## 28.4 \(C_2\) 反解边界

如果用：

\[
(C_1,Q_1,\tau_{0-80})
\]

搜索，则：

\[
C_2=\frac{0.8-q}{\tau_{0-80}/60-q/C_1}
\]

必须满足：

\[
\tau_{0-80}/60-q/C_1>0
\]

## 28.5 \(Q_1=80\%\) 特殊情况

当：

\[
Q_1=80\%
\]

第二阶段 SOC 长度为 0，本质是 0–80% 单阶段策略，必须代码单独分支。

---

# 29. Q4 保守寿命：电芯级 bootstrap 保守下界

不要把 bootstrap 结果解释成真实寿命条件分布。

固定 \(B\ge1000\)，以物理电芯 `barcode` 为重采样单位，并严格区分两类重采样：

1. **可信域支持率 bootstrap**：始终只重采样 Train，不加入 Primary；使用已冻结的 Train 标准化参数、\(c_{raw}/c_{soc}\) 和 5-NN 规则，仅改变本次出现的不同 Train barcodes；
2. **最终预测不确定性 bootstrap**：Primary 受限确认前只重采样 Train；模型通过确认并锁定后，从 \(\mathcal D_{dev}=Train\cup Primary\) 重采样，Secondary 永不进入母集。

每个预测 bootstrap 样本内必须重新执行全部训练流程，包括填补、标准化、特征处理，以及在**冻结的搜索网格和选择规则内**重新选择超参数并拟合模型；不能只对最终预测残差抽样。Q2 与 Q3 必须使用同一第 \(b\) 次 barcode 抽样进行 paired bootstrap，\(L_{rob,b}=\min(L_{Q2,b},L_{Q3,b})\) 不得把两套独立重采样按编号硬配。单侧高估惩罚 \(\delta_m\) 始终固定自 Train OOF，不因加入 Primary 或 bootstrap 重估。

Q2 在 \(\ln L\) 空间拟合时，每次重采样均先得到 \(\hat z_b(x)\)，再反变换：

\[
\hat L_b(x)=\exp(\hat z_b(x))
\]

对每条待确认的流水线 \(m\in\{Q2,Q3\}\)，只用 Train 外层 policy-group OOF 预测预先定义单侧过预测惩罚：

\[
\delta_m=Q_{0.90}\left(\left\{\max(0,\hat z^{OOF}_{m,i}-z_i):i\in Train\right\}\right)
\]

然后采用默认的保守合并规则：

\[
z_{m,LCB}(x)=Q_{0.10}\left(\{\hat z_{m,b}(x)\}_{b=1}^{B}\right)-\delta_m,
\qquad
L_{m,LCB}(x)=\exp(z_{m,LCB}(x))
\]

这同时惩罚模型重拟合不确定性和 policy-held-out 场景中的寿命高估风险。0.10/0.90 分位点、\(\delta_m\) 和确认规则都在 V2.1 的 Primary 受限确认运行前冻结。Primary 只检查该固定下界：unseen-policy 中真实寿命不低于预测下界的比例默认至少为 80%（20 枚时至少 16 枚），且不得出现协议中定义的灾难性高估；确认失败时该模型不得进入 Q4，不能用 Primary 残差重估 \(\delta_m\) 或修改分位点。正文同时报告未惩罚下界、惩罚量和 Primary 覆盖计数，避免包装成精确概率保证。

Q3 对已有策略或已完成早期试验的新策略采用同样的全流水线重拟合，另得到 \(SOH^{nom}_{LCB}(120)\)。Secondary 只作最终压力测试，不用于选择分位点、惩罚系数或可信域阈值。

定义：

\[
L_{LCB}(x)
\]

称为：

> **bootstrap 保守预测下界**

每次重采样的邻域检查按不同 `barcode` 计数，重复抽到同一电芯不能冒充多个邻居。预先要求候选在至少 80% 的 bootstrap 重采样中仍满足双空间 5-NN；否则统一标记 `status=rejected, reason=no_support`，而不是另造状态或仍给出看似精确的下界。

正文推荐措辞：

> “该下界用于衡量模型估计不确定性下的保守寿命，不解释为真实电芯寿命条件分布的严格概率分位数。”

---

# 30. Q4 批次适用范围

由于 Q2 策略模型可能在 Secondary 上明显失效，最终推荐不能写：

> “该策略适用于所有同类电芯”。

更合理：

> “推荐策略主要适用于与训练集和 Primary 验证集在电芯初始状态、实验环境和批次条件上相近的场景；跨批次应用前需要重新验证或校准。”

---

# 31. Q4 优化算法：优先网格搜索

推荐流程：

```text
冻结网格步长、距离阈值、k* 和评价规则
↓
生成候选 C1/Q1/τ0-80
↓
反解 C2
↓
检查数学可行性
↓
检查参数边界
↓
计算理论充电时间
↓
计算 SOC 暴露
↓
计算 raw/SOC 双空间 5-NN 距离与邻居数
↓
Q2 预测、全流水线 bootstrap 与 Train policy-held-out 高估惩罚
↓
按需计算模型分歧；单模型时记 N/A
↓
淘汰缺乏稳定邻域支持的候选
↓
已有策略：接入真实截止 k* 特征并运行 Q3
↓
新策略：先标 Q2_provisional，完成早期试验后再运行 Q3
↓
仅对 Q2+Q3 已确认、且至少有两枚电芯支持的候选形成正式二维 Pareto 前沿
```

不建议为了“高级”强行 NSGA-II。

---

# 32. Q4 最终不要只给一个“最优点”

推荐输出三个代表点，且选择规则在看最终结果前冻结。若外部给出 \(\tau_{max}\)、最低寿命或 \(s_{min}\)，先按这些可追溯约束过滤；若没有，则使用下面的数据内默认规则，不能看结果后手工改阈值。

## 激进方案

- 选择正式 Pareto 中 \(\tau_{0-80}\) 最小者；
- 时间差不超过一个冻结网格步长时，依次选择 \(L_{rob}\) 更高、\(SOH^{nom}_{LCB}(120)\) 更高、双空间距离更小者。

## 平衡方案

- 只在 \((\tau_{0-80},L_{rob})\) 二维前沿上做 0–1 归一化；
- 取到前沿两端连线垂直距离最大的点作为膝点；距离并列时依次比较 SOH 下界和邻域距离；
- 若少于 3 个不同前沿点，或任一轴极差为 0，则明确报告“无法稳定定义平衡膝点”，不强行给平衡方案。

## 保寿命方案

- 若有外部 \(\tau_{max}\)，先在该预算内求最大 \(L_{rob}\)；否则在全体正式 Pareto 点中求最大值；
- 对与最大值之差不超过其 bootstrap 一个标准误的点，优先选择 \(\tau_{0-80}\) 更短者，再按 SOH 下界和邻域距离裁决。

这里的标准误由每次重采样的 \(L_{rob,b}=\min(L_{Q2,b},L_{Q3,b})\) 经验分布计算，仍只用于稳定性筛选，不解释为真实寿命抽样误差。

若新候选相对最接近的已有实验策略的改进小于其不确定区间，则不推荐新点，保留已有策略作为更稳妥结果。单电芯策略只称“案例”，不包装成稳定基准。

每个候选至少报告：

| 项目 | 内容 |
|---|---|
| \(C_1\) | 第一阶段倍率 |
| \(Q_1\) | 切换 SOC |
| \(C_2\) | 第二阶段倍率 |
| 候选状态 | `observed_Q2Q3_confirmed` / `observed_single_cell_case` / `Q2_provisional` / `Q3_confirmed` / `downgraded` / `rejected` |
| 状态原因 | 如 `no_support`、`model_disagreement`、`pilot_below_tolerance`、`prediction_failure` |
| \(\tau_{0-80}\) | 理论 0–80% 快充时间 |
| 实测/校准时间 | 单位确认后的实测值或校准预测；不可用则记 N/A |
| 实际寿命与样本数 | 已有策略的寿命分布和电芯数；新策略记 N/A |
| Q2 预测与下界 | 设计前寿命预测、\(L_{Q2,LCB}\) |
| Q3 校正与下界 | 截止 \(k^*\) 的寿命预测、\(L_{Q3,LCB}\)；未试验新策略记 N/A |
| \(L_{rob}\) | 仅对 Q2+Q3 已确认候选计算 |
| \(SOH^{nom}_{LCB}(120)\) | 共同未来点 SOH 下界 |
| 邻域支持 | 邻居数、\(d^{(5)}_{raw}\)、\(d^{(5)}_{soc}\) 及阈值 |
| 模型分歧 | 多模型时报告；单模型记 N/A |
| 适用范围 | 训练/Primary 相近条件 |
| 风险提示 | 是否靠近边界 |
| Q1 基准对比 | 与典型长寿命、短寿命策略同口径比较 |

---

# 33. 推荐图表总清单

正文控制在 6–8 张主图，其余移入附录或支撑材料。推荐正文保留以下 8 张：

1. **数据全貌多面板图**：寿命分布、分区/批次对比和理论 \(\tau_{0-80}\) 分布；
2. **Train–Primary 重复策略一致性图**：说明策略是否携带可重复的寿命信息；
3. **典型长短寿命 SOH 曲线**：明确单电芯只作案例；
4. **Q2 SOC 相对分配敏感度图**：横轴为四个 SOC 区间，纵轴为带区间的 \(\gamma_j\)，并同时报告“整体倍率强度 + SOC 相对分配”的折外增益；
5. **Q2 Primary 预测图**：Observed vs Predicted，区分 seen/unseen，并标注样本量和区间；
6. **Q3 观察窗口与消融多面板图**：一侧展示 \(k=5,10,20,50,100\) 的泛化误差，另一侧比较 M1/M2/M3/M4；
7. **未来 SOH 轨迹图**：画出截止点、截止前观测、截止后真实曲线、双端锚定预测曲线和 bootstrap 模型稳定性带，不能只画两条平滑线；
8. **可信域与正式 Pareto 图**：区分已有 Q2+Q3 策略、`Q3_confirmed` 新策略、`Q2_provisional` 点和因双空间距离被拒绝的点，并标出三档选择。

以下内容放附录或诊断报告：浅层决策树、各批次完整箱线图、所有窗口的逐项特征图、RAW challenger 对照、模型分歧图、bootstrap 分布和所有电芯的 SOH 小图。这样既保留证据链，也避免正文被 12 张以上图挤满。

---

# 34. 数据泄漏防护清单

## 34.1 只能在 Train 中拟合的东西

包括：

- StandardScaler；
- 缺失值填补规则；
- 统计异常阈值；
- Ridge alpha；
- ElasticNet 参数；
- GAM 平滑度；
- PLS 维数；
- 特征选择；
- RAW 电压网格、插值和平滑参数；
- Train 开发阶段的 bootstrap 规则；
- Q4 可信距离阈值；
- 模型分歧阈值。

以上项目必须在每个交叉验证训练折内重拟合。模型锁定后若用 Train+Primary 最终重拟合，可以在合并训练集内重新估计模型参数和无监督变换，但**不能改变**已冻结的特征定义、超参数搜索范围、距离规则、阈值分位数和评价指标。

## 34.2 Primary 的使用

允许：

- 对 Train 嵌套 CV 预先入围的极少量候选按冻结协议做一次受限确认；
- 按预注册门槛判断 Q2/Q3 路线是否可以锁定；
- 分 seen/unseen 报告受限确认误差和探索性区间。

不允许：

- 在大量候选中反复挑最好者；
- 根据 Primary 样本误差反复定制特征、阈值或超参数；
- 用 Primary 选型后仍把同一成绩称为独立测试成绩。

Primary 已有探索暴露，任何成绩都不能再称完全独立测试。若受限确认失败，必须回到 Train 形成新版本，并明确 Primary 已参与开发；旧 Primary 成绩不能继续充当独立验证证据。

## 34.3 Secondary 的使用

只允许：

> 模型完全锁定后，进行最终跨批次压力测试。

---

# 35. Train 内交叉验证建议

Train 有 41 枚电芯、40 种策略。虽然多数策略唯一，仍必须按 `policy_id` 分组，确保同一策略的重复电芯不会跨训练折与验证折。

推荐外层使用 Leave-One-Policy-Out，或在可保持折间规模时使用重复 GroupKFold；内层继续按策略分组选择填补、标准化、特征、正则化和 PLS 维数。若某次划分无法稳定运行，可退回 policy-group LOOCV，而不是改用会拆散重复策略的普通随机 K 折。

真正的新策略泛化主要看：

\[
Primary\ unseen-policy
\]

但它只能是模型冻结后的确认结果，不能代替 Train 内部的无泄漏选型。

---

# 36. 指标体系

寿命预测以 \(RMSE_{\ln L}\) 作为预注册调参主指标，同时报告：

\[
RMSE_{cycle},\quad MAE_{cycle},\quad MedianAE_{cycle},\quad R^2
\]

每个结果必须同时给出样本量、95% 区间和相对常数基线的改进；负 \(R^2\) 原样保留。Primary 分 seen/unseen，Secondary 同时报电芯等权和 8 个策略等权结果，并按策略聚类 bootstrap。MAPE 可附加，但不作为主指标。

未来 SOH 轨迹只在 `valid_QDischarge=1` 的未来点按电芯先算、再等权汇总，至少报告 SOH-MAE、SOH-RMSE、归一化 IAE、`future_valid_count/ratio`、\(|\hat L-L_{Table9}|\)、\(n^*=120\) 的 SOH 误差、模板失败率，以及 bootstrap 稳定性带包含率和平均宽度；0.8 穿越仅作曲线—寿命一致性检查，五个截止点全部报告。

---

# 37. 正式 PoC 的实验记录规范

建议目录：

```text
outputs/
  experiments/
    q2_ridge_001/
      config.json
      metrics.json
      predictions.csv
      coefficients.csv
      notes.md
      manifest.json
```

每个实验至少记录：

```text
experiment_id
date
input_file_hash
script_sha256
config_sha256
feature_version
feature_schema_id
train_split
validation_split
model
hyperparameters
random_seed
cv_method
metrics
prediction_file
```

若没有稳定可追溯的 Git 提交链，`script_sha256`、`config_sha256` 和输入文件哈希就是最低复现要求；同时保存运行环境、包版本和命令行。模型竞赛期间另维护 `ai_usage_log.csv` 或等价 Markdown，逐条记录：

```text
date
tool
version
purpose
key_interaction
adopted_content
manual_edits
operator
```

该日志用于按竞赛官方要求在正文、参考文献和支撑材料中如实披露 AI 使用，不记录账号、令牌或无关个人信息。

没有这些信息的性能数字统一标记：

\[
\boxed{\text{待核验}}
\]

---

# 38. 推荐执行顺序

## P0：正式建模视图

完成：

- EOL 截断；
- cycle 2 起算；
- field-cycle mask；
- 两种 SOH；
- 5/10/20/50/100 五个窗口特征。

交付：

```text
data/processed/cycle_model_view.csv
data/processed/early_features_k5.csv
data/processed/early_features_k10.csv
data/processed/early_features_k20.csv
data/processed/early_features_k50.csv
data/processed/early_features_k100.csv
data/processed/p0_summary.json
data/p0_audit_report.md
```

## P1：Q1

完成：

- 寿命分布；
- batch / dataset 对比；
- 充电时间分布；
- SOH；
- 重复策略一致性；
- 长短寿命案例；
- 浅层决策树。

交付：4～6 张主图 + 一张策略统计表 + 一页 Q1 结论。

## P2：Q2 第一轮 PoC

只用 Train 做嵌套 policy-group CV，优先跑：

- 常数基线；
- 原始策略参数 Ridge；
- “整体暴露 \(A\) + SOC 相对分配 \(D_j\)”fused-ridge 解释模型。

只有在 Train 折外结果稳定入围后，才预注册至多一个 ElasticNet/GAM challenger 进入 Primary；提升树同理，不得由 Primary 先挑中。

## P3：锁定 Q2

在 V2.1 的 Primary 受限确认运行前冻结特征、候选、超参数规则和通过门槛；随后只按协议运行一次，依据：

- Primary 表现；
- 模型稳定性；
- 解释性；
- Q4 可用性；

确认通过后明确：

```text
Q2解释模型 = ?
Q2预测代理模型 = ?
```

若未通过，只能结论为“当前 Q2 不足以支持可靠新策略外推”，并启动带版本号的新一轮 Train 开发，不能在同一 Primary 上循环调参。

## P4：Q3 第一轮 PoC

跑：

\[
M1,M2,M3,M4
\]

并且：

\[
k=5,10,20,50,100
\]

先只在 Train 内完成嵌套 policy-group CV。每个外层折内重新生成 Q2 内层 OOF 先验、Q3 残差、填补、标准化和 SOH 模板；不得复用一次全 Train OOF。主线冻结 12–18 个汇总特征，另做 1–3 个已连接 RAW 掩码的低维 challenger。

## P5：锁定 Q3

先在 Train 中预注册极少量入围组合，再由已暴露 Primary 做一次受限确认并锁定：

- Ridge / ElasticNet / PLS；
- 直接联合还是残差校正；
- 按 Train-only 失败率 + one-standard-error 规则选出的最小观察截止 \(k^*\)；
- SOH 模板形式。

锁定时必须同时检查寿命和未来 SOH 指标；RAW challenger 只有 Train 折外入围且 Primary 受限确认仍有稳定增益才保留，否则正式淘汰。

## P6：最终重拟合并冻结 Q4 推荐

模型族、特征定义、阈值规则、超参数搜索网格/选择规则和 \(k^*\) 全部锁定后，用 Train+Primary 共 84 枚电芯拟合最终代理；具体超参数只按冻结规则在合并训练集内重选。同时用冻结流水线在该开发池内生成按策略分组的交叉拟合预测，作为已有策略的诚实 Q4 证据。此阶段不得读取 Secondary 结果。

完成：

- 运行并归档 Train-only 候选流量 dry-run；
- 冻结双空间 5-NN 可信域、网格、模型分歧阈值和 \(k^*\)；
- 对至少有两枚电芯的已有策略计算 Q2/Q3 下界、\(L_{rob}\) 与 \(SOH^{nom}_{LCB}(120)\)；单电芯策略另列案例；
- 对新策略只先给 `Q2_provisional` 提名，不虚构 early features；当前数据没有新增 pilot，因此不能生成新的 `Q3_confirmed`；
- 只对 Q2+Q3 已确认策略做正式二维 Pareto、SOH 风险叠加和三档选择；
- 与 Q1 长/短寿命基准同表比较，冻结推荐表、适用范围和风险边界。

## P7：Secondary 一次外部压力测试

推荐、模型和全部门槛冻结后，只运行一次 Secondary，输出：

- Q2 与 Q3 的 cell-level、8-policy 等权结果；
- 逐策略误差、policy-cluster bootstrap 和 leave-one-policy-out 敏感性；
- SOH 稳定性带包含率、寿命误差与域偏移诊断；
- 冻结推荐在跨批次证据下的适用范围复核。

若 Secondary 失败，只能降低结论强度、缩小适用范围或报告“跨批次不通过”；不得反向修改模型、阈值、候选或推荐后再次查看 Secondary。

---

# 39. 论文结构建议

## 第一章：问题重述与总体思路

重点：四问不是独立问题，而是“设计前预测—运行后校正—策略优化”的连续链条。

## 第二章：数据整理与正式建模视图

写：

- 官方标签；
- EOL 截断；
- cycle 2 起算；
- 字段级 mask；
- 两种 SOH；
- 数据分区职责。

## 第三章：Q1 数据规律

写：

- 寿命分布；
- 批次差异；
- 重复策略；
- 长短寿命案例；
- 决策树辅助。

## 第四章：Q2 策略影响与设计前寿命估计

拆两节：

### 4.1 解释模型

整体倍率强度 \(A\) 与 SOC 相对分配 \(D_j\) 的 fused-ridge；图示带区间的 \(\gamma_j\)，只解释为条件统计关联。

### 4.2 预测模型

Ridge / ElasticNet / GAM。

## 第五章：Q3 早期运行数据寿命校正

写：

- 5 个观察截止循环；
- 五类早期特征；
- M1/M2/M3/M4；
- seen/unseen；
- 完整嵌套交叉拟合；
- 截止点锚定的 SOH 模板和未来轨迹定量评价；
- 低维 RAW challenger 的保留/淘汰结果。

## 第六章：Q4 可信范围内的快充优化

写：

- 理论 0–80% 时间与实测时间校准；
- Q2 提名—早期试验—Q3 确认的两阶段闭环；
- 双空间 5-NN 可信域；
- 电芯级全流水线 bootstrap 保守下界；
- 正式 Q2+Q3 Pareto、`Q2_provisional` 待试验表与三档推荐。

## 第七章：稳健性与局限性

必须主动写：

- batch 与策略不能完全分离；
- Secondary 域偏移；
- 小样本；
- 单电芯策略较多；
- Q4 推荐仅适用于训练条件附近；
- 模型输出是统计关联，不是严格因果。

---

# 40. 目前已知的主要风险

## 风险 1：样本少

Train 只有约 41 个电芯。

处理：简单模型优先；复杂模型必须先在 Train 嵌套 policy-group CV 中稳定入围，Primary 只按冻结协议做一次受限确认。

## 风险 2：策略重复不足

大量策略只有一个电芯。

处理：Q1 策略结论优先重复策略；单电芯极端值只作为案例。

## 风险 3：batch 与策略纠缠

处理：

- within-batch；
- 重复策略；
- batch 敏感性；
- 主动承认不可完全辨识。

## 风险 4：Secondary 域偏移

处理：把 Secondary 当压力测试，而不是想办法把它“清洗得和 Train 一样”。

## 风险 5：SOH 定义混乱

处理：同时保留 \(SOH^{rel}\) 和 \(SOH^{nom}\)。

## 风险 6：Q2 解释模型被误当预测模型

处理：解释模型和代理预测模型分开评估。

## 风险 7：Q3 残差校正泄漏

处理：每个 Q3 外层折内重新生成 Q2 的内层 OOF 先验与残差；禁止复用一次全 Train OOF。

## 风险 8：bootstrap 被过度解释

处理：只称模型不确定性下的保守下界，不称真实寿命分位数。

## 风险 9：Q4 优化器钻模型漏洞

处理：

- 不自由外推；
- Train 中位数/IQR 标准化后的 raw/SOC 双空间 5-NN；
- 参数边界；
- 模型分歧；
- 全流水线 bootstrap 下界；
- 邻域支持在重采样中不稳定时直接拒绝。

## 风险 10：性能数字不可复现

处理：所有正式数字必须有实验目录、配置、预测文件、输入哈希、`script_sha256` 和 `config_sha256`。

## 风险 11：Primary 选择乐观偏差

处理：Train 内完成选型，只让极少量预注册候选进入已暴露 Primary 做一次受限确认；确认失败后不得在同一 Primary 上无痕循环调参。

## 风险 12：SOH 预测在截止点断裂或被长寿命电芯支配

处理：预测曲线在实测 \(SOH_i(k)\) 与官方 0.8 终点双端锚定；未来误差继承容量掩码，先按电芯计算再等权汇总，并报告寿命终点误差和模型稳定性带包含率。

## 风险 13：RAW 掩码连接或插值泄漏

处理：按 `(barcode, source_file, batch_index, cycle_index)` 一对一连接官方 RAW flags；`global_cycle_index` 只用于连接后的全局顺序；差值两端均须合格；电压网格、插值和平滑只在训练折拟合。

## 风险 14：新策略没有 early features

处理：只给 `Q2_provisional` 提名；运行至冻结的 \(k^*\) 并取得真实早期数据后，才能由 Q3 晋级为正式推荐。

## 风险 15：理论时间与实测时间混淆

处理：统一记 \(\tau_{0-80}\)，明确它不是完整 CC-CV 时间；先核验 `chargetime` 单位，再在 Train 中校准并报告偏差。

---

# 41. 明确禁止事项

后续代码和论文都应避免：

1. 把 \(C_1,Q_1,C_2\) 高阶回归系数解释成独立因果贡献；
2. 把 SHAP 数值写成物理贡献百分比；
3. 把单个极端电芯直接称“长寿命策略”；
4. 把决策树切分点写成物理临界点；
5. 用 Primary 选模型后仍称其为最终独立测试集；
6. 用 Secondary 调参；
7. 给未运行的新策略虚构 early features；
8. 把 bootstrap 低分位叫真实寿命分布；
9. 强迫所有电芯都有 knee；
10. 在 41 个训练样本上主推深度网络；
11. 允许 Q4 在盒状 min/max 范围内无限自由搜索；
12. 为了提高 Secondary \(R^2\) 把整体域偏移当异常删除；
13. 把待核验快速压力测试数字直接写进论文摘要；
14. 维护五套互不一致的早期特征生成逻辑；
15. 用 Q2-only 的新策略充当问题四最终推荐；
16. 在 Q3 各外层折中复用一次全 Train OOF 先验；
17. 按曲线行数直接汇总未来 SOH 误差，使长寿命电芯获得更高权重；
18. 未连接 `mat_deep_cycle_flags.csv` 或未检查两端循环就使用 RAW 差值特征；
19. 把 \(\tau_{0-80}\) 或单位未确认的 `chargetime` 写成完整实测充电时间；
20. 把单模型的 `D_z` 人为记成 0 并宣称模型一致。

---

# 42. 当前最值得优先验证的四个问题

## 问题 A

Q2 的原始参数 Ridge 能否先在 Train 嵌套 policy-group CV 中稳定优于常数基线，并在 Primary seen/unseen 的受限确认中保持方向？

## 问题 B

在控制整体暴露 \(A\) 后，SOC 相对分配模型能否得到稳定的：

\[
\gamma_j:\ SOC\ relative\ allocation\rightarrow\ln L
\]

曲线？

如果 bootstrap 后方向乱跳，就不能作为核心结论。

## 问题 C

Q3：

\[
\text{直接联合 M3}
\]

和：

\[
\text{残差校正 M4}
\]

谁先在 Train 完整嵌套交叉拟合中更稳，并通过 Primary 受限确认？同时，双端锚定 SOH 模板能否在五个截止点给出可接受的未来轨迹误差、模板失败率和模型稳定性带包含率？

## 问题 D

Q4：最终 Q2/Q3 流水线在什么策略区域开始：

- 预测极端；
- 不同模型分歧；
- bootstrap 不稳定？

这决定可信域边界。

---

# 43. 推荐的“锁方案”标准

## Q2 锁定条件

- Train 嵌套 policy-group CV 完成，主指标稳定优于常数基线；
- 候选、特征、调参规则和通过门槛在 V2.1 的 Primary 受限确认运行前冻结；
- Primary 受限确认中 seen/unseen 均未触发预注册失败门槛；
- \(\gamma_j\) 的 bootstrap 方向、区间和排名稳定性足以支持结论；否则明确“无法稳定辨识”；
- 预测代理在双空间支持域内无明显极端预测。

## Q3 锁定条件

- M1/M2/M3/M4 在 Train 完整嵌套交叉拟合中比较完成；
- 5/10/20/50/100 五个窗口均完成且 `feature_schema_id` 已冻结；
- Primary seen/unseen 受限确认完成；
- 未来 SOH 的掩码后按电芯等权误差、寿命终点误差、\(n^*=120\) 误差、模板失败率和稳定性带包含率完成；
- RAW challenger 的掩码连接、Train 入围和 Primary 保留/淘汰结论完成；
- \(k^*\) 按第 23.2 节的 Train-only 失败率 + one-standard-error 最小窗口规则冻结。

## Q4 锁定条件

- Q2、Q3 代理和最终重拟合方式确定；
- raw/SOC 双空间 5-NN、阈值分位数、网格步长和数学边界冻结；
- 电芯级 \(B\ge1000\)、10% 下分位的全流水线 bootstrap 完成；
- 已有策略与新策略的候选状态分开，Q2-only 点不进入正式 Pareto；
- 正式二维 Pareto、SOH 风险叠加（仅有可追溯 \(s_{min}\) 时硬过滤）、三档规则、Q1 基准对比和风险边界全部完成；
- Secondary 只完成一次压力测试，没有反向调参。

---

# 44. 最终建议的三个论文亮点

## 亮点 1：识别近固定快充时间下的策略约束

说明：

> 数据并非三个自由参数的全因子实验，因此不做简单的独立因果系数解释。

## 亮点 2：设计前预测与运行后校正分层

定义：

\[
\hat L_0
\]

和：

\[
\hat L_k
\]

清楚区分设计阶段和运行阶段。

## 亮点 3：只在模型有数据支撑的区域推荐策略

Q4 不只追求：

\[
\max \hat L
\]

而同时考虑：

- 时间；
- raw/SOC 双空间 5-NN 支持；
- 模型分歧；
- bootstrap 保守下界；
- Q3 早期运行确认与未来 SOH 下界；
- 批次适用范围。

---

# 45. 最终工作原则

后续每做一步，都问自己六个问题：

1. **这个输入在现实中当时真的能获得吗？**
2. **这个阈值是不是偷看了验证/测试集？**
3. **这个结论是相关还是因果？**
4. **这个策略有没有真实数据支撑？**
5. **这个性能数字能不能一键复现？**
6. **有没有更简单的方法能得到同样结论？**

如果其中任何一个答案不清楚，就不要急着把结果写成最终结论。

---

# 46. 当前状态判断

本次方法审查并完成 P0 后的判断为：

\[
\boxed{\text{方案框架条件性通过；P0 数据门禁通过}}
\]

“条件性通过”表示 Q1–Q4 的方法链条已经修到可执行候选框架；P0 已生成 99,279 行 `cycle_model_view.csv`、七字段逐循环掩码、五套统一窗口特征和机器审计报告。因此可以开始 Q1 和 Q2 的 Train 内首轮 PoC，但在候选模型尚未经过 PoC、Primary 受限确认和 Secondary 外部压力测试前，仍不能说：

> “最终模型已经确定。”

更准确的模型状态是：

\[
\boxed{\text{P0 已冻结；具体模型、超参数与推荐策略须经 PoC 后锁定}}
\]

现在不应该继续无限讨论新算法。

下一步最合理的动作：

\[
\boxed{Q1\rightarrow Q2首轮PoC\rightarrow Q3窗口比较}
\]

即：

1. 使用已冻结 P0 长表完成 Q1；
2. 只在 Train 内运行 Q2 首轮嵌套 policy-group CV；
3. 再按同一 P0 五套窗口完成 Q3 比较；
4. Q2 首轮只跑：
   - 原始参数 Ridge；
   - SOC 分区解释模型；
5. 只根据 Train 嵌套 CV 决定是否让 GAM/ElasticNet 等极少量 challenger 入围；
6. 在 V2.1 的 Primary 受限确认运行前冻结候选和门槛，随后只按协议运行一次；
7. 然后进入 Q3 的 M1/M2/M3/M4，并执行同样的 Train 选型—Primary 受限确认规则。

---

# 47. 参考文件

本方案当前基于：

- `B.docx`
- `paper/data_processing_and_split_details.md`
- `1710560890-r2I8.pdf`
- `交接文档.md`
- `data/processed/cell_labels.csv`
- `data/processed/cycle_summary_clean.csv`
- `data/processed/early_cycle_features.csv`
- `data/processed/feature_columns.json`
- `data/processed/data_preparation_summary.json`
- `outputs/data_audit/data_audit_report.md`
- `outputs/data_audit/mat_deep_cycle_flags.csv`
- `outputs/data_audit/mat_deep_cycle_summary.json`
- `data/deep_mat_audit_report.md`
- `src/reviews/l1_deep_mat_audit_review.md`
- `paper/qa_report.md`
- `D:/13470/Downloads/B题_优化建模方案与快速压力测试报告.docx`（外部历史参考，未纳入本目录正式证据链）

---

# 48. 一句话版路线

> **先完成 EOL、字段—循环掩码和五套窗口的 P0；Q1 解释数据规律；Q2 用 Train 嵌套验证做设计前寿命提名；Q3 用真实早期数据校正寿命与未来 SOH；最后 Q4 只在 raw/SOC 双空间可信域内，让已有或经早期试验确认的策略进入正式 Pareto，新策略在 Q3 确认前只保留为 `Q2_provisional`。**

---

# 附录 A：当前执行状态修订（2026-08-02）

本附录不改动 V2 的问题分解、变量定义和验证原则，只记录已执行实验与原计划之间必须在论文中据实反映的口径更新。若正文的“计划”与下列“已执行”冲突，以本附录和对应的可复现结果文件为准。

1. **对数口径**：已执行的 Q2/Q3/Q4 全部使用 \(z=\ln L\) 和 \(\hat L=\exp(\hat z)\)。历史字段名 `RMSE_log`、`MAE_log` 仍保留，但均指自然对数寿命尺度。
2. **Q3 实验补齐**：Round 2 已完整比较 M1（策略）、M2（早期运行）、M3（策略+早期）和 M4（P3 先验残差校正）；每个窗口均采用 Train 内 `policy_table9` 分组交叉验证。Round 3 另外以通过六字段深层掩码的充电曲线构造三个低维电压特征，形成 M3R，不替代主线的字段—循环掩码规则。
3. **当前 Q3 候选角色**：M3R-k=5 的 Train OOF 指标为 `RMSE_log=0.24070`、电芯等权未来 SOH RMSE=`0.03299`，是最早的曲线增强筛查候选；其相对 M2-k=5 的寿命误差差值区间仍跨 0，不能称已稳健改善寿命。M2-k=100 的对应指标为 `0.23174/0.03475`，是当前开发集内最低误差的正式校正**候选**。二者并非同一精度目标下的胜负关系。
4. **Primary/Secondary 边界**：此前 k=5/k=100 的 Primary 受限观察对应 M2 的早期特征流程，不能倒标为 M3 或 M3R 的外部确认。Primary 已暴露，只能保留为一次受限观察；M3R 和 M2-k=100 的最终外部压力测试仍只能在所有规则冻结后一次性使用 Secondary。
5. **Q4 当前可报告范围**：对已有策略的 Round 2 重算只使用 Train+Primary 的 84 枚电芯，得到 60 个已有策略、其中 4 个开发池非支配点；这是已有策略的开发池比较，不是最终推荐。历史网格产生的 1,775 条候选仍仅为 `Q2_provisional`，新策略没有真实早期运行数据时不得晋级为 `Q3_confirmed` 或正式 Pareto。
6. **尚未满足的锁定条件**：Q3 Round 3 的稳定性/结果人工裁决仍为 `PENDING`，且尚未进行 Secondary 压力测试。因此当前可继续做开发版写作与图表整理，但不得生成 `frozen_numbers.json`、最终推荐策略或“已通过外部验证”的论文表述。

证据入口：`methods/Q3/q3_round2_scope_update.md`、`robustness/Q3/q3_robustness_report.md`、`results/Q3/experiments/round3_raw_curve_challenger/`、`results/Q4/experiments/existing_policy_round2_m2k100/`。
