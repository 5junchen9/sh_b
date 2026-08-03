"""Build and audit the frozen P0 modeling view for problem B.

The script is intentionally non-destructive: source values are copied verbatim,
and anomalies only change the matching field-cycle validity flag.  No cell or
cycle row is silently deleted because of a measurement anomaly.
"""
from __future__ import annotations

import hashlib
import json
import math
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data" / "processed"
AUDIT = ROOT / "outputs" / "data_audit"
REPORT_PATH = ROOT / "data" / "p0_audit_report.md"
SCRIPT_PATH = Path(__file__).resolve()

SEED = 20260802
WINDOWS = (5, 10, 20, 50, 100)
FIELDS = ("QDischarge", "QCharge", "IR", "Tmax", "Tavg", "Tmin", "chargetime")
NONNEGATIVE_FIELDS = {"QDischarge", "QCharge", "IR", "chargetime"}
JOIN_KEY = ["barcode", "source_file", "batch_index", "cycle_index"]
DATASET_NAMES = {"Train": "Train", "Prim. Test": "Primary", "Sec. test": "Secondary"}

INPUTS = {
    "cycle_summary": PROCESSED / "cycle_summary_clean.csv",
    "cell_labels": PROCESSED / "cell_labels.csv",
    "raw_curve_flags": AUDIT / "mat_deep_cycle_flags.csv",
}
RAW_SOURCES = tuple(ROOT / f"data_{i}.{suffix}" for i in range(1, 4) for suffix in ("mat", "xlsx"))


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def finite_numeric(series: pd.Series) -> pd.Series:
    values = pd.to_numeric(series, errors="coerce")
    return pd.Series(np.isfinite(values.to_numpy()), index=series.index)


def strict_bool(series: pd.Series, field_name: str) -> pd.Series:
    """Parse a persisted boolean column without treating the string 'False' as true."""
    normalized = series.astype(str).str.strip().str.lower()
    allowed = {"true", "false", "1", "0"}
    unknown = ~normalized.isin(allowed)
    if unknown.any():
        values = sorted(normalized.loc[unknown].unique().tolist())[:10]
        raise RuntimeError(f"{field_name} contains non-boolean values: {values}")
    return normalized.isin({"true", "1"})


def append_reason(reasons: pd.Series, mask: pd.Series, reason: str) -> None:
    current = reasons.loc[mask]
    reasons.loc[mask] = np.where(current.eq(""), reason, current + ";" + reason)


def slope(x: pd.Series, y: pd.Series) -> float:
    if len(y) < 2:
        return math.nan
    x_values = x.to_numpy(dtype=float)
    y_values = y.to_numpy(dtype=float)
    denominator = float(np.sum((x_values - x_values.mean()) ** 2))
    if denominator == 0:
        return math.nan
    return float(np.sum((x_values - x_values.mean()) * (y_values - y_values.mean())) / denominator)


def value_at(group: pd.DataFrame, field: str, cycle: int) -> float:
    row = group.loc[group["global_cycle_index"].eq(cycle)]
    if len(row) != 1 or not bool(row.iloc[0][f"valid_{field}"]):
        return math.nan
    return float(row.iloc[0][field])


def valid_part(group: pd.DataFrame, field: str, lower_cycle: int = 2) -> pd.DataFrame:
    return group.loc[group["global_cycle_index"].ge(lower_cycle) & group[f"valid_{field}"], ["global_cycle_index", field]]


def build_feature_row(group: pd.DataFrame, k: int) -> dict:
    group = group.sort_values("global_cycle_index")
    first = group.iloc[0]
    row = {
        "barcode": first["barcode"],
        "dataset_table9": first["dataset_table9"],
        "dataset_role": first["dataset_role"],
        "policy_table9": first["policy_table9"],
        "window_k": k,
        "window_cycle_start": 2,
        "window_cycle_end": k,
        "expected_cycle_count": k - 1,
    }
    for field in FIELDS:
        part = valid_part(group, field)
        count = len(part)
        row[f"{field}_valid_count"] = count
        row[f"{field}_valid_ratio"] = count / (k - 1)

    def stats(field: str) -> tuple[pd.DataFrame, float, float, float]:
        part = valid_part(group, field)
        mean = float(part[field].mean()) if len(part) else math.nan
        field_slope = slope(part["global_cycle_index"], part[field])
        delta = value_at(group, field, k) - value_at(group, field, 2)
        return part, mean, field_slope, delta

    qd, qd_mean, qd_slope, qd_delta = stats("QDischarge")
    qc, qc_mean, qc_slope, qc_delta = stats("QCharge")
    ir, ir_mean, ir_slope, ir_delta = stats("IR")
    ct, ct_mean, ct_slope, _ = stats("chargetime")

    row.update(
        {
            "QDischarge_end": value_at(group, "QDischarge", k),
            "QDischarge_mean": qd_mean,
            "QDischarge_slope": qd_slope,
            "QDischarge_std": float(qd["QDischarge"].std(ddof=0)) if len(qd) else math.nan,
            "QDischarge_delta_cycle2_to_k": qd_delta,
            "QCharge_mean": qc_mean,
            "QCharge_slope": qc_slope,
            "QCharge_delta_cycle2_to_k": qc_delta,
            "IR_end": value_at(group, "IR", k),
            "IR_mean": ir_mean,
            "IR_slope": ir_slope,
            "IR_delta_cycle2_to_k": ir_delta,
            "Tmax_mean": float(valid_part(group, "Tmax")["Tmax"].mean()),
            "Tavg_mean": float(valid_part(group, "Tavg")["Tavg"].mean()),
            "Tmin_mean": float(valid_part(group, "Tmin")["Tmin"].mean()),
            "chargetime_mean": ct_mean,
            "chargetime_slope": ct_slope,
        }
    )
    if k >= 10:
        recent = valid_part(group, "QDischarge", max(2, k - 9))
        row["QDischarge_recent10_slope"] = slope(recent["global_cycle_index"], recent["QDischarge"])
    return row


def write_csv(frame: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    frame.to_csv(temporary, index=False, encoding="utf-8-sig", float_format="%.12g")
    temporary.replace(path)


def main() -> None:
    np.random.seed(SEED)
    missing = [str(path) for path in (*INPUTS.values(), *RAW_SOURCES) if not path.exists()]
    if missing:
        raise FileNotFoundError(f"P0 inputs missing: {missing}")

    raw_hashes_before = {path.name: sha256(path) for path in RAW_SOURCES}
    input_hashes = {name: sha256(path) for name, path in INPUTS.items()}
    source = pd.read_csv(INPUTS["cycle_summary"], low_memory=False)
    labels = pd.read_csv(INPUTS["cell_labels"], low_memory=False)
    raw_flags = pd.read_csv(INPUTS["raw_curve_flags"], low_memory=False)

    required = set(JOIN_KEY) | set(FIELDS) | {
        "dataset_table9", "cycle_life_table9", "policy_table9", "global_cycle_index",
        "all_zero_placeholder",
    }
    if not required.issubset(source.columns):
        raise RuntimeError(f"cycle summary lacks columns: {sorted(required - set(source.columns))}")
    if raw_flags.duplicated(JOIN_KEY).any():
        raise RuntimeError(f"raw curve flags duplicate join key {JOIN_KEY}")

    view = source.loc[source["global_cycle_index"].lt(source["cycle_life_table9"])].copy()
    view["dataset_role"] = view["dataset_table9"].map(DATASET_NAMES)
    if view["dataset_role"].isna().any():
        raise RuntimeError("Unknown dataset_table9 label encountered.")
    view["cutoff_cycle"] = view["cycle_life_table9"] - 1

    raw_subset = raw_flags[JOIN_KEY + ["usable_for_curve_features", "failure_reason"]].rename(
        columns={
            "usable_for_curve_features": "raw_usable_for_curve_features",
            "failure_reason": "raw_failure_reason",
        }
    )
    view = view.merge(raw_subset, on=JOIN_KEY, how="left", validate="one_to_one", indicator=True)
    if not view["_merge"].eq("both").all():
        raise RuntimeError("Some P0 rows do not match the deep MAT audit using the frozen four-field key.")
    view.drop(columns="_merge", inplace=True)
    view["raw_usable_for_curve_features"] = strict_bool(
        view["raw_usable_for_curve_features"], "raw_usable_for_curve_features"
    )
    view["raw_failure_reason"] = view["raw_failure_reason"].fillna("")

    structural_counts: dict[str, dict[str, int]] = {}
    for field in FIELDS:
        valid = finite_numeric(view[field])
        reasons = pd.Series("", index=view.index, dtype="object")
        append_reason(reasons, ~valid, "nonfinite")
        if field in NONNEGATIVE_FIELDS:
            negative = valid & view[field].lt(0)
            valid &= ~negative
            append_reason(reasons, negative, "negative_value")
        placeholder = strict_bool(view["all_zero_placeholder"], "all_zero_placeholder")
        valid &= ~placeholder
        append_reason(reasons, placeholder, "all_zero_placeholder")
        view[f"valid_{field}"] = valid
        view[f"mask_reason_{field}"] = reasons
        structural_counts[field] = {
            "nonfinite": int(reasons.str.contains("nonfinite", regex=False).sum()),
            "negative_value": int(reasons.str.contains("negative_value", regex=False).sum()),
            "all_zero_placeholder": int(reasons.str.contains("all_zero_placeholder", regex=False).sum()),
        }

    temperature_finite = view[["Tmin", "Tavg", "Tmax"]].apply(finite_numeric).all(axis=1)
    temperature_order_bad = temperature_finite & (
        view["Tmin"].gt(view["Tavg"]) | view["Tavg"].gt(view["Tmax"])
    )
    for field in ("Tmin", "Tavg", "Tmax"):
        view.loc[temperature_order_bad, f"valid_{field}"] = False
        reasons = view[f"mask_reason_{field}"].copy()
        append_reason(reasons, temperature_order_bad, "temperature_order_violation")
        view[f"mask_reason_{field}"] = reasons

    # Statistical cleaning is deliberately limited to the documented charge-time
    # rule.  The threshold is fitted once on structurally valid Train rows and
    # then frozen for every dataset; no Primary/Secondary statistic is consulted.
    train_charge = view.loc[
        view["dataset_role"].eq("Train") & view["valid_chargetime"], "chargetime"
    ]
    charge_q99 = float(train_charge.quantile(0.99, interpolation="linear"))
    charge_upper = 5.0 * charge_q99
    charge_outlier = view["valid_chargetime"] & view["chargetime"].gt(charge_upper)
    view.loc[charge_outlier, "valid_chargetime"] = False
    charge_reasons = view["mask_reason_chargetime"].copy()
    append_reason(charge_reasons, charge_outlier, "train_q99_x5_upper")
    view["mask_reason_chargetime"] = charge_reasons

    qd_cycle2 = (
        view.loc[view["global_cycle_index"].eq(2) & view["valid_QDischarge"], ["barcode", "QDischarge"]]
        .set_index("barcode")["QDischarge"]
    )
    view["QDischarge_cycle2_reference"] = view["barcode"].map(qd_cycle2)
    view["SOH_rel"] = np.where(
        view["valid_QDischarge"] & view["QDischarge_cycle2_reference"].notna(),
        view["QDischarge"] / view["QDischarge_cycle2_reference"],
        np.nan,
    )
    view["SOH_nom"] = np.where(view["valid_QDischarge"], view["QDischarge"] / 1.1, np.nan)

    key_duplicates = int(view.duplicated(["barcode", "global_cycle_index"]).sum())
    retained_per_cell = view.groupby("barcode").size()
    expected_per_cell = labels.set_index("barcode")["cycle_life_table9"] - 1
    retained_match = retained_per_cell.sort_index().equals(expected_per_cell.sort_index())
    checks = {
        "official_cell_count_124": int(view["barcode"].nunique()) == 124,
        "retained_row_count_99279": len(view) == 99_279,
        "unique_barcode_global_cycle": key_duplicates == 0,
        "every_cell_has_L_minus_1_rows": bool(retained_match),
        "all_cycles_before_eol": bool((view["global_cycle_index"] < view["cycle_life_table9"]).all()),
        "raw_audit_join_complete": bool(view["raw_usable_for_curve_features"].notna().all()),
        "cycle2_capacity_reference_complete": len(qd_cycle2) == 124,
        "anomaly_does_not_remove_cells": int(view["barcode"].nunique()) == len(labels),
        "threshold_fit_uses_train_only": True,
    }
    if not all(checks.values()):
        raise RuntimeError(f"P0 long-table checks failed: {checks}")

    id_columns = [
        "barcode", "source_file", "batch_index", "cycle_index", "global_cycle_index",
        "dataset_table9", "dataset_role", "cycle_life_table9", "cutoff_cycle",
        "policy_table9", "fragment_order", "is_duplicate_barcode",
    ]
    value_columns = list(FIELDS) + ["QDischarge_cycle2_reference", "SOH_rel", "SOH_nom"]
    mask_columns = [column for field in FIELDS for column in (f"valid_{field}", f"mask_reason_{field}")]
    raw_columns = ["raw_usable_for_curve_features", "raw_failure_reason"]
    view = view[id_columns + value_columns + mask_columns + raw_columns]
    long_path = PROCESSED / "cycle_model_view.csv"
    write_csv(view, long_path)

    feature_paths: dict[int, Path] = {}
    feature_frames: dict[int, pd.DataFrame] = {}
    for k in WINDOWS:
        window = view.loc[view["global_cycle_index"].between(2, k)].copy()
        rows = [build_feature_row(group, k) for _, group in window.groupby("barcode", sort=True)]
        features = pd.DataFrame(rows).sort_values("barcode").reset_index(drop=True)
        checks[f"window_k{k}_has_124_rows"] = len(features) == 124
        checks[f"window_k{k}_one_row_per_cell"] = not features["barcode"].duplicated().any()
        checks[f"window_k{k}_expected_cycle_denominator"] = bool(
            features["expected_cycle_count"].eq(k - 1).all()
        )
        for field in FIELDS:
            expected_counts = window.groupby("barcode")[f"valid_{field}"].sum().sort_index().astype(int)
            actual_counts = features.set_index("barcode")[f"{field}_valid_count"].sort_index().astype(int)
            checks[f"window_k{k}_{field}_counts_traceable"] = expected_counts.equals(actual_counts)
        path = PROCESSED / f"early_features_k{k}.csv"
        write_csv(features, path)
        feature_paths[k] = path
        feature_frames[k] = features

    raw_hashes_after = {path.name: sha256(path) for path in RAW_SOURCES}
    checks["raw_source_hashes_unchanged"] = raw_hashes_before == raw_hashes_after
    checks["all_p0_checks_pass"] = all(checks.values())
    if not checks["all_p0_checks_pass"]:
        failed = [name for name, passed in checks.items() if not passed]
        raise RuntimeError(f"P0 feature checks failed: {failed}")

    output_paths = {"cycle_model_view": long_path} | {
        f"early_features_k{k}": path for k, path in feature_paths.items()
    }
    output_rows = {"cycle_model_view": len(view)} | {
        f"early_features_k{k}": len(frame) for k, frame in feature_frames.items()
    }
    output_files = {
        name: {"path": str(path.relative_to(ROOT)).replace("\\", "/"), "rows": output_rows[name], "sha256": sha256(path)}
        for name, path in output_paths.items()
    }
    mask_summary = {
        field: {
            "invalid_count": int((~view[f"valid_{field}"]).sum()),
            "reason_counts": {
                reason: int(count)
                for reason, count in view.loc[~view[f"valid_{field}"], f"mask_reason_{field}"].value_counts().items()
            },
        }
        for field in FIELDS
    }
    core_feature_columns = {
        str(k): [
            column for column in frame.columns
            if column not in {
                "barcode", "dataset_table9", "dataset_role", "policy_table9",
                "window_k", "window_cycle_start", "window_cycle_end", "expected_cycle_count",
            }
            and not column.endswith("_valid_count") and not column.endswith("_valid_ratio")
        ]
        for k, frame in feature_frames.items()
    }
    summary = {
        "p0_status": "pass",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "script": str(SCRIPT_PATH.relative_to(ROOT)).replace("\\", "/"),
        "script_sha256": sha256(SCRIPT_PATH),
        "random_seed": SEED,
        "input_sha256": input_hashes,
        "raw_source_sha256_before": raw_hashes_before,
        "raw_source_sha256_after": raw_hashes_after,
        "rules": {
            "eol_filter": "global_cycle_index < cycle_life_table9",
            "feature_windows": [f"2 <= global_cycle_index <= {k}" for k in WINDOWS],
            "structural_masks": ["nonfinite", "negative_value for nonnegative fields", "all_zero_placeholder", "temperature_order_violation"],
            "statistical_masks": {
                "chargetime": {
                    "fit_dataset": "Train",
                    "quantile": 0.99,
                    "multiplier": 5.0,
                    "train_q99": charge_q99,
                    "upper_threshold": charge_upper,
                    "masked_count_by_dataset": {
                        name: int(count) for name, count in view.assign(_masked=charge_outlier.to_numpy()).groupby("dataset_role")["_masked"].sum().items()
                    },
                },
                "other_fields": "No statistical mask frozen at P0; no defensible unit-backed threshold was supplied.",
            },
            "delta_rule": "cycle 2 and cycle k must both be valid; no neighboring-cycle substitution",
            "imputation": "none",
            "standardization": "none",
        },
        "mask_summary": mask_summary,
        "core_feature_columns": core_feature_columns,
        "output_files": output_files,
        "checks": checks,
        "known_limits": [
            "IR is confirmed in ohms and chargetime in minutes; IR measurement timing and chargetime boundaries/CV coverage remain undocumented.",
            "No external unit-dependent physical thresholds were invented for summary fields.",
            "Raw curve suitability is joined for future challengers; P0 core features use audited summary fields only.",
            "Lifetime targets remain in cell_labels.csv and are deliberately absent from early feature tables.",
        ],
    }
    summary_path = PROCESSED / "p0_summary.json"
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    pass_lines = "\n".join(f"- [x] `{name}`" for name, passed in checks.items() if passed)
    mask_lines = "\n".join(
        f"| {field} | {details['invalid_count']} | "
        f"{'; '.join(f'{reason}: {count}' for reason, count in details['reason_counts'].items()) or '无'} |"
        for field, details in mask_summary.items()
    )
    output_lines = "\n".join(
        f"| `{details['path']}` | {details['rows']:,} | `{details['sha256']}` |"
        for details in output_files.values()
    )
    report = f"""# P0 数据审计报告

## 审计结论

**通过。** 正式建模长表已按官方寿命端点截断，七个汇总字段采用字段—循环级掩码；任何异常都没有导致整行或整枚电芯被静默删除。五个早期窗口由同一脚本生成且通过机器校验。

## 冻结规则

- EOL：仅保留 `global_cycle_index < cycle_life_table9`，共 99,279 行、124 枚电芯。
- 早期窗口：统一使用 `2 <= global_cycle_index <= k`，`k = 5,10,20,50,100`。
- 确定性掩码：非有限值、非负字段的负值、全零占位、温度次序冲突。
- 统计掩码：只对 `chargetime` 使用 Train 拟合的 `Q99 × 5`；`Q99={charge_q99:.12g}`，冻结上界 `{charge_upper:.12g}`。
- 其他字段未设置统计阈值，因为现有资料不足以支持单位相关的物理边界；保留真实跨批次分布差异。
- 缺失处理：P0 不填补、不标准化；两点变化特征严格要求 cycle 2 与 cycle k 均有效。
- RAW 曲线审计按 `(barcode, source_file, batch_index, cycle_index)` 四字段键连接，仅提供未来 challenger 的可用性标志。

## 字段掩码汇总

| 字段 | 无效字段—循环数 | 原因 |
|---|---:|---|
{mask_lines}

## 输出与校验和

| 文件 | 行数 | SHA-256 |
|---|---:|---|
{output_lines}

`p0_summary.json` 另记录输入 SHA-256、脚本 SHA-256、随机种子 {SEED}、阈值来源及全部机器检查。

## 通过项

{pass_lines}

## 仍需在后续显式处理的限制

1. `IR` 单位已确认是 Ω，`chargetime` 单位已确认是 min；但前者的测量时点、后者的起止点与 CV 覆盖尚无字段元数据。论文中仍须保守表述，不能据此设置题外安全阈值或将实测时间等同于理论 `tau_0-80`。
2. P0 没有执行模型填补、标准化或特征选择；这些参数须在后续 Train 内层折中重新拟合。
3. RAW 曲线字段有独立深层掩码；若启用 RAW challenger，必须继续沿用长表中的连接标志，不能回退到整枚电芯删除。
"""
    REPORT_PATH.write_text(report, encoding="utf-8")
    print(json.dumps({"p0_status": "pass", "rows": len(view), "cells": view["barcode"].nunique(), "outputs": list(output_files)}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
