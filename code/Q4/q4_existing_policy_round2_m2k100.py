"""Run the existing-policy Q4 aggregation with Q3 Round 2 M2-k100 evidence.

The imported implementation supplies the common aggregation and plotting logic.
This thin, explicit entry point changes only output/input locations, preserving the
historical Round 1 artifact and preventing a Round 2 result from being mislabeled.
"""
from __future__ import annotations

import sys
from pathlib import Path

CODE_DIR = Path(__file__).resolve().parent
if str(CODE_DIR) not in sys.path:
    sys.path.insert(0, str(CODE_DIR))
import q4_existing_policy_evaluation as core


ROOT = Path(__file__).resolve().parents[2]
core.OUT = ROOT / "results" / "Q4" / "experiments" / "existing_policy_round2_m2k100"
core.TABLES, core.FIGURES, core.METRICS, core.LOGS = (core.OUT / item for item in ("tables", "figures", "metrics", "logs"))
core.Q3_TRAIN = ROOT / "results" / "Q3" / "experiments" / "round2_joint" / "tables" / "joint_oof_life_predictions.csv"
core.SOH_TRAIN = ROOT / "results" / "Q3" / "experiments" / "round2_joint" / "tables" / "joint_oof_soh120_predictions.csv"

if __name__ == "__main__":
    core.main()
