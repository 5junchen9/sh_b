"""Q3 PoC M2: extrapolate early nominal-SOH slope to the 0.8 life threshold."""
from __future__ import annotations

from pathlib import Path
import json
import numpy as np
import pandas as pd
from sklearn.metrics import mean_squared_error

ROOT = Path(__file__).resolve().parents[3]
summary = json.loads((ROOT / "data" / "processed" / "p0_summary.json").read_text(encoding="utf-8"))
if summary.get("p0_status") != "pass":
    raise RuntimeError("Q3 PoC requires frozen P0 input.")
labels = pd.read_csv(ROOT / "data" / "processed" / "cell_labels.csv")
view = pd.read_csv(ROOT / "data" / "processed" / "cycle_model_view.csv", low_memory=False)
train = labels.loc[labels["dataset_table9"].eq("Train"), ["barcode", "cycle_life_table9"]]
predictions = []
for row in train.itertuples(index=False):
    curve = view.loc[(view["barcode"].eq(row.barcode)) & view["global_cycle_index"].between(2, 20) & view["valid_QDischarge"].astype(bool), ["global_cycle_index", "SOH_nom"]]
    if len(curve) < 3:
        continue
    slope, intercept = np.polyfit(curve["global_cycle_index"], curve["SOH_nom"], 1)
    estimate = (0.8 - intercept) / slope if slope < 0 else np.nan
    if np.isfinite(estimate) and estimate > 20:
        predictions.append((row.cycle_life_table9, estimate))
if not predictions:
    raise RuntimeError("No cell has a usable decreasing early-SOH slope.")
actual, predicted = map(np.asarray, zip(*predictions))
log_error = np.log(actual) - np.log(predicted)
result = {"candidate": "Q3-M2", "window_k": 20, "valid_cells": len(predictions), "rmse_log": float(mean_squared_error(np.log(actual), np.log(predicted)) ** 0.5), "mae_log": float(np.mean(abs(log_error)))}
print(json.dumps(result, ensure_ascii=False))
