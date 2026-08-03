"""Q4 Round 1: aggregate frozen Q2/Q3 evidence for already observed development-pool policies.

This script does not rank new strategies.  Train rows use OOF predictions and
Primary rows use the one-time frozen confirmation; the source remains explicit.
The policy bootstrap resamples cells only, so its lower quantile is an empirical
within-policy summary, not a calibrated life-confidence bound.
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
matplotlib.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["Microsoft YaHei", "SimHei", "DejaVu Sans"],
    "axes.unicode_minus": False,
    "svg.fonttype": "none",
})
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

SCRIPT = Path(__file__).resolve()
ROOT = SCRIPT.parents[2]
OUT = ROOT / "results" / "Q4" / "experiments" / "existing_policy_round1"
TABLES, FIGURES, METRICS, LOGS = (OUT / x for x in ("tables", "figures", "metrics", "logs"))
SEED = 20260802
N_BOOT = 2000

LABELS = ROOT / "data" / "processed" / "cell_labels.csv"
Q2_TRAIN = ROOT / "results" / "Q2" / "experiments" / "q2b_proxy_round1" / "tables" / "q2b_oof_predictions.csv"
Q2_PRIMARY = ROOT / "results" / "Q2" / "experiments" / "q2b_primary_confirmation_round1" / "tables" / "q2b_primary_predictions.csv"
Q3_TRAIN = ROOT / "results" / "Q3" / "experiments" / "round1" / "tables" / "m3_oof_life_predictions.csv"
Q3_PRIMARY = ROOT / "results" / "Q3" / "experiments" / "primary_confirmation_round1" / "tables" / "q3_primary_life_predictions.csv"
SOH_TRAIN = ROOT / "results" / "Q3" / "experiments" / "round1" / "tables" / "m3_oof_soh120_predictions.csv"
SOH_PRIMARY = ROOT / "results" / "Q3" / "experiments" / "primary_confirmation_round1" / "tables" / "q3_primary_soh120_predictions.csv"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def tau_0_80(c1: float, q_pct: float, c2: float) -> float:
    q = q_pct / 100.0
    return 60.0 * (q / c1 + (0.8 - q) / c2)


def is_pareto(frame: pd.DataFrame) -> pd.Series:
    """Minimise time and maximise empirical robust-life summary."""
    time = frame["tau_0_80_min"].to_numpy(float)
    life = frame["life_rob_empirical_p10_cycle"].to_numpy(float)
    keep = np.ones(len(frame), dtype=bool)
    for i in range(len(frame)):
        dominates = (time <= time[i]) & (life >= life[i]) & ((time < time[i]) | (life > life[i]))
        if dominates.any():
            keep[i] = False
    return pd.Series(keep, index=frame.index)


def bootstrap_policy(group: pd.DataFrame, rng: np.random.Generator) -> dict[str, float]:
    q2 = group["q2_pred_log_life"].to_numpy(float)
    q3 = group["q3_pred_log_life_k100"].to_numpy(float)
    if len(q2) != len(q3) or len(q2) == 0:
        raise RuntimeError("Each policy must have paired Q2/Q3 life predictions.")
    draws = rng.integers(0, len(group), size=(N_BOOT, len(group)))
    q2_median = np.median(q2[draws], axis=1)
    q3_median = np.median(q3[draws], axis=1)
    q2_p10 = float(np.quantile(q2_median, 0.10))
    q3_p10 = float(np.quantile(q3_median, 0.10))
    available_soh = group["q3_pred_soh_nom_120"].dropna().to_numpy(float)
    soh_p10 = float("nan")
    soh_median = float("nan")
    if len(available_soh):
        soh_draws = rng.integers(0, len(available_soh), size=(N_BOOT, len(available_soh)))
        soh_samples = np.median(available_soh[soh_draws], axis=1)
        soh_p10 = float(np.quantile(soh_samples, 0.10))
        soh_median = float(np.median(available_soh))
    return {
        "q2_pred_median_log": float(np.median(q2)),
        "q3_pred_median_log": float(np.median(q3)),
        "q2_pred_empirical_p10_log": q2_p10,
        "q3_pred_empirical_p10_log": q3_p10,
        "q2_pred_empirical_p10_cycle": float(np.exp(q2_p10)),
        "q3_pred_empirical_p10_cycle": float(np.exp(q3_p10)),
        "life_rob_empirical_p10_cycle": float(np.exp(min(q2_p10, q3_p10))),
        "q3_pred_soh_nom_120_median": soh_median,
        "q3_pred_soh_nom_120_empirical_p10": soh_p10,
        "soh120_prediction_cell_count": int(len(available_soh)),
    }


def collect_cell_evidence() -> pd.DataFrame:
    labels = pd.read_csv(LABELS)
    dev = labels.loc[labels["dataset_table9"].isin(["Train", "Prim. Test"])].copy()
    if len(dev) != 84 or dev["barcode"].duplicated().any():
        raise RuntimeError("Frozen development pool must have 84 unique Train/Primary barcodes.")

    q2_train = pd.read_csv(Q2_TRAIN)[["barcode", "P3_additive_gam"]].rename(columns={"P3_additive_gam": "q2_pred_log_life"})
    q2_train["q2_source"] = "Train_policy_group_OOF"
    q2_primary = pd.read_csv(Q2_PRIMARY)[["barcode", "predicted_log_life"]].rename(columns={"predicted_log_life": "q2_pred_log_life"})
    q2_primary["q2_source"] = "Primary_frozen_confirmation"
    q2 = pd.concat([q2_train, q2_primary], ignore_index=True, verify_integrity=True)

    q3_train_raw = pd.read_csv(Q3_TRAIN)
    # Round 1 historical output has no model_id; Round 2 holds all candidates.
    q3_train_filter = q3_train_raw.k.eq(100)
    if "model_id" in q3_train_raw.columns:
        q3_train_filter &= q3_train_raw.model_id.eq("M2")
    q3_train = q3_train_raw.loc[q3_train_filter, ["barcode", "pred_log_life"] if "pred_log_life" in q3_train_raw.columns else ["barcode", "predicted_log_life"]].copy()
    q3_train = q3_train.rename(columns={"pred_log_life": "q3_pred_log_life_k100", "predicted_log_life": "q3_pred_log_life_k100"})
    q3_train["q3_source"] = "Train_policy_group_OOF"
    q3_primary = pd.read_csv(Q3_PRIMARY).query("k == 100")[["barcode", "predicted_log_life"]].rename(columns={"predicted_log_life": "q3_pred_log_life_k100"})
    q3_primary["q3_source"] = "Primary_frozen_confirmation"
    q3 = pd.concat([q3_train, q3_primary], ignore_index=True, verify_integrity=True)

    soh_train_raw = pd.read_csv(SOH_TRAIN)
    soh_train_filter = soh_train_raw.k.eq(100)
    if "model_id" in soh_train_raw.columns:
        soh_train_filter &= soh_train_raw.model_id.eq("M2")
    soh_train = soh_train_raw.loc[soh_train_filter, ["barcode", "predicted_soh_nom_120", "actual_soh_nom_120"]].rename(columns={"predicted_soh_nom_120": "q3_pred_soh_nom_120", "actual_soh_nom_120": "actual_soh_nom_120_audit"})
    soh_primary = pd.read_csv(SOH_PRIMARY).query("k == 100")[["barcode", "predicted_soh_nom_120", "actual_soh_nom_120"]].rename(columns={"predicted_soh_nom_120": "q3_pred_soh_nom_120", "actual_soh_nom_120": "actual_soh_nom_120_audit"})
    soh = pd.concat([soh_train, soh_primary], ignore_index=True, verify_integrity=True)

    out = dev.merge(q2, on="barcode", how="left", validate="one_to_one").merge(q3, on="barcode", how="left", validate="one_to_one").merge(soh, on="barcode", how="left", validate="one_to_one")
    if out[["q2_pred_log_life", "q3_pred_log_life_k100"]].isna().any().any():
        raise RuntimeError("Q4 observed-policy aggregation is missing a paired frozen Q2 or Q3 life prediction.")
    out["tau_0_80_min"] = out.apply(lambda r: tau_0_80(r.C1, r.Q1_percent, r.C2), axis=1)
    out["evidence_role"] = np.where(out.dataset_table9.eq("Train"), "cross_fitted_development_evidence", "restricted_confirmation_evidence")
    return out


def plot(policy: pd.DataFrame) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(12, 5.4), gridspec_kw={"width_ratios": [1.35, 1]})
    ax = axes[0]
    eligible = policy["status"].eq("observed_Q2Q3_confirmed")
    base = policy.loc[~eligible]
    if len(base):
        ax.scatter(base.tau_0_80_min, base.life_rob_empirical_p10_cycle, c="#A8A8A8", s=42, alpha=.8, label="单电芯案例（不入帕累托比较）")
    main = policy.loc[eligible]
    bubbles = ax.scatter(main.tau_0_80_min, main.life_rob_empirical_p10_cycle, c=main.q3_pred_soh_nom_120_empirical_p10, cmap="viridis", s=60 + 35 * main.cell_count, edgecolor="white", linewidth=.7, label="至少 2 枚电芯的已有策略")
    pareto = main.loc[main.development_pareto]
    ax.scatter(pareto.tau_0_80_min, pareto.life_rob_empirical_p10_cycle, facecolors="none", edgecolors="#E53935", linewidth=1.8, s=190, label="开发池内非支配策略")
    ax.set(title="已有策略：时间—保守寿命摘要", xlabel="理论 0–80% 充电时间（min）", ylabel="Q2/Q3 经验 P10 保守寿命摘要（cycle）")
    ax.grid(axis="both", alpha=.18, linestyle="--")
    ax.legend(fontsize=8, loc="best")
    cbar = fig.colorbar(bubbles, ax=ax, fraction=.046, pad=.04)
    cbar.set_label("Q3 预测 SOH_nom(120) 的经验 P10")

    ax = axes[1]
    source = policy[["train_oof_cell_count", "primary_confirmation_cell_count"]].sum()
    bars = ax.bar(["训练集\n交叉拟合", "主确认集\n冻结确认"], source.values, color=["#1A6FC4", "#E28E2C"], width=.58)
    for bar, value in zip(bars, source.values):
        ax.text(bar.get_x() + bar.get_width() / 2, value + .6, str(int(value)), ha="center", va="bottom")
    ax.set(title="策略级汇总的证据来源", xlabel="电芯预测来源", ylabel="电芯数")
    ax.set_ylim(0, max(source.values) * 1.22)
    ax.grid(axis="y", alpha=.18, linestyle="--")
    fig.suptitle("Q4：开发池已有策略的冻结 Q2+Q3 证据（非独立外部验证）", fontsize=13, fontweight="bold")
    fig.tight_layout()
    for ext, kwargs in (("svg", {}), ("png", {"dpi": 320})):
        fig.savefig(FIGURES / f"q4_existing_policy_pareto.{ext}", bbox_inches="tight", **kwargs)
    plt.close(fig)


def main() -> None:
    for folder in (TABLES, FIGURES, METRICS, LOGS):
        folder.mkdir(parents=True, exist_ok=True)
    cell = collect_cell_evidence()
    rng = np.random.default_rng(SEED)
    records: list[dict[str, object]] = []
    for policy_name, group in cell.groupby("policy_table9", sort=True):
        if group[["C1", "Q1_percent", "C2"]].drop_duplicates().shape[0] != 1:
            raise RuntimeError(f"Policy {policy_name} has inconsistent parameter triples.")
        summary = bootstrap_policy(group, rng)
        first = group.iloc[0]
        n = len(group)
        records.append({
            "policy_table9": policy_name,
            "C1": float(first.C1), "Q1_percent": float(first.Q1_percent), "C2": float(first.C2),
            "tau_0_80_min": float(first.tau_0_80_min),
            "cell_count": int(n),
            "train_oof_cell_count": int(group.dataset_table9.eq("Train").sum()),
            "primary_confirmation_cell_count": int(group.dataset_table9.eq("Prim. Test").sum()),
            "status": "observed_Q2Q3_confirmed" if n >= 2 else "observed_single_cell_case",
            "evidence_scope": "Train rows are policy-group OOF; Primary rows are one-time frozen confirmation; not independent external validation.",
            **summary,
        })
    policy = pd.DataFrame(records).sort_values(["tau_0_80_min", "life_rob_empirical_p10_cycle"], ascending=[True, False]).reset_index(drop=True)
    policy["development_pareto"] = False
    eligible = policy.status.eq("observed_Q2Q3_confirmed") & policy.q3_pred_soh_nom_120_empirical_p10.notna()
    policy.loc[eligible, "development_pareto"] = is_pareto(policy.loc[eligible])
    policy["pareto_scope"] = np.where(policy.development_pareto, "development_pool_non_dominated_not_external", "not_on_development_pool_pareto")

    pareto = policy.loc[policy.development_pareto].copy()
    cell.to_csv(TABLES / "q4_existing_policy_cell_evidence.csv", index=False, encoding="utf-8-sig")
    policy.to_csv(TABLES / "q4_existing_policy_summary.csv", index=False, encoding="utf-8-sig")
    pareto.to_csv(TABLES / "q4_existing_policy_development_pareto.csv", index=False, encoding="utf-8-sig")
    plot(policy)

    report = f"""# Q4 已有实验策略：冻结 Q2+Q3 聚合评价（Round 1）

> **状态：development_pool_evidence_only。** 本报告只评价已有实验策略；Train 使用策略分组交叉拟合，Primary 使用一次冻结确认。由于 Primary 已有探索暴露且 Secondary 未参与，本结果不是独立外部验证，也不替代最终压力测试。

## 1. 输入与口径

- 开发池：Train 41 枚 + Primary 43 枚 = 84 枚物理电芯；Secondary 完全未读取。
- Q2：Train 使用 P3 加性 GAM 的 OOF 对数寿命预测；Primary 使用冻结 P3 的一次确认预测。
- Q3：使用固定 k=100 的寿命预测与第 120 循环 SOH 预测；Train 是 OOF，Primary 是冻结确认。
- 可追溯性账本：`outputs/experiments/primary_confirmation_manifest_post_exposure.json` 汇总了两次 Primary 确认的脚本、协议和输入哈希。该账本为事后重建，不能将 Primary 重新表述为前瞻预注册或独立测试。
- 每一策略先在电芯层面汇总，再作 2,000 次**电芯重抽样**。因此 `empirical_p10` 是策略内预测离散度的经验下分位摘要，**不是**经模型重拟合或覆盖率校准的置信下界。

## 2. 汇总结果

- 共有 {len(policy)} 个已有策略；其中 {int((policy.cell_count >= 2).sum())} 个策略至少由两枚物理电芯支持，具备开发池内策略级比较资格。
- 开发池内非支配策略数为 {len(pareto)}；这些点只是在理论时间最小、经验 P10 保守寿命摘要最大这两个方向上不被已有策略支配，不能称为最终推荐。
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
"""
    (OUT / "q4_existing_policy_report.md").write_text(report, encoding="utf-8")
    inputs = {str(p.relative_to(ROOT)).replace("\\\\", "/"): sha(p) for p in (LABELS, Q2_TRAIN, Q2_PRIMARY, Q3_TRAIN, Q3_PRIMARY, SOH_TRAIN, SOH_PRIMARY)}
    payload = {
        "question": "Q4", "round": OUT.name, "status": "development_pool_evidence_only",
        "execution_timestamp": datetime.now(timezone.utc).isoformat(), "random_seed": SEED,
        "development_cells": int(len(cell)), "secondary_read": False, "policy_count": int(len(policy)),
        "multi_cell_policy_count": int((policy.cell_count >= 2).sum()), "development_pareto_count": int(len(pareto)),
        "bootstrap": {"repeats": N_BOOT, "unit": "barcode within policy", "interpretation": "empirical lower summary only; no model refit or calibrated coverage"},
        "input_sha256": inputs, "script_sha256": sha(SCRIPT),
        "outputs": ["tables/q4_existing_policy_cell_evidence.csv", "tables/q4_existing_policy_summary.csv", "tables/q4_existing_policy_development_pareto.csv", "figures/q4_existing_policy_pareto.png", "figures/q4_existing_policy_pareto.svg", "q4_existing_policy_report.md"],
    }
    text = json.dumps(payload, ensure_ascii=False, indent=2)
    (METRICS / "q4_existing_policy_summary.json").write_text(text, encoding="utf-8")
    (OUT / "run_summary.json").write_text(text, encoding="utf-8")
    (LOGS / "run.log").write_text(text + "\n", encoding="utf-8")
    print(json.dumps({"status": payload["status"], "policies": len(policy), "pareto": len(pareto)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
