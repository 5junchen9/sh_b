"""补充 Q1 论文初稿所需的策略层与实测充电时间图表。

本脚本只读取 P0 冻结后的 Q1 汇总表和循环视图，不修改原始数据；输出与
q1_baseline.py 并列，便于论文初稿直接引用，同时保留描述性分析的边界。
"""
from __future__ import annotations

import json
import hashlib
from datetime import datetime, timezone
from pathlib import Path

import matplotlib
import numpy as np
import pandas as pd

matplotlib.use("Agg")
matplotlib.rcParams.update(
    {
        "font.family": "sans-serif",
        "font.sans-serif": ["Microsoft YaHei", "SimHei", "DejaVu Sans"],
        "axes.unicode_minus": False,
    }
)
import matplotlib.pyplot as plt


SCRIPT = Path(__file__).resolve()
ROOT = SCRIPT.parents[2]
OUT = ROOT / "results" / "Q1" / "experiments" / "round1"
TABLES = OUT / "tables"
FIGURES = OUT / "figures"
LOGS = OUT / "logs"
DATA = ROOT / "data" / "processed"
GROUP_ORDER = ["Train", "Prim. Test", "Sec. test"]
GROUP_LABELS = {"Train": "训练集", "Prim. Test": "主测试集", "Sec. test": "次测试集"}
GROUP_COLORS = {"Train": "#0072B2", "Prim. Test": "#D55E00", "Sec. test": "#009E73"}
LONG_COLOR = "#0072B2"
SHORT_COLOR = "#D55E00"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    digest.update(path.read_bytes())
    return digest.hexdigest()


def save(fig: plt.Figure, name: str) -> Path:
    path = FIGURES / name
    fig.tight_layout()
    fig.savefig(path, dpi=240, bbox_inches="tight")
    plt.close(fig)
    return path


def policy_table(cells: pd.DataFrame) -> pd.DataFrame:
    """按充电策略汇总，避免只看单个电池造成过度解读。"""
    table = cells.groupby("policy_table9").agg(
        cell_count=("barcode", "size"),
        life_mean=("cycle_life_table9", "mean"),
        life_median=("cycle_life_table9", "median"),
        life_std=("cycle_life_table9", "std"),
        life_min=("cycle_life_table9", "min"),
        life_max=("cycle_life_table9", "max"),
        C1=("C1", "first"),
        Q1_percent=("Q1_percent", "first"),
        C2=("C2", "first"),
        early_chargetime_median=("early_chargetime_median", "mean"),
        tau_0_80_theory_min=("tau_0_80_theory_min", "first"),
        datasets=("dataset_table9", lambda x: ";".join(GROUP_LABELS.get(v, v) for v in sorted(x.unique()))),
    ).reset_index()
    table["life_std"] = table["life_std"].fillna(0.0)
    table["charge_minus_tau_min"] = table["early_chargetime_median"] - table["tau_0_80_theory_min"]
    table["repeated_policy"] = table["cell_count"].ge(2)
    return table.sort_values(["life_mean", "policy_table9"], ascending=[False, True]).reset_index(drop=True)


def choose_representative_policies(summary: pd.DataFrame) -> tuple[pd.Series, pd.Series]:
    repeated = summary.loc[summary["repeated_policy"]].copy()
    if len(repeated) < 2:
        raise RuntimeError("至少需要两个重复策略才能进行长短策略比较。")
    return repeated.loc[repeated["life_mean"].idxmax()], repeated.loc[repeated["life_mean"].idxmin()]


def plot_policy_rank(summary: pd.DataFrame) -> Path:
    repeated = summary.loc[summary["repeated_policy"]].copy()
    k = min(8, len(repeated) // 2)
    # barh 的最后一行显示在最上方：短寿命面板按降序排列，使最短策略位于最上方。
    short = repeated.nsmallest(k, "life_mean").sort_values("life_mean", ascending=False)
    long = repeated.nlargest(k, "life_mean").sort_values("life_mean")
    fig, axes = plt.subplots(1, 2, figsize=(13.5, 5.8), sharex=True)
    for ax, frame, title, color in [
        (axes[0], short, "短寿命重复策略（策略内 n≥2）", SHORT_COLOR),
        (axes[1], long, "长寿命重复策略（策略内 n≥2）", LONG_COLOR),
    ]:
        y = np.arange(len(frame))
        labels = [f"{p}  (n={n})" for p, n in zip(frame["policy_table9"], frame["cell_count"])]
        ax.barh(y, frame["life_mean"], color=color, alpha=0.82)
        ax.hlines(y, frame["life_min"], frame["life_max"], color="#444444", linewidth=1.5)
        ax.scatter(frame["life_min"], y, color="#444444", s=16, zorder=3)
        ax.scatter(frame["life_max"], y, color="#444444", s=16, zorder=3)
        for yi, value in zip(y, frame["life_mean"]):
            ax.text(value + 18, yi, f"{value:.0f}", va="center", fontsize=8)
        ax.set_yticks(y, labels)
        ax.set_xlabel("策略内平均循环寿命（循环）")
        ax.set_title(title)
        ax.grid(axis="x", alpha=0.25)
    axes[0].set_ylabel("充电策略（横线为策略内最小–最大值）")
    fig.suptitle("重复充电策略的寿命排名：用于识别典型长寿命与短寿命策略", fontsize=14)
    return save(fig, "q1_07_policy_lifetime_top_bottom.png")


def plot_charge_time_lifetime(cells: pd.DataFrame, long: pd.Series, short: pd.Series) -> Path:
    fig, ax = plt.subplots(figsize=(8.3, 5.4))
    for group in GROUP_ORDER:
        subset = cells.loc[cells["dataset_table9"].eq(group)]
        ax.scatter(
            subset["early_chargetime_median"], subset["cycle_life_table9"],
            label=GROUP_LABELS[group], color=GROUP_COLORS[group], alpha=0.62, s=30,
        )
    for item, color, label in [
        (long, LONG_COLOR, "长寿命典型策略内均值"),
        (short, SHORT_COLOR, "短寿命典型策略内均值"),
    ]:
        ax.scatter(item["early_chargetime_median"], item["life_mean"], s=130, marker="*", color=color,
                   edgecolor="black", linewidth=0.7, zorder=5, label=label)
        ax.annotate(item["policy_table9"], (item["early_chargetime_median"], item["life_mean"]),
                    xytext=(7, 7), textcoords="offset points", fontsize=8)
    med_t = cells["early_chargetime_median"].median()
    med_l = cells["cycle_life_table9"].median()
    ax.axvline(med_t, color="#777777", linestyle="--", linewidth=1)
    ax.axhline(med_l, color="#777777", linestyle=":", linewidth=1)
    rho = cells["early_chargetime_median"].corr(cells["cycle_life_table9"], method="spearman")
    ax.text(0.02, 0.97, f"全体 Spearman ρ = {rho:.3f}\n虚线：全体中位数", transform=ax.transAxes, va="top", fontsize=9)
    ax.set(title="实测早期充电时间与循环寿命", xlabel="第2–20圈实测充电时间中位数（min）", ylabel="循环寿命（循环）")
    ax.legend(fontsize=8, loc="best")
    ax.grid(alpha=0.2)
    return save(fig, "q1_08_observed_charge_time_vs_lifetime.png")


def plot_long_short_soh(cells: pd.DataFrame, view: pd.DataFrame, long: pd.Series, short: pd.Series) -> Path:
    grid = np.linspace(0, 1, 101)
    fig, ax = plt.subplots(figsize=(8.6, 5.5))
    for item, color, label in [
        (long, LONG_COLOR, f"长寿命策略：{long['policy_table9']}（n={int(long['cell_count'])}）"),
        (short, SHORT_COLOR, f"短寿命策略：{short['policy_table9']}（n={int(short['cell_count'])}）"),
    ]:
        curves = []
        for barcode in cells.loc[cells["policy_table9"].eq(item["policy_table9"]), "barcode"]:
            curve = view.loc[(view["barcode"].eq(barcode)) & (view["valid_QDischarge"].astype(str).str.lower().isin(["true", "1"]))].copy()
            curve = curve.sort_values("global_cycle_index")
            if len(curve) < 10:
                continue
            x = curve["global_cycle_index"].to_numpy(dtype=float) / float(cells.loc[cells["barcode"].eq(barcode), "cycle_life_table9"].iloc[0])
            y = curve["SOH_nom"].to_numpy(dtype=float)
            order = np.argsort(x)
            curves.append(np.interp(grid, x[order], y[order]))
        arr = np.vstack(curves)
        median = np.nanmedian(arr, axis=0)
        low = np.nanpercentile(arr, 10, axis=0)
        high = np.nanpercentile(arr, 90, axis=0)
        ax.plot(grid, median, color=color, linewidth=2.3, label=label)
        ax.fill_between(grid, low, high, color=color, alpha=0.18, label="10–90%区间")
    ax.axhline(0.8, color="#444444", linestyle="--", linewidth=1, label="SOH=0.8")
    ax.set(title="典型长短寿命策略的 SOH 轨迹（策略内中位数及区间）",
           xlabel="相对寿命进程：当前循环 / 该电池官方循环寿命", ylabel="SOH_nom")
    ax.set_ylim(0.79, 1.0)
    ax.grid(alpha=0.2)
    ax.legend(fontsize=8, loc="best")
    return save(fig, "q1_09_long_short_soh_band.png")


def main() -> None:
    FIGURES.mkdir(parents=True, exist_ok=True)
    TABLES.mkdir(parents=True, exist_ok=True)
    LOGS.mkdir(parents=True, exist_ok=True)
    cells_path = TABLES / "q1_cell_level_summary.csv"
    view_path = DATA / "cycle_model_view.csv"
    p0_path = DATA / "p0_summary.json"
    p0 = json.loads(p0_path.read_text(encoding="utf-8"))
    if p0.get("p0_status") != "pass":
        raise RuntimeError("P0 is not passed; Q1 enhanced outputs are blocked.")
    cells = pd.read_csv(cells_path)
    view = pd.read_csv(view_path, low_memory=False)
    required_cell_columns = {
        "barcode", "dataset_table9", "policy_table9", "cycle_life_table9",
        "C1", "Q1_percent", "C2", "early_chargetime_median", "tau_0_80_theory_min",
    }
    missing_columns = sorted(required_cell_columns - set(cells.columns))
    if missing_columns or len(cells) != 124 or cells["barcode"].nunique() != 124:
        raise RuntimeError(
            f"Stale or invalid Q1 baseline table: missing={missing_columns}, "
            f"rows={len(cells)}, unique_barcodes={cells['barcode'].nunique()}"
        )
    summary = policy_table(cells)
    long, short = choose_representative_policies(summary)
    summary.to_csv(TABLES / "q1_strategy_lifetime_summary_enhanced.csv", index=False, encoding="utf-8-sig")
    comparison = pd.DataFrame([
        {"case": "典型长寿命策略", "policy": long["policy_table9"], **long.drop(labels=["policy_table9"]).to_dict()},
        {"case": "典型短寿命策略", "policy": short["policy_table9"], **short.drop(labels=["policy_table9"]).to_dict()},
    ])
    comparison.to_csv(TABLES / "q1_long_short_strategy_comparison.csv", index=False, encoding="utf-8-sig")
    figures = [
        plot_policy_rank(summary),
        plot_charge_time_lifetime(cells, long, short),
        plot_long_short_soh(cells, view, long, short),
    ]
    payload = {
        "status": "enhanced_descriptive_outputs_complete",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "script_sha256": sha256(SCRIPT),
        "input_sha256": {
            "q1_cell_level_summary.csv": sha256(cells_path),
            "cycle_model_view.csv": sha256(view_path),
            "p0_summary.json": sha256(p0_path),
        },
        "input_checks": {"cell_rows": len(cells), "unique_barcodes": int(cells["barcode"].nunique()), "p0_status": p0["p0_status"]},
        "representative_long_policy": str(long["policy_table9"]),
        "representative_short_policy": str(short["policy_table9"]),
        "outputs": [str(p.relative_to(ROOT)).replace("\\", "/") for p in figures]
        + [str((TABLES / n).relative_to(ROOT)).replace("\\", "/") for n in ["q1_strategy_lifetime_summary_enhanced.csv", "q1_long_short_strategy_comparison.csv"]],
        "interpretation_scope": "descriptive only; no causal effect or final prediction claim",
    }
    (OUT / "q1_enhanced_summary.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    (LOGS / "q1_enhanced_run.log").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False))


if __name__ == "__main__":
    main()
