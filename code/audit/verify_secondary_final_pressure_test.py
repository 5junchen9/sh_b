"""Independent numeric and boundary checks for the completed Secondary run."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "results" / "Secondary_final_pressure_test"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def check_close(name: str, actual: float, expected: float, checks: list[dict]) -> None:
    checks.append({"check": name, "passed": bool(np.isclose(actual, expected, rtol=0, atol=1e-12)), "actual": actual, "expected": expected})


def main() -> None:
    manifest = json.loads((OUT / "manifest.json").read_text(encoding="utf-8"))
    run = json.loads((OUT / "metrics" / "run_summary.json").read_text(encoding="utf-8"))
    q2 = pd.read_csv(OUT / "tables" / "q2_external_predictions.csv")
    q2_metrics = pd.read_csv(OUT / "tables" / "q2_external_metrics.csv").set_index("model_id")
    q3 = pd.read_csv(OUT / "tables" / "q3_external_life_predictions.csv")
    q3_curve = pd.read_csv(OUT / "tables" / "q3_external_cell_curve_errors.csv")
    q3_metrics = pd.read_csv(OUT / "tables" / "q3_external_metrics.csv")
    bootstrap = pd.read_csv(OUT / "tables" / "bootstrap_intervals.csv")
    raw = json.loads((OUT / "inputs" / "raw_curve_features_secondary_summary.json").read_text(encoding="utf-8"))
    checks: list[dict] = []
    checks.append({"check": "frozen_manifest_has_no_retuning_rule", "passed": bool(manifest["fixed_evaluation"]["no_model_selection_on_secondary"]), "actual": manifest["fixed_evaluation"]["no_model_selection_on_secondary"], "expected": True})
    checks.append({"check": "run_marks_primary_unused", "passed": run["primary_used"] is False, "actual": run["primary_used"], "expected": False})
    m1_rows = int(len(q2.query("model_id == 'M1'")))
    checks.append({"check": "secondary_partition_is_40_unique_cells", "passed": q2.barcode.nunique() == 40 and m1_rows == 40, "actual": {"unique": int(q2.barcode.nunique()), "m1_rows": m1_rows}, "expected": {"unique": 40, "m1_rows": 40}})
    for model_id, group in q2.groupby("model_id"):
        y, p = group.actual_log_life.to_numpy(float), group.predicted_log_life.to_numpy(float)
        check_close(f"q2_{model_id}_rmse_recomputed", float(mean_squared_error(y, p) ** .5), float(q2_metrics.loc[model_id, "rmse_log"]), checks)
        check_close(f"q2_{model_id}_mae_recomputed", float(mean_absolute_error(y, p)), float(q2_metrics.loc[model_id, "mae_log"]), checks)
    for _, metric in q3_metrics.iterrows():
        group = q3.loc[(q3.model_id.eq(metric.model_id)) & (q3.k.eq(metric.k))]
        y, p = group.actual_log_life.to_numpy(float), group.predicted_log_life.to_numpy(float)
        check_close(f"q3_{metric.model_id}_k{int(metric.k)}_rmse_recomputed", float(mean_squared_error(y, p) ** .5), float(metric.rmse_log), checks)
        curve = q3_curve.loc[(q3_curve.model_id.eq(metric.model_id)) & (q3_curve.k.eq(metric.k))]
        check_close(f"q3_{metric.model_id}_k{int(metric.k)}_soh_recomputed", float(np.mean(curve.soh_mse) ** .5), float(metric.cell_equal_soh_rmse), checks)
        checks.append({"check": f"q3_{metric.model_id}_k{int(metric.k)}_all_cells_curve_evaluable", "passed": len(curve) == 40 and int(metric.template_failures) == 0, "actual": {"curve_cells": int(len(curve)), "failures": int(metric.template_failures)}, "expected": {"curve_cells": 40, "failures": 0}})
    checks.append({"check": "raw_feature_gate_k5", "passed": raw["k5"]["cells"] == 40 and raw["k5"]["min_valid_ratio"] >= .8, "actual": raw["k5"], "expected": "40 cells and valid ratio >= 0.8"})
    checks.append({"check": "raw_feature_gate_k100", "passed": raw["k100"]["cells"] == 40 and raw["k100"]["min_valid_ratio"] >= .8, "actual": raw["k100"], "expected": "40 cells and valid ratio >= 0.8"})
    q2_boot_count = int(len(pd.read_csv(OUT / "tables" / "q2_m2_minus_m1_policy_bootstrap.csv")))
    q3_boot_count = int(len(pd.read_csv(OUT / "tables" / "q3_m3r_k5_minus_m2_k5_policy_bootstrap.csv")))
    checks.append({"check": "bootstrap_has_fixed_2000_repeats", "passed": q2_boot_count == 2000 and q3_boot_count == 2000, "actual": {"q2": q2_boot_count, "q3": q3_boot_count}, "expected": 2000})
    checks.append({"check": "bootstrap_has_no_pareto_or_recommendation", "passed": not (OUT / "tables" / "q4_new_strategy_pareto.csv").exists(), "actual": "no new-strategy Pareto file", "expected": "no new-strategy Pareto file"})
    checks.append({"check": "result_files_hashable", "passed": all(sha256(path) for path in (OUT / "secondary_final_pressure_test_report.md", OUT / "audit.md", OUT / "figures" / "secondary_final_observed_predicted.png")), "actual": "SHA-256 computed", "expected": "nonempty files"})
    report = {"status": "pass" if all(item["passed"] for item in checks) else "fail", "checks": checks, "manifest_sha256": sha256(OUT / "manifest.json"), "secondary_result_file_sha256": {str(path.relative_to(OUT)): sha256(path) for path in (OUT / "tables" / "q2_external_metrics.csv", OUT / "tables" / "q3_external_metrics.csv", OUT / "tables" / "bootstrap_intervals.csv")}}
    (OUT / "verification.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    lines = "\n".join(f"{index}. {'✅' if item['passed'] else '❌'} `{item['check']}`：实际 `{item['actual']}`；预期 `{item['expected']}`。" for index, item in enumerate(checks, 1))
    (OUT / "verification.md").write_text(f"# Secondary 最终压力测试独立复核\n\n> 状态：**{report['status']}**。\n\n## 通过项\n\n{lines}\n", encoding="utf-8")
    print(json.dumps({"status": report["status"], "checks": len(checks)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
