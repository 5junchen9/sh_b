"""Q1-M1 PoC: cell-level lifetime description on the actual label table."""
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[3]
LABELS = ROOT / "data" / "processed" / "cell_labels.csv"


def main() -> None:
    df = pd.read_csv(LABELS)
    life = pd.to_numeric(df["cycle_life_table9"], errors="raise")
    if len(df) != 124:
        raise RuntimeError(f"expected 124 official cells, got {len(df)}")
    if life.isna().any() or (life <= 0).any():
        raise RuntimeError("life label is missing or non-positive")
    summary = {
        "n": int(life.size),
        "median": float(life.median()),
        "q1": float(life.quantile(0.25)),
        "q3": float(life.quantile(0.75)),
        "min": float(life.min()),
        "max": float(life.max()),
    }
    print("Q1-M1 cell-level descriptive PoC PASS")
    print(
        "n={n}; median={median:.1f}; IQR=[{q1:.2f}, {q3:.2f}]; "
        "range=[{min:.0f}, {max:.0f}]".format(**summary)
    )


if __name__ == "__main__":
    main()
