"""Q1-M3 PoC: descriptive Train-Primary repeated-policy agreement."""
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[3]
TABLE = (
    ROOT / "results" / "Q1" / "experiments" / "round1" / "tables"
    / "q1_train_primary_repeated_policy.csv"
)


def main() -> None:
    df = pd.read_csv(TABLE)
    needed = {"train_life_mean", "primary_life_mean", "absolute_difference"}
    if not needed.issubset(df.columns):
        raise RuntimeError("agreement table has required columns missing")
    if df.empty:
        raise RuntimeError("agreement table is empty")
    if (df["absolute_difference"] < 0).any():
        raise RuntimeError("absolute differences must be non-negative")
    pearson = df["train_life_mean"].corr(df["primary_life_mean"], method="pearson")
    median_abs = df["absolute_difference"].median()
    if len(df) < 2 or pd.isna(pearson):
        raise RuntimeError("insufficient repeated-policy pairs")
    print("Q1-M3 repeated-policy agreement PoC PASS")
    print(f"pairs={len(df)}; pearson={pearson:.3f}; median_abs_diff={median_abs:.1f}")


if __name__ == "__main__":
    main()
