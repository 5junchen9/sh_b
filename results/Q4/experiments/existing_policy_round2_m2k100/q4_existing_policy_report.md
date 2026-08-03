# Q4 已有实验策略：冻结 Q2+Q3 聚合评价（Round 1）

> **状态：development_pool_evidence_only。** 本报告只评价已有实验策略；Train 使用策略分组交叉拟合，Primary 使用一次冻结确认。由于 Primary 已有探索暴露且 Secondary 未参与，本结果不是独立外部验证，也不替代最终压力测试。

## 1. 输入与口径

- 开发池：Train 41 枚 + Primary 43 枚 = 84 枚物理电芯；Secondary 完全未读取。
- Q2：Train 使用 P3 加性 GAM 的 OOF 对数寿命预测；Primary 使用冻结 P3 的一次确认预测。
- Q3：使用固定 k=100 的寿命预测与第 120 循环 SOH 预测；Train 是 OOF，Primary 是冻结确认。
- 可追溯性账本：`outputs/experiments/primary_confirmation_manifest_post_exposure.json` 汇总了两次 Primary 确认的脚本、协议和输入哈希。该账本为事后重建，不能将 Primary 重新表述为前瞻预注册或独立测试。
- 每一策略先在电芯层面汇总，再作 2,000 次**电芯重抽样**。因此 `empirical_p10` 是策略内预测离散度的经验下分位摘要，**不是**经模型重拟合或覆盖率校准的置信下界。

## 2. 汇总结果

- 共有 60 个已有策略；其中 19 个策略至少由两枚物理电芯支持，具备开发池内策略级比较资格。
- 开发池内非支配策略数为 4；这些点只是在理论时间最小、经验 P10 保守寿命摘要最大这两个方向上不被已有策略支配，不能称为最终推荐。
- 第 120 循环 SOH 预测作为并列风险信息显示，不设置题外硬阈值，也不与寿命重复加权。

## 3. 使用边界

1. 所有策略均为**已有实验策略**，本报告不新增或排序 `Q2_provisional` 新策略。
2. 对 `cell_count=1` 的策略只保留为 `observed_single_cell_case`，不进入 Pareto。
3. Q4 的正式新策略路径仍为：Q2 提名 → 真实 k=5 筛查 → 真实 k=100 Q3 确认 → 再形成 Q2+Q3 Pareto。
4. Secondary 仅在推荐、参数与评价规则完全冻结后作为最终独立压力测试，不能用于当前重选策略。

## 4. 产物

- `tables/q4_existing_policy_cell_evidence.csv`：84 枚电芯的预测来源与合并证据。
- `tables/q4_existing_policy_summary.csv`：策略级汇总、样本数、经验 P10 与状态。
- `tables/q4_existing_policy_development_pareto.csv`：开发池内非支配策略；非最终推荐。
- `figures/q4_existing_policy_pareto.png/svg`：中文策略级权衡图。
