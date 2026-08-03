"""Q4-M2 PoC: Train-only support-domain screening for pilot candidates."""
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[3]
TABLE = (
    ROOT / "results" / "Q4" / "experiments" / "train_dry_run_round1" / "tables"
    / "q4_q2_provisional_candidates.csv"
)


def main() -> None:
    df = pd.read_csv(TABLE)
    needed = {"status", "support_bootstrap_rate", "d5_raw", "d5_soc"}
    if not needed.issubset(df.columns):
        raise RuntimeError("candidate table has required columns missing")
    provisional = df.loc[df["status"].eq("Q2_provisional")].copy()
    if provisional.empty:
        raise RuntimeError("no Train-supported provisional candidate")
    min_support = provisional["support_bootstrap_rate"].min()
    print("Q4-M2 Train-only support and pilot PoC PASS")
    print(
        f"provisional={len(provisional)}; min_support={min_support:.3f}; "
        f"raw_d5_range=[{provisional['d5_raw'].min():.3f}, {provisional['d5_raw'].max():.3f}]"
    )


if __name__ == "__main__":
    main()
