"""Run Q4 existing-policy sensitivity checks for the Round 2 M2-k100 aggregation."""
from __future__ import annotations

import sys
from pathlib import Path

CODE_DIR = Path(__file__).resolve().parent
if str(CODE_DIR) not in sys.path:
    sys.path.insert(0, str(CODE_DIR))
import q4_existing_policy_sensitivity as core


ROOT = Path(__file__).resolve().parents[2]
core.INPUT = ROOT / "results" / "Q4" / "experiments" / "existing_policy_round2_m2k100" / "tables" / "q4_existing_policy_summary.csv"
core.OUT = ROOT / "robustness" / "Q4" / "round2_m2k100"

if __name__ == "__main__":
    core.main()
