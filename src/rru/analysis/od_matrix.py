"""
OD Matrix Extraction — Build origin-destination matrices from backbone-labeled trips.

Produces:
1. Aggregate OD matrix (6×6)
2. Hourly OD matrices (24 × 6×6)
3. Peak vs off-peak OD matrices
4. Weekday vs weekend OD matrices
5. Monthly OD matrices

OD uses the backbone-only analytical dataset generated after fishbone preprocessing.
"""

import polars as pl
import numpy as np
import json
from pathlib import Path
from datetime import datetime, timezone

from src.rru.analysis.intersection_labeling import INTERSECTION_ORDER

# ── Configuration ───────────────────────────────────────────────────
INPUT_LABELED = Path("./data/matched/backbone/gps_rru_labeled.parquet")
OUTPUT_DIR = Path("./results/od_matrix")

# WIB = UTC+7
WIB_OFFSET_HOURS = 7

# Peak hours (WIB)
MORNING_PEAK = (7, 9)    # 07:00–09:00
EVENING_PEAK = (16, 18)  # 16:00–18:00


def _ts_to_wib_hour(ts_col: pl.Expr) -> pl.Expr:
    """Convert unix timestamp to hour-of-day in WIB (UTC+7)."""
    return ((ts_col + WIB_OFFSET_HOURS * 3600) % 86400) // 3600


def _ts_to_wib_dow(ts_col: pl.Expr) -> pl.Expr:
    """Convert unix timestamp to day-of-week in WIB (0=Mon, 6=Sun)."""
    # Unix epoch (1970-01-01) was a Thursday (3)
    return ((ts_col + WIB_OFFSET_HOURS * 3600) // 86400 + 3) % 7


def _ts_to_month(ts_col: pl.Expr) -> pl.Expr:
    """Convert unix timestamp to YYYY-MM string."""
    return (
        pl.from_epoch(ts_col, time_unit="s")
        .dt.offset_by(f"{WIB_OFFSET_HOURS}h")
        .dt.strftime("%Y-%m")
    )


def build_trip_table(df: pl.DataFrame) -> pl.DataFrame:
    """
    Build a trip-level table with OD and temporal attributes.

    Each row represents one trip with:
    - trip_id, maid
    - trip_origin, trip_destination
    - start_time, end_time
    - hour_wib, dow, month, is_weekday, is_peak
    """
    trips = (
        df.sort(["trip_id", "timestamp"])
        .group_by("trip_id", maintain_order=True)
        .agg(
            maid=pl.col("maid").first(),
            trip_origin=pl.col("trip_origin").first(),
            trip_destination=pl.col("trip_destination").first(),
            start_time=pl.col("timestamp").min(),
            end_time=pl.col("timestamp").max(),
            n_pings=pl.len(),
        )
    )

    # Add temporal attributes
    trips = trips.with_columns(
        hour_wib=_ts_to_wib_hour(pl.col("start_time")).cast(pl.Int32),
        dow=_ts_to_wib_dow(pl.col("start_time")).cast(pl.Int32),
        month=_ts_to_month(pl.col("start_time")),
    )

    trips = trips.with_columns(
        is_weekday=pl.col("dow") < 5,
        is_peak=(
            (pl.col("hour_wib").is_between(MORNING_PEAK[0], MORNING_PEAK[1] - 1))
            | (pl.col("hour_wib").is_between(EVENING_PEAK[0], EVENING_PEAK[1] - 1))
        ),
    )

    return trips


def compute_od_matrix(
    trips: pl.DataFrame,
    filter_expr: pl.Expr | None = None,
) -> np.ndarray:
    """
    Compute a 6×6 OD matrix from a trip table.

    Rows = origins (INTERSECTION_ORDER), Columns = destinations.
    Only trips with known origin AND destination are counted.
    """
    filtered = trips.filter(
        (pl.col("trip_origin") != "unknown")
        & (pl.col("trip_destination") != "unknown")
    )
    if filter_expr is not None:
        filtered = filtered.filter(filter_expr)

    n = len(INTERSECTION_ORDER)
    matrix = np.zeros((n, n), dtype=int)

    od_counts = (
        filtered.group_by(["trip_origin", "trip_destination"])
        .len()
    )

    for row in od_counts.iter_rows():
        origin, dest, count = row
        if origin in INTERSECTION_ORDER and dest in INTERSECTION_ORDER:
            i = INTERSECTION_ORDER.index(origin)
            j = INTERSECTION_ORDER.index(dest)
            matrix[i, j] = count

    return matrix


def classify_turning_movement(trips: pl.DataFrame) -> pl.DataFrame:
    """
    Classify each trip's turning movement at each intersection it passes through.

    Categories:
    - through_east: enters from west, exits east (along backbone)
    - through_west: enters from east, exits west (along backbone)
    - turn_north: interacts with north branch
    - turn_south: interacts with south branch
    - u_turn: same origin and destination
    - other: unclassifiable

    Returns a DataFrame with columns: intersection, movement, count.
    """
    # For the fishbone network, turning movement is approximated by
    # comparing trip_origin and trip_destination relative to the intersection
    movements = []

    valid_trips = trips.filter(
        (pl.col("trip_origin") != "unknown")
        & (pl.col("trip_destination") != "unknown")
    )

    for intersection in INTERSECTION_ORDER:
        idx = INTERSECTION_ORDER.index(intersection)

        # Trips that pass through this intersection:
        # origin is west of intersection AND destination is east, or vice versa
        for row in valid_trips.iter_rows(named=True):
            origin = row["trip_origin"]
            dest = row["trip_destination"]
            o_idx = INTERSECTION_ORDER.index(origin) if origin in INTERSECTION_ORDER else -1
            d_idx = INTERSECTION_ORDER.index(dest) if dest in INTERSECTION_ORDER else -1

            if o_idx < 0 or d_idx < 0:
                continue

            # Only count if this intersection is between origin and destination
            # or IS the origin/destination
            if origin == intersection or dest == intersection:
                if origin == dest:
                    movement = "u_turn"
                elif o_idx < idx and d_idx > idx:
                    movement = "through_east"
                elif o_idx > idx and d_idx < idx:
                    movement = "through_west"
                elif o_idx < idx and d_idx == idx:
                    movement = "arriving_from_west"
                elif o_idx > idx and d_idx == idx:
                    movement = "arriving_from_east"
                elif o_idx == idx and d_idx > idx:
                    movement = "departing_east"
                elif o_idx == idx and d_idx < idx:
                    movement = "departing_west"
                else:
                    movement = "other"

                movements.append({
                    "intersection": intersection,
                    "movement": movement,
                })

    if not movements:
        return pl.DataFrame(
            schema={"intersection": pl.String, "movement": pl.String, "count": pl.Int64}
        )

    return (
        pl.DataFrame(movements)
        .group_by(["intersection", "movement"])
        .len()
        .rename({"len": "count"})
        .sort(["intersection", "count"], descending=[False, True])
    )


def save_od_results(trips: pl.DataFrame, output_dir: Path):
    """Save all OD matrix variants and turning movement results."""
    output_dir.mkdir(parents=True, exist_ok=True)

    # 1. Aggregate OD matrix
    od_all = compute_od_matrix(trips)
    np.savetxt(output_dir / "od_matrix_all.csv", od_all, delimiter=",",
               header=",".join(INTERSECTION_ORDER), fmt="%d", comments="")

    # 2. Weekday vs Weekend
    od_weekday = compute_od_matrix(trips, pl.col("is_weekday"))
    od_weekend = compute_od_matrix(trips, ~pl.col("is_weekday"))
    np.savetxt(output_dir / "od_matrix_weekday.csv", od_weekday,
               delimiter=",", header=",".join(INTERSECTION_ORDER),
               fmt="%d", comments="")
    np.savetxt(output_dir / "od_matrix_weekend.csv", od_weekend,
               delimiter=",", header=",".join(INTERSECTION_ORDER),
               fmt="%d", comments="")

    # 3. Peak vs Off-peak
    od_peak = compute_od_matrix(trips, pl.col("is_peak"))
    od_offpeak = compute_od_matrix(trips, ~pl.col("is_peak"))
    np.savetxt(output_dir / "od_matrix_peak.csv", od_peak,
               delimiter=",", header=",".join(INTERSECTION_ORDER),
               fmt="%d", comments="")
    np.savetxt(output_dir / "od_matrix_offpeak.csv", od_offpeak,
               delimiter=",", header=",".join(INTERSECTION_ORDER),
               fmt="%d", comments="")

    # 4. Hourly OD matrices
    hourly_dir = output_dir / "hourly"
    hourly_dir.mkdir(exist_ok=True)
    for h in range(24):
        od_h = compute_od_matrix(trips, pl.col("hour_wib") == h)
        np.savetxt(hourly_dir / f"od_matrix_hour_{h:02d}.csv", od_h,
                   delimiter=",", header=",".join(INTERSECTION_ORDER),
                   fmt="%d", comments="")

    # 5. Monthly OD matrices
    monthly_dir = output_dir / "monthly"
    monthly_dir.mkdir(exist_ok=True)
    months = trips["month"].unique().sort().to_list()
    for m in months:
        od_m = compute_od_matrix(trips, pl.col("month") == m)
        safe_m = m.replace("-", "_")
        np.savetxt(monthly_dir / f"od_matrix_{safe_m}.csv", od_m,
                   delimiter=",", header=",".join(INTERSECTION_ORDER),
                   fmt="%d", comments="")

    # 6. Trip summary stats
    summary = {
        "total_trips": int(trips.height),
        "trips_with_known_od": int(
            trips.filter(
                (pl.col("trip_origin") != "unknown")
                & (pl.col("trip_destination") != "unknown")
            ).height
        ),
        "intersections": INTERSECTION_ORDER,
        "total_od_flow": int(od_all.sum()),
        "months_covered": months,
    }
    (output_dir / "summary.json").write_text(json.dumps(summary, indent=2))

    print(f"✓ OD matrices saved to {output_dir}")
    print(f"  Aggregate OD total flow: {od_all.sum():,}")
    print(f"  Weekday total: {od_weekday.sum():,}, Weekend total: {od_weekend.sum():,}")
    print(f"  Peak total: {od_peak.sum():,}, Off-peak total: {od_offpeak.sum():,}")


def main():
    """Run OD matrix extraction on the backbone-only labeled dataset."""
    if not INPUT_LABELED.exists():
        print("❌ Labeled data not found. Run intersection_labeling.py first.")
        return

    print(f"Reading {INPUT_LABELED}...")
    df = pl.read_parquet(INPUT_LABELED)
    print(f"  {df.height:,} pings")

    # Build trip table
    print("Building trip table...")
    trips = build_trip_table(df)
    print(f"  {trips.height:,} trips")

    # Save OD results
    save_od_results(trips, OUTPUT_DIR)



if __name__ == "__main__":
    main()
