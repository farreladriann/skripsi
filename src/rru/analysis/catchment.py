"""
Catchment Area Mapping — Identify geographic origin zones of RRU users.

For each MAID observed on Ring Road Utara, this module traces their
broader movement footprint across the DIY region to estimate their
"home" or "primary origin" location.

Method based on the Anchor Point Model (Ahas et al., 2010, J. Urban Tech.):
1. Load the full bbox-filtered dataset (15M pings, all of DIY RRU area)
2. For each MAID that appears on the RRU fishbone network:
   a. Find all their pings across the broader area
   b. Estimate home location = most-frequent nighttime grid cell (22:00–06:00 WIB)
   c. If insufficient nighttime data, use most-frequent overall grid cell
3. Aggregate home locations into a spatial grid
4. Visualize as heatmap per intersection

Grid resolution: ~550m × 550m (0.005° grid at lat -7.75°)

References:
- Ahas, R., Silm, S., Järv, O., Saluveer, E., & Tiru, M. (2010). Using mobile
  positioning data to model locations meaningful to users. J. Urban Technology, 17(1).
- Alexander, L., Jiang, S., Murga, M., & González, M.C. (2015). Origin–destination
  trips inferred from mobile phone data. Transportation Research Part C, 58.
"""

import polars as pl
import numpy as np
import json
from pathlib import Path

from configs import bounding_boxes, intersections
from src.rru.analysis.intersection_labeling import INTERSECTION_ORDER

# ── Configuration ───────────────────────────────────────────────────
INPUT_LABELED = Path("./data/matched/backbone/gps_rru_labeled.parquet")
INPUT_BBOX = Path("./data/interim/output_bbox.parquet")
OUTPUT_DIR = Path("./results/catchment")

WIB_OFFSET_HOURS = 7
NIGHT_START_HOUR = 22  # WIB
NIGHT_END_HOUR = 6     # WIB

# Grid resolution in degrees (approximate 500m at this latitude)
# At lat ~7.75°S: 1° lat ≈ 111 km, 1° lon ≈ 110 km
# 500m ≈ 0.0045°
GRID_SIZE_DEG = 0.005  # ~550m


def _grid_coord(val: pl.Expr, grid_size: float) -> pl.Expr:
    """Snap a coordinate to the nearest grid cell center."""
    return ((val / grid_size).floor() * grid_size + grid_size / 2).round(6)


def estimate_home_locations(
    rru_maids: list[str],
    bbox_df: pl.DataFrame,
    grid_size: float = GRID_SIZE_DEG,
) -> pl.DataFrame:
    """
    Estimate home/origin location for each MAID using nighttime pings.

    Strategy:
    1. Filter bbox_df to only MAIDs seen on RRU
    2. Add WIB hour column
    3. For each MAID, find the grid cell with the most nighttime pings
    4. If no nighttime pings, use the most-frequent overall grid cell

    Returns DataFrame with columns: [maid, home_lat, home_lon, n_night_pings, n_total_pings]
    """
    # Filter to RRU MAIDs only
    rru_maid_set = set(rru_maids)
    df = bbox_df.filter(pl.col("maid").is_in(rru_maid_set))

    if df.height == 0:
        return pl.DataFrame(
            schema={
                "maid": pl.String,
                "home_lat": pl.Float64,
                "home_lon": pl.Float64,
                "n_night_pings": pl.Int64,
                "n_total_pings": pl.Int64,
            }
        )

    # Add temporal and grid columns
    ts_wib = pl.col("timestamp") + WIB_OFFSET_HOURS * 3600
    hour_wib = ((ts_wib % 86400) // 3600).cast(pl.Int32)

    df = df.with_columns(
        hour_wib=hour_wib,
        grid_lat=_grid_coord(pl.col("latitude"), grid_size),
        grid_lon=_grid_coord(pl.col("longitude"), grid_size),
        is_night=(hour_wib >= NIGHT_START_HOUR) | (hour_wib < NIGHT_END_HOUR),
    )

    # Strategy 1: nighttime-based home estimation
    night_df = df.filter(pl.col("is_night"))
    night_homes = (
        night_df.group_by(["maid", "grid_lat", "grid_lon"])
        .len()
        .sort(["maid", "len"], descending=[False, True])
        .group_by("maid", maintain_order=True)
        .first()
        .rename({"grid_lat": "home_lat", "grid_lon": "home_lon", "len": "n_night_pings"})
    )

    # Strategy 2: fallback for MAIDs without nighttime data
    all_homes = (
        df.group_by(["maid", "grid_lat", "grid_lon"])
        .len()
        .sort(["maid", "len"], descending=[False, True])
        .group_by("maid", maintain_order=True)
        .first()
        .rename({"grid_lat": "home_lat", "grid_lon": "home_lon", "len": "n_total_pings"})
    )

    # Merge: prefer nighttime, fallback to overall
    homes = night_homes.join(
        all_homes.select("maid", "n_total_pings"),
        on="maid",
        how="left",
    )

    # For MAIDs not in night_homes, use all_homes
    missing_maids = set(rru_maids) - set(homes["maid"].to_list())
    if missing_maids:
        fallback = all_homes.filter(pl.col("maid").is_in(missing_maids)).with_columns(
            n_night_pings=pl.lit(0).cast(pl.UInt32),
        )
        homes = pl.concat([homes, fallback], how="diagonal_relaxed")

    return homes


def compute_catchment_grid(
    homes: pl.DataFrame,
    intersection_maids: dict[str, list[str]],
) -> dict[str, pl.DataFrame]:
    """
    Aggregate home locations into a spatial grid per intersection.

    Returns dict mapping intersection name → grid DataFrame with columns:
    [home_lat, home_lon, n_maids]
    """
    grids = {}

    for int_name, maids in intersection_maids.items():
        maid_set = set(maids)
        int_homes = homes.filter(pl.col("maid").is_in(maid_set))

        grid = (
            int_homes.group_by(["home_lat", "home_lon"])
            .agg(n_maids=pl.len())
            .sort("n_maids", descending=True)
        )
        grids[int_name] = grid

    return grids


def save_catchment_results(
    homes: pl.DataFrame,
    grids: dict[str, pl.DataFrame],
    output_dir: Path,
):
    """Save catchment area results."""
    output_dir.mkdir(parents=True, exist_ok=True)

    # Save home locations
    homes.write_csv(output_dir / "home_locations.csv")

    # Save per-intersection grids
    for int_name, grid in grids.items():
        grid.write_csv(output_dir / f"catchment_grid_{int_name}.csv")

    # Summary
    summary = {
        "total_maids_with_homes": int(homes.height),
        "grid_size_degrees": GRID_SIZE_DEG,
        "grid_size_meters_approx": int(GRID_SIZE_DEG * 111000),
    }

    for int_name, grid in grids.items():
        summary[int_name] = {
            "n_maids": int(grid["n_maids"].sum()),
            "n_grid_cells": int(grid.height),
            "top_5_cells": [
                {"lat": r[0], "lon": r[1], "count": r[2]}
                for r in grid.head(5).iter_rows()
            ],
        }

    (output_dir / "summary.json").write_text(json.dumps(summary, indent=2))

    print(f"✓ Catchment results saved to {output_dir}")
    for int_name, grid in grids.items():
        print(f"  {int_name}: {grid['n_maids'].sum():,} MAIDs in "
              f"{grid.height:,} grid cells")


def main():
    """Run catchment area mapping."""
    if not INPUT_LABELED.exists():
        print("❌ Labeled data not found. Run intersection_labeling.py first.")
        return
    if not INPUT_BBOX.exists():
        print("❌ Bbox data not found at {INPUT_BBOX}.")
        return

    print(f"Reading labeled data from {INPUT_LABELED}...")
    df_labeled = pl.read_parquet(INPUT_LABELED)

    # Get list of MAIDs per intersection
    in_zone = df_labeled.filter(pl.col("in_intersection_zone"))
    intersection_maids = {}
    for int_name in INTERSECTION_ORDER:
        maids = (
            in_zone.filter(pl.col("nearest_intersection") == int_name)
            ["maid"].unique().to_list()
        )
        intersection_maids[int_name] = maids
        print(f"  {int_name}: {len(maids):,} unique MAIDs")

    all_rru_maids = df_labeled["maid"].unique().to_list()
    print(f"\nTotal RRU MAIDs: {len(all_rru_maids):,}")

    # Load full bbox data for home estimation
    print(f"\nReading bbox data from {INPUT_BBOX}...")
    df_bbox = pl.read_parquet(INPUT_BBOX)
    print(f"  {df_bbox.height:,} pings, {df_bbox['maid'].n_unique():,} MAIDs")

    # Estimate home locations
    print("\nEstimating home locations (nighttime-based)...")
    homes = estimate_home_locations(all_rru_maids, df_bbox)
    print(f"  Homes estimated for {homes.height:,} / {len(all_rru_maids):,} MAIDs")

    # Compute catchment grids
    print("\nComputing catchment grids per intersection...")
    grids = compute_catchment_grid(homes, intersection_maids)

    # Save
    save_catchment_results(homes, grids, OUTPUT_DIR)


if __name__ == "__main__":
    main()
