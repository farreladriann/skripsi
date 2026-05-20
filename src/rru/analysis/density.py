"""
Traffic Density Estimation — Count unique MAIDs per intersection zone per time window.

Produces:
1. Time-of-day density profiles per intersection (hourly, 15-min bins)
2. Daily density time series
3. Peak vs off-peak comparison
4. Weekday vs weekend comparison
5. Monthly aggregated profiles

Density is measured as unique MAID count, not raw ping count,
to avoid over-counting devices with high ping frequencies.
"""

import polars as pl
import numpy as np
import json
from pathlib import Path

from src.rru.analysis.intersection_labeling import INTERSECTION_ORDER

# ── Configuration ───────────────────────────────────────────────────
INPUT_LABELED = Path("./data/matched/gps_rru_labeled.parquet")
OUTPUT_DIR = Path("./results/density")

WIB_OFFSET_HOURS = 7
MORNING_PEAK = (7, 9)
EVENING_PEAK = (16, 18)


def _add_temporal_columns(df: pl.DataFrame) -> pl.DataFrame:
    """Add WIB-based temporal columns for density aggregation."""
    ts = pl.col("timestamp")
    ts_wib = ts + WIB_OFFSET_HOURS * 3600

    return df.with_columns(
        hour_wib=((ts_wib % 86400) // 3600).cast(pl.Int32),
        minute_15=((ts_wib % 86400) // 900).cast(pl.Int32),  # 0–95 (96 bins)
        date_wib=(
            pl.from_epoch(ts, time_unit="s")
            .dt.offset_by(f"{WIB_OFFSET_HOURS}h")
            .dt.date()
        ),
        dow=((ts_wib // 86400 + 3) % 7).cast(pl.Int32),  # 0=Mon
        month=(
            pl.from_epoch(ts, time_unit="s")
            .dt.offset_by(f"{WIB_OFFSET_HOURS}h")
            .dt.strftime("%Y-%m")
        ),
    ).with_columns(
        is_weekday=pl.col("dow") < 5,
        is_peak=(
            (pl.col("hour_wib").is_between(MORNING_PEAK[0], MORNING_PEAK[1] - 1))
            | (pl.col("hour_wib").is_between(EVENING_PEAK[0], EVENING_PEAK[1] - 1))
        ),
    )


def compute_hourly_density(df: pl.DataFrame) -> pl.DataFrame:
    """
    Count unique MAIDs per intersection per hour-of-day (WIB).

    Returns: DataFrame with columns [intersection, hour_wib, n_maids, n_pings]
    averaged across all days in the dataset.
    """
    # Only pings in intersection zones
    in_zone = df.filter(pl.col("in_intersection_zone"))

    # Count unique MAIDs per intersection per date per hour
    daily_hourly = (
        in_zone.group_by(["nearest_intersection", "date_wib", "hour_wib"])
        .agg(
            n_maids=pl.col("maid").n_unique(),
            n_pings=pl.len(),
        )
    )

    # Average across days to get typical hourly profile
    hourly = (
        daily_hourly.group_by(["nearest_intersection", "hour_wib"])
        .agg(
            avg_maids=pl.col("n_maids").mean().round(1),
            avg_pings=pl.col("n_pings").mean().round(1),
            total_maids=pl.col("n_maids").sum(),
            n_days=pl.len(),
        )
        .sort(["nearest_intersection", "hour_wib"])
    )

    return hourly


def compute_15min_density(df: pl.DataFrame) -> pl.DataFrame:
    """Count unique MAIDs per intersection per 15-minute bin (WIB)."""
    in_zone = df.filter(pl.col("in_intersection_zone"))

    daily_15min = (
        in_zone.group_by(["nearest_intersection", "date_wib", "minute_15"])
        .agg(
            n_maids=pl.col("maid").n_unique(),
            n_pings=pl.len(),
        )
    )

    profile = (
        daily_15min.group_by(["nearest_intersection", "minute_15"])
        .agg(
            avg_maids=pl.col("n_maids").mean().round(2),
            total_maids=pl.col("n_maids").sum(),
            n_days=pl.len(),
        )
        .sort(["nearest_intersection", "minute_15"])
    )

    return profile


def compute_daily_density(df: pl.DataFrame) -> pl.DataFrame:
    """Count unique MAIDs per intersection per day."""
    in_zone = df.filter(pl.col("in_intersection_zone"))

    return (
        in_zone.group_by(["nearest_intersection", "date_wib"])
        .agg(
            n_maids=pl.col("maid").n_unique(),
            n_pings=pl.len(),
            dow=pl.col("dow").first(),
            is_weekday=pl.col("is_weekday").first(),
            month=pl.col("month").first(),
        )
        .sort(["nearest_intersection", "date_wib"])
    )


def compute_weekday_weekend_density(df: pl.DataFrame) -> pl.DataFrame:
    """Compare weekday vs weekend hourly density profiles."""
    in_zone = df.filter(pl.col("in_intersection_zone"))

    daily_hourly = (
        in_zone.group_by(["nearest_intersection", "date_wib", "hour_wib", "is_weekday"])
        .agg(
            n_maids=pl.col("maid").n_unique(),
        )
    )

    return (
        daily_hourly.group_by(["nearest_intersection", "hour_wib", "is_weekday"])
        .agg(
            avg_maids=pl.col("n_maids").mean().round(1),
            n_days=pl.len(),
        )
        .sort(["nearest_intersection", "is_weekday", "hour_wib"])
    )


def compute_monthly_density(df: pl.DataFrame) -> pl.DataFrame:
    """Monthly total unique MAIDs per intersection."""
    in_zone = df.filter(pl.col("in_intersection_zone"))

    return (
        in_zone.group_by(["nearest_intersection", "month"])
        .agg(
            n_maids=pl.col("maid").n_unique(),
            n_pings=pl.len(),
        )
        .sort(["nearest_intersection", "month"])
    )


def save_density_results(df: pl.DataFrame, output_dir: Path):
    """Run all density computations and save results."""
    output_dir.mkdir(parents=True, exist_ok=True)

    # Add temporal columns
    df_t = _add_temporal_columns(df)

    # 1. Hourly density profiles
    print("  Computing hourly density profiles...")
    hourly = compute_hourly_density(df_t)
    hourly.write_csv(output_dir / "density_hourly.csv")

    # 2. 15-minute density profiles
    print("  Computing 15-minute density profiles...")
    q15 = compute_15min_density(df_t)
    q15.write_csv(output_dir / "density_15min.csv")

    # 3. Daily density time series
    print("  Computing daily density time series...")
    daily = compute_daily_density(df_t)
    daily.write_csv(output_dir / "density_daily.csv")

    # 4. Weekday vs Weekend
    print("  Computing weekday/weekend comparison...")
    wdwe = compute_weekday_weekend_density(df_t)
    wdwe.write_csv(output_dir / "density_weekday_weekend.csv")

    # 5. Monthly
    print("  Computing monthly density...")
    monthly = compute_monthly_density(df_t)
    monthly.write_csv(output_dir / "density_monthly.csv")

    # 6. Summary statistics
    in_zone = df_t.filter(pl.col("in_intersection_zone"))
    n_days = in_zone["date_wib"].n_unique()

    summary = {
        "total_pings_in_zones": int(in_zone.height),
        "total_unique_maids_in_zones": int(in_zone["maid"].n_unique()),
        "observation_days": int(n_days),
        "intersections": INTERSECTION_ORDER,
    }

    # Per-intersection summary
    int_summary = {}
    for name in INTERSECTION_ORDER:
        int_data = in_zone.filter(pl.col("nearest_intersection") == name)
        int_summary[name] = {
            "total_pings": int(int_data.height),
            "unique_maids": int(int_data["maid"].n_unique()),
            "avg_daily_maids": round(int_data["maid"].n_unique() / max(n_days, 1), 1),
        }
    summary["per_intersection"] = int_summary

    (output_dir / "summary.json").write_text(json.dumps(summary, indent=2))

    print(f"\n✓ Density results saved to {output_dir}")
    print(f"  Observation period: {n_days} days")
    for name in INTERSECTION_ORDER:
        s = int_summary[name]
        print(f"  {name}: {s['unique_maids']:,} MAIDs, "
              f"~{s['avg_daily_maids']:.0f}/day")


def main():
    """Run traffic density estimation."""
    if not INPUT_LABELED.exists():
        print("❌ Labeled data not found. Run intersection_labeling.py first.")
        return

    print(f"Reading {INPUT_LABELED}...")
    df = pl.read_parquet(INPUT_LABELED)
    print(f"  {df.height:,} pings, {df['maid'].n_unique():,} MAIDs")

    save_density_results(df, OUTPUT_DIR)


if __name__ == "__main__":
    main()
