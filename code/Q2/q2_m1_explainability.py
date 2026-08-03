"""Train-only explanatory supplement for the frozen Q2-A M1 Ridge baseline."""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
matplotlib.rcParams.update({"font.family": "sans-serif", "font.sans-serif": ["Microsoft YaHei", "SimHei", "DejaVu Sans"], "axes.unicode_minus": False, "svg.fonttype": "none"})
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error
from sklearn.model_selection import GroupKFold
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

SCRIPT = Path(__file__).resolve()
ROOT = SCRIPT.parents[2]
OUT = ROOT / "results" / "Q2" / "experiments" / "m1_explainability_round1"
TABLES, FIGURES, METRICS, LOGS = (OUT / x for x in ("tables", "figures", "metrics", "logs"))
LABELS = ROOT / "data" / "processed" / "cell_labels.csv"
P0 = ROOT / "data" / "processed" / "p0_summary.json"
DESIGN = ROOT / "code" / "Q2" / "q2_explainability_code_design.md"
EXISTING_OOF = ROOT / "results" / "Q2" / "experiments" / "round1" / "tables" / "m1_oof_predictions.csv"
FEATURES = ["C1", "Q1_percent", "C2"]
ALPHAS = [0.01, 0.1, 1.0, 3.0, 10.0, 30.0, 100.0]
SEED = 20260802
N_BOOT = 2000


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def model(alpha: float):
    return make_pipeline(StandardScaler(), Ridge(alpha=alpha))


def choose_alpha(x: np.ndarray, y: np.ndarray, groups: np.ndarray) -> float:
    cv = GroupKFold(n_splits=min(4, pd.Series(groups).nunique()))
    scores = []
    for alpha in ALPHAS:
        fold_errors = [mean_squared_error(y[va], model(alpha).fit(x[tr], y[tr]).predict(x[va])) for tr, va in cv.split(x, y, groups)]
        scores.append(float(np.mean(fold_errors)))
    return float(ALPHAS[int(np.argmin(scores))])


def nested_oof(data: pd.DataFrame, columns: list[str]) -> tuple[np.ndarray, np.ndarray, list[dict[str, float]]]:
    x = data[columns].to_numpy(float)
    y = np.log(data.cycle_life_table9.to_numpy(float))
    groups = data.policy_table9.to_numpy()
    outer = GroupKFold(n_splits=min(5, pd.Series(groups).nunique()))
    pred = np.full(len(data), np.nan)
    fold_ids = np.full(len(data), -1, dtype=int)
    tuning = []
    for fold, (tr, te) in enumerate(outer.split(x, y, groups), 1):
        alpha = choose_alpha(x[tr], y[tr], groups[tr])
        pred[te] = model(alpha).fit(x[tr], y[tr]).predict(x[te])
        fold_ids[te] = fold
        tuning.append({"model_columns": "|".join(columns), "fold": fold, "alpha": alpha, "test_cells": int(len(te))})
    if np.isnan(pred).any() or (fold_ids < 1).any():
        raise RuntimeError("Nested OOF assignment incomplete.")
    return pred, fold_ids, tuning


def grouped_bootstrap_deltas(data: pd.DataFrame, prediction_table: pd.DataFrame, rng: np.random.Generator) -> pd.DataFrame:
    group_indices = [idx.to_numpy() for _, idx in data.groupby("policy_table9").groups.items()]
    full_abs = np.abs(prediction_table.full_pred_log.to_numpy() - prediction_table.actual_log_life.to_numpy())
    rows = []
    for name in ["drop_C1", "drop_Q1_percent", "drop_C2"]:
        ablated_abs = np.abs(prediction_table[f"{name}_pred_log"].to_numpy() - prediction_table.actual_log_life.to_numpy())
        for repeat in range(N_BOOT):
            selected_blocks = rng.integers(0, len(group_indices), size=len(group_indices))
            indices = np.concatenate([group_indices[i] for i in selected_blocks])
            rows.append({"feature_model": name, "repeat": repeat + 1, "delta_mae_log_ablated_minus_full": float(ablated_abs[indices].mean() - full_abs[indices].mean())})
    return pd.DataFrame(rows)


def coefficient_bootstrap(data: pd.DataFrame, alpha: float, rng: np.random.Generator) -> pd.DataFrame:
    group_indices = [idx.to_numpy() for _, idx in data.groupby("policy_table9").groups.items()]
    x = data[FEATURES].to_numpy(float)
    y = np.log(data.cycle_life_table9.to_numpy(float))
    rows = []
    for repeat in range(N_BOOT):
        chosen = rng.integers(0, len(group_indices), size=len(group_indices))
        indices = np.concatenate([group_indices[i] for i in chosen])
        fitted = model(alpha).fit(x[indices], y[indices])
        coef = fitted.named_steps["ridge"].coef_
        for feature, value in zip(FEATURES, coef):
            rows.append({"repeat": repeat + 1, "feature": feature, "standardized_coefficient": float(value)})
    return pd.DataFrame(rows)


def plot(coef: pd.DataFrame, ablation: pd.DataFrame) -> None:
    labels = {"C1": "第一段倍率 C1", "Q1_percent": "切换 SOC q", "C2": "第二段倍率 C2", "drop_C1": "删除 C1", "drop_Q1_percent": "删除 q", "drop_C2": "删除 C2"}
    fig, axes = plt.subplots(1, 2, figsize=(12.2, 4.8))
    ax = axes[0]
    c = coef.copy().sort_values("standardized_coefficient")
    colors = np.where(c.standardized_coefficient >= 0, "#1A6FC4", "#E28E2C")
    ax.barh([labels[x] for x in c.feature], c.standardized_coefficient, xerr=[c.standardized_coefficient - c.ci95_low, c.ci95_high - c.standardized_coefficient], color=colors, alpha=.9, capsize=3)
    ax.axvline(0, color="#555555", linewidth=.8)
    ax.set(title="M1 标准化系数与策略组重抽样区间", xlabel="标准化系数（ln 寿命尺度）", ylabel="策略变量")
    ax.grid(axis="x", alpha=.2, linestyle="--")

    ax = axes[1]
    a = ablation.copy().sort_values("delta_mae_log")
    colors = np.where(a.delta_mae_log >= 0, "#2E9E44", "#E53935")
    ax.barh([labels[x] for x in a.feature_model], a.delta_mae_log, xerr=[a.delta_mae_log - a.ci95_low, a.ci95_high - a.delta_mae_log], color=colors, alpha=.9, capsize=3)
    ax.axvline(0, color="#555555", linewidth=.8)
    ax.set(title="删一变量对折外 MAE 的影响", xlabel="ΔMAE_log = 删除后 − 完整 M1", ylabel="删一变量模型")
    ax.grid(axis="x", alpha=.2, linestyle="--")
    fig.suptitle("Q2：主效应 Ridge 的条件关联解释（非因果贡献）", fontweight="bold", fontsize=13)
    fig.tight_layout()
    for ext, kwargs in (("svg", {}), ("png", {"dpi": 320})):
        fig.savefig(FIGURES / f"q2_m1_factor_explainability.{ext}", bbox_inches="tight", **kwargs)
    plt.close(fig)


def main() -> None:
    for folder in (TABLES, FIGURES, METRICS, LOGS):
        folder.mkdir(parents=True, exist_ok=True)
    if json.loads(P0.read_text(encoding="utf-8")).get("p0_status") != "pass":
        raise RuntimeError("P0 is not passed; Q2 explanatory supplement is blocked.")
    data = pd.read_csv(LABELS).query("dataset_table9 == 'Train'").reset_index(drop=True)
    if len(data) != 41 or data.policy_table9.nunique() != 40:
        raise RuntimeError("Frozen Q2 Train partition must contain 41 cells and 40 policy groups.")
    actual = np.log(data.cycle_life_table9.to_numpy(float))
    full_pred, fold_ids, tuning = nested_oof(data, FEATURES)
    existing = pd.read_csv(EXISTING_OOF).set_index("barcode").loc[data.barcode]
    if not np.allclose(full_pred, existing.pred_log_life.to_numpy(float), rtol=0, atol=1e-12):
        raise RuntimeError("Recomputed full M1 OOF predictions do not match the frozen Q2 Round 1 table.")

    out = data[["barcode", "policy_table9", "cycle_life_table9", *FEATURES]].copy()
    out["actual_log_life"] = actual
    out["outer_fold"] = fold_ids
    out["full_pred_log"] = full_pred
    metric_rows = [{"feature_model": "full_M1", "feature_removed": "", "rmse_log": float(mean_squared_error(actual, full_pred) ** .5), "mae_log": float(mean_absolute_error(actual, full_pred))}]
    for feature in FEATURES:
        kept = [x for x in FEATURES if x != feature]
        pred, ablation_folds, tune = nested_oof(data, kept)
        name = f"drop_{feature}"
        if not np.array_equal(fold_ids, ablation_folds):
            raise RuntimeError("Ablation must share M1 outer policy-group folds.")
        out[f"{name}_pred_log"] = pred
        metric_rows.append({"feature_model": name, "feature_removed": feature, "rmse_log": float(mean_squared_error(actual, pred) ** .5), "mae_log": float(mean_absolute_error(actual, pred))})
        tuning.extend(tune)
    metrics = pd.DataFrame(metric_rows)
    full_mae = float(metrics.loc[metrics.feature_model.eq("full_M1"), "mae_log"].iloc[0])
    metrics["delta_mae_log"] = metrics.mae_log - full_mae

    alpha_full = choose_alpha(data[FEATURES].to_numpy(float), actual, data.policy_table9.to_numpy())
    fitted = model(alpha_full).fit(data[FEATURES].to_numpy(float), actual)
    coefficient = pd.DataFrame({"feature": FEATURES, "standardized_coefficient": fitted.named_steps["ridge"].coef_})
    rng = np.random.default_rng(SEED)
    coeff_boot = coefficient_bootstrap(data, alpha_full, rng)
    coeff_summary = coeff_boot.groupby("feature").standardized_coefficient.agg(["median", lambda s: s.quantile(.025), lambda s: s.quantile(.975), lambda s: float(max((s > 0).mean(), (s < 0).mean()))]).reset_index()
    coeff_summary.columns = ["feature", "bootstrap_median", "ci95_low", "ci95_high", "dominant_sign_rate"]
    coefficient = coefficient.merge(coeff_summary, on="feature", validate="one_to_one")

    delta_boot = grouped_bootstrap_deltas(data, out, rng)
    delta_summary = delta_boot.groupby("feature_model").delta_mae_log_ablated_minus_full.agg(["median", lambda s: s.quantile(.025), lambda s: s.quantile(.975), lambda s: (s > 0).mean()]).reset_index()
    delta_summary.columns = ["feature_model", "bootstrap_median_delta", "ci95_low", "ci95_high", "positive_delta_rate"]
    ablation = metrics.loc[metrics.feature_model.ne("full_M1")].merge(delta_summary, on="feature_model", validate="one_to_one")
    plot(coefficient.drop(columns=["standardized_coefficient"]).rename(columns={"bootstrap_median": "standardized_coefficient"}), ablation)

    out.to_csv(TABLES / "q2_m1_feature_ablation_oof.csv", index=False, encoding="utf-8-sig")
    metrics.to_csv(TABLES / "q2_m1_feature_ablation_metrics.csv", index=False, encoding="utf-8-sig")
    ablation.to_csv(TABLES / "q2_m1_feature_ablation_summary.csv", index=False, encoding="utf-8-sig")
    coefficient.to_csv(TABLES / "q2_m1_standardized_coefficients.csv", index=False, encoding="utf-8-sig")
    coeff_boot.to_csv(TABLES / "q2_m1_coefficient_bootstrap.csv", index=False, encoding="utf-8-sig")
    delta_boot.to_csv(TABLES / "q2_m1_feature_ablation_bootstrap.csv", index=False, encoding="utf-8-sig")
    pd.DataFrame(tuning).to_csv(TABLES / "q2_m1_explainability_tuning.csv", index=False, encoding="utf-8-sig")

    summary_text = "\n".join(f"| {r.feature_model} | {r.feature_removed or '—'} | {r.rmse_log:.5f} | {r.mae_log:.5f} | {r.delta_mae_log:+.5f} |" for _, r in metrics.iterrows())
    report = f"""# Q2 M1 因素排序与条件关联补充报告

> **定位：** 仅补充冻结 Q2-A M1 主效应 Ridge 的解释证据；所有结果只用 Train，不能解释为因果贡献，也不会改变 M1 主线、M2 敏感性或 P3 provisional 的既有角色。

## 1. 方法

- 样本：41 枚 Train 电芯、40 个 `policy_table9` 组；目标为 `ln(cycle_life_table9)`。
- 完整 M1 与删一变量模型均使用相同的外层策略分组折和内层 alpha 选择；完整 M1 的 OOF 预测与既有 Round 1 表逐元素一致。
- 系数是在 Train 全量、内层选定 `alpha={alpha_full:g}` 后得到的标准化 Ridge 系数；系数区间来自 2,000 次策略组块重抽样、固定 alpha 重拟合。
- 变量重要性以 `ΔMAE_log=MAE_删除后−MAE_完整` 表示。正值说明删去该变量后典型折外误差上升；它仍只是相关结构下的条件预测信息，不能称为物理因果贡献。

## 2. 删一变量结果

| 模型 | 删除变量 | RMSE_log | MAE_log | ΔMAE_log |
|---|---|---:|---:|---:|
{summary_text}

## 3. 使用边界

1. 三个策略变量受两段式协议约束，彼此并非充分独立；删一变量差值不等于独立贡献百分比。
2. 任何 bootstrap 区间跨 0 的删一差值只能称“证据不足以稳定排序”，不应在论文中强行排出唯一第一因素。
3. 系数、删一误差与 M2 交互均在 `ln(L)` 尺度计算；反变换为 cycle 时只使用 `exp`。

## 4. 产物

- `tables/q2_m1_standardized_coefficients.csv`
- `tables/q2_m1_feature_ablation_summary.csv`
- `tables/q2_m1_feature_ablation_bootstrap.csv`
- `figures/q2_m1_factor_explainability.png/svg`
"""
    (OUT / "q2_m1_explainability_report.md").write_text(report, encoding="utf-8")
    inputs = {str(path.relative_to(ROOT)).replace("\\\\", "/"): sha(path) for path in (LABELS, P0, DESIGN, EXISTING_OOF)}
    payload = {"question": "Q2", "round": "m1_explainability_round1", "status": "train_only_descriptive_supplement", "execution_timestamp": datetime.now(timezone.utc).isoformat(), "random_seed": SEED, "bootstrap_repeats": N_BOOT, "alpha_full_train": alpha_full, "validation": "5-fold outer policy-group CV plus up-to-4-fold inner policy-group CV", "input_sha256": inputs, "script_sha256": sha(SCRIPT), "outputs": ["tables/q2_m1_feature_ablation_oof.csv", "tables/q2_m1_feature_ablation_summary.csv", "tables/q2_m1_standardized_coefficients.csv", "figures/q2_m1_factor_explainability.png", "figures/q2_m1_factor_explainability.svg", "q2_m1_explainability_report.md"]}
    text = json.dumps(payload, ensure_ascii=False, indent=2)
    (METRICS / "q2_m1_explainability_summary.json").write_text(text, encoding="utf-8")
    (OUT / "run_summary.json").write_text(text, encoding="utf-8")
    (LOGS / "run.log").write_text(text + "\n", encoding="utf-8")
    print(json.dumps({"status": payload["status"], "alpha_full_train": alpha_full, "ablation": ablation[["feature_model", "delta_mae_log", "ci95_low", "ci95_high"]].to_dict("records")}, ensure_ascii=False))


if __name__ == "__main__":
    main()
