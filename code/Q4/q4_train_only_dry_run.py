"""Q4 Train-only candidate-flow dry-run; this is not a final optimization.

Candidates passing the double-space support checks are deliberately labelled
Q2_provisional.  No Q3 features, Primary/Secondary labels, lifetime LCB, or
formal Pareto recommendation is generated here.
"""
from __future__ import annotations

import hashlib
import json
import platform
import sys
from datetime import datetime, timezone
from itertools import product
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
matplotlib.rcParams.update(
    {
        "font.family": "sans-serif",
        "font.sans-serif": ["Microsoft YaHei", "SimHei", "DejaVu Sans"],
        "axes.unicode_minus": False,
        "svg.fonttype": "none",
    }
)
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_squared_error
from sklearn.model_selection import GroupKFold
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import SplineTransformer, StandardScaler


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "results" / "Q4" / "experiments" / "train_dry_run_round1"
TABLES, FIGURES, METRICS, LOGS = (OUT / "tables", OUT / "figures", OUT / "metrics", OUT / "logs")
SEED = 20260802
SUPPORT_BOOTSTRAP_REPLICATES = 1000
QDIST = 0.95
SUPPORT_RATE_MIN = 0.80
RAW_COLUMNS = ["C1", "q", "C2_effective"]
SOC_COLUMNS = ["E0_20", "E20_40", "E40_60", "E60_80", "tau_0_80_min"]
P3_GRID = [
    {"n_knots": n_knots, "alpha": alpha}
    for n_knots in [3, 4]
    for alpha in [0.03, 0.1, 0.3, 1.0, 3.0, 10.0, 30.0]
]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def overlap(left: float, right: float, interval_left: float, interval_right: float) -> float:
    return max(0.0, min(right, interval_right) - max(left, interval_left))


def derive_policy_frame(frame: pd.DataFrame) -> pd.DataFrame:
    """Derive theoretical time and four SOC exposures, with an explicit q=80% branch."""
    data = frame.copy()
    data["q"] = data["Q1_percent"].astype(float) / 100.0
    data["single_stage_0_80"] = np.isclose(data["q"], 0.8)
    # At q=80% C2 is physically inactive.  Train itself records C2=C1 there,
    # so the same convention is used in raw-space distance calculations.
    data["C2_effective"] = np.where(data["single_stage_0_80"], data["C1"], data["C2"])
    data["tau_0_80_min"] = 60.0 * (
        data["q"] / data["C1"] + (0.8 - data["q"]) / data["C2_effective"]
    )
    for lower, upper, name in [(0.0, 0.2, "E0_20"), (0.2, 0.4, "E20_40"), (0.4, 0.6, "E40_60"), (0.6, 0.8, "E60_80")]:
        first = np.array([overlap(lower, upper, 0.0, q) for q in data["q"]])
        second = (upper - lower) - first
        data[name] = (data["C1"].to_numpy(float) * first + data["C2_effective"].to_numpy(float) * second) / (upper - lower)
    return data


def make_p3(params: dict):
    return make_pipeline(
        SplineTransformer(n_knots=params["n_knots"], degree=2, include_bias=False, extrapolation="linear"),
        StandardScaler(),
        Ridge(alpha=params["alpha"]),
    )


def choose_p3_params(x: np.ndarray, y: np.ndarray, groups: np.ndarray) -> tuple[dict, pd.DataFrame]:
    splitter = GroupKFold(n_splits=min(5, pd.Series(groups).nunique()))
    rows: list[dict] = []
    for index, params in enumerate(P3_GRID):
        fold_values = []
        for train_index, valid_index in splitter.split(x, y, groups):
            model = make_p3(params).fit(x[train_index], y[train_index])
            fold_values.append(float(mean_squared_error(y[valid_index], model.predict(x[valid_index])) ** 0.5))
        rows.append({"parameter_index": index, "params_json": json.dumps(params, sort_keys=True), "group_cv_rmse_log": float(np.mean(fold_values))})
    scores = pd.DataFrame(rows).sort_values(["group_cv_rmse_log", "parameter_index"], kind="stable").reset_index(drop=True)
    return json.loads(scores.loc[0, "params_json"]), scores


def robust_standardize(reference: np.ndarray, values: np.ndarray) -> tuple[np.ndarray, dict]:
    median = np.median(reference, axis=0)
    q25, q75 = np.quantile(reference, [0.25, 0.75], axis=0)
    iqr = q75 - q25
    active = iqr > 0.0
    if not active.any():
        raise RuntimeError("Every support-space IQR is zero.")
    return (values[:, active] - median[active]) / iqr[active], {
        "median": median.tolist(),
        "iqr": iqr.tolist(),
        "active_dimension_indices": np.flatnonzero(active).tolist(),
    }


def euclidean_distances(left: np.ndarray, right: np.ndarray) -> np.ndarray:
    return np.sqrt(((left[:, None, :] - right[None, :, :]) ** 2).sum(axis=2))


def leave_one_out_d5(standardized: np.ndarray) -> np.ndarray:
    distances = euclidean_distances(standardized, standardized)
    np.fill_diagonal(distances, np.inf)
    return np.partition(distances, kth=4, axis=1)[:, 4]


def candidate_lattice(train: pd.DataFrame) -> pd.DataFrame:
    c1_values = sorted(train["C1"].unique())
    q_values = sorted(train["Q1_percent"].unique())
    c2_values = sorted(train["C2"].unique())
    normal_q = [q for q in q_values if not np.isclose(q, 80.0)]
    rows = [{"C1": c1, "Q1_percent": q, "C2": c2} for c1, q, c2 in product(c1_values, normal_q, c2_values)]
    rows.extend({"C1": c1, "Q1_percent": 80.0, "C2": c1} for c1 in c1_values)
    candidate = derive_policy_frame(pd.DataFrame(rows))
    expected = len(c1_values) * len(normal_q) * len(c2_values) + len(c1_values)
    if len(candidate) != expected:
        raise RuntimeError("Candidate lattice count mismatch.")
    return candidate


def support_bootstrap(candidate_raw: np.ndarray, candidate_soc: np.ndarray, train_raw: np.ndarray, train_soc: np.ndarray, c_raw: float, c_soc: float) -> np.ndarray:
    rng = np.random.default_rng(SEED)
    passes = np.zeros(len(candidate_raw), dtype=np.int32)
    n_train = len(train_raw)
    for _ in range(SUPPORT_BOOTSTRAP_REPLICATES):
        unique = np.unique(rng.integers(0, n_train, size=n_train))
        if len(unique) < 5:
            continue
        raw_d5 = np.partition(euclidean_distances(candidate_raw, train_raw[unique]), kth=4, axis=1)[:, 4]
        soc_d5 = np.partition(euclidean_distances(candidate_soc, train_soc[unique]), kth=4, axis=1)[:, 4]
        passes += (raw_d5 <= c_raw) & (soc_d5 <= c_soc)
    return passes / SUPPORT_BOOTSTRAP_REPLICATES


def save_figures(flow: pd.DataFrame, candidate: pd.DataFrame) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(12.0, 4.5))
    short_stages = ["总格点", "可行", "边界", "原始参数 5近邻", "SOC 5近邻", "双空间", "稳定支持"]
    bars = axes[0].bar(short_stages, flow["count"], color=["#9FA7B3", "#5B9BD5", "#E28E2C", "#2E9E44", "#1A6FC4", "#7B5FD6", "#7B5FD6"])
    for bar, value in zip(bars, flow["count"]):
        axes[0].text(bar.get_x() + bar.get_width() / 2, value + 55, f"{value}", ha="center", va="bottom", fontsize=8)
    axes[0].set_title("Q4 仅训练集候选流量（非正式推荐）")
    axes[0].set_xlabel("筛选阶段")
    axes[0].set_ylabel("候选数量")
    axes[0].tick_params(axis="x", rotation=22)
    axes[0].grid(axis="y", alpha=0.25, linestyle="--")

    rejected = candidate.loc[candidate["status"].eq("rejected")]
    provisional = candidate.loc[candidate["status"].eq("Q2_provisional")]
    axes[1].scatter(rejected["tau_0_80_min"], rejected["q2b_pred_cycle_life"], s=9, alpha=0.22, color="#A8A8A8", label="支持不足")
    axes[1].scatter(provisional["tau_0_80_min"], provisional["q2b_pred_cycle_life"], s=18, alpha=0.75, color="#1A6FC4", label="Q2 暂定候选")
    axes[1].set_title("支持域通过的 Q2 暂定候选（并非帕累托解）")
    axes[1].set_xlabel("理论 0–80% 充电时间 τ0-80（min）")
    axes[1].set_ylabel("P3 设计前寿命点预测（cycle）")
    axes[1].legend(frameon=False)
    axes[1].grid(alpha=0.22, linestyle="--")
    fig.suptitle("仅训练集：仅作候选流量与支持域诊断")
    fig.tight_layout()
    for suffix in ["svg", "png"]:
        fig.savefig(FIGURES / f"q4_train_only_candidate_flow.{suffix}", dpi=240, bbox_inches="tight")
    plt.close(fig)


def write_report(flow: pd.DataFrame, candidate: pd.DataFrame, thresholds: dict, params: dict) -> None:
    provisional = candidate.loc[candidate["status"].eq("Q2_provisional")]
    report = f"""# Q4 Train-only 候选流量 dry-run

## 状态

本次只完成候选格点、双空间支持域与 barcode bootstrap 支持率审计。通过者均为
`Q2_provisional`，**不是最终推荐，也不进入正式 Q2+Q3 Pareto**。

## 冻结配置

- 格点：Train 离散水平组合；`Q1<80%` 的完整组合加上 `Q1=80%` 时 `C2=C1` 的单阶段分支。
- 距离：Train 中位数/IQR 标准化的 raw `(C1,q,C2_effective)` 与 SOC
  `(E0-20,E20-40,E40-60,E60-80,tau0-80)` 双空间欧氏 5-NN。
- 阈值：留一第 5 邻居距离的 95% 分位，`c_raw={thresholds['c_raw']:.4f}`，`c_soc={thresholds['c_soc']:.4f}`。
- 支持率：{SUPPORT_BOOTSTRAP_REPLICATES} 次 Train barcode bootstrap，门槛 {SUPPORT_RATE_MIN:.0%}。
- Q2 点预测：Train 全量 refit 的 P3 加性样条 GAM，分组 CV 选择 `n_knots={params['n_knots']}`、`alpha={params['alpha']}`；仅供候选审计，不提供寿命下界。

## 候选流量

| 阶段 | 数量 |
|---|---:|
{chr(10).join(f'| {r.stage} | {r.count} |' for r in flow.itertuples(index=False))}

## 使用边界

- 候选表含有点预测只是为了发现明显异常；不把它作为最终寿命或保守寿命下界。
- 新策略必须至少有 3 枚不同物理电芯运行到 Q3 冻结窗口 `k=100`，方可升级为 `Q3_confirmed`。
- Primary/Secondary 均未读取；不得用之后的结果修改本格点、距离阈值或 80% 支持率。
- 单模型下模型分歧统一记录为 `N/A`，不是 0。

## 文件

- 全部候选：`tables/q4_train_only_all_candidates.csv`
- 可供 pilot 的暂定候选：`tables/q4_q2_provisional_candidates.csv`
- 流量和阈值：`metrics/q4_train_only_dry_run_summary.json`
- 图：`figures/q4_train_only_candidate_flow.svg`（内部诊断图）
"""
    (OUT / "q4_train_only_dry_run_report.md").write_text(report, encoding="utf-8")


def main() -> None:
    for directory in [TABLES, FIGURES, METRICS, LOGS]:
        directory.mkdir(parents=True, exist_ok=True)
    p0_path, labels_path = ROOT / "data" / "processed" / "p0_summary.json", ROOT / "data" / "processed" / "cell_labels.csv"
    p0 = json.loads(p0_path.read_text(encoding="utf-8"))
    if p0.get("p0_status") != "pass":
        raise RuntimeError("P0 audit is not pass; Q4 dry-run is blocked.")
    labels = pd.read_csv(labels_path)
    train = labels.loc[labels["dataset_table9"].eq("Train")].copy().reset_index(drop=True)
    required = ["barcode", "policy_table9", "cycle_life_table9", "C1", "Q1_percent", "C2"]
    if train[required].isna().any().any() or len(train) != 41 or train["policy_table9"].nunique() != 40:
        raise RuntimeError("Unexpected Train roster or missing Q4 fields; no row was dropped.")
    train = derive_policy_frame(train)
    candidate = candidate_lattice(train)
    existing = set(zip(train["C1"], train["Q1_percent"], train["C2_effective"]))
    candidate["observed_train_parameter_combo"] = [tuple(row) in existing for row in candidate[["C1", "Q1_percent", "C2_effective"]].to_numpy()]

    train_raw_original = train[RAW_COLUMNS].to_numpy(float)
    train_soc_original = train[SOC_COLUMNS].to_numpy(float)
    candidate_raw, raw_scaler = robust_standardize(train_raw_original, candidate[RAW_COLUMNS].to_numpy(float))
    train_raw, _ = robust_standardize(train_raw_original, train_raw_original)
    candidate_soc, soc_scaler = robust_standardize(train_soc_original, candidate[SOC_COLUMNS].to_numpy(float))
    train_soc, _ = robust_standardize(train_soc_original, train_soc_original)
    c_raw = float(np.quantile(leave_one_out_d5(train_raw), QDIST))
    c_soc = float(np.quantile(leave_one_out_d5(train_soc), QDIST))
    candidate["d5_raw"] = np.partition(euclidean_distances(candidate_raw, train_raw), kth=4, axis=1)[:, 4]
    candidate["d5_soc"] = np.partition(euclidean_distances(candidate_soc, train_soc), kth=4, axis=1)[:, 4]
    candidate["passes_raw_5nn"] = candidate["d5_raw"] <= c_raw
    candidate["passes_soc_5nn"] = candidate["d5_soc"] <= c_soc
    candidate["passes_double_5nn"] = candidate["passes_raw_5nn"] & candidate["passes_soc_5nn"]
    candidate["support_bootstrap_rate"] = support_bootstrap(candidate_raw, candidate_soc, train_raw, train_soc, c_raw, c_soc)
    candidate["passes_support_bootstrap"] = candidate["support_bootstrap_rate"] >= SUPPORT_RATE_MIN

    x = train[["C1", "Q1_percent", "C2"]].to_numpy(float)
    y = np.log(train["cycle_life_table9"].to_numpy(float))
    params, tuning = choose_p3_params(x, y, train["policy_table9"].to_numpy())
    model = make_p3(params).fit(x, y)
    candidate["q2b_pred_log_life"] = model.predict(candidate[["C1", "Q1_percent", "C2"]].to_numpy(float))
    candidate["q2b_pred_cycle_life"] = np.exp(candidate["q2b_pred_log_life"])
    candidate["model_disagreement_log"] = "N/A"
    candidate["candidate_type"] = np.where(candidate["observed_train_parameter_combo"], "existing_parameter_combo", "new_parameter_combo")
    candidate["status"] = np.where(candidate["passes_double_5nn"] & candidate["passes_support_bootstrap"], "Q2_provisional", "rejected")
    candidate["status_reason"] = np.where(candidate["status"].eq("Q2_provisional"), "requires_pilot_and_Q3_k100_confirmation", "no_support")
    candidate.to_csv(TABLES / "q4_train_only_all_candidates.csv", index=False, encoding="utf-8-sig")
    candidate.loc[candidate["status"].eq("Q2_provisional")].sort_values(["tau_0_80_min", "q2b_pred_cycle_life"], ascending=[True, False]).to_csv(
        TABLES / "q4_q2_provisional_candidates.csv", index=False, encoding="utf-8-sig"
    )
    tuning.to_csv(TABLES / "q4_p3_full_train_tuning.csv", index=False, encoding="utf-8-sig")
    stages = [
        ("候选格点总数", len(candidate)),
        ("数学可行", len(candidate)),
        ("参数边界通过", len(candidate)),
        ("raw 5-NN 通过", int(candidate["passes_raw_5nn"].sum())),
        ("SOC 5-NN 通过", int(candidate["passes_soc_5nn"].sum())),
        ("双空间通过", int(candidate["passes_double_5nn"].sum())),
        ("双空间且支持率≥80%（Q2 暂定候选）", int(candidate["status"].eq("Q2_provisional").sum())),
    ]
    flow = pd.DataFrame(stages, columns=["stage", "count"])
    flow.to_csv(TABLES / "q4_candidate_flow.csv", index=False, encoding="utf-8-sig")
    thresholds = {"c_raw": c_raw, "c_soc": c_soc, "raw_scaler": raw_scaler, "soc_scaler": soc_scaler}
    summary = {
        "question": "Q4",
        "round": "train_dry_run_round1",
        "scope": "Train-only candidate support dry-run. It does not create formal Pareto or final recommendations.",
        "seed": SEED,
        "train_cells": len(train),
        "policy_groups": int(train["policy_table9"].nunique()),
        "candidate_grid": {"rule": "observed-level lattice with q=80 single-stage branch", "total": len(candidate)},
        "support": {"nearest_neighbors": 5, "threshold_quantile": QDIST, "bootstrap_replicates": SUPPORT_BOOTSTRAP_REPLICATES, "bootstrap_support_min": SUPPORT_RATE_MIN, **thresholds},
        "p3_refit": {"parameters": params, "feature_columns": ["C1", "Q1_percent", "C2"], "target": "ln(cycle_life_table9)"},
        "flow": flow.to_dict(orient="records"),
        "input_sha256": {"p0_summary.json": sha256(p0_path), "cell_labels.csv": sha256(labels_path)},
        "script_sha256": sha256(Path(__file__)),
        "environment": {"python": sys.version, "platform": platform.platform()},
    }
    (METRICS / "q4_train_only_dry_run_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    (OUT / "run_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    (LOGS / "run.log").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    save_figures(flow, candidate)
    write_report(flow, candidate, thresholds, params)
    print(json.dumps({"flow": summary["flow"], "p3_params": params}, ensure_ascii=False))


if __name__ == "__main__":
    main()
