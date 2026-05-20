"""
Trajectory Segmentation Module — Time-gap based trip splitting.

Splits each MAID's ping sequence into separate "trips" using a configurable
time-gap threshold. A gap exceeding the threshold indicates a stop (parking,
entering a building, etc.) and marks the boundary between trips.

Reference: Zheng et al. (2015) — Trajectory Data Mining: An Overview.
Standard gap threshold: 30 minutes.
"""

import polars as pl
from pathlib import Path

# ── Configuration ───────────────────────────────────────────────────
# Gap threshold: 10 minutes (600 seconds).
# Nurlita (2024, same dataset/supervisors) used 10 min citing Zheng et al.:
# "observation gaps >10 minutes significantly degrade trajectory accuracy."
# This is more conservative than the common 30-min default, but appropriate
# for low-sampling-rate active MPD data where ~85% of pings are stationary.
DEFAULT_GAP_SECONDS = 600  # 10 minutes
MIN_PINGS_PER_TRIP = 2

INPUT_MATCHED = Path("./data/matched/gps_rru_matched.parquet")
OUTPUT_SEGMENTED = Path("./data/matched/gps_rru_segmented.parquet")


def segment_trips(
    df: pl.DataFrame,
    gap_seconds: int = DEFAULT_GAP_SECONDS,
    min_pings: int = MIN_PINGS_PER_TRIP,
) -> pl.DataFrame:
    """
    Segment MAID trajectories into trips by time-gap splitting.

    For each MAID, sequential pings are grouped into the same trip as long
    as the time gap between consecutive pings is ≤ gap_seconds. When a gap
    exceeds the threshold, a new trip_id is assigned.

    Parameters
    ----------
    df : pl.DataFrame
        Must contain columns: maid, timestamp (int64, unix seconds).
        Must be sorted by [maid, timestamp].
    gap_seconds : int
        Maximum allowed gap (seconds) between consecutive pings within a trip.
    min_pings : int
        Minimum number of pings required for a trip to be kept.

    Returns
    -------
    pl.DataFrame
        Input DataFrame with added column:
        - trip_id: str — Unique trip identifier (format: "maid__seq")
    """
    # Ensure sorted
    df = df.sort(["maid", "timestamp"])

    # Compute time gap between consecutive pings within the same MAID
    df = df.with_columns(
        dt=pl.col("timestamp") - pl.col("timestamp").shift(1).over("maid")
    )

    # Mark trip boundaries: first ping of a MAID OR gap > threshold
    df = df.with_columns(
        is_new_trip=(
            pl.col("dt").is_null() | (pl.col("dt") > gap_seconds)
        ).cast(pl.Int32)
    )

    # Cumulative sum of trip boundaries within each MAID = trip sequence number
    df = df.with_columns(
        trip_seq=pl.col("is_new_trip").cum_sum().over("maid")
    )

    # Build unique trip_id: maid + "__" + sequence number
    df = df.with_columns(
        trip_id=pl.col("maid") + "__" + pl.col("trip_seq").cast(pl.String)
    )

    # Filter trips with fewer than min_pings pings
    trip_counts = (
        df.group_by("trip_id")
        .len()
        .filter(pl.col("len") >= min_pings)
        .select("trip_id")
    )
    df = df.join(trip_counts, on="trip_id", how="inner")

    # Clean up temporary columns
    df = df.drop(["dt", "is_new_trip", "trip_seq"])

    return df


def summarize_trips(df: pl.DataFrame) -> pl.DataFrame:
    """
    Produce a trip-level summary table.

    Returns a DataFrame with one row per trip containing:
    - trip_id, maid
    - n_pings: number of pings
    - duration_seconds: time span of the trip
    - start_time, end_time: unix timestamps
    - start_lat, start_lon, end_lat, end_lon: coordinates
    - n_edges: number of unique matched edges traversed
    """
    return (
        df.sort(["trip_id", "timestamp"])
        .group_by("trip_id", maintain_order=True)
        .agg(
            maid=pl.col("maid").first(),
            n_pings=pl.len(),
            start_time=pl.col("timestamp").min(),
            end_time=pl.col("timestamp").max(),
            duration_seconds=pl.col("timestamp").max() - pl.col("timestamp").min(),
            start_lat=pl.col("latitude").first(),
            start_lon=pl.col("longitude").first(),
            end_lat=pl.col("latitude").last(),
            end_lon=pl.col("longitude").last(),
            n_edges=pl.col("matched_edge").n_unique(),
            edges_traversed=pl.col("matched_edge").unique(),
        )
    )


def main():
    """Run trajectory segmentation on matched data."""
    if not INPUT_MATCHED.exists():
        print("❌ Map-matched data not found. Run map_matching.py first.")
        return

    print(f"Reading {INPUT_MATCHED}...")
    df = pl.read_parquet(INPUT_MATCHED)
    print(f"  {df.height:,} pings, {df['maid'].n_unique():,} MAIDs")

    # Segment into trips
    print(f"Segmenting trips (gap threshold: {DEFAULT_GAP_SECONDS}s, "
          f"min pings: {MIN_PINGS_PER_TRIP})...")
    df_seg = segment_trips(df, DEFAULT_GAP_SECONDS, MIN_PINGS_PER_TRIP)

    n_trips = df_seg["trip_id"].n_unique()
    n_maids = df_seg["maid"].n_unique()
    print(f"\n--- Segmentation Summary ---")
    print(f"  Total trips: {n_trips:,}")
    print(f"  Total pings (in valid trips): {df_seg.height:,}")
    print(f"  MAIDs with valid trips: {n_maids:,}")
    print(f"  Avg trips/MAID: {n_trips / n_maids:.1f}")

    # Trip-level summary
    trip_summary = summarize_trips(df_seg)
    print(f"\n  Trip duration stats (seconds):")
    print(f"    min={trip_summary['duration_seconds'].min()}")
    print(f"    median={trip_summary['duration_seconds'].median():.0f}")
    print(f"    mean={trip_summary['duration_seconds'].mean():.0f}")
    print(f"    max={trip_summary['duration_seconds'].max():,}")
    print(f"  Pings/trip stats:")
    print(f"    min={trip_summary['n_pings'].min()}")
    print(f"    median={trip_summary['n_pings'].median():.0f}")
    print(f"    mean={trip_summary['n_pings'].mean():.1f}")
    print(f"    max={trip_summary['n_pings'].max():,}")

    # Save segmented data
    OUTPUT_SEGMENTED.parent.mkdir(parents=True, exist_ok=True)
    df_seg.write_parquet(OUTPUT_SEGMENTED, compression="zstd")
    size_mb = OUTPUT_SEGMENTED.stat().st_size / 1024 / 1024
    print(f"\n✓ Saved: {OUTPUT_SEGMENTED.resolve()} ({size_mb:.1f} MB)")

    # Save trip summary
    trip_summary_path = OUTPUT_SEGMENTED.parent / "trip_summary.parquet"
    trip_summary.write_parquet(trip_summary_path, compression="zstd")
    print(f"✓ Trip summary: {trip_summary_path.resolve()}")


if __name__ == "__main__":
    main()
