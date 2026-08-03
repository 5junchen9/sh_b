"""Q3 Round 2 policy-cluster bootstrap and early-window Pareto diagnostics.

Consumes only the Train-only OOF outputs from q3_run_joint_comparison.py.  It does
not refit or select a model: it quantifies paired error differences under resampling
of policy groups, using both policy-equal and cell-equal aggregations.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
matplotlib.rcParams.update({"font.family": "sans-serif", "font.sans-serif": ["Microsoft YaHei", "SimHei", "DejaVu Sans"], "axes.unicode_minus": False, "svg.fonttype": "none"})
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "results" / "Q3" / "experiments" / "round2_joint" / "tables"
OUT = ROOT / "robustness" / "Q3"
TABLES, FIGURES, METRICS = (OUT / item for item in ("tables", "figures", "metrics"))
SEED, B = 20260802, 2000

# Named comparisons needed for the V2.1 alternatives and the dual-window statement.
COMPARISONS = [
    ("M3_k5_vs_M2_k5", "M2", 5, "M3", 5),
    ("M3_k10_vs_M2_k10", "M2", 10, "M3", 10),
    ("M3_k20_vs_M2_k20", "M2", 20, "M3", 20),
    ("M3_k50_vs_M2_k50", "M2", 50, "M3", 50),
    ("M3_k100_vs_M2_k100", "M2", 100, "M3", 100),
    ("M4_k5_vs_M2_k5", "M2", 5, "M4", 5),
    ("M3_k5_vs_M2_k100", "M2", 100, "M3", 5),
    ("M2_k5_vs_M2_k100", "M2", 100, "M2", 5),
    ("M3_k5_vs_M3_k10", "M3", 10, "M3", 5),
]


def metric_samples(life: pd.DataFrame, curve: pd.DataFrame, model: str, k: int, weighting: str) -> dict[str, tuple[np.ndarray, np.ndarray]]:
    """Return policy labels and per-unit metric components for one model-window."""
    life_block = life.loc[(life.model_id.eq(model)) & (life.k.eq(k))].copy()
    curve_block = curve.loc[(curve.model_id.eq(model)) & (curve.k.eq(k))].copy()
    if len(life_block) != 41 or len(curve_block) != 41:
        raise RuntimeError(f"{model}, k={k} 未覆盖全部 41 枚 Train 电芯。")
    merged = life_block.merge(curve_block[["barcode", "soh_mse"]], on="barcode", validate="one_to_one")
    merged["log_error"] = merged.predicted_log_life - merged.actual_log_life
    merged["squared_log_error"] = merged.log_error ** 2
    merged["absolute_log_error"] = merged.log_error.abs()
    if weighting == "policy_equal":
        group = merged.groupby("policy_table9", sort=True).agg(
            squared_log_error=("squared_log_error", "mean"), absolute_log_error=("absolute_log_error", "mean"), soh_mse=("soh_mse", "mean")
        ).reset_index()
        return {name: (group.policy_table9.to_numpy(), group[name].to_numpy(float)) for name in ("squared_log_error", "absolute_log_error", "soh_mse")}
    if weighting == "cell_equal":
        return {name: (merged.policy_table9.to_numpy(), merged[name].to_numpy(float)) for name in ("squared_log_error", "absolute_log_error", "soh_mse")}
    raise ValueError(weighting)


def paired_bootstrap(life: pd.DataFrame, curve: pd.DataFrame, baseline: tuple[str, int], candidate: tuple[str, int], weighting: str) -> list[dict]:
    """Policy-cluster resampling; delta is candidate error minus baseline error."""
    b_life = life.loc[(life.model_id.eq(baseline[0])) & (life.k.eq(baseline[1]))].copy()
    c_life = life.loc[(life.model_id.eq(candidate[0])) & (life.k.eq(candidate[1]))].copy()
    b_curve = curve.loc[(curve.model_id.eq(baseline[0])) & (curve.k.eq(baseline[1]))].copy()
    c_curve = curve.loc[(curve.model_id.eq(candidate[0])) & (curve.k.eq(candidate[1]))].copy()
    base = metric_samples(life, curve, baseline[0], baseline[1], weighting)
    cand = metric_samples(life, curve, candidate[0], candidate[1], weighting)
    policy_order = np.sort(np.unique(b_life.policy_table9))
    if not np.array_equal(policy_order, np.sort(np.unique(c_life.policy_table9))):
        raise RuntimeError("成对比较的策略组集合不一致。")
    rng = np.random.default_rng(SEED + baseline[1] * 100 + candidate[1] * 10 + ord(candidate[0][-1]))
    rows = []
    for component, label, transform in (
        ("squared_log_error", "RMSE_log", lambda x: np.sqrt(np.mean(x))),
        ("absolute_log_error", "MAE_log", lambda x: np.mean(x)),
        ("soh_mse", "cell_equal_soh_rmse", lambda x: np.sqrt(np.mean(x))),
    ):
        base_group, base_values = base[component]
        cand_group, cand_values = cand[component]
        # Policy-equal has one row per group.  Cell-equal retains cells but samples their group clusters.
        boot = np.empty(B)
        for rep in range(B):
            sampled = rng.choice(policy_order, size=len(policy_order), replace=True)
            base_idx = np.concatenate([np.flatnonzero(base_group == group) for group in sampled])
            cand_idx = np.concatenate([np.flatnonzero(cand_group == group) for group in sampled])
            boot[rep] = transform(cand_values[cand_idx]) - transform(base_values[base_idx])
        point = transform(cand_values) - transform(base_values)
        rows.append({
            "weighting": weighting, "metric": label, "baseline_model": baseline[0], "baseline_k": baseline[1],
            "candidate_model": candidate[0], "candidate_k": candidate[1], "point_delta_candidate_minus_baseline": float(point),
            "ci95_low": float(np.quantile(boot, 0.025)), "ci95_high": float(np.quantile(boot, 0.975)),
            "candidate_improvement_rate": float(np.mean(boot < 0)), "bootstrap_replicates": B,
        })
    return rows


def pareto_table(metrics: pd.DataFrame) -> pd.DataFrame:
    """Non-dominated on earlier k, lifetime RMSE and SOH RMSE (all minimized)."""
    tab = metrics[["model_id", "model_name", "k", "rmse_log", "mae_log", "cell_equal_soh_rmse", "overprediction_rate"]].copy()
    dominated = []
    values = tab[["k", "rmse_log", "cell_equal_soh_rmse"]].to_numpy(float)
    for idx, value in enumerate(values):
        other = np.arange(len(tab)) != idx
        better_or_equal = np.all(values[other] <= value, axis=1)
        strictly_better = np.any(values[other] < value, axis=1)
        dominated.append(bool(np.any(better_or_equal & strictly_better)))
    tab["strictly_dominated"] = dominated
    tab["pareto_status"] = np.where(tab.strictly_dominated, "严格支配", "非支配")
    return tab.sort_values(["strictly_dominated", "k", "rmse_log"])


def draw(comparisons: pd.DataFrame, pareto: pd.DataFrame) -> None:
    selected = comparisons.loc[
        comparisons.weighting.eq("policy_equal")
        & comparisons.metric.eq("RMSE_log")
        & comparisons.comparison_id.isin(["M3_k5_vs_M2_k5", "M3_k5_vs_M2_k100", "M2_k5_vs_M2_k100", "M3_k5_vs_M3_k10"])
    ].copy()
    labels = selected.comparison_id.str.replace("_vs_", "\n对 ").str.replace("_", " ")
    fig, axes = plt.subplots(1, 2, figsize=(12.2, 4.6))
    for pos, row in enumerate(selected.itertuples()):
        axes[0].errorbar(pos, row.point_delta_candidate_minus_baseline,
                         yerr=[[row.point_delta_candidate_minus_baseline - row.ci95_low], [row.ci95_high - row.point_delta_candidate_minus_baseline]],
                         fmt="o", color="#4C78A8", capsize=4)
    axes[0].axhline(0, color="#555555", linestyle="--", linewidth=1)
    axes[0].set(xticks=range(len(selected)), xticklabels=labels, ylabel="误差差值（候选 − 基线）", title="(a) 策略等权 bootstrap：寿命 RMSE 差值")
    axes[0].grid(axis="y", alpha=0.22)
    palette = {"M1": "#4C78A8", "M2": "#F58518", "M3": "#54A24B", "M4": "#B279A2"}
    for method, block in pareto.groupby("model_id"):
        axes[1].scatter(block.k, block.rmse_log, s=np.where(block.strictly_dominated, 38, 86), color=palette[method], label=method, alpha=np.where(block.strictly_dominated, 0.35, 0.95))
    axes[1].set(xlabel="观察截止循环 k（循环）", ylabel="寿命 RMSE（ln 尺度）", title="(b) 三目标 Pareto：时间—寿命—SOH")
    axes[1].grid(alpha=0.22); axes[1].legend(title="模型")
    fig.suptitle("Q3 第二轮：候选差异的分组重抽样与窗口权衡", y=1.03, fontsize=13)
    fig.tight_layout()
    for ext, kwargs in (("png", {"dpi": 300}), ("svg", {})):
        fig.savefig(FIGURES / f"q3_round2_bootstrap_pareto.{ext}", bbox_inches="tight", **kwargs)
    plt.close(fig)


def main() -> None:
    for directory in (TABLES, FIGURES, METRICS):
        directory.mkdir(parents=True, exist_ok=True)
    life = pd.read_csv(SOURCE / "joint_oof_life_predictions.csv")
    curve = pd.read_csv(SOURCE / "joint_cell_curve_errors.csv")
    metrics = pd.read_csv(SOURCE / "joint_window_metrics.csv")
    rows = []
    for comparison_id, base_model, base_k, cand_model, cand_k in COMPARISONS:
        for weighting in ("policy_equal", "cell_equal"):
            for result in paired_bootstrap(life, curve, (base_model, base_k), (cand_model, cand_k), weighting):
                result["comparison_id"] = comparison_id
                rows.append(result)
    comparison = pd.DataFrame(rows)
    pareto = pareto_table(metrics)
    comparison.to_csv(TABLES / "q3_round2_policy_bootstrap_comparisons.csv", index=False, encoding="utf-8-sig")
    pareto.to_csv(TABLES / "q3_round2_window_pareto.csv", index=False, encoding="utf-8-sig")
    draw(comparison, pareto)
    payload = {
        "question": "Q3", "round": "round2_joint_robustness", "execution_timestamp": datetime.now(timezone.utc).isoformat(),
        "random_seed": SEED, "bootstrap_replicates": B,
        "scope": "Train-only paired policy-cluster bootstrap of Round 2 OOF outputs; no refitting and no Primary/Secondary input.",
        "weighting_definitions": {
            "policy_equal": "每个策略组内先平均，再在 bootstrap 中对策略组等权采样。",
            "cell_equal": "以策略组为重抽样簇，保留每个被抽中策略组的所有电芯。",
        },
        "pareto_axes": ["minimize k", "minimize rmse_log", "minimize cell_equal_soh_rmse"],
        "outputs": ["tables/q3_round2_policy_bootstrap_comparisons.csv", "tables/q3_round2_window_pareto.csv", "figures/q3_round2_bootstrap_pareto.png"],
    }
    (METRICS / "q3_round2_bootstrap_summary.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(comparison.to_string(index=False))
    print("\nPareto:\n", pareto.to_string(index=False))


if __name__ == "__main__":
    main()
