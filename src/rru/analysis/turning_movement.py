"""
Turning Movement Analysis — fishbone-labeled RRU intersection vehicles.

Turning movement remains based on the fishbone preprocessing/labeled dataset
because the branch links are needed to describe intersection activity beyond the
RRU backbone analytical filter used for OD.
"""

from pathlib import Path

import polars as pl

from src.rru.analysis.od_matrix import build_trip_table, classify_turning_movement

INPUT_LABELED = Path("./data/matched/gps_rru_labeled.parquet")
OUTPUT_DIR = Path("./results/turning_movement")


def main():
    """Run turning movement analysis on fishbone-labeled trajectories."""
    if not INPUT_LABELED.exists():
        print("❌ Fishbone labeled data not found. Run intersection_labeling.py first.")
        return

    print(f"Reading {INPUT_LABELED}...")
    df = pl.read_parquet(INPUT_LABELED)
    print(f"  {df.height:,} pings")

    print("Building trip table...")
    trips = build_trip_table(df)
    print(f"  {trips.height:,} trips")

    print("Computing turning movements...")
    tm = classify_turning_movement(trips)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    tm_path = OUTPUT_DIR / "turning_movements.csv"
    tm.write_csv(tm_path)
    print(f"✓ Turning movements saved to {tm_path}")
    print(tm)


if __name__ == "__main__":
    main()
