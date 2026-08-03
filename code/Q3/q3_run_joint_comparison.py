"""Q3 Round 2: strict Train-only comparison of strategy, early, joint and residual models.

Round 1 intentionally remains untouched as a historical early-feature diagnostic.  This
script implements the V2.1 M1--M4 comparison.  In particular, M4 creates its P3
strategy prior anew inside every outer fold and cross-fits it on the outer-training
cells before learning an early-feature residual; this avoids reuse of a whole-Train
prior for a validation cell.
"""
from __future__ import annotations

import hashlib
import json
import platform
import sys
from datetime import datetime, timezone
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
matplotlib.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["Microsoft YaHei", "SimHei", "DejaVu Sans"],
    "axes.unicode_minus": False,
    "svg.fonttype": "none",
})
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import sklearn
from sklearn.impute import SimpleImputer
from sklearn.isotonic import IsotonicRegression
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error
from sklearn.model_selection import GroupKFold
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import SplineTransformer, StandardScaler


SCRIPT = Path(__file__).resolve()
ROOT = SCRIPT.parents[2]
OUT = ROOT / "results" / "Q3" / "experiments" / "round2_joint"
TABLES, FIGURES, METRICS, LOGS = (OUT / item for item in ("tables", "figures", "metrics", "logs"))
SEED = 20260802
KS = [5, 10, 20, 50, 100]
RIDGE_ALPHAS = [0.01, 0.1, 1.0, 3.0, 10.0, 30.0, 100.0]
GRID = np.linspace(0.001, 1.0, 1000)
STRATEGY_COLS = ["C1", "Q1_percent", "C2"]
EARLY_COLS = [
    "QDischarge_mean", "QDischarge_slope", "QDischarge_delta_cycle2_to_k",
    "QCharge_mean", "QCharge_slope", "IR_mean", "IR_slope", "Tmax_mean",
    "Tavg_mean", "Tmin_mean", "chargetime_mean", "chargetime_slope",
]
METHODS = {
    "M1": "策略参数 Ridge（设计前基线）",
    "M2": "早期运行特征 Ridge（运行后基线）",
    "M3": "策略＋早期特征联合 Ridge",
    "M4": "P3 策略先验＋早期残差 Ridge",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def valid_mask(series: pd.Series) -> pd.Series:
    if pd.api.types.is_bool_dtype(series):
        return series.fillna(False)
    return series.astype(str).str.strip().str.lower().isin(["true", "1"])


def n_splits(groups: np.ndarray, maximum: int) -> int:
    count = pd.Series(groups).nunique()
    if count < 2:
        raise RuntimeError("策略组不足两个，无法进行无泄漏分组验证。")
    return min(maximum, count)


def ridge(alpha: float):
    return make_pipeline(SimpleImputer(strategy="median"), StandardScaler(), Ridge(alpha=alpha))


def p3_gam():
    """Frozen Q2 P3 proxy: quadratic B-spline strategy surface plus fixed ridge."""
    return make_pipeline(
        SplineTransformer(n_knots=4, degree=2, include_bias=False, extrapolation="linear"),
        StandardScaler(),
        Ridge(alpha=0.03),
    )


def choose_ridge_alpha(x: np.ndarray, y: np.ndarray, groups: np.ndarray) -> float:
    cv = GroupKFold(n_splits=n_splits(groups, 4))
    scores: list[float] = []
    for alpha in RIDGE_ALPHAS:
        fold_mse = []
        for train_idx, valid_idx in cv.split(x, y, groups):
            fitted = ridge(alpha).fit(x[train_idx], y[train_idx])
            fold_mse.append(mean_squared_error(y[valid_idx], fitted.predict(x[valid_idx])))
        scores.append(float(np.mean(fold_mse)))
    return float(RIDGE_ALPHAS[int(np.argmin(scores))])


def build_template(train_barcodes: list[str], train_life: dict[str, float], view: pd.DataFrame) -> np.ndarray:
    rows = []
    for barcode in train_barcodes:
        curve = view.loc[
            view.barcode.eq(barcode) & valid_mask(view.valid_QDischarge),
            ["global_cycle_index", "SOH_nom"],
        ]
        u = curve.global_cycle_index.to_numpy(float) / train_life[barcode]
        if len(u) < 10:
            continue
        aligned = np.full(len(GRID), np.nan)
        support = (GRID >= u.min()) & (GRID <= u.max())
        aligned[support] = np.interp(GRID[support], u, curve.SOH_nom.to_numpy(float))
        rows.append(aligned)
    if not rows:
        raise RuntimeError("外层训练集中没有至少含十个有效放电容量点的 SOH 曲线。")
    matrix = np.vstack(rows)
    support = np.sum(np.isfinite(matrix), axis=0) >= 5
    if not support.any():
        raise RuntimeError("外层训练 SOH 模板支持电芯少于五枚。")
    x = np.r_[GRID[support], 1.0]
    y = np.r_[np.nanmedian(matrix[:, support], axis=0), 0.8]
    iso = IsotonicRegression(increasing=False, out_of_bounds="clip").fit(x, y)
    return iso.predict(GRID)


def predict_soh(anchor: float, k: int, predicted_life: float, template: np.ndarray, cycle: float) -> float | None:
    gk = np.interp(k / predicted_life, GRID, template)
    denominator = 0.8 - gk
    if abs(denominator) < 1e-6:
        return None
    shape = (np.interp(min(cycle / predicted_life, 1.0), GRID, template) - gk) / denominator
    value = float(anchor) + (0.8 - float(anchor)) * shape
    return 0.8 if cycle >= predicted_life else float(value)


def curve_residual(
    barcode: str, k: int, predicted_life: float, actual_life: float, template: np.ndarray, view: pd.DataFrame
) -> tuple[np.ndarray | None, float | None, str | None]:
    if predicted_life <= k:
        return None, None, "predicted_life_not_after_k"
    curve = view.loc[
        view.barcode.eq(barcode) & valid_mask(view.valid_QDischarge),
        ["global_cycle_index", "SOH_nom"],
    ]
    anchors = curve.loc[curve.global_cycle_index.eq(k), "SOH_nom"]
    future = curve.loc[
        curve.global_cycle_index.gt(k) & curve.global_cycle_index.lt(actual_life),
        ["global_cycle_index", "SOH_nom"],
    ]
    if anchors.empty:
        return None, None, "missing_anchor"
    if future.empty:
        return None, None, "no_future_observation"
    gk = np.interp(k / predicted_life, GRID, template)
    denominator = 0.8 - gk
    if abs(denominator) < 1e-6:
        return None, None, "template_anchor_denominator"
    u = np.minimum(future.global_cycle_index.to_numpy(float) / predicted_life, 1.0)
    shape = (np.interp(u, GRID, template) - gk) / denominator
    prediction = float(anchors.iloc[0]) + (0.8 - float(anchors.iloc[0])) * shape
    prediction = np.where(future.global_cycle_index.to_numpy(float) >= predicted_life, 0.8, prediction)
    soh120 = predict_soh(float(anchors.iloc[0]), k, predicted_life, template, 120.0) if k < 120 else None
    return prediction - future.SOH_nom.to_numpy(float), soh120, None


def crossfit_p3_prior(x_strategy: np.ndarray, y: np.ndarray, groups: np.ndarray) -> np.ndarray:
    """Create P3 priors for outer-training targets without fitting their own groups."""
    prior = np.full(len(y), np.nan)
    inner = GroupKFold(n_splits=n_splits(groups, 4))
    for fit_idx, held_idx in inner.split(x_strategy, y, groups):
        prior[held_idx] = p3_gam().fit(x_strategy[fit_idx], y[fit_idx]).predict(x_strategy[held_idx])
    if np.isnan(prior).any():
        raise RuntimeError("P3 内层交叉拟合未覆盖所有外层训练电芯。")
    return prior


def outer_predictions(
    method_id: str,
    train_x_strategy: np.ndarray,
    train_x_early: np.ndarray,
    test_x_strategy: np.ndarray,
    test_x_early: np.ndarray,
    y_train: np.ndarray,
    groups_train: np.ndarray,
) -> tuple[np.ndarray, float, dict[str, float]]:
    """Fit one method inside a single outer fold and return outer-test log-life predictions."""
    if method_id == "M1":
        alpha = choose_ridge_alpha(train_x_strategy, y_train, groups_train)
        return ridge(alpha).fit(train_x_strategy, y_train).predict(test_x_strategy), alpha, {}
    if method_id == "M2":
        alpha = choose_ridge_alpha(train_x_early, y_train, groups_train)
        return ridge(alpha).fit(train_x_early, y_train).predict(test_x_early), alpha, {}
    if method_id == "M3":
        x_train = np.c_[train_x_strategy, train_x_early]
        x_test = np.c_[test_x_strategy, test_x_early]
        alpha = choose_ridge_alpha(x_train, y_train, groups_train)
        return ridge(alpha).fit(x_train, y_train).predict(x_test), alpha, {}
    if method_id == "M4":
        prior_train = crossfit_p3_prior(train_x_strategy, y_train, groups_train)
        residual = y_train - prior_train
        alpha = choose_ridge_alpha(train_x_early, residual, groups_train)
        residual_model = ridge(alpha).fit(train_x_early, residual)
        prior_test = p3_gam().fit(train_x_strategy, y_train).predict(test_x_strategy)
        return prior_test + residual_model.predict(test_x_early), alpha, {"p3_alpha": 0.03}
    raise ValueError(f"Unknown method: {method_id}")


def life_metrics(actual_log: np.ndarray, predicted_log: np.ndarray) -> dict[str, float]:
    actual = np.exp(actual_log)
    predicted = np.exp(predicted_log)
    return {
        "rmse_log": float(mean_squared_error(actual_log, predicted_log) ** 0.5),
        "mae_log": float(mean_absolute_error(actual_log, predicted_log)),
        "rmse_cycle": float(mean_squared_error(actual, predicted) ** 0.5),
        "mae_cycle": float(mean_absolute_error(actual, predicted)),
        "overprediction_rate": float(np.mean(predicted_log > actual_log)),
    }


def draw_figure(metrics: pd.DataFrame) -> None:
    colors = {"M1": "#4C78A8", "M2": "#F58518", "M3": "#54A24B", "M4": "#B279A2"}
    fig, axes = plt.subplots(1, 2, figsize=(12.2, 4.6))
    for method_id, block in metrics.groupby("model_id", sort=False):
        axes[0].plot(block.k, block.rmse_log, marker="o", linewidth=2.1, color=colors[method_id], label=method_id)
        axes[1].plot(block.k, block.cell_equal_soh_rmse, marker="s", linewidth=2.1, color=colors[method_id], label=method_id)
    axes[0].set(title="(a) 寿命预测：策略分组折外误差", xlabel="早期窗口截止循环 k（循环）", ylabel="寿命 RMSE（ln 尺度）")
    axes[1].set(title="(b) 未来 SOH：逐电芯等权误差", xlabel="早期窗口截止循环 k（循环）", ylabel="SOH 均方根误差")
    for axis in axes:
        axis.grid(alpha=0.22)
        axis.legend(title="模型")
    fig.suptitle("Q3 第二轮：策略、早期运行与残差校正的严格仅训练集比较", y=1.03, fontsize=13)
    fig.tight_layout()
    for extension, kwargs in (("png", {"dpi": 300}), ("svg", {})):
        fig.savefig(FIGURES / f"q3_joint_window_comparison.{extension}", bbox_inches="tight", **kwargs)
    plt.close(fig)


def main() -> None:
    for directory in (TABLES, FIGURES, METRICS, LOGS):
        directory.mkdir(parents=True, exist_ok=True)
    p0_path = ROOT / "data" / "processed" / "p0_summary.json"
    labels_path = ROOT / "data" / "processed" / "cell_labels.csv"
    view_path = ROOT / "data" / "processed" / "cycle_model_view.csv"
    p0 = json.loads(p0_path.read_text(encoding="utf-8"))
    if p0.get("p0_status") != "pass":
        raise RuntimeError("P0 未通过，Q3 Round 2 被阻止。")
    labels = pd.read_csv(labels_path)
    view = pd.read_csv(view_path, low_memory=False)
    train_labels = labels.loc[labels.dataset_table9.eq("Train")].copy().reset_index(drop=True)
    if len(train_labels) != 41 or train_labels.barcode.duplicated().any():
        raise RuntimeError("冻结 Train 划分必须是 41 个唯一条码。")
    if set(STRATEGY_COLS).difference(train_labels.columns):
        raise RuntimeError("cell_labels 缺少冻结的策略参数列。")

    metric_rows: list[dict] = []
    life_rows: list[dict] = []
    curve_rows: list[dict] = []
    soh120_rows: list[dict] = []
    tuning_rows: list[dict] = []

    for k in KS:
        feature_path = ROOT / "data" / "processed" / f"early_features_k{k}.csv"
        feature = pd.read_csv(feature_path)
        needed = {"barcode", *EARLY_COLS}
        if needed.difference(feature.columns):
            raise RuntimeError(f"k={k} 的早期特征列不完整。")
        data = train_labels.merge(feature[["barcode", *EARLY_COLS]], on="barcode", validate="one_to_one")
        if len(data) != 41:
            raise RuntimeError(f"k={k} 合并早期特征后 Train 电芯数发生变化。")
        y = np.log(data.cycle_life_table9.to_numpy(float))
        groups = data.policy_table9.to_numpy()
        x_strategy = data[STRATEGY_COLS].to_numpy(float)
        x_early = data[EARLY_COLS].to_numpy(float)
        splits = list(GroupKFold(n_splits=n_splits(groups, 5)).split(x_strategy, y, groups))

        for method_id in METHODS:
            prediction = np.full(len(data), np.nan)
            outer_fold = np.full(len(data), -1, dtype=int)
            curve_mse: list[float] = []
            pooled_residuals: list[float] = []
            failures = {name: 0 for name in ("predicted_life_not_after_k", "missing_anchor", "no_future_observation", "template_anchor_denominator")}
            for fold, (fit_idx, held_idx) in enumerate(splits, start=1):
                fit_groups, held_groups = set(groups[fit_idx]), set(groups[held_idx])
                if fit_groups.intersection(held_groups):
                    raise RuntimeError("外层策略组泄漏。")
                test_prediction, alpha, extras = outer_predictions(
                    method_id,
                    x_strategy[fit_idx], x_early[fit_idx], x_strategy[held_idx], x_early[held_idx], y[fit_idx], groups[fit_idx],
                )
                prediction[held_idx] = test_prediction
                outer_fold[held_idx] = fold
                tuning_rows.append({
                    "model_id": method_id, "model_name": METHODS[method_id], "k": k, "outer_fold": fold,
                    "alpha": alpha, "train_cells": int(len(fit_idx)), "train_policy_groups": int(pd.Series(groups[fit_idx]).nunique()), **extras,
                })
                template = build_template(
                    data.barcode.iloc[fit_idx].tolist(),
                    dict(zip(data.barcode.iloc[fit_idx], data.cycle_life_table9.iloc[fit_idx].astype(float))),
                    view,
                )
                for row_idx in held_idx:
                    row = data.iloc[row_idx]
                    predicted_life = float(np.exp(prediction[row_idx]))
                    residual, predicted_soh120, reason = curve_residual(
                        row.barcode, k, predicted_life, float(row.cycle_life_table9), template, view,
                    )
                    life_rows.append({
                        "model_id": method_id, "model_name": METHODS[method_id], "barcode": row.barcode,
                        "policy_table9": row.policy_table9, "k": k, "outer_fold": fold,
                        "cycle_life_table9": float(row.cycle_life_table9), "actual_log_life": float(y[row_idx]),
                        "predicted_log_life": float(prediction[row_idx]), "predicted_cycle_life": predicted_life,
                        "prediction_role": "outer_fold_train_only",
                    })
                    if reason is not None:
                        failures[reason] += 1
                        continue
                    assert residual is not None
                    mse = float(np.mean(np.square(residual)))
                    curve_mse.append(mse)
                    pooled_residuals.extend(residual.tolist())
                    curve_rows.append({
                        "model_id": method_id, "model_name": METHODS[method_id], "barcode": row.barcode,
                        "policy_table9": row.policy_table9, "k": k, "outer_fold": fold,
                        "future_point_count": int(len(residual)), "soh_mse": mse,
                        "soh_rmse": float(mse ** 0.5), "soh_mae": float(np.mean(np.abs(residual))),
                    })
                    if predicted_soh120 is not None:
                        actual120 = view.loc[
                            view.barcode.eq(row.barcode) & valid_mask(view.valid_QDischarge) & view.global_cycle_index.eq(120),
                            "SOH_nom",
                        ]
                        soh120_rows.append({
                            "model_id": method_id, "model_name": METHODS[method_id], "barcode": row.barcode,
                            "policy_table9": row.policy_table9, "k": k, "outer_fold": fold,
                            "predicted_cycle_life": predicted_life, "predicted_soh_nom_120": predicted_soh120,
                            "actual_soh_nom_120": float(actual120.iloc[0]) if not actual120.empty else np.nan,
                            "prediction_role": "outer_fold_train_only",
                        })
            if np.isnan(prediction).any() or (outer_fold < 1).any():
                raise RuntimeError(f"{method_id} k={k} 未覆盖全部 Train 电芯。")
            if not curve_mse:
                raise RuntimeError(f"{method_id} k={k} 没有可评价的未来 SOH 曲线。")
            metric_rows.append({
                "model_id": method_id, "model_name": METHODS[method_id], "k": k,
                **life_metrics(y, prediction),
                "cell_equal_soh_rmse": float(np.mean(curve_mse) ** 0.5),
                "future_point_pooled_soh_rmse": float(np.mean(np.square(pooled_residuals)) ** 0.5),
                "curve_cells": len(curve_mse), "template_failures": int(sum(failures.values())),
                **{f"failure_{key}": value for key, value in failures.items()},
            })

    metrics = pd.DataFrame(metric_rows)
    metrics.to_csv(TABLES / "joint_window_metrics.csv", index=False, encoding="utf-8-sig")
    pd.DataFrame(life_rows).to_csv(TABLES / "joint_oof_life_predictions.csv", index=False, encoding="utf-8-sig")
    pd.DataFrame(curve_rows).to_csv(TABLES / "joint_cell_curve_errors.csv", index=False, encoding="utf-8-sig")
    pd.DataFrame(soh120_rows).to_csv(TABLES / "joint_oof_soh120_predictions.csv", index=False, encoding="utf-8-sig")
    pd.DataFrame(tuning_rows).to_csv(TABLES / "joint_tuning.csv", index=False, encoding="utf-8-sig")
    draw_figure(metrics)
    inputs = {
        "p0_summary.json": sha256(p0_path), "cell_labels.csv": sha256(labels_path), "cycle_model_view.csv": sha256(view_path),
        **{f"early_features_k{k}.csv": sha256(ROOT / "data" / "processed" / f"early_features_k{k}.csv") for k in KS},
    }
    summary = {
        "question": "Q3", "round": "round2_joint", "execution_timestamp": datetime.now(timezone.utc).isoformat(),
        "implementation_target": "python", "random_seed": SEED, "target_transform": "natural_log", "inverse_transform": "exp",
        "scope": "Train-only strict candidate comparison; Primary and Secondary are not read.",
        "validation": {
            "outer": "up to 5-fold GroupKFold by policy_table9", "inner": "up to 4-fold GroupKFold by policy_table9",
            "M4_prior": "P3 strategy prior cross-fitted anew within each Q3 outer-training fold", "soh_template": "outer-training cells only",
        },
        "methods": [{"method_id": key, "method_name": value, "status": "success"} for key, value in METHODS.items()],
        "metric_definitions": {
            "rmse_log": "ln(cycle_life_table9) 的折外 RMSE", "cell_equal_soh_rmse": "逐电芯未来 SOH MSE 等权平均后开方，为正式 SOH 指标",
            "future_point_pooled_soh_rmse": "合并观测点诊断指标，不能替代电芯等权指标",
        },
        "metrics": metric_rows, "input_sha256": inputs, "script_sha256": sha256(SCRIPT),
        "environment": {"python": sys.version, "platform": platform.platform(), "scikit_learn": sklearn.__version__},
        "warnings": ["Round 2 是 Train-only 比较，不自动锁定模型或窗口；Round 1 早期特征输出不再代表 V2.1 的联合模型。"],
    }
    payload = json.dumps(summary, ensure_ascii=False, indent=2)
    (METRICS / "q3_joint_metrics.json").write_text(payload, encoding="utf-8")
    (OUT / "run_summary.json").write_text(payload, encoding="utf-8")
    (LOGS / "run.log").write_text(payload + "\n", encoding="utf-8")
    print(metrics[["model_id", "k", "rmse_log", "mae_log", "cell_equal_soh_rmse", "template_failures"]].to_string(index=False))


if __name__ == "__main__":
    main()
