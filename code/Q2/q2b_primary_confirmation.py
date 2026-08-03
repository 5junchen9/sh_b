"""One-time Primary confirmation of the frozen Q2-B P3 lifetime proxy.

This script fits the already selected P3 additive GAM exactly once on Train and
evaluates the untouched Primary partition.  It deliberately has no tuning,
candidate comparison, early-cycle input, or feedback path from Primary to
model selection.
"""
from __future__ import annotations

import hashlib
import json
import os
import platform
import sys
from datetime import datetime, timezone
from pathlib import Path

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
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import SplineTransformer, StandardScaler


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "results" / "Q2" / "experiments" / "q2b_primary_confirmation_round1"
TABLES = OUT / "tables"
FIGURES = OUT / "figures"
METRICS = OUT / "metrics"
LOGS = OUT / "logs"
P0 = ROOT / "data" / "processed" / "p0_summary.json"
LABELS = ROOT / "data" / "processed" / "cell_labels.csv"
SELECTION = ROOT / "results" / "Q2" / "experiments" / "q2b_proxy_round1" / "metrics" / "q2b_proxy_selection.json"
TUNING = ROOT / "results" / "Q4" / "experiments" / "train_dry_run_round1" / "tables" / "q4_p3_full_train_tuning.csv"
PROTOCOL = ROOT / "methods" / "Q2" / "q2b_primary_confirmation_protocol.md"
SCRIPT = Path(__file__)
FEATURES = ["C1", "Q1_percent", "C2"]
TARGET = "cycle_life_table9"
TRAIN_PARTITION = "Train"
PRIMARY_PARTITION = "Prim. Test"
FROZEN_PARAMS = {"n_knots": 4, "alpha": 0.03}
SEED = 20260802


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


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


def plot_observed_vs_predicted(actual: np.ndarray, predicted: np.ndarray) -> None:
    low = float(min(actual.min(), predicted.min()))
    high = float(max(actual.max(), predicted.max()))
    margin = 0.05 * (high - low)
    fig, ax = plt.subplots(figsize=(6.5, 5.8))
    ax.scatter(actual, predicted, color="#2878B5", edgecolor="white", linewidth=0.6, s=54, label="主确认集电芯")
    ax.plot([low - margin, high + margin], [low - margin, high + margin], "--", color="#555555", label="理想预测线")
    ax.set_xlim(low - margin, high + margin)
    ax.set_ylim(low - margin, high + margin)
    ax.set_xlabel("实际循环寿命（循环）")
    ax.set_ylabel("P3 预测循环寿命（循环）")
    ax.set_title("Q2-B P3：主确认集一次受限确认（观察—预测）")
    ax.legend()
    ax.grid(alpha=0.2)
    fig.tight_layout()
    for suffix, kwargs in (("png", {"dpi": 300}), ("svg", {})):
        fig.savefig(FIGURES / f"q2b_primary_observed_vs_predicted.{suffix}", bbox_inches="tight", **kwargs)
    plt.close(fig)


def main() -> None:
    for directory in (TABLES, FIGURES, METRICS, LOGS):
        directory.mkdir(parents=True, exist_ok=True)

    p0 = json.loads(P0.read_text(encoding="utf-8"))
    if p0.get("p0_status") != "pass":
        raise RuntimeError("P0 is not passed; Primary confirmation is blocked.")
    selection = json.loads(SELECTION.read_text(encoding="utf-8"))
    if selection.get("final_selected_proxy") != "P3_additive_gam":
        raise RuntimeError("Frozen Train-only selection is not P3_additive_gam; Primary confirmation is blocked.")

    tuning = pd.read_csv(TUNING)
    frozen_json = json.dumps(FROZEN_PARAMS, ensure_ascii=False, sort_keys=True)
    if not tuning["params_json"].eq(frozen_json).any():
        raise RuntimeError("Frozen P3 parameters are absent from the recorded Train-only tuning table.")

    labels = pd.read_csv(LABELS)
    required = {"barcode", "dataset_table9", *FEATURES, TARGET}
    missing = sorted(required.difference(labels.columns))
    if missing:
        raise RuntimeError(f"Missing required label fields: {missing}")
    train = labels.loc[labels["dataset_table9"].eq(TRAIN_PARTITION)].copy()
    primary = labels.loc[labels["dataset_table9"].eq(PRIMARY_PARTITION)].copy()
    if len(train) != 41 or len(primary) != 43:
        raise RuntimeError(f"Unexpected frozen partition sizes: Train={len(train)}, Primary={len(primary)}")
    if train[FEATURES + [TARGET]].isna().any().any() or primary[FEATURES + [TARGET]].isna().any().any():
        raise RuntimeError("Missing feature or target values are not allowed in this confirmation.")
    if train["barcode"].duplicated().any() or primary["barcode"].duplicated().any():
        raise RuntimeError("Barcode must be unique within each frozen partition.")

    model = make_pipeline(
        SplineTransformer(n_knots=FROZEN_PARAMS["n_knots"], degree=2, include_bias=False, extrapolation="linear"),
        StandardScaler(),
        Ridge(alpha=FROZEN_PARAMS["alpha"]),
    )
    x_train = train[FEATURES].to_numpy(float)
    y_train = np.log(train[TARGET].to_numpy(float))
    x_primary = primary[FEATURES].to_numpy(float)
    y_primary = np.log(primary[TARGET].to_numpy(float))
    model.fit(x_train, y_train)
    predicted_log = model.predict(x_primary)
    metrics = metric_values(y_primary, predicted_log)

    predictions = primary[["barcode", "policy_table9", "C1", "Q1_percent", "C2", TARGET]].copy()
    predictions["actual_log_life"] = y_primary
    predictions["predicted_log_life"] = predicted_log
    predictions["predicted_cycle_life"] = np.exp(predicted_log)
    predictions["log_residual_pred_minus_actual"] = predicted_log - y_primary
    predictions["confirmation_role"] = "Primary_restricted_confirmation"
    predictions.to_csv(TABLES / "q2b_primary_predictions.csv", index=False, encoding="utf-8-sig")
    plot_observed_vs_predicted(predictions[TARGET].to_numpy(float), predictions["predicted_cycle_life"].to_numpy(float))

    metrics_payload = {
        "confirmation_status": "observed_not_adjudicated",
        "scope": "One-time frozen P3 confirmation on Primary; no tuning, replacement or threshold-based automatic pass/fail.",
        "method_id": "P3_additive_gam",
        "frozen_params": FROZEN_PARAMS,
        "feature_columns": FEATURES,
        "target_transform": "natural_log",
        "inverse_transform": "exp",
        "train_cells": int(len(train)),
        "primary_cells": int(len(primary)),
        "primary_policy_groups": int(primary["policy_table9"].nunique()),
        **metrics,
    }
    (METRICS / "q2b_primary_metrics.json").write_text(json.dumps(metrics_payload, ensure_ascii=False, indent=2), encoding="utf-8")

    report = f"""# Q2-B P3 Primary 一次受限确认\n\n> 状态：**observed_not_adjudicated**。本报告只给出冻结模型的确认观察，不自动决定通过、换模型或写入最终 Q4。\n\n- 训练：41 枚 Train 电芯；确认：43 枚 Primary 电芯。\n- 冻结模型：P3 低自由度加性 GAM，`n_knots=4`、`alpha=0.03`。\n- 特征：`C1`、`Q1_percent`、`C2`；目标：`ln(cycle_life_table9)`。\n- 禁止：不重调参数、不比较 C1、不读取早期循环特征、不用 Primary 结果反向修改模型。\n\n| 指标 | Primary 结果 |\n|---|---:|\n| RMSE_log（ln 尺度） | {metrics['rmse_log']:.6f} |\n| MAE_log（ln 尺度） | {metrics['mae_log']:.6f} |\n| RMSE_cycle | {metrics['rmse_cycle']:.2f} |\n| MAE_cycle | {metrics['mae_cycle']:.2f} |\n| 过预测比例 | {metrics['overprediction_rate']:.2%} |\n| 平均正向 ln 误差 | {metrics['mean_positive_log_error']:.6f} |\n| 平均正向 cycle 误差 | {metrics['mean_positive_cycle_error']:.2f} |\n\n图 `figures/q2b_primary_observed_vs_predicted.png` 为中文观察—预测图；逐电芯结果见 `tables/q2b_primary_predictions.csv`。\n\n限制：Primary 已有探索暴露，因此只能称受限确认；Secondary 才是最终压力测试集。本次没有预注册自动通过阈值，结果置信与论文主张范围仍由建模者在 Gate G4.5 记录。\n"""
    (OUT / "q2b_primary_confirmation_report.md").write_text(report, encoding="utf-8")

    summary = {
        "question": "Q2-B",
        "round": "q2b_primary_confirmation_round1",
        "execution_timestamp": datetime.now(timezone.utc).isoformat(),
        "implementation_target": "python",
        "random_seed": SEED,
        "scope": metrics_payload["scope"],
        "frozen_selection": {"method_id": "P3_additive_gam", "params": FROZEN_PARAMS, "features": FEATURES},
        "partitions": {"train": TRAIN_PARTITION, "primary": PRIMARY_PARTITION, "train_cells": len(train), "primary_cells": len(primary)},
        "target_transform": "natural_log",
        "inverse_transform": "exp",
        "metrics": metrics,
        "input_sha256": {
            "p0_summary.json": sha256(P0),
            "cell_labels.csv": sha256(LABELS),
            "q2b_proxy_selection.json": sha256(SELECTION),
            "q4_p3_full_train_tuning.csv": sha256(TUNING),
            "q2b_primary_confirmation_protocol.md": sha256(PROTOCOL),
        },
        "script_sha256": sha256(SCRIPT),
        "environment": {"python": sys.version, "platform": platform.platform(), "scikit_learn": sklearn.__version__},
        "outputs": [
            "tables/q2b_primary_predictions.csv",
            "metrics/q2b_primary_metrics.json",
            "figures/q2b_primary_observed_vs_predicted.png",
            "figures/q2b_primary_observed_vs_predicted.svg",
            "q2b_primary_confirmation_report.md",
        ],
    }
    text = json.dumps(summary, ensure_ascii=False, indent=2)
    (OUT / "run_summary.json").write_text(text, encoding="utf-8")
    (LOGS / "run.log").write_text(text + "\n", encoding="utf-8")
    print(json.dumps({"metrics": metrics, "status": metrics_payload["confirmation_status"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
