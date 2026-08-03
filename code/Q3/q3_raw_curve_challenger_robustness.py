"""Paired policy-bootstrap for the Q3 RAW challenger; no refitting or selection."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
matplotlib.rcParams.update({"font.family":"sans-serif", "font.sans-serif":["Microsoft YaHei","SimHei","DejaVu Sans"], "axes.unicode_minus":False, "svg.fonttype":"none"})
import matplotlib.pyplot as plt
import pandas as pd

from q3_round2_robustness import paired_bootstrap, pareto_table

ROOT = Path(__file__).resolve().parents[2]
ROUND2 = ROOT / "results" / "Q3" / "experiments" / "round2_joint" / "tables"
RAW = ROOT / "results" / "Q3" / "experiments" / "round3_raw_curve_challenger" / "tables"
OUT = ROOT / "robustness" / "Q3" / "round3_raw_curve_challenger"
TABLES, FIGURES, METRICS = (OUT / item for item in ("tables", "figures", "metrics"))
COMPARISONS = [
    ("M3R_k5_vs_M3_k5", "M3", 5, "M3R", 5),
    ("M3R_k5_vs_M2_k5", "M2", 5, "M3R", 5),
    ("M3R_k5_vs_M2_k100", "M2", 100, "M3R", 5),
    ("M3R_k20_vs_M3_k20", "M3", 20, "M3R", 20),
    ("M3R_k100_vs_M3_k100", "M3", 100, "M3R", 100),
]


def main() -> None:
    for directory in (TABLES, FIGURES, METRICS):
        directory.mkdir(parents=True, exist_ok=True)
    life = pd.concat([
        pd.read_csv(ROUND2 / "joint_oof_life_predictions.csv").rename(columns={"predicted_log_life":"predicted_log_life", "actual_log_life":"actual_log_life"}),
        pd.read_csv(RAW / "m3r_raw_curve_oof_life_predictions.csv"),
    ], ignore_index=True)
    curve = pd.concat([pd.read_csv(ROUND2 / "joint_cell_curve_errors.csv"), pd.read_csv(RAW / "m3r_raw_curve_cell_curve_errors.csv")], ignore_index=True)
    rows = []
    for comparison_id, base_model, base_k, cand_model, cand_k in COMPARISONS:
        for weighting in ("policy_equal", "cell_equal"):
            for row in paired_bootstrap(life, curve, (base_model, base_k), (cand_model, cand_k), weighting):
                row["comparison_id"] = comparison_id
                rows.append(row)
    result = pd.DataFrame(rows)
    result.to_csv(TABLES / "q3_raw_curve_policy_bootstrap.csv", index=False, encoding="utf-8-sig")
    combined_metrics = pd.concat([
        pd.read_csv(ROUND2 / "joint_window_metrics.csv"),
        pd.read_csv(RAW / "m3r_raw_curve_window_metrics.csv"),
    ], ignore_index=True)
    combined_pareto = pareto_table(combined_metrics)
    combined_pareto.to_csv(TABLES / "q3_round3_combined_window_pareto.csv", index=False, encoding="utf-8-sig")
    focus = result.loc[result.weighting.eq("policy_equal") & result.metric.eq("RMSE_log")].copy()
    fig, ax = plt.subplots(figsize=(9.2, 4.6))
    for pos, row in enumerate(focus.itertuples()):
        ax.errorbar(pos, row.point_delta_candidate_minus_baseline, yerr=[[row.point_delta_candidate_minus_baseline-row.ci95_low], [row.ci95_high-row.point_delta_candidate_minus_baseline]], fmt="o", color="#B279A2", capsize=4)
    ax.axhline(0, color="#555555", linestyle="--", linewidth=1)
    ax.set(xticks=range(len(focus)), xticklabels=focus.comparison_id.str.replace("_vs_", "\n对 ").str.replace("_", " "), ylabel="寿命均方根误差差值（候选 − 基线）", title="Q3 原始电压候选模型：策略等权重抽样区间")
    ax.grid(axis="y", alpha=.22); fig.tight_layout()
    for ext, kwargs in (("png", {"dpi":300}), ("svg", {})):
        fig.savefig(FIGURES / f"q3_raw_curve_bootstrap.{ext}", bbox_inches="tight", **kwargs)
    plt.close(fig)
    payload = {"question":"Q3", "round":"round3_raw_curve_challenger_robustness", "execution_timestamp":datetime.now(timezone.utc).isoformat(), "scope":"Train-only paired policy-cluster bootstrap of M3R against existing Round 2 outputs; no refitting or Primary/Secondary input.", "comparisons":COMPARISONS, "outputs":["tables/q3_raw_curve_policy_bootstrap.csv", "tables/q3_round3_combined_window_pareto.csv"]}
    (METRICS / "q3_raw_curve_bootstrap_summary.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(result.to_string(index=False))

if __name__ == "__main__":
    main()
