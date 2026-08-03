"""Q2 PoC M2: low-degree interaction Ridge, policy-group OOF."""
from __future__ import annotations

from pathlib import Path
import json
import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_squared_error
from sklearn.model_selection import GroupKFold
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import PolynomialFeatures, StandardScaler

ROOT = Path(__file__).resolve().parents[3]
summary = json.loads((ROOT / "data" / "processed" / "p0_summary.json").read_text(encoding="utf-8"))
if summary.get("p0_status") != "pass":
    raise RuntimeError("Q2 PoC requires frozen P0 input.")
labels = pd.read_csv(ROOT / "data" / "processed" / "cell_labels.csv")
train = labels.loc[labels["dataset_table9"].eq("Train")].copy()
X = train[["C1", "Q1_percent", "C2"]].to_numpy(float)
y = np.log(train["cycle_life_table9"].to_numpy(float))
groups = train["policy_table9"].to_numpy()
n_splits = min(5, pd.Series(groups).nunique())
oof = np.full(len(train), np.nan)
for fit_idx, test_idx in GroupKFold(n_splits=n_splits).split(X, y, groups):
    model = make_pipeline(PolynomialFeatures(degree=2, include_bias=False), StandardScaler(), Ridge(alpha=3.0))
    model.fit(X[fit_idx], y[fit_idx])
    oof[test_idx] = model.predict(X[test_idx])
rmse_log = float(mean_squared_error(y, oof) ** 0.5)
mae_log = float(np.mean(np.abs(y - oof)))
print(json.dumps({"candidate": "Q2-M2", "n_cells": len(train), "n_policy_groups": int(pd.Series(groups).nunique()), "rmse_log": rmse_log, "mae_log": mae_log}, ensure_ascii=False))
