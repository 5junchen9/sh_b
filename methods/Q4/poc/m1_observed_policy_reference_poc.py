"""Q4-M1 PoC: summarize existing-policy reference records, without new-policy selection."""
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[3]
TABLE = (
    ROOT / "results" / "Q4" / "experiments" / "existing_policy_round1" / "tables"
    / "q4_existing_policy_summary.csv"
)


def main() -> None:
    df = pd.read_csv(TABLE)
    required = {"policy_table9", "cell_count", "development_pareto", "pareto_scope"}
    if not required.issubset(df.columns):
        raise RuntimeError("existing-policy table has required columns missing")
    if df.empty:
        raise RuntimeError("existing-policy table is empty")
    if (pd.to_numeric(df["cell_count"], errors="raise") <= 0).any():
        raise RuntimeError("cell counts must be positive")
    pareto_n = int(df["development_pareto"].fillna(False).astype(bool).sum())
    total_cells = int(df["cell_count"].sum())
    scopes = set(df["pareto_scope"].dropna().astype(str))
    if not scopes:
        raise RuntimeError("pareto scope must be recorded")
    print("Q4-M1 observed-policy reference PoC PASS")
    print(f"policies={len(df)}; cells={total_cells}; development_pareto_count={pareto_n}")


if __name__ == "__main__":
    main()
