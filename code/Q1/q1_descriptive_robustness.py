"""Bootstrap uncertainty for Q1 descriptive summaries; no predictive fitting or causal claims."""
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
from scipy.stats import spearmanr

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "robustness" / "Q1"
TABLES, FIGURES, METRICS = (OUT / item for item in ("tables", "figures", "metrics"))
LABELS = ROOT / "data" / "processed" / "cell_labels.csv"
REPEATED = ROOT / "results" / "Q1" / "experiments" / "round1" / "tables" / "q1_train_primary_repeated_policy.csv"
SEED, B = 20260802, 2000


def ci(values: np.ndarray) -> tuple[float, float]:
    return float(np.quantile(values, .025)), float(np.quantile(values, .975))


def main() -> None:
    for directory in (TABLES, FIGURES, METRICS):
        directory.mkdir(parents=True, exist_ok=True)
    labels = pd.read_csv(LABELS)
    repeated = pd.read_csv(REPEATED)
    life = labels.cycle_life_table9.to_numpy(float)
    rng = np.random.default_rng(SEED)
    draws = rng.integers(0, len(life), size=(B, len(life)))
    dist = {
        "mean_life": life[draws].mean(axis=1), "median_life": np.median(life[draws], axis=1),
        "q1_life": np.quantile(life[draws], .25, axis=1), "q3_life": np.quantile(life[draws], .75, axis=1),
    }
    summary = pd.DataFrame([{
        "statistic": key, "point_estimate": float({"mean_life": life.mean(), "median_life": np.median(life), "q1_life": np.quantile(life,.25), "q3_life": np.quantile(life,.75)}[key]),
        "ci95_low": ci(value)[0], "ci95_high": ci(value)[1], "bootstrap_replicates": B,
    } for key, value in dist.items()])
    # The 19 repeated policies, not the individual cells, are resampling units here.
    pair_draws = rng.integers(0, len(repeated), size=(B, len(repeated)))
    pearson, spearman, mad = [], [], []
    x, y = repeated.train_life_mean.to_numpy(float), repeated.primary_life_mean.to_numpy(float)
    for index in pair_draws:
        bx, by = x[index], y[index]
        pearson.append(float(np.corrcoef(bx, by)[0, 1]))
        spearman.append(float(spearmanr(bx, by).statistic))
        mad.append(float(np.mean(np.abs(by - bx))))
    agreement = pd.DataFrame([
        {"statistic": "Pearson相关", "point_estimate": float(np.corrcoef(x, y)[0, 1]), "ci95_low": ci(np.array(pearson))[0], "ci95_high": ci(np.array(pearson))[1], "bootstrap_unit": "重复策略组", "bootstrap_replicates": B},
        {"statistic": "Spearman相关", "point_estimate": float(spearmanr(x, y).statistic), "ci95_low": ci(np.array(spearman))[0], "ci95_high": ci(np.array(spearman))[1], "bootstrap_unit": "重复策略组", "bootstrap_replicates": B},
        {"statistic": "平均绝对寿命差（cycle）", "point_estimate": float(np.mean(np.abs(y-x))), "ci95_low": ci(np.array(mad))[0], "ci95_high": ci(np.array(mad))[1], "bootstrap_unit": "重复策略组", "bootstrap_replicates": B},
    ])
    summary.to_csv(TABLES / "q1_lifetime_distribution_bootstrap.csv", index=False, encoding="utf-8-sig")
    agreement.to_csv(TABLES / "q1_repeated_policy_agreement_bootstrap.csv", index=False, encoding="utf-8-sig")
    fig, axes = plt.subplots(1, 3, figsize=(14.5, 4.5), gridspec_kw={"width_ratios": [1.25, 1, 1]})
    axes[0].errorbar(summary.point_estimate, np.arange(len(summary)), xerr=[summary.point_estimate-summary.ci95_low, summary.ci95_high-summary.point_estimate], fmt="o", color="#1A6FC4", capsize=4)
    axes[0].set(yticks=np.arange(len(summary)), yticklabels=["均值", "中位数", "第一四分位数", "第三四分位数"], xlabel="循环寿命（cycle）", title="(a) 寿命分布摘要的电芯 bootstrap 区间")
    axes[0].grid(axis="x", alpha=.22)
    corr = agreement.iloc[:2]
    axes[1].errorbar(corr.point_estimate, np.arange(len(corr)), xerr=[corr.point_estimate-corr.ci95_low, corr.ci95_high-corr.point_estimate], fmt="o", color="#E28E2C", capsize=4)
    axes[1].axvline(0, color="#555555", linestyle="--", linewidth=1)
    axes[1].set(yticks=np.arange(len(corr)), yticklabels=corr.statistic, title="(b) 重复策略一致性的相关", xlabel="相关系数", xlim=(-.1, 1.05))
    axes[1].grid(axis="x", alpha=.22)
    difference = agreement.iloc[2]
    axes[2].errorbar([difference.point_estimate], [0], xerr=[[difference.point_estimate-difference.ci95_low], [difference.ci95_high-difference.point_estimate]], fmt="o", color="#54A24B", capsize=4)
    axes[2].set(yticks=[0], yticklabels=["平均绝对寿命差"], title="(c) 重复策略的跨分区差异", xlabel="寿命差（cycle）")
    axes[2].grid(axis="x", alpha=.22)
    fig.suptitle("Q1：描述性结论的 bootstrap 不确定性（不作因果推断）", y=1.03, fontsize=13)
    fig.tight_layout()
    for ext, kwargs in (("png", {"dpi":300}), ("svg", {})):
        fig.savefig(FIGURES / f"q1_descriptive_bootstrap.{ext}", bbox_inches="tight", **kwargs)
    plt.close(fig)
    payload = {"question":"Q1", "status":"descriptive_uncertainty_computed", "execution_timestamp":datetime.now(timezone.utc).isoformat(), "random_seed":SEED, "bootstrap_replicates":B, "scope":"All official cells for lifetime-distribution resampling; 19 Train-Primary repeated policies for agreement resampling. No model fitting or causal inference.", "distribution":summary.to_dict(orient="records"), "agreement":agreement.to_dict(orient="records")}
    (METRICS / "q1_descriptive_bootstrap_summary.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(summary.to_string(index=False)); print(agreement.to_string(index=False))

if __name__ == "__main__":
    main()
