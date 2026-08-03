"""Create a three-strategy, k=100 pilot batch from frozen Q2 provisional candidates."""
from __future__ import annotations

import hashlib
import json
import platform
import sys
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
SOURCE = ROOT / "results" / "Q4" / "experiments" / "train_dry_run_round1" / "tables" / "q4_q2_provisional_candidates.csv"
PROTOCOL = ROOT / "methods" / "Q4" / "q4_k100_pilot_protocol.md"
OUT = ROOT / "results" / "Q4" / "experiments" / "pilot_design_round1"
TABLES, FIGURES, METRICS, LOGS = (OUT / x for x in ("tables", "figures", "metrics", "logs"))
SEED = 20260802
REPLICATES_PER_STRATEGY = 3


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def pareto_mask(frame: pd.DataFrame) -> np.ndarray:
    """Keep records not dominated on shorter tau and larger provisional P3 prediction."""
    tau = frame["tau_0_80_min"].to_numpy(float)
    life = frame["q2b_pred_cycle_life"].to_numpy(float)
    keep = np.ones(len(frame), dtype=bool)
    for i in range(len(frame)):
        dominates_i = (tau <= tau[i]) & (life >= life[i]) & ((tau < tau[i]) | (life > life[i]))
        if dominates_i.any():
            keep[i] = False
    return keep


def select_representatives(pareto: pd.DataFrame) -> pd.DataFrame:
    """Select fast / midpoint / longevity representatives without scalarizing objectives."""
    ordered = pareto.sort_values(["tau_0_80_min", "q2b_pred_cycle_life", "support_bootstrap_rate"], ascending=[True, False, False]).reset_index(drop=True)
    fast = ordered.iloc[0]
    life = pareto.sort_values(["q2b_pred_cycle_life", "tau_0_80_min", "support_bootstrap_rate"], ascending=[False, True, False]).iloc[0]
    scaled = (pareto["tau_0_80_min"] - pareto["tau_0_80_min"].min()) / (pareto["tau_0_80_min"].max() - pareto["tau_0_80_min"].min())
    mid_order = pareto.assign(_middle_distance=np.abs(scaled - 0.5)).sort_values(["_middle_distance", "support_bootstrap_rate", "q2b_pred_cycle_life"], ascending=[True, False, False])
    chosen = [("快速端代表", fast), ("中间权衡代表", None), ("寿命端代表", life)]
    used = {int(fast.name), int(life.name)}
    for idx, row in mid_order.iterrows():
        if int(idx) not in used:
            chosen[1] = ("中间权衡代表", row)
            used.add(int(idx))
            break
    if chosen[1][1] is None:
        raise RuntimeError("Pareto 集不足三个不同候选，无法构造最小三策略 pilot。")
    rows = []
    for role, row in chosen:
        record = row.drop(labels=[x for x in row.index if x.startswith("_")], errors="ignore").to_dict()
        record.update({"pilot_role": role, "required_distinct_physical_cells": REPLICATES_PER_STRATEGY, "candidate_status": "Q2_provisional", "pilot_status": "planned", "selection_scope": "试验排程代表点，非最终最优或正式 Pareto"})
        rows.append(record)
    out = pd.DataFrame(rows)
    if out[["C1", "Q1_percent", "C2"]].duplicated().any():
        raise RuntimeError("Representative selection produced duplicated strategy triples.")
    return out


def allocation_template(selected: pd.DataFrame) -> pd.DataFrame:
    """Expand three representative strategies into nine unassigned physical-cell slots."""
    rows = []
    role_codes = {"快速端代表": "FAST", "中间权衡代表": "MID", "寿命端代表": "LIFE"}
    for _, strategy in selected.iterrows():
        for replicate in range(1, REPLICATES_PER_STRATEGY + 1):
            rows.append({
                "pilot_id": f"Q4_{role_codes[strategy.pilot_role]}_{replicate:02d}",
                "barcode": "",
                "C1": strategy.C1,
                "Q1_percent": strategy.Q1_percent,
                "C2": strategy.C2,
                "q": strategy.q,
                "single_stage_0_80": strategy.single_stage_0_80,
                "tau_0_80_min": strategy.tau_0_80_min,
                "candidate_source": f"pilot_design_round1:{strategy.pilot_role}",
                "status": "planned",
                "cycle_5_complete": False,
                "k5_screen_status": "not_due",
                "cycle_100_complete": False,
                "raw_data_path": "",
                "p0_compatible_view_path": "",
                "notes": "待分配不同物理电芯；仅为试验排程代表点，不是正式推荐。",
            })
    output = pd.DataFrame(rows)
    if len(output) != REPLICATES_PER_STRATEGY * len(selected) or output.pilot_id.duplicated().any():
        raise RuntimeError("Pilot allocation template is incomplete or has duplicated pilot IDs.")
    return output


def plot(candidates: pd.DataFrame, pareto: pd.DataFrame, selected: pd.DataFrame) -> None:
    fig, ax = plt.subplots(figsize=(8.5, 5.5))
    ax.scatter(candidates["tau_0_80_min"], candidates["q2b_pred_cycle_life"], s=12, alpha=0.20, color="#8AA6C1", label="全部 Q2 暂定候选")
    ax.scatter(pareto["tau_0_80_min"], pareto["q2b_pred_cycle_life"], s=26, color="#DD8452", label="时间—P3 点预测非支配候选")
    for _, row in selected.iterrows():
        ax.scatter(row["tau_0_80_min"], row["q2b_pred_cycle_life"], s=100, marker="*", color="#C44E52", edgecolor="black", linewidth=0.5, zorder=3)
        ax.annotate(row["pilot_role"], (row["tau_0_80_min"], row["q2b_pred_cycle_life"]), xytext=(5, 5), textcoords="offset points", fontsize=9)
    ax.set(title="Q4：仅用于 k=100 pilot 排程的代表性候选", xlabel="理论 0–80% 恒流时间 tau_0-80（min）", ylabel="P3 设计前预测寿命（cycle）")
    ax.grid(alpha=0.2)
    ax.legend()
    fig.tight_layout()
    for ext, kwargs in (("png", {"dpi": 300}), ("svg", {})):
        fig.savefig(FIGURES / f"q4_pilot_representatives.{ext}", bbox_inches="tight", **kwargs)
    plt.close(fig)


def main() -> None:
    for directory in (TABLES, FIGURES, METRICS, LOGS):
        directory.mkdir(parents=True, exist_ok=True)
    if not SOURCE.exists() or not PROTOCOL.exists():
        raise RuntimeError("Frozen Q4 candidate table or k=100 pilot protocol is missing.")
    candidates = pd.read_csv(SOURCE)
    required = {"C1", "Q1_percent", "C2", "tau_0_80_min", "q2b_pred_cycle_life", "support_bootstrap_rate", "status", "passes_double_5nn", "passes_support_bootstrap"}
    if missing := required.difference(candidates.columns):
        raise RuntimeError(f"Frozen candidate table missing columns: {sorted(missing)}")
    allowed = candidates.loc[(candidates.status == "Q2_provisional") & candidates.passes_double_5nn.astype(bool) & candidates.passes_support_bootstrap.astype(bool)].copy()
    if len(allowed) != 1775 or not (allowed.support_bootstrap_rate >= 0.8).all():
        raise RuntimeError("Frozen Q2 provisional candidate pool no longer matches the 1,775-record support rule.")
    if not np.isfinite(allowed[["tau_0_80_min", "q2b_pred_cycle_life", "support_bootstrap_rate"]].to_numpy(float)).all():
        raise RuntimeError("Candidate pool contains non-finite time, life prediction, or support values.")
    pareto = allowed.loc[pareto_mask(allowed)].copy().sort_values("tau_0_80_min").reset_index(drop=True)
    selected = select_representatives(pareto)
    allocation = allocation_template(selected)
    pareto.to_csv(TABLES / "q4_pilot_time_life_pareto_candidates.csv", index=False, encoding="utf-8-sig")
    selected.to_csv(TABLES / "q4_k100_pilot_representatives.csv", index=False, encoding="utf-8-sig")
    allocation.to_csv(TABLES / "q4_k100_pilot_allocation_template.csv", index=False, encoding="utf-8-sig")
    plot(allowed, pareto, selected)
    summary = {
        "question": "Q4",
        "round": "pilot_design_round1",
        "status": "planned_not_executed",
        "scope": "Three representative strategies selected only for k=100 pilot scheduling; P3 values are not final rankings or robust life lower bounds.",
        "random_seed": SEED,
        "frozen_candidate_count": int(len(allowed)),
        "time_life_pareto_count": int(len(pareto)),
        "representative_count": int(len(selected)),
        "required_distinct_physical_cells_per_strategy": REPLICATES_PER_STRATEGY,
        "minimum_cell_count": int(len(selected) * REPLICATES_PER_STRATEGY),
        "input_sha256": {"q4_q2_provisional_candidates.csv": sha(SOURCE), "q4_k100_pilot_protocol.md": sha(PROTOCOL)},
        "script_sha256": sha(SCRIPT),
        "environment": {"python": sys.version, "platform": platform.platform(), "pandas": pd.__version__, "numpy": np.__version__},
        "outputs": ["tables/q4_pilot_time_life_pareto_candidates.csv", "tables/q4_k100_pilot_representatives.csv", "tables/q4_k100_pilot_allocation_template.csv", "figures/q4_pilot_representatives.png", "figures/q4_pilot_representatives.svg"],
        "representatives": selected[["pilot_role", "C1", "Q1_percent", "C2", "tau_0_80_min", "q2b_pred_cycle_life", "support_bootstrap_rate"]].to_dict(orient="records"),
        "execution_timestamp": datetime.now(timezone.utc).isoformat(),
    }
    (METRICS / "q4_pilot_design_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    report_rows = "\n".join(f"| {r.pilot_role} | {r.C1:.2f} | {r.Q1_percent:.0f}% | {r.C2:.2f} | {r.tau_0_80_min:.3f} | {r.q2b_pred_cycle_life:.1f} | {r.support_bootstrap_rate:.3f} | 3 |" for _, r in selected.iterrows())
    report = f"""# Q4 k=100 Pilot 排程代表点\n\n> 状态：**planned_not_executed**。本文件只把冻结的 `Q2_provisional` 候选压缩成最小三策略 pilot 批次，不能视为最终最优策略或正式 Pareto。\n\n在 1,775 条双空间支持且 bootstrap 支持率不少于 80% 的候选中，时间—P3 点预测的非支配集有 {len(pareto)} 条。本轮不把两个目标加权成单一分数，而从该集选快速端、中间权衡和寿命端各一个代表，以覆盖试验排程的不同取舍。每条策略均需 3 枚不同物理电芯，因此最小 pilot 规模为 9 枚。\n\n| 排程角色 | C1（C） | Q1（SOC） | C2（C） | τ₀₋₈₀（min） | P3 点预测寿命（cycle） | 支持率 | 最少电芯数 |\n|---|---:|---:|---:|---:|---:|---:|---:|\n{report_rows}\n\nP3 预测仅用于排程代表性，不能用于宣布寿命排序。各策略必须按 `methods/Q4/q4_k100_pilot_protocol.md` 运行到第 100 循环，并生成真实、P0 兼容的早期数据后，才可产生冻结 Q3 证据。\n"""
    report = report.replace(
        "各策略必须按 `methods/Q4/q4_k100_pilot_protocol.md` 运行到第 100 循环，并生成真实、P0 兼容的早期数据后，才可产生冻结 Q3 证据。",
        "各策略必须按 `methods/Q4/q4_k100_pilot_protocol.md` 先运行到第 5 循环并生成冻结 Q3 早期筛查记录，再继续至第 100 循环并形成真实、P0 兼容的正式 Q3 确认证据；k=5 不能单独升级或淘汰策略。",
    )
    (OUT / "q4_pilot_batch_design_report.md").write_text(report, encoding="utf-8")
    run = json.dumps(summary, ensure_ascii=False, indent=2)
    (OUT / "run_summary.json").write_text(run, encoding="utf-8")
    (LOGS / "run.log").write_text(run + "\n", encoding="utf-8")
    print(json.dumps({"status": summary["status"], "pareto_count": len(pareto), "representatives": summary["representatives"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
