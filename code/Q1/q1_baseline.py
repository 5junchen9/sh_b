"""Reproducible Q1 descriptive baseline based only on frozen P0 products.

This script performs no model selection and does not alter raw or P0 inputs.
It documents distributions, strategy repetition, and cautious exploratory
relationships required by Section 5 of the V2.1 plan.
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import matplotlib
import numpy as np
import pandas as pd

# 结果只写入 PNG；显式使用无界面后端，避免依赖本机 Tk 图形环境。
matplotlib.use("Agg")
matplotlib.rcParams.update(
    {
        "font.family": "sans-serif",
        "font.sans-serif": ["Microsoft YaHei", "SimHei", "DejaVu Sans"],
        "axes.unicode_minus": False,
    }
)
import matplotlib.pyplot as plt


ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data" / "processed"
OUT = ROOT / "results" / "Q1" / "experiments" / "round1"
TABLES = OUT / "tables"
FIGURES = OUT / "figures"
METRICS = OUT / "metrics"
LOGS = OUT / "logs"
SCRIPT = Path(__file__).resolve()
SEED = 20260802
DATASET_ORDER = ["Train", "Prim. Test", "Sec. test"]
DATASET_LABELS = {"Train": "训练集", "Prim. Test": "主测试集", "Sec. test": "次测试集"}
COLORS = {"Train": "#0072B2", "Prim. Test": "#D55E00", "Sec. test": "#009E73"}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def as_bool(series: pd.Series) -> pd.Series:
    if series.dtype == bool:
        return series
    return series.astype(str).str.strip().str.lower().isin({"true", "1"})


def theory_tau_minutes(frame: pd.DataFrame) -> pd.Series:
    q = frame["Q1_percent"] / 100.0
    return 60.0 * (q / frame["C1"] + (0.8 - q) / frame["C2"])


def save_figure(name: str) -> Path:
    path = FIGURES / name
    plt.tight_layout()
    plt.savefig(path, dpi=220, bbox_inches="tight")
    plt.close()
    return path


def create_cell_summary(labels: pd.DataFrame, view: pd.DataFrame) -> pd.DataFrame:
    early = view.loc[view["global_cycle_index"].between(2, 20)].copy()
    early_charge = early.loc[as_bool(early["valid_chargetime"])]
    charge_stats = early_charge.groupby("barcode")["chargetime"].agg(
        early_chargetime_median="median",
        early_chargetime_mean="mean",
        early_chargetime_valid_count="count",
    )
    qd2 = view.loc[
        view["global_cycle_index"].eq(2) & as_bool(view["valid_QDischarge"]),
        ["barcode", "QDischarge", "SOH_nom"],
    ].set_index("barcode").rename(columns={"QDischarge": "QDischarge_cycle2", "SOH_nom": "SOH_nom_cycle2"})
    result = labels.merge(charge_stats, left_on="barcode", right_index=True, how="left")
    result = result.merge(qd2, left_on="barcode", right_index=True, how="left")
    result["tau_0_80_theory_min"] = theory_tau_minutes(result)
    result["dataset_role"] = result["dataset_table9"].map(DATASET_LABELS)
    return result.sort_values("barcode").reset_index(drop=True)


def plot_lifetime_distribution(cells: pd.DataFrame) -> Path:
    fig, axes = plt.subplots(1, 2, figsize=(10.5, 4.1))
    lifetime = cells["cycle_life_table9"]
    axes[0].hist(lifetime, bins=15, color="#4C72B0", edgecolor="white")
    for value, label, color in [
        (lifetime.quantile(0.25), "下四分位数", "#666666"),
        (lifetime.median(), "中位数", "#000000"),
        (lifetime.quantile(0.75), "上四分位数", "#666666"),
    ]:
        axes[0].axvline(value, color=color, linestyle="--", linewidth=1.2, label=f"{label}: {value:.0f}")
    axes[0].set(title="循环寿命分布", xlabel="循环寿命（循环）", ylabel="电芯数量")
    axes[0].legend(fontsize=8)
    x = np.sort(lifetime.to_numpy())
    axes[1].step(x, np.arange(1, len(x) + 1) / len(x), where="post", color="#4C72B0", linewidth=2)
    axes[1].set(title="循环寿命经验累积分布", xlabel="循环寿命（循环）", ylabel="累计比例", ylim=(0, 1.02))
    return save_figure("q1_01_lifetime_distribution.png")


def plot_dataset_boxplot(cells: pd.DataFrame) -> Path:
    fig, ax = plt.subplots(figsize=(7.2, 4.4))
    values = [cells.loc[cells["dataset_table9"].eq(group), "cycle_life_table9"] for group in DATASET_ORDER]
    box = ax.boxplot(values, patch_artist=True, tick_labels=[DATASET_LABELS[x] for x in DATASET_ORDER])
    for patch, group in zip(box["boxes"], DATASET_ORDER):
        patch.set_facecolor(COLORS[group])
        patch.set_alpha(0.65)
    for idx, group in enumerate(DATASET_ORDER, start=1):
        sample = cells.loc[cells["dataset_table9"].eq(group), "cycle_life_table9"]
        jitter = np.linspace(-0.10, 0.10, len(sample))
        ax.scatter(np.full(len(sample), idx) + jitter, sample, s=18, color=COLORS[group], alpha=0.72, edgecolor="white", linewidth=0.35)
    ax.set(title="官方数据分区的观测循环寿命", xlabel="官方分区", ylabel="循环寿命（循环）")
    ax.text(0.02, -0.22, "仅作描述性比较：分区差异不能解释为因果批次效应。", transform=ax.transAxes, fontsize=8)
    return save_figure("q1_02_lifetime_by_dataset.png")


def plot_strategy_scatter(cells: pd.DataFrame) -> Path:
    fig, axes = plt.subplots(1, 3, figsize=(12.5, 3.9), sharey=True)
    settings = [("C1", "第一阶段倍率 C1（C 倍率）"), ("Q1_percent", "切换 SOC Q1（%）"), ("C2", "第二阶段倍率 C2（C 倍率）")]
    for ax, (column, label) in zip(axes, settings):
        for group in DATASET_ORDER:
            subset = cells.loc[cells["dataset_table9"].eq(group)]
            ax.scatter(subset[column], subset["cycle_life_table9"], label=DATASET_LABELS[group], color=COLORS[group], alpha=0.75, s=28)
        ax.set(xlabel=label, title=f"{label}与循环寿命的关系")
        ax.grid(alpha=0.2)
    axes[0].set_ylabel("循环寿命（循环）")
    axes[-1].legend(fontsize=8, loc="best")
    return save_figure("q1_03_strategy_parameters_vs_lifetime.png")


def plot_tau_lifetime(cells: pd.DataFrame) -> Path:
    fig, ax = plt.subplots(figsize=(7.2, 4.5))
    for group in DATASET_ORDER:
        subset = cells.loc[cells["dataset_table9"].eq(group)]
        ax.scatter(subset["tau_0_80_theory_min"], subset["cycle_life_table9"], label=DATASET_LABELS[group], color=COLORS[group], alpha=0.78, s=32)
    ax.set(
        title="理论 0–80% 恒流阶段时间与循环寿命",
        xlabel="理论 tau_0-80（min）",
        ylabel="循环寿命（循环）",
    )
    ax.legend(fontsize=8)
    ax.grid(alpha=0.2)
    ax.text(0.02, -0.23, "tau_0-80 为理论恒流阶段时间，不等同于实测充电时间。", transform=ax.transAxes, fontsize=8)
    return save_figure("q1_04_theory_time_vs_lifetime.png")


def repeated_policy_table(cells: pd.DataFrame) -> pd.DataFrame:
    train = cells.loc[cells["dataset_table9"].eq("Train")]
    primary = cells.loc[cells["dataset_table9"].eq("Prim. Test")]
    train_summary = train.groupby("policy_table9")["cycle_life_table9"].agg(train_n="size", train_life_mean="mean")
    primary_summary = primary.groupby("policy_table9")["cycle_life_table9"].agg(primary_n="size", primary_life_mean="mean")
    table = train_summary.join(primary_summary, how="inner").reset_index()
    table["absolute_difference"] = (table["train_life_mean"] - table["primary_life_mean"]).abs()
    table["primary_seen_cell_count"] = table["primary_n"]
    return table.sort_values("policy_table9").reset_index(drop=True)


def plot_repeated_policy_agreement(repeated: pd.DataFrame) -> Path:
    fig, ax = plt.subplots(figsize=(6.5, 5.0))
    ax.scatter(repeated["train_life_mean"], repeated["primary_life_mean"], s=42, color="#6A3D9A", alpha=0.85)
    low = min(repeated["train_life_mean"].min(), repeated["primary_life_mean"].min())
    high = max(repeated["train_life_mean"].max(), repeated["primary_life_mean"].max())
    ax.plot([low, high], [low, high], "--", color="#555555", linewidth=1)
    pearson = repeated["train_life_mean"].corr(repeated["primary_life_mean"], method="pearson")
    spearman = repeated["train_life_mean"].corr(repeated["primary_life_mean"], method="spearman")
    ax.set(
        title="训练集—主测试集重复策略的一致性",
        xlabel="训练集策略平均循环寿命",
        ylabel="主测试集策略平均循环寿命",
    )
    ax.text(0.03, 0.97, f"策略数 = {len(repeated)}\n皮尔逊相关系数 = {pearson:.3f}\n斯皮尔曼相关系数 = {spearman:.3f}", transform=ax.transAxes, va="top", fontsize=9)
    ax.grid(alpha=0.2)
    return save_figure("q1_05_train_primary_repeated_policy_agreement.png")


def plot_representative_soh(cells: pd.DataFrame, view: pd.DataFrame) -> tuple[Path, pd.DataFrame]:
    group_stats = cells.groupby("policy_table9").agg(n=("barcode", "size"), life_mean=("cycle_life_table9", "mean"))
    eligible = group_stats.loc[group_stats["n"].ge(2)]
    long_policy = eligible["life_mean"].idxmax()
    short_policy = eligible["life_mean"].idxmin()
    selected_rows = []
    for role, policy in [("重复策略的长寿命案例", long_policy), ("重复策略的短寿命案例", short_policy)]:
        candidates = cells.loc[cells["policy_table9"].eq(policy)].copy()
        center = candidates["cycle_life_table9"].mean()
        chosen = candidates.iloc[(candidates["cycle_life_table9"] - center).abs().argsort().iloc[0]]
        selected_rows.append({"case_role": role, "policy_table9": policy, "barcode": chosen["barcode"], "cycle_life_table9": int(chosen["cycle_life_table9"])})
    selected = pd.DataFrame(selected_rows)
    fig, ax = plt.subplots(figsize=(7.6, 4.7))
    palette = ["#0072B2", "#D55E00"]
    for item, color in zip(selected.itertuples(index=False), palette):
        curve = view.loc[(view["barcode"].eq(item.barcode)) & as_bool(view["valid_QDischarge"])].copy()
        curve["life_fraction"] = curve["global_cycle_index"] / item.cycle_life_table9
        ax.plot(curve["life_fraction"], curve["SOH_nom"], label=f"{item.case_role}: {item.barcode}", color=color, linewidth=1.5)
    ax.axhline(0.8, color="#444444", linestyle="--", linewidth=1, label="额定 SOH = 0.8")
    ax.set(title="代表性额定 SOH 轨迹", xlabel="全局循环数／官方循环寿命", ylabel="SOH_nom")
    ax.legend(fontsize=7.5, loc="best")
    ax.grid(alpha=0.2)
    return save_figure("q1_06_representative_soh_trajectories.png"), selected


def main() -> None:
    np.random.seed(SEED)
    TABLES.mkdir(parents=True, exist_ok=True)
    FIGURES.mkdir(parents=True, exist_ok=True)
    METRICS.mkdir(parents=True, exist_ok=True)
    LOGS.mkdir(parents=True, exist_ok=True)
    label_path = DATA / "cell_labels.csv"
    view_path = DATA / "cycle_model_view.csv"
    p0_path = DATA / "p0_summary.json"
    labels = pd.read_csv(label_path)
    view = pd.read_csv(view_path, low_memory=False)
    p0 = json.loads(p0_path.read_text(encoding="utf-8"))
    if p0.get("p0_status") != "pass":
        raise RuntimeError("Q1 requires a passed P0 summary.")
    if len(labels) != 124 or labels["barcode"].nunique() != 124:
        raise RuntimeError("Official label table is not the expected 124-cell roster.")
    if len(view) != 99_279 or view["barcode"].nunique() != 124:
        raise RuntimeError("P0 cycle model view is not the expected frozen input.")

    cells = create_cell_summary(labels, view)
    repeated = repeated_policy_table(cells)
    figures = [
        plot_lifetime_distribution(cells),
        plot_dataset_boxplot(cells),
        plot_strategy_scatter(cells),
        plot_tau_lifetime(cells),
        plot_repeated_policy_agreement(repeated),
    ]
    soh_figure, representatives = plot_representative_soh(cells, view)
    figures.append(soh_figure)

    dataset_summary = cells.groupby("dataset_table9")["cycle_life_table9"].agg(
        cell_count="size", mean="mean", median="median", std="std", minimum="min", maximum="max"
    ).reindex(DATASET_ORDER)
    strategy_summary = cells.groupby("policy_table9").agg(
        cell_count=("barcode", "size"), life_mean=("cycle_life_table9", "mean"), life_std=("cycle_life_table9", "std"),
        datasets=("dataset_table9", lambda x: ";".join(sorted(x.unique()))),
    ).sort_values(["cell_count", "life_mean"], ascending=[False, False]).reset_index()
    cells.to_csv(TABLES / "q1_cell_level_summary.csv", index=False, encoding="utf-8-sig")
    dataset_summary.reset_index().to_csv(TABLES / "q1_dataset_lifetime_summary.csv", index=False, encoding="utf-8-sig")
    strategy_summary.to_csv(TABLES / "q1_policy_summary.csv", index=False, encoding="utf-8-sig")
    repeated.to_csv(TABLES / "q1_train_primary_repeated_policy.csv", index=False, encoding="utf-8-sig")
    representatives.to_csv(TABLES / "q1_representative_soh_cases.csv", index=False, encoding="utf-8-sig")

    pearson = float(repeated["train_life_mean"].corr(repeated["primary_life_mean"], method="pearson"))
    spearman = float(repeated["train_life_mean"].corr(repeated["primary_life_mean"], method="spearman"))
    differences = repeated["absolute_difference"]
    summary = {
        "status": "descriptive_baseline_complete_not_a_final_model",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "script": str(SCRIPT.relative_to(ROOT)).replace("\\", "/"),
        "script_sha256": sha256(SCRIPT),
        "random_seed": SEED,
        "input_sha256": {"cell_labels.csv": sha256(label_path), "cycle_model_view.csv": sha256(view_path), "p0_summary.json": sha256(p0_path)},
        "input_checks": {"official_cells": len(labels), "p0_rows": len(view), "p0_status": p0["p0_status"]},
        "lifetime_summary": {
            "mean": float(cells["cycle_life_table9"].mean()),
            "median": float(cells["cycle_life_table9"].median()),
            "q1": float(cells["cycle_life_table9"].quantile(0.25)),
            "q3": float(cells["cycle_life_table9"].quantile(0.75)),
            "minimum": int(cells["cycle_life_table9"].min()),
            "maximum": int(cells["cycle_life_table9"].max()),
        },
        "repeated_train_primary_policy_agreement": {
            "policy_count": int(len(repeated)),
            "primary_seen_cell_count": int(repeated["primary_n"].sum()),
            "pearson": pearson,
            "spearman": spearman,
            "absolute_difference_median": float(differences.median()),
            "absolute_difference_mean": float(differences.mean()),
            "absolute_difference_max": float(differences.max()),
        },
        "representative_soh_cases": representatives.to_dict(orient="records"),
        "limitations": [
            "All Q1 comparisons are descriptive; observed split or policy differences are not causal estimates.",
            "Primary has prior exploratory exposure and is not an untouched independent test set.",
            "IR is recorded in ohms and chargetime in minutes; chargetime boundaries and CV coverage remain undocumented, so it is not interchangeable with theoretical tau_0_80.",
            "This script does not select or validate a final Q2/Q3 model.",
        ],
        "outputs": [str(path.relative_to(ROOT)).replace("\\", "/") for path in [*figures, *(TABLES / name for name in ["q1_cell_level_summary.csv", "q1_dataset_lifetime_summary.csv", "q1_policy_summary.csv", "q1_train_primary_repeated_policy.csv", "q1_representative_soh_cases.csv"])]]
    }
    (OUT / "run_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    (METRICS / "q1_key_metrics.json").write_text(
        json.dumps(
            {
                "lifetime_summary": summary["lifetime_summary"],
                "repeated_train_primary_policy_agreement": summary["repeated_train_primary_policy_agreement"],
                "interpretation_scope": "descriptive only; not a causal or final prediction-model result",
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    (LOGS / "q1_baseline.log").write_text(
        f"status={summary['status']}\nscript_sha256={summary['script_sha256']}\n"
        f"official_cells={len(labels)}\np0_rows={len(view)}\nfigures={len(figures)}\n",
        encoding="utf-8",
    )
    print(json.dumps({"status": summary["status"], "figures": len(figures), "repeated_policies": len(repeated)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
