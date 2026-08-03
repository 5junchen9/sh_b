# Q2 最终方法说明：策略—寿命条件关联与受限设计前代理

## 1. 方法选择摘要

- **正文主线**：Q2-A M1 主效应 Ridge。
- **敏感性分析**：Q2-A M2 二阶交互 Ridge。
- **Q4 接口**：Q2-B P3 低自由度加性 GAM，仅生成 `Q2_provisional` 候选。

### 候选方法及其角色

| 方法 | 最终角色 | 人工依据 |
|---|---|---|
| M1 主效应 Ridge | 正文保守主线 | M2 的典型误差点估计虽改善，但 bootstrap 差值区间跨 0；选择最简单且透明的主线。<!-- from Q2-D02, Q2-D05 --> |
| M2 二阶交互 Ridge | SOC 阶段倍率交互的敏感性分析 | 只作探索性条件关联，不写为显著优于 M1 或因果机制。<!-- from Q2-D02, Q2-D05 --> |
| P3 加性 GAM | Q4 的冻结 `provisional` 代理 | 不作为最终最优或正式寿命排序模型；Secondary 也未支持其升级。<!-- from Q2-D04, Q2-D05 --> |
| C1 受限提升树 | 受限 challenger | 不以一次点估计较低替换 P3；相对 P3 的 bootstrap 差值区间跨 0。<!-- from Q2-D05 --> |

### 选择理由（人工决定转录）

“以 M1 主效应 Ridge 作为保守基线；M2 保留为不同 SOC 阶段倍率交互的探索性关联/敏感性分析；Q4 不直接使用这两个当前 PoC 模型直接优化，而进入 Q2-B 的 Train-only 代理比较。”<!-- from Q2-D02 -->

“相同可信域、同样的分组验证和 bootstrap 下，选择误差不劣、过预测风险不更高、且最简单的模型。”<!-- from Q2-D02 -->

接受的取舍是：M1 牺牲了交互项的拟合自由度，以避免把小样本策略网格中的偶然差异写成机制；M2 保留信息价值，但不承担正文主结论。

## 2. 模型假设

| 编号 | 假设 | 分类与来源 | 违反影响 |
|---|---|---|---|
| Q2-A1 | 在 Train 支持域内，低自由度模型近似策略与 `ln(L)` 的条件关系。 | 简化。<!-- from q2_method_explanation --> | 强阈值或高阶结构会造成欠拟合，不能用其推断域外关系。 |
| Q2-A2 | 对数寿命误差可描述相对误差，同时报告 cycle 尺度误差。 | 简化。<!-- from q2_method_explanation --> | 若决策只关心绝对 cycle 误差，模型排序可能改变。 |
| Q2-A3 | 策略组折外验证与策略组块 bootstrap 近似刻画未见策略不确定性。 | 简化。<!-- from q2_method_explanation --> | 少数重复策略与批次异质性会使区间偏乐观。 |
| A4 | 相同 `policy_table9` 必须在验证与 bootstrap 中保持同组。 | 必要。<!-- from planning/model_assumptions.md --> | 拆散重复策略会泄漏策略信息并夸大表现。 |
| A5 | 当前数据只支持条件关联与预测。 | 必要。<!-- from planning/model_assumptions.md --> | 因果解释会超过研究设计支持范围。 |

## 3. 符号与数据对象

| 符号 | 含义 | 单位/范围 |
|---|---|---|
| `i∈𝓘` | 电芯索引 | Train 中 41 枚 |
| `p(i)` | 电芯 `i` 所属 `policy_table9` 策略组 | Train 中 40 组 |
| `x_i=(C_{1i},q_i,C_{2i})` | 两段式策略参数，`q_i=Q1_percent/100` | C-rate、无量纲、C-rate |
| `L_i` | Table 9 循环寿命 | cycle |
| `z_i=ln(L_i)` | 回归目标 | 无量纲 |
| `\hat z_i, \hat L_i` | 预测对数寿命及 `exp(\hat z_i)` | 无量纲、cycle |
| `α` | Ridge/GAM 正则化强度 | 内层策略组 CV 选择 |
| `β, γ` | 主效应与二阶交互的回归系数 | 折内估计 |

## 4. 数学模型与求解

### 4.1 主效应 Ridge（M1）

对折内标准化后的 `\tilde x_i`，拟合

`\hat z_i=β_0+β_1\tilde C_{1i}+β_2\tilde q_i+β_3\tilde C_{2i}`，

并最小化

`\sum_{i∈Train_f}(z_i-\hat z_i)^2+α\lVert β\rVert_2^2`。

它给出三个策略参数与寿命的低复杂度条件关联，是正文可解释基线。

### 4.2 二阶交互 Ridge（M2）

在 M1 的主效应基础上加入二次项和两两交互：

`\hat z_i=β_0+β^T\tilde x_i+γ^T(\tilde C_1^2,\tilde q^2,\tilde C_2^2,\tilde C_1\tilde q,\tilde C_1\tilde C_2,\tilde q\tilde C_2)_i`。

同样以 Ridge 惩罚控制小样本系数膨胀。交互项只表示“在当前观测和控制变量下的联合关联”，不解释为电化学因果效应。

### 4.3 设计前 P3 加性 GAM（Q4 接口）

P3 将策略变量映射为

`\hat z_i=g_1(C_{1i})+g_2(q_i)+g_3(C_{2i})+β_0`，

其中每个 `g_j` 为低自由度平滑项；Train 内固定的 `n_knots=4`、`α=0.03` 仅用于候选筛查。P3 输出不能作为最终排序或寿命下界。

### 4.4 可复现流程

1. 从 P0 处理结果读取 `Train` 电芯、策略变量与 Table 9 寿命；目标固定为 `ln(L)`。
2. 按 `policy_table9` 做外层分组验证；标准化、缺失处理、参数选择均在训练折内进行。
3. 在内层分组 CV 选择 `α`，并保存所有折外预测。
4. 计算 `RMSE_log`、`MAE_log`、cycle 尺度误差和过预测比例。
5. 对策略组进行 2,000 次成对块 bootstrap，比较 M2−M1 与 P3/challenger 的误差差值。
6. 仅以冻结的 P3 形成 Q4 可信域内 `Q2_provisional` 候选；不把预测值写为工程推荐。

## 5. 评价指标与人工门槛

`RMSE_{lnL}=sqrt(N^{-1}Σ_i(\hat z_i-z_i)^2)`；
`MAE_{lnL}=N^{-1}Σ_i|\hat z_i-z_i|`；
`\hat L_i=exp(\hat z_i)` 后另报 cycle 尺度误差与过预测比例。

正式解释模型的人工预设门槛为：M2 的 `ΔMAE_log` 95% 置信区间上界小于 0、相对改善不少于 5%、主要交互项符号稳定率不少于 80%。当前 M2 的相对 MAE 改善为 8.91%，但区间上界为 0.02620，未满足联合门槛；因此不将 M2 升格为正文主模型。<!-- from q2_method_explanation -->

## 6. 写作指引

正文先给出 M1 的条件关联与误差，再用 M2 的符号稳定性和不确定性解释不同 SOC 阶段倍率的探索性联合关系。P3、C1 的比较放入“设计前候选与局限性”，并明确 P3 在 Secondary 未获升级。避免使用“最优倍率”“因果贡献”“可直接部署”等措辞。

**证据交接**：`results/Q2/reports/q2_final_result_analysis.md`、`robustness/Q2/q2_robustness_report.md`。
