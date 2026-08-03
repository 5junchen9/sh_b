"""Q3 PoC M1: early k=20 summary-feature Ridge, policy-group OOF."""
from __future__ import annotations

from pathlib import Path
import json
import numpy as np
import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_squared_error
from sklearn.model_selection import GroupKFold
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parents[3]
summary = json.loads((ROOT / "data" / "processed" / "p0_summary.json").read_text(encoding="utf-8"))
if summary.get("p0_status") != "pass":
    raise RuntimeError("Q3 PoC requires frozen P0 input.")
labels = pd.read_csv(ROOT / "data" / "processed" / "cell_labels.csv")
features = pd.read_csv(ROOT / "data" / "processed" / "early_features_k20.csv")
cols = ["QDischarge_mean", "QDischarge_slope", "QDischarge_delta_cycle2_to_k", "QCharge_mean", "QCharge_slope", "IR_mean", "IR_slope", "Tmax_mean", "Tavg_mean", "Tmin_mean", "chargetime_mean", "chargetime_slope"]
frame = labels.merge(features[["barcode", *cols]], on="barcode", how="inner")
train = frame.loc[frame["dataset_table9"].eq("Train")].copy()
X, y = train[cols].to_numpy(float), np.log(train["cycle_life_table9"].to_numpy(float))
groups = train["policy_table9"].to_numpy()
oof = np.full(len(train), np.nan)
for fit_idx, test_idx in GroupKFold(n_splits=min(5, pd.Series(groups).nunique())).split(X, y, groups):
    model = make_pipeline(SimpleImputer(strategy="median"), StandardScaler(), Ridge(alpha=3.0))
    model.fit(X[fit_idx], y[fit_idx])
    oof[test_idx] = model.predict(X[test_idx])
print(json.dumps({"candidate": "Q3-M1", "window_k": 20, "n_cells": len(train), "rmse_log": float(mean_squared_error(y, oof) ** 0.5), "mae_log": float(np.mean(abs(y-oof)))}, ensure_ascii=False))
