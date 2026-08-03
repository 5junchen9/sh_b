"""Q1-M2 PoC: policy-grouped lifetime comparison using real labels only."""
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[3]
LABELS = ROOT / "data" / "processed" / "cell_labels.csv"


def main() -> None:
    df = pd.read_csv(LABELS)
    grouped = (
        df.groupby("policy_table9", dropna=False)["cycle_life_table9"]
        .agg(["count", "mean", "min", "max"])
        .reset_index()
    )
    repeated = grouped.loc[grouped["count"] >= 2].sort_values("mean")
    if repeated.empty:
        raise RuntimeError("no repeated policy group is available")
    low = repeated.iloc[0]
    high = repeated.iloc[-1]
    print("Q1-M2 policy-grouped PoC PASS")
    print(
        f"all_policies={len(grouped)}; repeated_policies={len(repeated)}; "
        f"lowest_mean={low['mean']:.1f}; highest_mean={high['mean']:.1f}"
    )


if __name__ == "__main__":
    main()
