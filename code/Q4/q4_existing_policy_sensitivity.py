"""Sensitivity checks for the development-pool existing-policy Pareto summary."""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
matplotlib.rcParams.update({"font.family": "sans-serif", "font.sans-serif": ["Microsoft YaHei", "SimHei", "DejaVu Sans"], "axes.unicode_minus": False, "svg.fonttype": "none"})
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

SCRIPT = Path(__file__).resolve()
ROOT = SCRIPT.parents[2]
INPUT = ROOT / "results" / "Q4" / "experiments" / "existing_policy_round1" / "tables" / "q4_existing_policy_summary.csv"
OUT = ROOT / "robustness" / "Q4"
SEED = 20260802


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def pareto(frame: pd.DataFrame, life_col: str) -> pd.Series:
    t = frame.tau_0_80_min.to_numpy(float)
    l = frame[life_col].to_numpy(float)
    keep = np.ones(len(frame), dtype=bool)
    for i in range(len(frame)):
        dominating = (t <= t[i]) & (l >= l[i]) & ((t < t[i]) | (l > l[i]))
        if dominating.any():
            keep[i] = False
    return pd.Series(keep, index=frame.index)


def scenario(frame: pd.DataFrame, name: str, eligible: pd.Series, life_col: str) -> tuple[dict[str, object], set[str]]:
    part = frame.loc[eligible].copy()
    if len(part):
        part["on_pareto"] = pareto(part, life_col)
        names = set(part.loc[part.on_pareto, "policy_table9"])
    else:
        names = set()
    return ({"scenario": name, "eligible_policy_count": int(len(part)), "pareto_policy_count": int(len(names)), "pareto_policies": " | ".join(sorted(names))}, names)


def main() -> None:
    (OUT / "tables").mkdir(parents=True, exist_ok=True)
    (OUT / "figures").mkdir(parents=True, exist_ok=True)
    frame = pd.read_csv(INPUT)
    frame["life_rob_median_cycle"] = np.exp(np.minimum(frame.q2_pred_median_log, frame.q3_pred_median_log))
    base_ok = frame.status.eq("observed_Q2Q3_confirmed") & frame.q3_pred_soh_nom_120_empirical_p10.notna()
    scenarios: list[dict[str, object]] = []
    baseline, base_names = scenario(frame, "基线：n≥2，经验P10寿命摘要", base_ok, "life_rob_empirical_p10_cycle")
    scenarios.append(baseline)
    for name, ok, col in [
        ("样本阈值收紧：n≥3，经验P10寿命摘要", base_ok & frame.cell_count.ge(3), "life_rob_empirical_p10_cycle"),
        ("寿命摘要改变：n≥2，中位数寿命摘要", base_ok, "life_rob_median_cycle"),
        ("来源平衡：每策略至少1 Train与1 Primary", base_ok & frame.train_oof_cell_count.ge(1) & frame.primary_confirmation_cell_count.ge(1), "life_rob_empirical_p10_cycle"),
    ]:
        row, names = scenario(frame, name, ok, col)
        row["baseline_pareto_retained"] = int(len(base_names & names))
        row["baseline_pareto_retention_ratio"] = float(len(base_names & names) / len(base_names)) if base_names else float("nan")
        scenarios.append(row)

    loo_rows = []
    for _, row in frame.loc[frame.policy_table9.isin(base_names)].iterrows():
        for leave_idx in range(int(row.cell_count)):
            remaining = int(row.cell_count) - 1
            loo_rows.append({"policy_table9": row.policy_table9, "removed_cell_order": leave_idx + 1, "original_cell_count": int(row.cell_count), "remaining_cell_count": remaining, "keeps_n_ge_2_eligibility": remaining >= 2, "reason": "所有基线 Pareto 策略当前均仅有2枚电芯；留一后自动降为单电芯案例。" if remaining < 2 else "仍满足样本阈值"})
    loo = pd.DataFrame(loo_rows)
    loo_retained = int(loo.keeps_n_ge_2_eligibility.sum())
    scenarios.append({"scenario": "留一电芯：基线 Pareto 策略资格保持", "eligible_policy_count": len(base_names), "pareto_policy_count": loo_retained, "pareto_policies": "无（每个基线 Pareto 点均从n=2降为n=1）", "baseline_pareto_retained": loo_retained, "baseline_pareto_retention_ratio": float(loo_retained / len(loo)) if len(loo) else float("nan")})

    result = pd.DataFrame(scenarios)
    result.to_csv(OUT / "tables" / "q4_existing_policy_sensitivity.csv", index=False, encoding="utf-8-sig")
    loo.to_csv(OUT / "tables" / "q4_existing_policy_pareto_leave_one_cell.csv", index=False, encoding="utf-8-sig")

    labels = ["基线\nn≥2/P10", "收紧阈值\nn≥3", "中位数\nn≥2", "来源平衡", "留一\n资格保持"]
    retained = [1.0, result.iloc[1].baseline_pareto_retention_ratio, result.iloc[2].baseline_pareto_retention_ratio, result.iloc[3].baseline_pareto_retention_ratio, result.iloc[4].baseline_pareto_retention_ratio]
    fig, ax = plt.subplots(figsize=(8.8, 4.8))
    bars = ax.bar(labels, np.array(retained) * 100, color=["#1A6FC4", "#E53935", "#E28E2C", "#33B5A5", "#7B5FD6"], width=.62)
    for bar, value in zip(bars, retained):
        ax.text(bar.get_x() + bar.get_width()/2, value * 100 + 2.5, f"{value:.0%}", ha="center", va="bottom", fontsize=10)
    ax.set(title="开发池 Pareto 点对口径与样本量的敏感性", xlabel="敏感性情景", ylabel="基线 4 个 Pareto 点的保留比例（%）", ylim=(0, 116))
    ax.grid(axis="y", alpha=.2, linestyle="--")
    fig.tight_layout()
    for ext, kwargs in (("svg", {}), ("png", {"dpi": 320})):
        fig.savefig(OUT / "figures" / f"q4_existing_policy_sensitivity.{ext}", bbox_inches="tight", **kwargs)
    plt.close(fig)

    report = f"""# Q4 已有策略 Pareto 敏感性报告

## 1. 计算事实

- 基线口径（至少 2 枚电芯、Q2/Q3 经验 P10 寿命摘要）得到 {len(base_names)} 个开发池内非支配策略。
- 所有 {len(base_names)} 个基线 Pareto 策略均为 `n=2`，且各由 1 枚 Train OOF 与 1 枚 Primary 冻结确认电芯组成。
- 将最小策略样本数从 2 收紧为 3 后，基线 Pareto 点保留率为 {result.iloc[1].baseline_pareto_retention_ratio:.0%}；对每个基线点留出任一电芯后，策略均降为单电芯案例，资格保持率亦为 {result.iloc[4].baseline_pareto_retention_ratio:.0%}。
- 使用中位数寿命摘要及要求每个策略同时含 Train 与 Primary 证据时，结果见 `tables/q4_existing_policy_sensitivity.csv`；这些都是开发池内部敏感性而非外部验证。

## 2. 结论边界

当前 4 个点可作为“已有策略中的开发池内权衡案例”，但其 Pareto 身份高度依赖最小样本阈值。论文不得把它们称为稳健的最终推荐、工程最优或独立外部验证；应同时报告每个策略仅有 2 枚电芯及其来源构成。

## 3. 产物

- `tables/q4_existing_policy_sensitivity.csv`
- `tables/q4_existing_policy_pareto_leave_one_cell.csv`
- `figures/q4_existing_policy_sensitivity.png/svg`
"""
    (OUT / "q4_robustness_report.md").write_text(report, encoding="utf-8")
    payload = {"question": "Q4", "check": "existing_policy_pareto_sensitivity", "status": "computed_not_human_adjudicated", "execution_timestamp": datetime.now(timezone.utc).isoformat(), "random_seed": SEED, "baseline_pareto_count": len(base_names), "baseline_all_n2": bool((frame.loc[frame.policy_table9.isin(base_names), "cell_count"] == 2).all()), "input_sha256": {str(INPUT.relative_to(ROOT)).replace("\\\\", "/"): sha(INPUT)}, "script_sha256": sha(SCRIPT)}
    text = json.dumps(payload, ensure_ascii=False, indent=2)
    (OUT / "run_summary.json").write_text(text, encoding="utf-8")
    print(json.dumps({"baseline_pareto": len(base_names), "n3_retention": result.iloc[1].baseline_pareto_retention_ratio, "loo_retention": result.iloc[4].baseline_pareto_retention_ratio}, ensure_ascii=False))


if __name__ == "__main__":
    main()
