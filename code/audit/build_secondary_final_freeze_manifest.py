"""Freeze all selections required before the one-time Secondary pressure test.

The script selects full-Train Ridge penalties using the already fixed inner
policy-group CV rule, records hashes, and deliberately emits no Secondary
metric or feature.  The companion runner refuses to execute without this
manifest and its matching hashes.
"""
from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_squared_error
from sklearn.model_selection import GroupKFold
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import PolynomialFeatures, StandardScaler


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "results" / "Secondary_final_pressure_test" / "manifest.json"
LABELS = ROOT / "data" / "processed" / "cell_labels.csv"
P0 = ROOT / "data" / "processed" / "p0_summary.json"
ALPHAS = [0.01, 0.1, 1.0, 3.0, 10.0, 30.0, 100.0]
STRATEGY = ["C1", "Q1_percent", "C2"]
EARLY = [
    "QDischarge_mean", "QDischarge_slope", "QDischarge_delta_cycle2_to_k",
    "QCharge_mean", "QCharge_slope", "IR_mean", "IR_slope", "Tmax_mean",
    "Tavg_mean", "Tmin_mean", "chargetime_mean", "chargetime_slope",
]
RAW = ["raw_charge_v_mean_mean", "raw_charge_v_p95_mean", "raw_charge_v_p95_slope"]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def ridge(alpha: float):
    return make_pipeline(StandardScaler(), Ridge(alpha=alpha))


def q2_model(kind: str, alpha: float):
    steps = []
    if kind == "M2":
        steps.append(PolynomialFeatures(2, include_bias=False))
    steps += [StandardScaler(), Ridge(alpha=alpha)]
    return make_pipeline(*steps)


def choose_alpha(x: np.ndarray, y: np.ndarray, groups: np.ndarray, kind: str = "ridge") -> float:
    cv = GroupKFold(n_splits=min(4, pd.Series(groups).nunique()))
    scores: list[float] = []
    for alpha in ALPHAS:
        fold = []
        for train_idx, valid_idx in cv.split(x, y, groups):
            model = ridge(alpha) if kind == "ridge" else q2_model(kind, alpha)
            fold.append(mean_squared_error(y[valid_idx], model.fit(x[train_idx], y[train_idx]).predict(x[valid_idx])))
        scores.append(float(np.mean(fold)))
    return float(ALPHAS[int(np.argmin(scores))])


def require_decided(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    if "status: DECIDED" not in text or "<<<HUMAN>>>" in text:
        raise RuntimeError(f"Secondary gate is not decided: {path.relative_to(ROOT)}")


def main() -> None:
    require_decided(ROOT / "methods" / "Q3" / "decisions" / "robustness-checker_modeler_decision.md")
    require_decided(ROOT / "methods" / "Q3" / "decisions" / "result-report-generator_modeler_decision.md")
    if json.loads(P0.read_text(encoding="utf-8")).get("p0_status") != "pass":
        raise RuntimeError("P0 is not passed.")
    labels = pd.read_csv(LABELS)
    train = labels.loc[labels.dataset_table9.eq("Train")].copy()
    if len(train) != 41 or train.barcode.duplicated().any() or train.policy_table9.nunique() != 40:
        raise RuntimeError("Frozen Train partition must be 41 unique cells in 40 policy groups.")
    y = np.log(train.cycle_life_table9.to_numpy(float))
    groups = train.policy_table9.to_numpy()
    early_paths = {k: ROOT / "data" / "processed" / f"early_features_k{k}.csv" for k in (5, 100)}
    early = {k: pd.read_csv(path).query("dataset_table9 == 'Train'").set_index("barcode").loc[train.barcode] for k, path in early_paths.items()}
    raw_train = pd.read_csv(ROOT / "data" / "processed" / "raw_curve_features_train_k5.csv").set_index("barcode").loc[train.barcode]
    if (raw_train.raw_valid_ratio < 0.8).any():
        raise RuntimeError("Frozen M3R Train RAW validity gate failed.")
    q2_m1_alpha = choose_alpha(train[STRATEGY].to_numpy(float), y, groups, "M1")
    q2_m2_alpha = choose_alpha(train[STRATEGY].to_numpy(float), y, groups, "M2")
    q3_m2_k5_alpha = choose_alpha(early[5][EARLY].to_numpy(float), y, groups)
    q3_m2_k100_alpha = choose_alpha(early[100][EARLY].to_numpy(float), y, groups)
    m3r_x = np.c_[train[STRATEGY].to_numpy(float), early[5][EARLY].to_numpy(float), raw_train[RAW].to_numpy(float)]
    q3_m3r_k5_alpha = choose_alpha(m3r_x, y, groups)
    source_relatives = [
        "data/processed/p0_summary.json", "data/processed/cell_labels.csv", "data/processed/cycle_model_view.csv",
        "data/processed/early_features_k5.csv", "data/processed/early_features_k100.csv",
        "data/processed/raw_curve_features_train_k5.csv", "outputs/data_audit/mat_deep_cycle_flags.csv",
        "data_1.mat", "data_2.mat", "data_3.mat", "methods/secondary_final_pressure_test_protocol.md",
        "methods/Q3/decisions/robustness-checker_modeler_decision.md",
        "methods/Q3/decisions/result-report-generator_modeler_decision.md",
        "code/audit/build_secondary_final_freeze_manifest.py", "code/audit/run_secondary_final_pressure_test.py",
        "src/extract_q3_raw_curve_features_secondary.m", "code/Q2/q2_run_all.py",
        "code/Q2/q2b_primary_confirmation.py", "code/Q3/q3_run_joint_comparison.py", "code/Q3/q3_run_raw_curve_challenger.py",
    ]
    source_hashes = {relative: sha256(ROOT / relative) for relative in source_relatives}
    payload = {
        "schema_version": 1,
        "artifact_type": "prospective_secondary_final_pressure_test_freeze",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "authorization": "Human authorized one-time Secondary execution with no retuning or result-driven callback.",
        "secondary_status_before_run": "not_read_by_this_final_protocol",
        "fixed_partitions": {"train": "Train", "secondary": "Sec. test", "train_cells": 41, "secondary_cells": 40},
        "fixed_models": {
            "q2_m1_main_effect_ridge": {"features": STRATEGY, "alpha": q2_m1_alpha},
            "q2_m2_interaction_sensitivity": {"features": STRATEGY, "alpha": q2_m2_alpha, "polynomial_degree": 2},
            "q2_p3_provisional_for_q4_observation": {"features": STRATEGY, "n_knots": 4, "alpha": 0.03},
            "q3_m2_k5_comparator": {"features": EARLY, "alpha": q3_m2_k5_alpha},
            "q3_m2_k100_calibration": {"features": EARLY, "alpha": q3_m2_k100_alpha},
            "q3_m3r_k5_screening": {"features": [*STRATEGY, *EARLY, *RAW], "alpha": q3_m3r_k5_alpha, "raw_gate": "raw_valid_ratio >= 0.8"},
        },
        "fixed_evaluation": {"bootstrap_repeats": 2000, "bootstrap_unit": "policy_table9 blocks", "seed": 20260802, "q3_windows": [5, 100], "no_model_selection_on_secondary": True},
        "q4_scope": "existing Secondary policies may be described only; no new strategy optimization, Pareto selection, or recommendation is permitted.",
        "source_sha256": source_hashes,
        "runner_command": ".\\.venv\\Scripts\\python.exe -W error l1\\code\\audit\\run_secondary_final_pressure_test.py",
        "raw_feature_command": "D:\\13470\\matlab\\bin\\matlab.exe -batch \"addpath(fullfile(pwd,'l1','src')); extract_q3_raw_curve_features_secondary\"",
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"manifest": str(OUT), "fixed_models": payload["fixed_models"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
