"""Q3 Round 3: low-dimensional RAW voltage-curve challenger against Round 2 M3.

Only Train rows are used.  The three RAW features were extracted from charge points
of MAT cycles that passed the six-field audit; unusable cycles remain excluded by a
field-cycle mask.  This is a challenger, not an automatic model replacement.
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
matplotlib.rcParams.update({"font.family": "sans-serif", "font.sans-serif": ["Microsoft YaHei", "SimHei", "DejaVu Sans"], "axes.unicode_minus": False, "svg.fonttype": "none"})
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import sklearn
from sklearn.metrics import mean_absolute_error, mean_squared_error
from sklearn.model_selection import GroupKFold

from q3_run_joint_comparison import (
    EARLY_COLS, STRATEGY_COLS, build_template, choose_ridge_alpha, curve_residual,
    life_metrics, n_splits, ridge,
)

SCRIPT = Path(__file__).resolve()
ROOT = SCRIPT.parents[2]
OUT = ROOT / "results" / "Q3" / "experiments" / "round3_raw_curve_challenger"
TABLES, FIGURES, METRICS, LOGS = (OUT / item for item in ("tables", "figures", "metrics", "logs"))
KS = [5, 10, 20, 50, 100]
RAW_COLS = ["raw_charge_v_mean_mean", "raw_charge_v_p95_mean", "raw_charge_v_p95_slope"]
SEED = 20260802


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def plot(metrics: pd.DataFrame, m3: pd.DataFrame) -> None:
    baseline = m3.loc[m3.model_id.eq("M3"), ["k", "rmse_log", "cell_equal_soh_rmse"]].copy()
    fig, axes = plt.subplots(1, 2, figsize=(11.5, 4.4))
    axes[0].plot(baseline.k, baseline.rmse_log, "o-", color="#54A24B", linewidth=2, label="M3：策略＋早期")
    axes[0].plot(metrics.k, metrics.rmse_log, "s-", color="#B279A2", linewidth=2, label="M3R：M3＋原始电压")
    axes[1].plot(baseline.k, baseline.cell_equal_soh_rmse, "o-", color="#54A24B", linewidth=2, label="M3：策略＋早期")
    axes[1].plot(metrics.k, metrics.cell_equal_soh_rmse, "s-", color="#B279A2", linewidth=2, label="M3R：M3＋原始电压")
    axes[0].set(title="(a) 寿命折外误差", xlabel="早期窗口截止循环 k（循环）", ylabel="寿命 RMSE（ln 尺度）")
    axes[1].set(title="(b) 未来 SOH 逐电芯等权误差", xlabel="早期窗口截止循环 k（循环）", ylabel="SOH 均方根误差")
    for axis in axes:
        axis.grid(alpha=.22); axis.legend()
    fig.suptitle("Q3 第三轮：低维原始电压曲线候选模型（严格仅训练集）", y=1.03, fontsize=13)
    fig.tight_layout()
    for ext, kwargs in (("png", {"dpi":300}), ("svg", {})):
        fig.savefig(FIGURES / f"q3_raw_curve_challenger.{ext}", bbox_inches="tight", **kwargs)
    plt.close(fig)


def main() -> None:
    for directory in (TABLES, FIGURES, METRICS, LOGS):
        directory.mkdir(parents=True, exist_ok=True)
    p0 = json.loads((ROOT / "data" / "processed" / "p0_summary.json").read_text(encoding="utf-8"))
    if p0.get("p0_status") != "pass":
        raise RuntimeError("P0 未通过，RAW challenger 被阻止。")
    labels = pd.read_csv(ROOT / "data" / "processed" / "cell_labels.csv")
    view = pd.read_csv(ROOT / "data" / "processed" / "cycle_model_view.csv", low_memory=False)
    train = labels.loc[labels.dataset_table9.eq("Train")].copy().reset_index(drop=True)
    if len(train) != 41 or train.barcode.duplicated().any():
        raise RuntimeError("RAW challenger 需要 41 枚唯一 Train 电芯。")

    metric_rows, life_rows, curve_rows, tuning_rows = [], [], [], []
    for k in KS:
        early = pd.read_csv(ROOT / "data" / "processed" / f"early_features_k{k}.csv")
        raw = pd.read_csv(ROOT / "data" / "processed" / f"raw_curve_features_train_k{k}.csv")
        if set(["barcode", *EARLY_COLS]).difference(early.columns) or set(["barcode", *RAW_COLS]).difference(raw.columns):
            raise RuntimeError(f"k={k} 缺少已冻结早期或 RAW 特征。")
        data = train.merge(early[["barcode", *EARLY_COLS]], on="barcode", validate="one_to_one").merge(raw[["barcode", *RAW_COLS, "raw_valid_ratio"]], on="barcode", validate="one_to_one")
        if len(data) != 41 or (data.raw_valid_ratio < .8).any():
            raise RuntimeError(f"k={k} 的 RAW 特征合并或可用率门禁失败。")
        y = np.log(data.cycle_life_table9.to_numpy(float)); groups = data.policy_table9.to_numpy()
        x = data[[*STRATEGY_COLS, *EARLY_COLS, *RAW_COLS]].to_numpy(float)
        prediction = np.full(len(data), np.nan); outer_fold = np.full(len(data), -1, dtype=int)
        curve_mse, pooled = [], []
        failures = {name: 0 for name in ("predicted_life_not_after_k", "missing_anchor", "no_future_observation", "template_anchor_denominator")}
        for fold, (fit, held) in enumerate(GroupKFold(n_splits=n_splits(groups, 5)).split(x, y, groups), 1):
            if set(groups[fit]).intersection(set(groups[held])):
                raise RuntimeError("RAW challenger 外层策略组泄漏。")
            alpha = choose_ridge_alpha(x[fit], y[fit], groups[fit])
            prediction[held] = ridge(alpha).fit(x[fit], y[fit]).predict(x[held]); outer_fold[held] = fold
            tuning_rows.append({"model_id":"M3R", "k":k, "outer_fold":fold, "alpha":alpha, "train_cells":len(fit), "train_policy_groups":int(pd.Series(groups[fit]).nunique())})
            template = build_template(data.barcode.iloc[fit].tolist(), dict(zip(data.barcode.iloc[fit], data.cycle_life_table9.iloc[fit].astype(float))), view)
            for idx in held:
                row = data.iloc[idx]; predicted_life = float(np.exp(prediction[idx]))
                residual, _, reason = curve_residual(row.barcode, k, predicted_life, float(row.cycle_life_table9), template, view)
                life_rows.append({"model_id":"M3R", "barcode":row.barcode, "policy_table9":row.policy_table9, "k":k, "outer_fold":fold, "actual_log_life":float(y[idx]), "predicted_log_life":float(prediction[idx]), "predicted_cycle_life":predicted_life, "prediction_role":"outer_fold_train_only"})
                if reason is not None:
                    failures[reason] += 1; continue
                assert residual is not None
                mse = float(np.mean(residual ** 2)); curve_mse.append(mse); pooled.extend(residual.tolist())
                curve_rows.append({"model_id":"M3R", "barcode":row.barcode, "policy_table9":row.policy_table9, "k":k, "outer_fold":fold, "future_point_count":len(residual), "soh_mse":mse, "soh_rmse":float(mse**.5), "soh_mae":float(np.mean(abs(residual)))})
        if np.isnan(prediction).any() or not curve_mse:
            raise RuntimeError(f"M3R k={k} 未产生完整、可评价预测。")
        metric_rows.append({"model_id":"M3R", "model_name":"策略＋早期＋低维RAW电压 Ridge", "k":k, **life_metrics(y,prediction), "cell_equal_soh_rmse":float(np.mean(curve_mse)**.5), "future_point_pooled_soh_rmse":float(np.mean(np.square(pooled))**.5), "curve_cells":len(curve_mse), "template_failures":sum(failures.values()), **{f"failure_{name}":value for name,value in failures.items()}})
    metrics = pd.DataFrame(metric_rows); metrics.to_csv(TABLES / "m3r_raw_curve_window_metrics.csv", index=False, encoding="utf-8-sig")
    pd.DataFrame(life_rows).to_csv(TABLES / "m3r_raw_curve_oof_life_predictions.csv", index=False, encoding="utf-8-sig")
    pd.DataFrame(curve_rows).to_csv(TABLES / "m3r_raw_curve_cell_curve_errors.csv", index=False, encoding="utf-8-sig")
    pd.DataFrame(tuning_rows).to_csv(TABLES / "m3r_raw_curve_tuning.csv", index=False, encoding="utf-8-sig")
    m3 = pd.read_csv(ROOT / "results" / "Q3" / "experiments" / "round2_joint" / "tables" / "joint_window_metrics.csv")
    compare = m3.loc[m3.model_id.eq("M3"), ["k","rmse_log","mae_log","cell_equal_soh_rmse"]].merge(metrics[["k","rmse_log","mae_log","cell_equal_soh_rmse"]], on="k", suffixes=("_m3", "_m3r"))
    for metric in ("rmse_log", "mae_log", "cell_equal_soh_rmse"):
        compare[f"delta_{metric}_m3r_minus_m3"] = compare[f"{metric}_m3r"] - compare[f"{metric}_m3"]
    compare.to_csv(TABLES / "m3r_vs_m3_point_comparison.csv", index=False, encoding="utf-8-sig")
    plot(metrics, m3)
    inputs = {f"early_features_k{k}.csv":sha(ROOT / "data" / "processed" / f"early_features_k{k}.csv") for k in KS}
    inputs.update({f"raw_curve_features_train_k{k}.csv":sha(ROOT / "data" / "processed" / f"raw_curve_features_train_k{k}.csv") for k in KS})
    inputs.update({"cell_labels.csv":sha(ROOT / "data" / "processed" / "cell_labels.csv"), "cycle_model_view.csv":sha(ROOT / "data" / "processed" / "cycle_model_view.csv"), "mat_deep_cycle_flags.csv":sha(ROOT / "outputs" / "data_audit" / "mat_deep_cycle_flags.csv")})
    payload = {"question":"Q3", "round":"round3_raw_curve_challenger", "execution_timestamp":datetime.now(timezone.utc).isoformat(), "implementation_target":"python+matlab_precomputed_features", "random_seed":SEED, "scope":"Train-only challenger; no Primary/Secondary read.", "raw_feature_definition":"I>0.1A charge points of raw MAT cycles accepted by the six-field deep audit; features are charge-voltage mean average, p95 average and p95 slope.", "metrics":metric_rows, "comparison_with_M3":compare.to_dict(orient="records"), "input_sha256":inputs, "script_sha256":sha(SCRIPT), "environment":{"python":sys.version,"platform":platform.platform(),"scikit_learn":sklearn.__version__}, "warning":"Point comparison is not a selection verdict; require policy bootstrap before any retention claim."}
    text = json.dumps(payload, ensure_ascii=False, indent=2); (METRICS / "m3r_raw_curve_metrics.json").write_text(text, encoding="utf-8"); (OUT / "run_summary.json").write_text(text, encoding="utf-8"); (LOGS / "run.log").write_text(text+"\n", encoding="utf-8")
    print(compare.to_string(index=False))

if __name__ == "__main__":
    main()
