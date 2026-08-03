"""Train-only grouped-bootstrap robustness checks for Q2 and Q3.

This script consumes only the 41 rows tagged ``Train`` after loading the
approved processed files.  It does not read Primary/Secondary result files or
use their labels in fitting, resampling, selection, or scoring.

The Q2 bootstrap conditions on the already generated honest OOF predictions
and resamples policy blocks.  Coefficient signs are assessed by refitting M2
on policy-block bootstrap samples with the modal pre-registered alpha=0.1.
The Q3 section recreates the existing fold-specific M3 pipeline to save
per-cell future-SOH errors, then bootstraps policy blocks of those OOF errors.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
from datetime import datetime, timezone
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
matplotlib.rcParams.update(
    {
        "font.family": "sans-serif",
        "font.sans-serif": ["Microsoft YaHei", "SimHei", "DejaVu Sans"],
        "axes.unicode_minus": False,
        "svg.fonttype": "none",
        "pdf.fonttype": 42,
        "font.size": 10,
    }
)
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error
from sklearn.model_selection import GroupKFold


ROOT = Path(__file__).resolve().parents[2]
SEED = 20260802
B = 2000
Q2_OUT = ROOT / "robustness" / "Q2"
Q3_OUT = ROOT / "robustness" / "Q3"
Q2_FIG = Q2_OUT / "figures"
Q3_FIG = Q3_OUT / "figures"
Q2_TABLES = Q2_OUT / "tables"
Q3_TABLES = Q3_OUT / "tables"
Q2_METRICS = Q2_OUT / "metrics"
Q3_METRICS = Q3_OUT / "metrics"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def ensure_dirs() -> None:
    for directory in (Q2_FIG, Q3_FIG, Q2_TABLES, Q3_TABLES, Q2_METRICS, Q3_METRICS):
        directory.mkdir(parents=True, exist_ok=True)


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def train_labels() -> pd.DataFrame:
    labels = pd.read_csv(ROOT / "data" / "processed" / "cell_labels.csv")
    train = labels.loc[labels["dataset_table9"].eq("Train")].copy().reset_index(drop=True)
    if len(train) != 41 or train["barcode"].nunique() != 41:
        raise RuntimeError("Expected exactly 41 unique Train barcodes.")
    if not train["dataset_table9"].eq("Train").all():
        raise RuntimeError("Non-Train rows reached a Train-only robustness calculation.")
    return train


def percentile_ci(values: np.ndarray) -> tuple[float, float]:
    return tuple(float(x) for x in np.quantile(values, [0.025, 0.975]))


def grouped_bootstrap_indices(groups: np.ndarray, rng: np.random.Generator) -> np.ndarray:
    unique = np.unique(groups)
    sampled = rng.choice(unique, size=len(unique), replace=True)
    return np.concatenate([np.flatnonzero(groups == group) for group in sampled])


def q2_robustness(train: pd.DataFrame, q2_module) -> dict:
    m1 = pd.read_csv(ROOT / "results" / "Q2" / "experiments" / "round1" / "tables" / "m1_oof_predictions.csv")
    m2 = pd.read_csv(ROOT / "results" / "Q2" / "experiments" / "round1" / "tables" / "m2_oof_predictions.csv")
    key = ["barcode", "policy_table9", "cycle_life_table9"]
    oof = m1[key + ["pred_log_life"]].merge(
        m2[key + ["pred_log_life"]], on=key, suffixes=("_m1", "_m2"), validate="one_to_one"
    )
    if set(oof["barcode"]) != set(train["barcode"]) or len(oof) != len(train):
        raise RuntimeError("Q2 OOF rows do not match the Train roster.")
    y = np.log(oof["cycle_life_table9"].to_numpy(float))
    groups = oof["policy_table9"].to_numpy()
    rng = np.random.default_rng(SEED)
    records = []
    for replicate in range(1, B + 1):
        take = grouped_bootstrap_indices(groups, rng)
        y_b = y[take]
        p1 = oof["pred_log_life_m1"].to_numpy(float)[take]
        p2 = oof["pred_log_life_m2"].to_numpy(float)[take]
        rmse_1 = float(mean_squared_error(y_b, p1) ** 0.5)
        rmse_2 = float(mean_squared_error(y_b, p2) ** 0.5)
        mae_1 = float(mean_absolute_error(y_b, p1))
        mae_2 = float(mean_absolute_error(y_b, p2))
        records.append(
            {
                "replicate": replicate,
                "rmse_log_m1": rmse_1,
                "rmse_log_m2": rmse_2,
                "delta_rmse_log_m2_minus_m1": rmse_2 - rmse_1,
                "mae_log_m1": mae_1,
                "mae_log_m2": mae_2,
                "delta_mae_log_m2_minus_m1": mae_2 - mae_1,
                "relative_mae_improvement": (mae_1 - mae_2) / mae_1,
            }
        )
    boot = pd.DataFrame(records)
    boot.to_csv(Q2_TABLES / "q2_policy_block_bootstrap.csv", index=False, encoding="utf-8-sig")

    # The selected M2 procedure most often chose alpha=0.1 in the nested-CV
    # folds.  Fixing that pre-existing value isolates sampling stability of
    # interaction signs; it is not a second model-selection exercise.
    X = train[["C1", "Q1_percent", "C2"]].to_numpy(float)
    y_train = np.log(train["cycle_life_table9"].to_numpy(float))
    g_train = train["policy_table9"].to_numpy()
    feature_names = None
    coefficient_rows = []
    rng_coef = np.random.default_rng(SEED + 1)
    for replicate in range(1, B + 1):
        take = grouped_bootstrap_indices(g_train, rng_coef)
        fitted = q2_module.make_model("M2", 0.1).fit(X[take], y_train[take])
        polynomial = fitted.named_steps["polynomialfeatures"]
        ridge = fitted.named_steps["ridge"]
        if feature_names is None:
            feature_names = polynomial.get_feature_names_out(["C1", "Q1_percent", "C2"])
        coefficient_rows.append(dict(zip(feature_names, ridge.coef_)) | {"replicate": replicate})
    coefficients = pd.DataFrame(coefficient_rows)
    coefficients.to_csv(Q2_TABLES / "q2_m2_coefficient_bootstrap.csv", index=False, encoding="utf-8-sig")
    interaction_names = ["C1 Q1_percent", "C1 C2", "Q1_percent C2"]
    sign_rows = []
    for name in interaction_names:
        values = coefficients[name].to_numpy(float)
        pos = float(np.mean(values > 0))
        neg = float(np.mean(values < 0))
        sign_rows.append(
            {
                "term": name,
                "positive_share": pos,
                "negative_share": neg,
                "zero_share": float(np.mean(values == 0)),
                "dominant_sign": "positive" if pos >= neg else "negative",
                "sign_stability": max(pos, neg),
                "coefficient_ci_low": percentile_ci(values)[0],
                "coefficient_ci_high": percentile_ci(values)[1],
            }
        )
    signs = pd.DataFrame(sign_rows)
    signs.to_csv(Q2_TABLES / "q2_interaction_sign_stability.csv", index=False, encoding="utf-8-sig")

    original = {
        "rmse_log_m1": float(mean_squared_error(y, oof["pred_log_life_m1"]) ** 0.5),
        "rmse_log_m2": float(mean_squared_error(y, oof["pred_log_life_m2"]) ** 0.5),
        "mae_log_m1": float(mean_absolute_error(y, oof["pred_log_life_m1"])),
        "mae_log_m2": float(mean_absolute_error(y, oof["pred_log_life_m2"])),
    }
    original["delta_rmse_log_m2_minus_m1"] = original["rmse_log_m2"] - original["rmse_log_m1"]
    original["delta_mae_log_m2_minus_m1"] = original["mae_log_m2"] - original["mae_log_m1"]
    original["relative_mae_improvement"] = (original["mae_log_m1"] - original["mae_log_m2"]) / original["mae_log_m1"]
    rmse_ci = percentile_ci(boot["delta_rmse_log_m2_minus_m1"].to_numpy())
    mae_ci = percentile_ci(boot["delta_mae_log_m2_minus_m1"].to_numpy())
    gate = {
        "mae_ci_upper_lt_zero": bool(mae_ci[1] < 0),
        "relative_mae_improvement_ge_5pct": bool(original["relative_mae_improvement"] >= 0.05),
        "all_main_interaction_sign_stability_ge_80pct": bool((signs["sign_stability"] >= 0.80).all()),
    }
    summary = {
        "scope": "Train-only policy-block bootstrap conditional on stored Q2 OOF predictions",
        "seed": SEED,
        "bootstrap_replicates": B,
        "policy_groups": int(pd.Series(groups).nunique()),
        "train_cells": len(oof),
        "original_metrics": original,
        "bootstrap": {
            "delta_rmse_log_m2_minus_m1_ci95": rmse_ci,
            "delta_mae_log_m2_minus_m1_ci95": mae_ci,
            "m2_rmse_improvement_share": float(np.mean(boot["delta_rmse_log_m2_minus_m1"] < 0)),
            "m2_mae_improvement_share": float(np.mean(boot["delta_mae_log_m2_minus_m1"] < 0)),
            "relative_mae_improvement_ci95": percentile_ci(boot["relative_mae_improvement"].to_numpy()),
        },
        "interaction_sign_stability": sign_rows,
        "requested_gate_facts": gate,
        "coefficient_bootstrap_alpha": 0.1,
    }
    (Q2_METRICS / "q2_bootstrap_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    plot_q2(boot, signs)
    return summary


def q3_cell_errors(train: pd.DataFrame, q3_module) -> pd.DataFrame:
    view = pd.read_csv(ROOT / "data" / "processed" / "cycle_model_view.csv", low_memory=False)
    all_rows = []
    for k in q3_module.KS:
        features = pd.read_csv(ROOT / "data" / "processed" / f"early_features_k{k}.csv")
        d = train.merge(features[["barcode", *q3_module.COLS]], on="barcode", validate="one_to_one").reset_index(drop=True)
        X = d[q3_module.COLS].to_numpy(float)
        y = np.log(d["cycle_life_table9"].to_numpy(float))
        groups = d["policy_table9"].to_numpy()
        splitter = GroupKFold(n_splits=min(5, pd.Series(groups).nunique()))
        for fold, (tr, te) in enumerate(splitter.split(X, y, groups), start=1):
            alpha = q3_module.choose(X[tr], y[tr], groups[tr])
            fitted = q3_module.model(alpha).fit(X[tr], y[tr])
            predicted_log_life = fitted.predict(X[te])
            life_lookup = dict(zip(d.loc[tr, "barcode"], d.loc[tr, "cycle_life_table9"]))
            shape = q3_module.template(set(d.loc[tr, "barcode"]), life_lookup, view)
            for row_index, pred_log in zip(te, predicted_log_life):
                row = d.iloc[row_index]
                barcode = row["barcode"]
                actual_life = float(row["cycle_life_table9"])
                predicted_life = float(np.exp(pred_log))
                curve = view.loc[
                    (view["barcode"].eq(barcode)) & view["valid_QDischarge"].astype(bool),
                    ["global_cycle_index", "SOH_nom"],
                ]
                anchor = curve.loc[curve["global_cycle_index"].eq(k), "SOH_nom"]
                future = curve.loc[
                    (curve["global_cycle_index"].gt(k)) & (curve["global_cycle_index"].lt(actual_life))
                ]
                status = "success"
                if predicted_life <= k or anchor.empty or future.empty:
                    status = "prediction_or_curve_unavailable"
                else:
                    g_k = float(np.interp(k / predicted_life, q3_module.GRID, shape))
                    denominator = 0.8 - g_k
                    if abs(denominator) < 1e-6:
                        status = "anchor_denominator_near_zero"
                if status != "success":
                    all_rows.append(
                        {
                            "k": k,
                            "fold": fold,
                            "barcode": barcode,
                            "policy_table9": row["policy_table9"],
                            "cycle_life_table9": actual_life,
                            "pred_log_life": float(pred_log),
                            "pred_cycle_life": predicted_life,
                            "life_sq_error": float((pred_log - np.log(actual_life)) ** 2),
                            "life_abs_error": float(abs(pred_log - np.log(actual_life))),
                            "future_points": 0,
                            "soh_mse": np.nan,
                            "soh_mae": np.nan,
                            "soh_iae": np.nan,
                            "status": status,
                        }
                    )
                    continue
                q = (
                    np.interp(np.minimum(future["global_cycle_index"].to_numpy(float) / predicted_life, 1), q3_module.GRID, shape)
                    - g_k
                ) / denominator
                predicted_soh = float(anchor.iloc[0]) + (0.8 - float(anchor.iloc[0])) * q
                predicted_soh = np.where(future["global_cycle_index"].to_numpy(float) >= predicted_life, 0.8, predicted_soh)
                residual = predicted_soh - future["SOH_nom"].to_numpy(float)
                all_rows.append(
                    {
                        "k": k,
                        "fold": fold,
                        "barcode": barcode,
                        "policy_table9": row["policy_table9"],
                        "cycle_life_table9": actual_life,
                        "pred_log_life": float(pred_log),
                        "pred_cycle_life": predicted_life,
                        "life_sq_error": float((pred_log - np.log(actual_life)) ** 2),
                        "life_abs_error": float(abs(pred_log - np.log(actual_life))),
                        "future_points": int(len(residual)),
                        "soh_mse": float(np.mean(residual**2)),
                        "soh_mae": float(np.mean(np.abs(residual))),
                        "soh_iae": float(np.sum(np.abs(residual))),
                        "status": status,
                    }
                )
    table = pd.DataFrame(all_rows)
    table.to_csv(Q3_TABLES / "q3_cell_equal_oof_errors.csv", index=False, encoding="utf-8-sig")
    return table


def q3_metrics_from_cells(cells: pd.DataFrame) -> dict:
    successful = cells.loc[cells["status"].eq("success")]
    return {
        "cell_count": int(len(cells)),
        "successful_curve_cells": int(len(successful)),
        "template_failures": int((~cells["status"].eq("success")).sum()),
        "cell_equal_life_rmse_log": float(np.mean(cells["life_sq_error"]) ** 0.5),
        "cell_equal_life_mae_log": float(np.mean(cells["life_abs_error"])),
        "cell_equal_soh_rmse": float(np.mean(successful["soh_mse"]) ** 0.5),
        "cell_equal_soh_mae": float(np.mean(successful["soh_mae"])),
        "cell_equal_soh_iae": float(np.mean(successful["soh_iae"])),
        "future_point_count_median": float(successful["future_points"].median()),
    }


def q3_robustness(train: pd.DataFrame, q3_module) -> dict:
    cells = q3_cell_errors(train, q3_module)
    if not cells["barcode"].isin(train["barcode"]).all() or not cells["policy_table9"].isin(train["policy_table9"]).all():
        raise RuntimeError("A non-Train row reached Q3 robustness calculations.")
    view = pd.read_csv(ROOT / "data" / "processed" / "cycle_model_view.csv", low_memory=False)
    valid_soh_120 = view.loc[
        view["valid_QDischarge"].astype(bool) & view["global_cycle_index"].eq(120), "barcode"
    ]
    soh_120_cells = int(train["barcode"].isin(valid_soh_120).sum())
    soh_120_coverage = soh_120_cells / len(train)
    point_rows = []
    bootstrap_rows = []
    for k, cell_k in cells.groupby("k", sort=True):
        metric = q3_metrics_from_cells(cell_k)
        point_rows.append(
            {
                "k": int(k),
                **metric,
                "soh_nom_120_available_cells": soh_120_cells,
                "soh_nom_120_available_ratio": soh_120_coverage,
            }
        )
        groups = cell_k["policy_table9"].to_numpy()
        rng = np.random.default_rng(SEED + int(k))
        for replicate in range(1, B + 1):
            take = grouped_bootstrap_indices(groups, rng)
            sampled = cell_k.iloc[take]
            metrics = q3_metrics_from_cells(sampled)
            bootstrap_rows.append({"k": int(k), "replicate": replicate, **metrics})
    point = pd.DataFrame(point_rows).sort_values("k").reset_index(drop=True)
    boot = pd.DataFrame(bootstrap_rows)
    boot.to_csv(Q3_TABLES / "q3_policy_block_bootstrap.csv", index=False, encoding="utf-8-sig")

    summary_rows = []
    for item in point.itertuples(index=False):
        replicate = boot.loc[boot["k"].eq(item.k)]
        row = item._asdict()
        for metric_name in ("cell_equal_life_rmse_log", "cell_equal_life_mae_log", "cell_equal_soh_rmse", "cell_equal_soh_mae", "cell_equal_soh_iae"):
            low, high = percentile_ci(replicate[metric_name].to_numpy(float))
            row[f"{metric_name}_ci95_low"] = low
            row[f"{metric_name}_ci95_high"] = high
        summary_rows.append(row)
    summary = pd.DataFrame(summary_rows).sort_values("k").reset_index(drop=True)

    metric_columns = ["cell_equal_life_rmse_log", "cell_equal_soh_rmse"]
    dominated_by = []
    for index, row in summary.iterrows():
        dominators = []
        for other_index, other in summary.iterrows():
            if index == other_index:
                continue
            no_worse = (other["k"] <= row["k"]) and all(other[column] <= row[column] for column in metric_columns)
            strictly_better = (other["k"] < row["k"]) or any(other[column] < row[column] for column in metric_columns)
            if no_worse and strictly_better:
                dominators.append(int(other["k"]))
        dominated_by.append(",".join(str(x) for x in dominators) if dominators else "")
    summary["dominated_by_k"] = dominated_by
    summary["pareto_status"] = np.where(summary["dominated_by_k"].eq(""), "non_dominated", "dominated")

    best_life_index = summary["cell_equal_life_rmse_log"].idxmin()
    best_soh_index = summary["cell_equal_soh_rmse"].idxmin()
    life_upper = float(summary.loc[best_life_index, "cell_equal_life_rmse_log_ci95_high"])
    soh_upper = float(summary.loc[best_soh_index, "cell_equal_soh_rmse_ci95_high"])
    best_life_k = int(summary.loc[best_life_index, "k"])
    best_life_bootstrap_se = float(
        boot.loc[boot["k"].eq(best_life_k), "cell_equal_life_rmse_log"].std(ddof=1)
    )
    summary["within_best_life_upper_ci"] = summary["cell_equal_life_rmse_log"] <= life_upper
    summary["within_best_soh_upper_ci"] = summary["cell_equal_soh_rmse"] <= soh_upper
    summary["earliest_acceptable"] = (
        summary["pareto_status"].eq("non_dominated")
        & summary["within_best_life_upper_ci"]
        & summary["within_best_soh_upper_ci"]
        & summary["template_failures"].eq(0)
    )
    # The V2 plan separately prescribes a one-standard-error rule for the
    # eventual frozen Q3 cutoff.  Keep this diagnostic alongside the user's
    # requested bootstrap-upper-bound rule instead of silently replacing it.
    summary["within_plan_one_se_life"] = summary["cell_equal_life_rmse_log"] <= (
        float(summary.loc[best_life_index, "cell_equal_life_rmse_log"]) + best_life_bootstrap_se
    )
    summary["passes_v2_q3_window_prerequisites"] = (
        summary["template_failures"].eq(0)
        & summary["successful_curve_cells"].ge(0.9 * len(train))
        & summary["soh_nom_120_available_ratio"].ge(0.9)
    )
    eligible = summary.loc[summary["earliest_acceptable"]]
    earliest_k = int(eligible["k"].min()) if not eligible.empty else None
    lowest_error_k = int(summary.loc[best_life_index, "k"])
    summary.to_csv(Q3_TABLES / "q3_window_cell_equal_bootstrap_summary.csv", index=False, encoding="utf-8-sig")

    result = {
        "scope": "Train-only policy-block bootstrap of fold-specific OOF Q3 errors",
        "seed": SEED,
        "bootstrap_replicates_per_window": B,
        "train_cells": len(train),
        "policy_groups": int(train["policy_table9"].nunique()),
        "selection_rule": {
            "lowest_error_window": "minimum cell-equal life RMSE_log",
            "earliest_acceptable_window": "smallest non-dominated k whose cell-equal life and SOH RMSE do not exceed the respective 97.5% bootstrap bounds of the corresponding minimum-error windows",
            "life_rmse_upper_threshold": life_upper,
            "soh_rmse_upper_threshold": soh_upper,
            "v2_plan_one_standard_error_life_threshold": float(summary.loc[best_life_index, "cell_equal_life_rmse_log"]) + best_life_bootstrap_se,
            "v2_plan_one_standard_error_source": "bootstrap standard deviation of the minimum cell-equal life RMSE_log window",
        },
        "lowest_error_k": lowest_error_k,
        "earliest_acceptable_k": earliest_k,
        "v2_plan_one_standard_error_earliest_k": int(
            summary.loc[summary["within_plan_one_se_life"] & summary["passes_v2_q3_window_prerequisites"], "k"].min()
        ),
        "pareto_table": summary.to_dict(orient="records"),
    }
    (Q3_METRICS / "q3_bootstrap_summary.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    plot_q3(summary, life_upper, soh_upper)
    return result


def save_both(fig: plt.Figure, output_base: Path) -> None:
    fig.savefig(output_base.with_suffix(".svg"), bbox_inches="tight")
    fig.savefig(output_base.with_suffix(".png"), dpi=300, bbox_inches="tight")
    plt.close(fig)


def style_axis(axis: plt.Axes) -> None:
    axis.spines["right"].set_visible(False)
    axis.spines["top"].set_visible(False)
    axis.grid(axis="y", alpha=0.25, linestyle="--", linewidth=0.5)


def plot_q2(bootstrap: pd.DataFrame, signs: pd.DataFrame) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(11.2, 4.2), gridspec_kw={"width_ratios": [1.25, 1]})
    values = [bootstrap["delta_rmse_log_m2_minus_m1"], bootstrap["delta_mae_log_m2_minus_m1"]]
    axes[0].boxplot(values, tick_labels=["RMSE_log", "MAE_log"], showfliers=False, patch_artist=True, boxprops={"facecolor": "#5B9BD5"})
    axes[0].axhline(0, color="#4D4D4D", linestyle="--", linewidth=1, label="无差异")
    axes[0].set_title("Q2：M2 相对 M1 的策略组自助抽样差值")
    axes[0].set_xlabel("评价指标")
    axes[0].set_ylabel("M2−M1 误差差值（负值代表 M2 更优）")
    axes[0].legend()
    style_axis(axes[0])
    labels = ["C1×Q1", "C1×C2", "Q1×C2"]
    colors = ["#1A6FC4" if value >= 0.8 else "#E28E2C" for value in signs["sign_stability"]]
    bars = axes[1].bar(labels, signs["sign_stability"], color=colors)
    axes[1].axhline(0.8, color="#4D4D4D", linestyle="--", linewidth=1, label="80% 门槛")
    axes[1].set_ylim(0, 1.05)
    axes[1].set_title("Q2：二阶交互项的符号稳定率")
    axes[1].set_xlabel("二阶交互项")
    axes[1].set_ylabel("自助抽样中的主导符号占比")
    for bar, value in zip(bars, signs["sign_stability"]):
        axes[1].text(bar.get_x() + bar.get_width() / 2, value + 0.02, f"{value:.1%}", ha="center", va="bottom")
    axes[1].legend()
    style_axis(axes[1])
    fig.suptitle("诊断图（仅训练集；未作为论文图或最终模型结论）", fontsize=11)
    fig.tight_layout()
    save_both(fig, Q2_FIG / "q2_policy_block_bootstrap")


def plot_q3(summary: pd.DataFrame, life_upper: float, soh_upper: float) -> None:
    fig, axes = plt.subplots(1, 3, figsize=(16.0, 4.4))
    colors = np.where(summary["pareto_status"].eq("non_dominated"), "#1A6FC4", "#E53935")
    axes[0].errorbar(
        summary["k"], summary["cell_equal_life_rmse_log"],
        yerr=[
            summary["cell_equal_life_rmse_log"] - summary["cell_equal_life_rmse_log_ci95_low"],
            summary["cell_equal_life_rmse_log_ci95_high"] - summary["cell_equal_life_rmse_log"],
        ],
        marker="o", linewidth=1.8, capsize=3, color="#1A6FC4",
    )
    axes[0].set_title("Q3：电芯等权寿命误差")
    axes[0].set_xlabel("早期窗口截止循环 k（循环）")
    axes[0].set_ylabel("寿命 RMSE_log（95% 分位区间）")
    style_axis(axes[0])
    axes[1].errorbar(
        summary["k"], summary["cell_equal_soh_rmse"],
        yerr=[
            summary["cell_equal_soh_rmse"] - summary["cell_equal_soh_rmse_ci95_low"],
            summary["cell_equal_soh_rmse_ci95_high"] - summary["cell_equal_soh_rmse"],
        ],
        marker="o", linewidth=1.8, capsize=3, color="#E28E2C",
    )
    axes[1].set_title("Q3：电芯等权未来 SOH 误差")
    axes[1].set_xlabel("早期窗口截止循环 k（循环）")
    axes[1].set_ylabel("未来 SOH RMSE（95% 分位区间）")
    style_axis(axes[1])
    axes[2].scatter(summary["k"], summary["cell_equal_life_rmse_log"], s=110, c=colors, edgecolor="white", linewidth=0.8)
    for row in summary.itertuples(index=False):
        text = f"k={row.k}" + ("\n被支配" if row.pareto_status == "dominated" else "")
        axes[2].annotate(text, (row.k, row.cell_equal_life_rmse_log), xytext=(5, 5), textcoords="offset points", fontsize=8)
    axes[2].axhline(life_upper, color="#767676", linestyle="--", linewidth=1, label="最低寿命误差窗口的 95% 上界")
    axes[2].set_title("Q3：时效—寿命误差帕累托诊断")
    axes[2].set_xlabel("早期窗口截止循环 k（循环）")
    axes[2].set_ylabel("电芯等权寿命 RMSE_log")
    axes[2].legend(fontsize=8)
    style_axis(axes[2])
    fig.suptitle("诊断图（仅训练集；窗口结论待人工稳定性裁决）", fontsize=11)
    fig.tight_layout()
    save_both(fig, Q3_FIG / "q3_window_cell_equal_pareto")


def main() -> None:
    ensure_dirs()
    train = train_labels()
    q2_module = load_module("q2_round1", ROOT / "code" / "Q2" / "q2_run_all.py")
    q3_module = load_module("q3_round1", ROOT / "code" / "Q3" / "q3_run_all.py")
    q2 = q2_robustness(train, q2_module)
    q3 = q3_robustness(train, q3_module)
    common_summary = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "script": str(Path(__file__).relative_to(ROOT)).replace("\\", "/"),
        "script_sha256": sha256(Path(__file__)),
        "scope": "Train-only; Primary and Secondary are not used for fitting, resampling, selection, or scoring",
        "seed": SEED,
        "bootstrap_replicates": B,
    }
    q2_summary = {
        **common_summary,
        "question": "Q2",
        "input_sha256": {
            "cell_labels.csv": sha256(ROOT / "data" / "processed" / "cell_labels.csv"),
            "q2_run_all.py": sha256(ROOT / "code" / "Q2" / "q2_run_all.py"),
            "q2_m1_oof_predictions.csv": sha256(ROOT / "results" / "Q2" / "experiments" / "round1" / "tables" / "m1_oof_predictions.csv"),
            "q2_m2_oof_predictions.csv": sha256(ROOT / "results" / "Q2" / "experiments" / "round1" / "tables" / "m2_oof_predictions.csv"),
        },
        "result": q2,
    }
    q3_inputs = {
        "cell_labels.csv": sha256(ROOT / "data" / "processed" / "cell_labels.csv"),
        "cycle_model_view.csv": sha256(ROOT / "data" / "processed" / "cycle_model_view.csv"),
        "q3_run_all.py": sha256(ROOT / "code" / "Q3" / "q3_run_all.py"),
    }
    q3_inputs.update({
        f"early_features_k{k}.csv": sha256(ROOT / "data" / "processed" / f"early_features_k{k}.csv")
        for k in q3_module.KS
    })
    q3_summary = {
        **common_summary,
        "question": "Q3",
        "input_sha256": q3_inputs,
        "result": q3,
    }
    (Q2_OUT / "run_summary.json").write_text(json.dumps(q2_summary, ensure_ascii=False, indent=2), encoding="utf-8")
    (Q3_OUT / "run_summary.json").write_text(json.dumps(q3_summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"q2_gate_facts": q2["requested_gate_facts"], "q3": {"lowest_error_k": q3["lowest_error_k"], "earliest_acceptable_k": q3["earliest_acceptable_k"]}}, ensure_ascii=False))


if __name__ == "__main__":
    main()
