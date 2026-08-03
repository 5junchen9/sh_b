"""Execute the preregistered one-time Secondary pressure test without retuning."""
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
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import PolynomialFeatures, SplineTransformer, StandardScaler

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "results" / "Secondary_final_pressure_test"
MANIFEST = OUT / "manifest.json"
LABELS = ROOT / "data" / "processed" / "cell_labels.csv"
VIEW = ROOT / "data" / "processed" / "cycle_model_view.csv"
P0 = ROOT / "data" / "processed" / "p0_summary.json"
STRATEGY = ["C1", "Q1_percent", "C2"]
EARLY = ["QDischarge_mean", "QDischarge_slope", "QDischarge_delta_cycle2_to_k", "QCharge_mean", "QCharge_slope", "IR_mean", "IR_slope", "Tmax_mean", "Tavg_mean", "Tmin_mean", "chargetime_mean", "chargetime_slope"]
RAW = ["raw_charge_v_mean_mean", "raw_charge_v_p95_mean", "raw_charge_v_p95_slope"]
GRID = np.linspace(0.001, 1.0, 1000)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def valid_mask(series: pd.Series) -> pd.Series:
    if pd.api.types.is_bool_dtype(series):
        return series.fillna(False)
    return series.astype(str).str.strip().str.lower().isin(["true", "1"])


def ridge(alpha: float):
    return make_pipeline(StandardScaler(), Ridge(alpha=alpha))


def q2_model(kind: str, alpha: float):
    steps = []
    if kind == "M2":
        steps.append(PolynomialFeatures(2, include_bias=False))
    steps += [StandardScaler(), Ridge(alpha=alpha)]
    return make_pipeline(*steps)


def p3_model():
    return make_pipeline(SplineTransformer(n_knots=4, degree=2, include_bias=False, extrapolation="linear"), StandardScaler(), Ridge(alpha=0.03))


def life_metrics(actual_log: np.ndarray, predicted_log: np.ndarray) -> dict[str, float]:
    actual, predicted = np.exp(actual_log), np.exp(predicted_log)
    return {"rmse_log": float(mean_squared_error(actual_log, predicted_log) ** .5), "mae_log": float(mean_absolute_error(actual_log, predicted_log)), "rmse_cycle": float(mean_squared_error(actual, predicted) ** .5), "mae_cycle": float(mean_absolute_error(actual, predicted)), "overprediction_rate": float(np.mean(predicted_log > actual_log))}


def policy_metrics(frame: pd.DataFrame, predicted_col: str) -> dict[str, float]:
    rows = []
    for _, group in frame.groupby("policy_table9", sort=False):
        rows.append(life_metrics(group.actual_log_life.to_numpy(float), group[predicted_col].to_numpy(float)))
    output = {f"policy_equal_{key}": float(np.mean([row[key] for row in rows])) for key in ("rmse_log", "mae_log", "rmse_cycle", "mae_cycle", "overprediction_rate")}
    output["policy_group_count"] = int(len(rows))
    return output


def build_template(train_barcodes: list[str], life: dict[str, float], view: pd.DataFrame) -> np.ndarray:
    rows = []
    for barcode in train_barcodes:
        curve = view.loc[view.barcode.eq(barcode) & valid_mask(view.valid_QDischarge), ["global_cycle_index", "SOH_nom"]]
        u = curve.global_cycle_index.to_numpy(float) / life[barcode]
        if len(u) < 10:
            continue
        aligned = np.full(len(GRID), np.nan)
        support = (GRID >= u.min()) & (GRID <= u.max())
        aligned[support] = np.interp(GRID[support], u, curve.SOH_nom.to_numpy(float))
        rows.append(aligned)
    matrix = np.vstack(rows)
    support = np.sum(np.isfinite(matrix), axis=0) >= 5
    if not support.any():
        raise RuntimeError("Train SOH template support below five cells.")
    x = np.r_[GRID[support], 1.0]
    y = np.r_[np.nanmedian(matrix[:, support], axis=0), 0.8]
    from sklearn.isotonic import IsotonicRegression
    return IsotonicRegression(increasing=False, out_of_bounds="clip").fit(x, y).predict(GRID)


def curve_residual(barcode: str, k: int, predicted_life: float, actual_life: float, template: np.ndarray, view: pd.DataFrame):
    if predicted_life <= k:
        return None, "predicted_life_not_after_k"
    curve = view.loc[view.barcode.eq(barcode) & valid_mask(view.valid_QDischarge), ["global_cycle_index", "SOH_nom"]]
    anchor = curve.loc[curve.global_cycle_index.eq(k), "SOH_nom"]
    future = curve.loc[(curve.global_cycle_index.gt(k)) & (curve.global_cycle_index.lt(actual_life)), ["global_cycle_index", "SOH_nom"]]
    if anchor.empty:
        return None, "missing_anchor"
    if future.empty:
        return None, "no_future_observation"
    gk = np.interp(k / predicted_life, GRID, template)
    denominator = .8 - gk
    if abs(denominator) < 1e-6:
        return None, "template_anchor_denominator"
    shape = (np.interp(np.minimum(future.global_cycle_index.to_numpy(float) / predicted_life, 1), GRID, template) - gk) / denominator
    prediction = float(anchor.iloc[0]) + (.8 - float(anchor.iloc[0])) * shape
    prediction = np.where(future.global_cycle_index.to_numpy(float) >= predicted_life, .8, prediction)
    return prediction - future.SOH_nom.to_numpy(float), None


def q3_predict(model_id: str, k: int, train: pd.DataFrame, secondary: pd.DataFrame, view: pd.DataFrame, alpha: float) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, float]]:
    early = pd.read_csv(ROOT / "data" / "processed" / f"early_features_k{k}.csv").set_index("barcode")
    train_data = train.join(early[EARLY], on="barcode", validate="one_to_one")
    secondary_data = secondary.join(early[EARLY], on="barcode", validate="one_to_one")
    columns = EARLY.copy()
    if model_id == "M3R":
        raw_train = pd.read_csv(ROOT / "data" / "processed" / "raw_curve_features_train_k5.csv").set_index("barcode")
        raw_secondary = pd.read_csv(OUT / "inputs" / "raw_curve_features_secondary_k5.csv").set_index("barcode")
        train_data = train_data.join(raw_train[RAW + ["raw_valid_ratio"]], on="barcode", validate="one_to_one")
        secondary_data = secondary_data.join(raw_secondary[RAW + ["raw_valid_ratio"]], on="barcode", validate="one_to_one")
        if (train_data.raw_valid_ratio < .8).any() or (secondary_data.raw_valid_ratio < .8).any():
            raise RuntimeError("Frozen raw-validity gate failed.")
        columns = [*STRATEGY, *EARLY, *RAW]
    if train_data[columns].isna().any().any() or secondary_data[columns].isna().any().any():
        raise RuntimeError(f"{model_id}-k{k} has missing frozen features.")
    y_train = np.log(train_data.cycle_life_table9.to_numpy(float))
    prediction = ridge(alpha).fit(train_data[columns].to_numpy(float), y_train).predict(secondary_data[columns].to_numpy(float))
    actual = np.log(secondary_data.cycle_life_table9.to_numpy(float))
    life = secondary_data[["barcode", "policy_table9", "cycle_life_table9"]].copy()
    life["model_id"], life["k"] = model_id, k
    life["actual_log_life"], life["predicted_log_life"] = actual, prediction
    life["predicted_cycle_life"] = np.exp(prediction)
    template = build_template(train.barcode.tolist(), dict(zip(train.barcode, train.cycle_life_table9.astype(float))), view)
    curves, failures = [], {name: 0 for name in ("predicted_life_not_after_k", "missing_anchor", "no_future_observation", "template_anchor_denominator")}
    for _, row in life.iterrows():
        residual, reason = curve_residual(row.barcode, k, float(row.predicted_cycle_life), float(row.cycle_life_table9), template, view)
        if reason:
            failures[reason] += 1
            continue
        curves.append({"barcode": row.barcode, "policy_table9": row.policy_table9, "model_id": model_id, "k": k, "future_point_count": len(residual), "soh_mse": float(np.mean(residual ** 2)), "soh_mae": float(np.mean(abs(residual)),)})
    curve = pd.DataFrame(curves)
    if curve.empty:
        raise RuntimeError(f"{model_id}-k{k} has no evaluable Secondary SOH curve.")
    metrics = life_metrics(actual, prediction) | policy_metrics(life, "predicted_log_life")
    metrics |= {"model_id": model_id, "k": k, "cell_equal_soh_rmse": float(np.mean(curve.soh_mse) ** .5), "cell_equal_soh_mae": float(np.mean(curve.soh_mae)), "curve_cells": int(len(curve)), "template_failures": int(sum(failures.values())), **{f"failure_{key}": int(value) for key, value in failures.items()}}
    policy_soh = curve.groupby("policy_table9", sort=False).soh_mse.mean()
    metrics["policy_equal_soh_rmse"] = float(np.mean(policy_soh) ** .5)
    return life, curve, metrics


def bootstrap_deltas(left: pd.DataFrame, right: pd.DataFrame, left_curve: pd.DataFrame | None, right_curve: pd.DataFrame | None, repeats: int, seed: int) -> pd.DataFrame:
    pairs = left[["barcode", "policy_table9", "actual_log_life", "predicted_log_life"]].merge(right[["barcode", "predicted_log_life"]], on="barcode", suffixes=("_left", "_right"), validate="one_to_one")
    groups = [block.index.to_numpy() for _, block in pairs.groupby("policy_table9", sort=False)]
    rng = np.random.default_rng(seed)
    curve_pair = None
    if left_curve is not None and right_curve is not None:
        curve_pair = left_curve[["barcode", "soh_mse"]].merge(right_curve[["barcode", "soh_mse"]], on="barcode", suffixes=("_left", "_right"), validate="one_to_one")
    rows = []
    for repeat in range(repeats):
        idx = np.concatenate([groups[i] for i in rng.integers(0, len(groups), len(groups))])
        actual = pairs.actual_log_life.to_numpy(float)[idx]
        one = pairs.predicted_log_life_left.to_numpy(float)[idx]
        two = pairs.predicted_log_life_right.to_numpy(float)[idx]
        record = {"repeat": repeat + 1, "delta_rmse_log_right_minus_left": float(mean_squared_error(actual, two) ** .5 - mean_squared_error(actual, one) ** .5), "delta_mae_log_right_minus_left": float(mean_absolute_error(actual, two) - mean_absolute_error(actual, one))}
        if curve_pair is not None:
            barcode = pairs.iloc[idx].barcode
            mse = curve_pair.set_index("barcode").loc[barcode]
            record["delta_soh_rmse_right_minus_left"] = float(np.mean(mse.soh_mse_right) ** .5 - np.mean(mse.soh_mse_left) ** .5)
        rows.append(record)
    return pd.DataFrame(rows)


def summarize_bootstrap(name: str, values: pd.DataFrame) -> list[dict[str, float | str]]:
    rows = []
    for column in values.columns:
        if column == "repeat":
            continue
        series = values[column]
        rows.append({"comparison": name, "metric_delta": column, "point_bootstrap_median": float(series.median()), "ci95_low": float(series.quantile(.025)), "ci95_high": float(series.quantile(.975)), "right_model_improvement_proportion": float((series < 0).mean())})
    return rows


def figure(q2: pd.DataFrame, q3: pd.DataFrame) -> None:
    figures = OUT / "figures"; figures.mkdir(exist_ok=True)
    fig, axes = plt.subplots(1, 2, figsize=(12, 5.2))
    for model_id, color in [("M1", "#5B6573"), ("M2", "#1976B9")]:
        data = q2.loc[q2.model_id.eq(model_id)]
        axes[0].scatter(data.cycle_life_table9, data.predicted_cycle_life, s=38, alpha=.82, color=color, label=model_id)
    lo, hi = axes[0].get_xlim(); axes[0].plot([lo, hi], [lo, hi], "--", color="#555555", label="理想预测线")
    axes[0].set(title="Q2：Secondary 寿命观测—预测", xlabel="实际循环寿命（cycle）", ylabel="预测循环寿命（cycle）")
    axes[0].legend(); axes[0].grid(alpha=.2)
    for model_id, k, color, label in [("M3R", 5, "#D55E00", "M3R-k=5（早筛）"), ("M2", 100, "#0072B2", "M2-k=100（校正）")]:
        data = q3.loc[(q3.model_id.eq(model_id)) & (q3.k.eq(k))]
        axes[1].scatter(data.cycle_life_table9, data.predicted_cycle_life, s=38, alpha=.82, color=color, label=label)
    lo, hi = axes[1].get_xlim(); axes[1].plot([lo, hi], [lo, hi], "--", color="#555555", label="理想预测线")
    axes[1].set(title="Q3：Secondary 双窗口寿命观测—预测", xlabel="实际循环寿命（cycle）", ylabel="预测循环寿命（cycle）")
    axes[1].legend(fontsize=8); axes[1].grid(alpha=.2)
    fig.suptitle("最终一次 Secondary 压力测试：冻结模型的外部观测", fontweight="bold")
    fig.tight_layout()
    for suffix, kwargs in (("png", {"dpi": 320}), ("svg", {})):
        fig.savefig(figures / f"secondary_final_observed_predicted.{suffix}", bbox_inches="tight", **kwargs)
    plt.close(fig)


def main() -> None:
    if not MANIFEST.exists():
        raise RuntimeError("Freeze manifest missing; Secondary execution is blocked.")
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    if manifest.get("secondary_status_before_run") != "not_read_by_this_final_protocol":
        raise RuntimeError("Secondary manifest is not prospective.")
    for relative, expected in manifest["source_sha256"].items():
        path = ROOT / relative
        if not path.exists() or sha256(path) != expected:
            raise RuntimeError(f"Frozen input/script hash mismatch: {relative}")
    if json.loads(P0.read_text(encoding="utf-8")).get("p0_status") != "pass":
        raise RuntimeError("P0 is not passed.")
    tables, metrics_dir, logs = (OUT / name for name in ("tables", "metrics", "logs"))
    for folder in (tables, metrics_dir, logs): folder.mkdir(parents=True, exist_ok=True)
    raw_required = [OUT / "inputs" / "raw_curve_features_secondary_k5.csv", OUT / "inputs" / "raw_curve_features_secondary_k100.csv"]
    if not all(path.exists() for path in raw_required):
        raise RuntimeError("Frozen Secondary RAW features are missing; run the MATLAB extractor first.")
    labels, view = pd.read_csv(LABELS), pd.read_csv(VIEW, low_memory=False)
    train = labels.loc[labels.dataset_table9.eq("Train")].copy().reset_index(drop=True)
    secondary = labels.loc[labels.dataset_table9.eq("Sec. test")].copy().reset_index(drop=True)
    if len(train) != 41 or len(secondary) != 40 or train.barcode.duplicated().any() or secondary.barcode.duplicated().any():
        raise RuntimeError("Frozen 41/40 Train/Secondary partition check failed.")
    fixed = manifest["fixed_models"]
    y_train = np.log(train.cycle_life_table9.to_numpy(float)); y_secondary = np.log(secondary.cycle_life_table9.to_numpy(float))
    q2_rows = []
    for model_id, key in (("M1", "q2_m1_main_effect_ridge"), ("M2", "q2_m2_interaction_sensitivity"), ("P3", "q2_p3_provisional_for_q4_observation")):
        if model_id == "P3": model = p3_model()
        else: model = q2_model(model_id, float(fixed[key]["alpha"]))
        prediction = model.fit(train[STRATEGY].to_numpy(float), y_train).predict(secondary[STRATEGY].to_numpy(float))
        frame = secondary[["barcode", "policy_table9", "cycle_life_table9"]].copy()
        frame["model_id"], frame["actual_log_life"], frame["predicted_log_life"] = model_id, y_secondary, prediction
        frame["predicted_cycle_life"] = np.exp(prediction)
        q2_rows.append(frame)
    q2 = pd.concat(q2_rows, ignore_index=True)
    q2_metrics = []
    for model_id, block in q2.groupby("model_id", sort=False): q2_metrics.append({"model_id": model_id, **life_metrics(block.actual_log_life.to_numpy(float), block.predicted_log_life.to_numpy(float)), **policy_metrics(block, "predicted_log_life")})
    q2_boot = bootstrap_deltas(q2.query("model_id == 'M1'"), q2.query("model_id == 'M2'"), None, None, manifest["fixed_evaluation"]["bootstrap_repeats"], manifest["fixed_evaluation"]["seed"])
    q3_life, q3_curve, q3_metrics = [], [], []
    for model_id, k, key in (("M2", 5, "q3_m2_k5_comparator"), ("M3R", 5, "q3_m3r_k5_screening"), ("M2", 100, "q3_m2_k100_calibration")):
        life, curve, metric = q3_predict(model_id, k, train, secondary, view, float(fixed[key]["alpha"]))
        q3_life.append(life); q3_curve.append(curve); q3_metrics.append(metric)
    q3_life_frame, q3_curve_frame = pd.concat(q3_life, ignore_index=True), pd.concat(q3_curve, ignore_index=True)
    q3_boot = bootstrap_deltas(q3_life_frame.query("model_id == 'M2' and k == 5"), q3_life_frame.query("model_id == 'M3R' and k == 5"), q3_curve_frame.query("model_id == 'M2' and k == 5"), q3_curve_frame.query("model_id == 'M3R' and k == 5"), manifest["fixed_evaluation"]["bootstrap_repeats"], manifest["fixed_evaluation"]["seed"] + 1)
    boot_summary = pd.DataFrame(summarize_bootstrap("Q2_M2_minus_M1", q2_boot) + summarize_bootstrap("Q3_M3Rk5_minus_M2k5", q3_boot))
    q4 = secondary[["barcode", "policy_table9", "C1", "Q1_percent", "C2", "cycle_life_table9"]].copy()
    q4 = q4.merge(q2.query("model_id == 'P3'")[["barcode", "predicted_cycle_life"]].rename(columns={"predicted_cycle_life": "q2_p3_predicted_cycle_life"}), on="barcode", validate="one_to_one")
    q4 = q4.merge(q3_life_frame.query("model_id == 'M2' and k == 100")[["barcode", "predicted_cycle_life"]].rename(columns={"predicted_cycle_life": "q3_m2k100_predicted_cycle_life"}), on="barcode", validate="one_to_one")
    q4["status"] = "secondary_existing_policy_observation_only"
    q4_summary = q4.groupby(["policy_table9", "C1", "Q1_percent", "C2"], as_index=False).agg(cell_count=("barcode", "size"), actual_life_mean=("cycle_life_table9", "mean"), q2_p3_predicted_life_mean=("q2_p3_predicted_cycle_life", "mean"), q3_m2k100_predicted_life_mean=("q3_m2k100_predicted_cycle_life", "mean"))
    q4_summary["status"] = "no_recommendation_or_reoptimization"
    q2.to_csv(tables / "q2_external_predictions.csv", index=False, encoding="utf-8-sig")
    pd.DataFrame(q2_metrics).to_csv(tables / "q2_external_metrics.csv", index=False, encoding="utf-8-sig")
    q2_boot.to_csv(tables / "q2_m2_minus_m1_policy_bootstrap.csv", index=False, encoding="utf-8-sig")
    q3_life_frame.to_csv(tables / "q3_external_life_predictions.csv", index=False, encoding="utf-8-sig")
    q3_curve_frame.to_csv(tables / "q3_external_cell_curve_errors.csv", index=False, encoding="utf-8-sig")
    pd.DataFrame(q3_metrics).to_csv(tables / "q3_external_metrics.csv", index=False, encoding="utf-8-sig")
    q3_boot.to_csv(tables / "q3_m3r_k5_minus_m2_k5_policy_bootstrap.csv", index=False, encoding="utf-8-sig")
    boot_summary.to_csv(tables / "bootstrap_intervals.csv", index=False, encoding="utf-8-sig")
    q4.to_csv(tables / "q4_existing_policy_external_cell_observations.csv", index=False, encoding="utf-8-sig")
    q4_summary.to_csv(tables / "q4_existing_policy_external_summary.csv", index=False, encoding="utf-8-sig")
    figure(q2, q3_life_frame)
    q2_table = "\n".join(f"| {r['model_id']} | {r['rmse_log']:.6f} | {r['mae_log']:.6f} | {r['overprediction_rate']:.2%} |" for r in q2_metrics)
    q3_table = "\n".join(f"| {r['model_id']} | {r['k']} | {r['rmse_log']:.6f} | {r['mae_log']:.6f} | {r['cell_equal_soh_rmse']:.6f} | {r['curve_cells']} |" for r in q3_metrics)
    report = f"""# Secondary 最终一次压力测试报告

> 本报告只记录冻结模型在 40 枚 Secondary 电芯上的一次性外部观察。模型、窗口、特征、评价指标与 2,000 次策略组 bootstrap 已在执行前固定；本报告不据结果重选模型、窗口或策略。

## Q2：冻结策略—寿命模型

| 模型 | RMSE_log | MAE_log | 过预测比例 |
|---|---:|---:|---:|
{q2_table}

M1 为正文主线，M2 仍仅是二阶交互敏感性分析；P3 仅为 Q4 的 provisional 观察代理。M2−M1 的策略组 bootstrap 区间见 `tables/bootstrap_intervals.csv`，不得以单一指标替代完整误差结构。

## Q3：冻结双窗口

| 模型 | k | RMSE_log | MAE_log | 电芯等权未来 SOH RMSE | 可评价电芯 |
|---|---:|---:|---:|---:|---:|
{q3_table}

M3R-k=5 只对应最早曲线增强筛查候选；M2-k=100 对应较充分校正窗口。二者的任务角色由冻结前裁决确定，不会随本次结果改变。M3R-k=5 相对 M2-k=5 的策略组 bootstrap 差值亦见 `tables/bootstrap_intervals.csv`。

## Q4：已有策略的外部观察

仅汇总 Secondary 中已有策略的实际寿命和冻结预测，见 `tables/q4_existing_policy_external_summary.csv`。不生成新策略，不作 Pareto 重选，不输出最佳策略或推荐。

## 审计边界

- Train=41、Secondary=40；原始数据不改写；异常仅沿用字段—循环掩码。
- 原始曲线特征只取六字段审计可用循环中 `I>0.1 A` 的充电点，且 RAW 有效比例均要求不低于 0.8。
- 输入与脚本 SHA-256 已在 `manifest.json` 冻结并在运行开始时逐项复核。
- Primary 未参与本次拟合、调参或评分；Secondary 只用于本次输出，不反馈到任何模型选择。
"""
    (OUT / "secondary_final_pressure_test_report.md").write_text(report, encoding="utf-8")
    audit = {"status": "completed_without_retuning", "secondary_cells": 40, "train_cells": 41, "secondary_read": True, "primary_used": False, "models_fixed": manifest["fixed_models"], "manifest_sha256": sha256(MANIFEST), "inputs_and_scripts_verified": True, "raw_feature_inputs": {path.name: sha256(path) for path in raw_required}, "execution_timestamp": datetime.now(timezone.utc).isoformat(), "environment": {"python": sys.version, "platform": platform.platform(), "scikit_learn": sklearn.__version__}}
    (OUT / "audit.md").write_text("# Secondary 执行审计\n\n```json\n" + json.dumps(audit, ensure_ascii=False, indent=2) + "\n```\n", encoding="utf-8")
    (metrics_dir / "run_summary.json").write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8")
    (logs / "run.log").write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"q2": q2_metrics, "q3": q3_metrics, "bootstrap": boot_summary.to_dict("records")}, ensure_ascii=False))


if __name__ == "__main__":
    main()
