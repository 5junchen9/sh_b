"""Q2-B Train-only design-before lifetime-proxy comparison.

This script deliberately excludes Primary/Secondary and all early-cycle features.
It compares only the pre-registered policy inputs C1, Q1_percent and C2 under
nested policy-group validation, then quantifies OOF stability by policy-block
bootstrap.  Outputs are saved under results/Q2/experiments/q2b_proxy_round1.
"""
from __future__ import annotations

import hashlib
import json
import os
import platform
import sys
from datetime import datetime, timezone
from pathlib import Path

# Some Windows environments cannot report physical CPU cores to joblib.  Set a
# conservative default before scikit-learn imports so ``-W error`` remains a
# reproducibility check rather than an environment-probing failure.
os.environ.setdefault("LOKY_MAX_CPU_COUNT", str(os.cpu_count() or 1))

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
import sklearn
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.linear_model import ElasticNet, Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error
from sklearn.model_selection import GroupKFold
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import SplineTransformer, StandardScaler


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "results" / "Q2" / "experiments" / "q2b_proxy_round1"
TABLES = OUT / "tables"
FIGURES = OUT / "figures"
METRICS = OUT / "metrics"
LOGS = OUT / "logs"
SEED = 20260802
BOOTSTRAP_REPLICATES = 2000
FEATURES = ["C1", "Q1_percent", "C2"]
TARGET = "cycle_life_table9"
GROUP = "policy_table9"

# The order also defines the parsimonious tie break among parameter models.
MODEL_SPECS = {
    "P1_ridge": {
        "name": "P1 主效应 Ridge",
        "complexity": 1,
        "role": "parameter_baseline",
        "grid": [{"alpha": alpha} for alpha in [0.01, 0.1, 1.0, 3.0, 10.0, 30.0, 100.0]],
    },
    "P2_elasticnet": {
        "name": "P2 ElasticNet",
        "complexity": 2,
        "role": "parameter_candidate",
        "grid": [
            {"alpha": alpha, "l1_ratio": l1_ratio}
            for alpha in [0.005, 0.01, 0.03, 0.1, 0.3, 1.0]
            for l1_ratio in [0.05, 0.2, 0.5, 0.8]
        ],
    },
    "P3_additive_gam": {
        "name": "P3 低自由度加性样条 GAM",
        "complexity": 3,
        "role": "parameter_candidate",
        "grid": [
            {"n_knots": n_knots, "alpha": alpha}
            for n_knots in [3, 4]
            for alpha in [0.03, 0.1, 0.3, 1.0, 3.0, 10.0, 30.0]
        ],
    },
    "C1_restricted_boosting": {
        "name": "C1 严格受限提升树（挑战者）",
        "complexity": 4,
        "role": "challenger",
        "grid": [
            {
                "learning_rate": learning_rate,
                "max_iter": 100,
                "max_leaf_nodes": 3,
                "min_samples_leaf": min_samples_leaf,
                "l2_regularization": l2_regularization,
            }
            for learning_rate in [0.05, 0.1]
            for min_samples_leaf in [8, 12]
            for l2_regularization in [1.0, 10.0]
        ],
    },
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    digest.update(path.read_bytes())
    return digest.hexdigest()


def make_model(method_id: str, params: dict):
    """Create one pipeline; preprocessing is fit inside each validation fold."""
    if method_id == "P1_ridge":
        return make_pipeline(StandardScaler(), Ridge(alpha=params["alpha"]))
    if method_id == "P2_elasticnet":
        return make_pipeline(
            StandardScaler(),
            ElasticNet(alpha=params["alpha"], l1_ratio=params["l1_ratio"], max_iter=50_000, tol=1e-7),
        )
    if method_id == "P3_additive_gam":
        return make_pipeline(
            SplineTransformer(n_knots=params["n_knots"], degree=2, include_bias=False, extrapolation="linear"),
            StandardScaler(),
            Ridge(alpha=params["alpha"]),
        )
    if method_id == "C1_restricted_boosting":
        return HistGradientBoostingRegressor(random_state=SEED, **params)
    raise ValueError(f"Unknown method: {method_id}")


def nested_oof(method_id: str, x: np.ndarray, y: np.ndarray, groups: np.ndarray) -> tuple[np.ndarray, pd.DataFrame]:
    outer = GroupKFold(n_splits=min(5, pd.Series(groups).nunique()))
    predictions = np.full(len(y), np.nan, dtype=float)
    chosen_rows: list[dict] = []

    for fold, (train_index, test_index) in enumerate(outer.split(x, y, groups), start=1):
        inner_groups = groups[train_index]
        inner = GroupKFold(n_splits=min(4, pd.Series(inner_groups).nunique()))
        scores: list[dict] = []
        for parameter_index, params in enumerate(MODEL_SPECS[method_id]["grid"]):
            fold_scores = []
            for inner_train, inner_valid in inner.split(x[train_index], y[train_index], inner_groups):
                model = make_model(method_id, params)
                model.fit(x[train_index][inner_train], y[train_index][inner_train])
                prediction = model.predict(x[train_index][inner_valid])
                fold_scores.append(float(mean_squared_error(y[train_index][inner_valid], prediction) ** 0.5))
            scores.append({"parameter_index": parameter_index, "params": params, "inner_rmse_log": float(np.mean(fold_scores))})

        score_frame = pd.DataFrame(scores).sort_values(["inner_rmse_log", "parameter_index"], kind="stable")
        selected = score_frame.iloc[0].to_dict()
        selected_params = selected["params"]
        final_model = make_model(method_id, selected_params).fit(x[train_index], y[train_index])
        predictions[test_index] = final_model.predict(x[test_index])
        chosen_rows.append(
            {
                "method_id": method_id,
                "fold": fold,
                "train_cells": int(len(train_index)),
                "test_cells": int(len(test_index)),
                "train_policy_groups": int(pd.Series(groups[train_index]).nunique()),
                "test_policy_groups": int(pd.Series(groups[test_index]).nunique()),
                "selected_parameter_index": int(selected["parameter_index"]),
                "selected_params_json": json.dumps(selected_params, ensure_ascii=False, sort_keys=True),
                "inner_rmse_log": float(selected["inner_rmse_log"]),
            }
        )
    if not np.isfinite(predictions).all():
        raise RuntimeError(f"{method_id} did not generate a complete OOF vector.")
    return predictions, pd.DataFrame(chosen_rows)


def metric_values(actual_log: np.ndarray, predicted_log: np.ndarray) -> dict[str, float]:
    actual_cycle = np.exp(actual_log)
    predicted_cycle = np.exp(predicted_log)
    positive_log_error = np.maximum(predicted_log - actual_log, 0.0)
    positive_cycle_error = np.maximum(predicted_cycle - actual_cycle, 0.0)
    return {
        "rmse_log": float(mean_squared_error(actual_log, predicted_log) ** 0.5),
        "mae_log": float(mean_absolute_error(actual_log, predicted_log)),
        "rmse_cycle": float(mean_squared_error(actual_cycle, predicted_cycle) ** 0.5),
        "mae_cycle": float(mean_absolute_error(actual_cycle, predicted_cycle)),
        "overprediction_rate": float(np.mean(predicted_log > actual_log)),
        "mean_positive_log_error": float(np.mean(positive_log_error)),
        "mean_positive_cycle_error": float(np.mean(positive_cycle_error)),
    }


def policy_block_indices(groups: np.ndarray, rng: np.random.Generator) -> np.ndarray:
    unique_groups = np.unique(groups)
    sampled = rng.choice(unique_groups, size=len(unique_groups), replace=True)
    return np.concatenate([np.flatnonzero(groups == item) for item in sampled])


def ci95(values: pd.Series) -> tuple[float, float]:
    low, high = np.quantile(values.to_numpy(float), [0.025, 0.975])
    return float(low), float(high)


def bootstrap_metrics(oof: pd.DataFrame) -> pd.DataFrame:
    actual = oof["actual_log_life"].to_numpy(float)
    groups = oof[GROUP].to_numpy()
    method_columns = [method_id for method_id in MODEL_SPECS]
    rng = np.random.default_rng(SEED)
    records: list[dict] = []
    for replicate in range(1, BOOTSTRAP_REPLICATES + 1):
        take = policy_block_indices(groups, rng)
        for method_id in method_columns:
            records.append(
                {
                    "replicate": replicate,
                    "method_id": method_id,
                    **metric_values(actual[take], oof.loc[:, method_id].to_numpy(float)[take]),
                }
            )
    return pd.DataFrame(records)


def summarise_metrics(oof: pd.DataFrame, bootstrap: pd.DataFrame) -> pd.DataFrame:
    actual = oof["actual_log_life"].to_numpy(float)
    rows: list[dict] = []
    for method_id, spec in MODEL_SPECS.items():
        point = metric_values(actual, oof[method_id].to_numpy(float))
        sampled = bootstrap.loc[bootstrap["method_id"].eq(method_id)]
        row = {
            "method_id": method_id,
            "method_name": spec["name"],
            "role": spec["role"],
            "complexity": spec["complexity"],
            **point,
        }
        for name in point:
            low, high = ci95(sampled[name])
            row[f"{name}_ci95_low"] = low
            row[f"{name}_ci95_high"] = high
            row[f"{name}_bootstrap_se"] = float(sampled[name].std(ddof=1))
        rows.append(row)
    return pd.DataFrame(rows).sort_values("complexity").reset_index(drop=True)


def pairwise_bootstrap(bootstrap: pd.DataFrame, reference_id: str) -> pd.DataFrame:
    metrics = ["rmse_log", "mae_log", "overprediction_rate", "mean_positive_log_error"]
    pivot = bootstrap.pivot(index="replicate", columns="method_id", values=metrics)
    rows: list[dict] = []
    for method_id in MODEL_SPECS:
        if method_id == reference_id:
            continue
        row = {"method_id": method_id, "reference_method_id": reference_id}
        for metric in metrics:
            delta = pivot[metric][method_id] - pivot[metric][reference_id]
            low, high = ci95(delta)
            row[f"delta_{metric}_ci95_low"] = low
            row[f"delta_{metric}_ci95_high"] = high
            row[f"delta_{metric}_bootstrap_mean"] = float(delta.mean())
        rows.append(row)
    return pd.DataFrame(rows)


def choose_proxy(summary: pd.DataFrame, bootstrap: pd.DataFrame) -> tuple[dict, pd.DataFrame]:
    parameter = summary.loc[summary["role"].ne("challenger")].copy()
    rmse_anchor = parameter.loc[parameter["rmse_log"].idxmin()]
    mae_anchor = parameter.loc[parameter["mae_log"].idxmin()]
    error_anchor = rmse_anchor
    parameter["within_best_rmse_one_se"] = parameter["rmse_log"] <= (
        float(rmse_anchor["rmse_log"]) + float(rmse_anchor["rmse_log_bootstrap_se"])
    )
    parameter["within_best_mae_one_se"] = parameter["mae_log"] <= (
        float(mae_anchor["mae_log"]) + float(mae_anchor["mae_log_bootstrap_se"])
    )
    parameter["overprediction_not_higher_than_error_anchor"] = parameter["overprediction_rate"] <= float(
        error_anchor["overprediction_rate"]
    )
    parameter["parameter_eligible"] = (
        parameter["within_best_rmse_one_se"]
        & parameter["within_best_mae_one_se"]
        & parameter["overprediction_not_higher_than_error_anchor"]
    )
    eligible = parameter.loc[parameter["parameter_eligible"]].sort_values("complexity")
    # A deterministic fallback is recorded rather than silently relaxing the rule.
    if eligible.empty:
        parameter_selected = error_anchor
        selection_note = "没有参数模型同时满足三项严格条件；按预注册回退规则采用 RMSE_log 最优参数模型。"
        fallback_used = True
    else:
        parameter_selected = eligible.iloc[0]
        selection_note = "在误差一标准误范围且过预测风险不高于误差锚点的参数模型中，选择复杂度最低者。"
        fallback_used = False

    reference_id = str(parameter_selected["method_id"])
    challenger_pair = pairwise_bootstrap(bootstrap, reference_id)
    challenger_row = challenger_pair.loc[challenger_pair["method_id"].eq("C1_restricted_boosting")].iloc[0]
    challenger_admitted = bool(
        challenger_row["delta_rmse_log_ci95_high"] < 0.0
        and challenger_row["delta_mae_log_ci95_high"] < 0.0
        and challenger_row["delta_overprediction_rate_ci95_high"] <= 0.0
    )
    final_id = "C1_restricted_boosting" if challenger_admitted else reference_id
    result = {
        "parameter_error_anchor": str(error_anchor["method_id"]),
        "parameter_rmse_anchor": str(rmse_anchor["method_id"]),
        "parameter_mae_anchor": str(mae_anchor["method_id"]),
        "parameter_selected": reference_id,
        "parameter_selection_note": selection_note,
        "parameter_selection_fallback_used": fallback_used,
        "challenger_admitted": challenger_admitted,
        "final_selected_proxy": final_id,
        "final_selected_name": MODEL_SPECS[final_id]["name"],
        "challenger_requirement": "相对参数代理，RMSE_log 与 MAE_log 的 bootstrap 差值95%上界均<0，且过预测比例差值上界<=0。",
    }
    parameter_columns = [
        "method_id",
        "within_best_rmse_one_se",
        "within_best_mae_one_se",
        "overprediction_not_higher_than_error_anchor",
        "parameter_eligible",
    ]
    selection_table = summary.merge(parameter[parameter_columns], on="method_id", how="left")
    selection_table["selected_parameter_proxy"] = selection_table["method_id"].eq(reference_id)
    selection_table["selected_final_proxy"] = selection_table["method_id"].eq(final_id)
    return result, selection_table.merge(challenger_pair, on="method_id", how="left")


def save_figures(summary: pd.DataFrame, selection: dict) -> None:
    labels = summary["method_name"].tolist()
    colors = ["#4E79A7", "#59A14F", "#F28E2B", "#B07AA1"]
    fig, axes = plt.subplots(1, 2, figsize=(12.2, 4.6))
    for ax, metric, title, ylabel in [
        (axes[0], "rmse_log", "寿命预测误差（越低越好）", "折外 RMSE_log"),
        (axes[1], "mae_log", "典型误差（越低越好）", "折外 MAE_log"),
    ]:
        value = summary[metric].to_numpy(float)
        low = summary[f"{metric}_ci95_low"].to_numpy(float)
        high = summary[f"{metric}_ci95_high"].to_numpy(float)
        ax.bar(range(len(summary)), value, color=colors)
        ax.errorbar(range(len(summary)), value, yerr=[value - low, high - value], fmt="none", color="#333333", capsize=3)
        ax.set_title(title)
        ax.set_ylabel(ylabel)
        ax.set_xticks(range(len(summary)), labels, rotation=18, ha="right")
        ax.grid(axis="y", alpha=0.25, linestyle="--")
    fig.suptitle("Q2-B：仅 Train、策略分组折外验证与 2000 次自助抽样")
    fig.tight_layout()
    for suffix in ["png", "svg"]:
        fig.savefig(FIGURES / f"q2b_proxy_error_comparison.{suffix}", dpi=240, bbox_inches="tight")
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(7.4, 4.6))
    value = summary["overprediction_rate"].to_numpy(float)
    low = summary["overprediction_rate_ci95_low"].to_numpy(float)
    high = summary["overprediction_rate_ci95_high"].to_numpy(float)
    bars = ax.bar(range(len(summary)), value, color=colors)
    ax.errorbar(range(len(summary)), value, yerr=[value - low, high - value], fmt="none", color="#333333", capsize=3)
    final_index = summary.index[summary["method_id"].eq(selection["final_selected_proxy"])][0]
    bars[final_index].set_edgecolor("#111111")
    bars[final_index].set_linewidth(2.0)
    ax.set_xticks(range(len(summary)), labels, rotation=18, ha="right")
    ax.set_ylabel("预测寿命高于真实寿命的比例")
    ax.set_title("Q2-B：过预测风险（黑框为按规则选定的代理）")
    ax.grid(axis="y", alpha=0.25, linestyle="--")
    fig.tight_layout()
    for suffix in ["png", "svg"]:
        fig.savefig(FIGURES / f"q2b_proxy_overprediction_risk.{suffix}", dpi=240, bbox_inches="tight")
    plt.close(fig)


def write_report(summary: pd.DataFrame, selection_table: pd.DataFrame, selection: dict) -> None:
    selected = summary.loc[summary["method_id"].eq(selection["final_selected_proxy"])].iloc[0]
    rows = []
    for item in selection_table.itertuples(index=False):
        rows.append(
            f"| {item.method_name} | {item.rmse_log:.4f} | {item.mae_log:.4f} | "
            f"{item.overprediction_rate:.1%} | {item.mean_positive_log_error:.4f} | {item.role} |"
        )
    challenger_sentence = (
        "满足预注册的三项明确增益条件，允许替代参数代理。"
        if selection["challenger_admitted"]
        else "未同时满足对参数代理的明确增益门槛，因此只保留为挑战者。"
    )
    report = f"""# Q2-B：设计前寿命预测代理比较报告

## 结论

按冻结规则，本轮供 Q4 使用的设计前寿命代理为 **{selection['final_selected_name']}**。
其 Train 策略分组折外指标为 `RMSE_log={selected.rmse_log:.4f}`、
`MAE_log={selected.mae_log:.4f}`，预测寿命高于真实寿命的比例为
`{selected.overprediction_rate:.1%}`。

参数模型选择说明：{selection['parameter_selection_note']}
受限提升树：{challenger_sentence}

## 评价范围

- 数据：仅 `dataset_table9 == 'Train'` 的 41 枚电芯、40 个 `policy_table9` 组。
- 输入：设计前可知的 `C1`、`Q1_percent`、`C2`；不读取早期曲线、Primary 或 Secondary。
- 验证：外层 5 折策略分组 OOF，内层 4 折策略分组调参。
- 稳健性：对 OOF 误差做 2000 次策略组块 bootstrap；区间反映 Train 内重抽样稳定性，不等于外部泛化保证。

## 候选模型结果

| 模型 | RMSE_log | MAE_log | 过预测比例 | 平均正向对数误差 | 角色 |
|---|---:|---:|---:|---:|---|
{chr(10).join(rows)}

## 对 Q4 的使用规则

1. 仅在 Train 的原始/SOC 双空间支持域内调用本代理，不做域外外推。
2. 优化结果只能标记为 `Q2_provisional`，直到按 Q3 冻结窗口 `k=100` 完成受限确认。
3. 本报告不替代 Q2-A 的机制解释：M1 仍是正文保守基线，M2 仍仅为交互敏感性分析。
4. 不能用 Primary 或 Secondary 重新调模型、改阈值或扩充候选池。

## 可复现入口

- 脚本：`code/Q2/q2b_train_proxy_comparison.py`
- 全部数表：`results/Q2/experiments/q2b_proxy_round1/tables/`
- 指标与选择记录：`results/Q2/experiments/q2b_proxy_round1/metrics/`
- 图：`results/Q2/experiments/q2b_proxy_round1/figures/`
"""
    (OUT / "q2b_proxy_comparison_report.md").write_text(report, encoding="utf-8")


def main() -> None:
    for directory in [TABLES, FIGURES, METRICS, LOGS]:
        directory.mkdir(parents=True, exist_ok=True)
    p0_path = ROOT / "data" / "processed" / "p0_summary.json"
    label_path = ROOT / "data" / "processed" / "cell_labels.csv"
    p0 = json.loads(p0_path.read_text(encoding="utf-8"))
    if p0.get("p0_status") != "pass":
        raise RuntimeError("P0 audit is not pass; Q2-B may not run.")
    labels = pd.read_csv(label_path)
    train = labels.loc[labels["dataset_table9"].eq("Train")].copy().reset_index(drop=True)
    required = ["barcode", GROUP, TARGET, *FEATURES]
    missing = [column for column in required if column not in train.columns]
    if missing:
        raise RuntimeError(f"Required columns missing: {missing}")
    if train[required].isna().any().any():
        raise RuntimeError("Train rows contain missing values in Q2-B required fields; no row was dropped.")
    if len(train) != 41 or train[GROUP].nunique() != 40:
        raise RuntimeError("Unexpected Train roster; expected 41 cells and 40 policy groups.")

    x = train[FEATURES].to_numpy(float)
    y = np.log(train[TARGET].to_numpy(float))
    groups = train[GROUP].to_numpy()
    oof = train[["barcode", GROUP, TARGET, *FEATURES]].copy()
    oof["actual_log_life"] = y
    folds: list[pd.DataFrame] = []
    for method_id in MODEL_SPECS:
        prediction, selected_folds = nested_oof(method_id, x, y, groups)
        oof[method_id] = prediction
        selected_folds["method_name"] = MODEL_SPECS[method_id]["name"]
        folds.append(selected_folds)
    for method_id in MODEL_SPECS:
        oof[f"{method_id}_pred_cycle_life"] = np.exp(oof[method_id])
        oof[f"{method_id}_residual_log"] = oof[method_id] - oof["actual_log_life"]
    oof.to_csv(TABLES / "q2b_oof_predictions.csv", index=False, encoding="utf-8-sig")
    pd.concat(folds, ignore_index=True).to_csv(TABLES / "q2b_nested_cv_selected_params.csv", index=False, encoding="utf-8-sig")

    bootstrap = bootstrap_metrics(oof)
    bootstrap.to_csv(TABLES / "q2b_policy_block_bootstrap.csv", index=False, encoding="utf-8-sig")
    summary = summarise_metrics(oof, bootstrap)
    selection, selection_table = choose_proxy(summary, bootstrap)
    selection_table.to_csv(TABLES / "q2b_model_comparison_and_selection.csv", index=False, encoding="utf-8-sig")
    summary.to_csv(TABLES / "q2b_model_metrics.csv", index=False, encoding="utf-8-sig")
    with (METRICS / "q2b_proxy_selection.json").open("w", encoding="utf-8") as handle:
        json.dump(selection, handle, ensure_ascii=False, indent=2)
    save_figures(summary, selection)
    write_report(summary, selection_table, selection)

    run_summary = {
        "question": "Q2-B",
        "round": "q2b_proxy_round1",
        "execution_timestamp": datetime.now(timezone.utc).isoformat(),
        "implementation_target": "python",
        "random_seed": SEED,
        "scope": "Train-only; Primary/Secondary and early-cycle features are excluded from fitting, tuning, bootstrap, selection and scoring.",
        "data": {"train_cells": len(train), "policy_groups": int(train[GROUP].nunique()), "features": FEATURES, "target": f"ln({TARGET})"},
        "validation": {"outer": "5-fold GroupKFold(policy_table9)", "inner": "4-fold GroupKFold(policy_table9)", "tuning_metric": "mean inner RMSE_log"},
        "bootstrap": {"replicates": BOOTSTRAP_REPLICATES, "unit": "policy_table9 block", "condition": "stored outer-fold OOF predictions"},
        "methods": [{"method_id": item, **MODEL_SPECS[item]} for item in MODEL_SPECS],
        "selection": selection,
        "input_sha256": {"p0_summary.json": sha256(p0_path), "cell_labels.csv": sha256(label_path)},
        "script_sha256": sha256(Path(__file__)),
        "environment": {"python": sys.version, "platform": platform.platform(), "scikit_learn": sklearn.__version__},
    }
    (OUT / "run_summary.json").write_text(json.dumps(run_summary, ensure_ascii=False, indent=2), encoding="utf-8")
    (LOGS / "run.log").write_text(json.dumps(run_summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"selection": selection, "metrics": summary[["method_id", "rmse_log", "mae_log", "overprediction_rate"]].to_dict(orient="records")}, ensure_ascii=False))


if __name__ == "__main__":
    main()
