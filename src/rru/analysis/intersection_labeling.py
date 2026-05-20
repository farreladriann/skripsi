"""
Intersection Labeling — Assign each GPS ping to its nearest intersection zone.

Each of the 6 RRU intersections has a defined zone (circular buffer).
Pings within the zone are labeled with the intersection name.
Pings on the backbone between intersections are labeled with the
segment name (e.g., "kronggahan_jombor").

This module is the bridge between map-matched trajectories and
the downstream analysis modules (OD matrix, density, etc.).
"""

import polars as pl
import numpy as np
from pathlib import Path

from configs import intersections
from src.rru.utils import haversine_m

# ── Configuration ───────────────────────────────────────────────────
INTERSECTION_ZONE_RADIUS_M = 200  # meters

# Ordered west to east (consistent with GOALS.md and configs.py)
INTERSECTION_ORDER = [
    "kronggahan", "jombor", "monjali",
    "kentungan", "condongcatur", "upn",
]

# Backbone segments between consecutive intersections
BACKBONE_SEGMENTS = [
    ("kronggahan", "jombor"),
    ("jombor", "monjali"),
    ("monjali", "kentungan"),
    ("kentungan", "condongcatur"),
    ("condongcatur", "upn"),
]

INPUT_SEGMENTED = Path("./data/matched/gps_rru_segmented.parquet")
OUTPUT_LABELED = Path("./data/matched/gps_rru_labeled.parquet")


def label_intersection_zones(
    df: pl.DataFrame,
    zone_radius_m: float = INTERSECTION_ZONE_RADIUS_M,
) -> pl.DataFrame:
    """
    Assign each ping to the nearest intersection zone (if within radius).

    Adds columns:
    - nearest_intersection: str — name of the closest intersection
    - dist_to_intersection: float — distance in meters
    - in_intersection_zone: bool — True if within zone_radius_m
    - zone_label: str — intersection name if in zone, else segment label
    """
    # Build intersection coordinate arrays
    int_names = []
    int_lats = []
    int_lons = []
    for name in INTERSECTION_ORDER:
        coord = intersections[name]
        int_names.append(name)
        int_lats.append(coord["latitude"])
        int_lons.append(coord["longitude"])

    int_lats_arr = np.array(int_lats)
    int_lons_arr = np.array(int_lons)

    # Compute distance from each ping to each intersection
    lats = df["latitude"].to_numpy()
    lons = df["longitude"].to_numpy()

    # Distance matrix: (n_pings, n_intersections)
    dist_matrix = np.zeros((len(lats), len(int_lats_arr)))
    for i, (ilat, ilon) in enumerate(zip(int_lats_arr, int_lons_arr)):
        dist_matrix[:, i] = haversine_m(lats, lons, ilat, ilon)

    # Find nearest intersection for each ping
    nearest_idx = np.argmin(dist_matrix, axis=1)
    nearest_dist = dist_matrix[np.arange(len(lats)), nearest_idx]
    nearest_name = [int_names[idx] for idx in nearest_idx]

    # Add columns
    df = df.with_columns(
        nearest_intersection=pl.Series(nearest_name),
        dist_to_intersection=pl.Series(nearest_dist).round(1),
        in_intersection_zone=pl.Series(nearest_dist < zone_radius_m),
    )

    # Assign zone_label: intersection name if in zone, else backbone segment
    # For pings not in any zone, assign segment based on longitude position
    zone_labels = []
    for i in range(len(lats)):
        if nearest_dist[i] < zone_radius_m:
            zone_labels.append(nearest_name[i])
        else:
            # Determine backbone segment by longitude
            lon = lons[i]
            segment = _determine_segment(lon, int_lons_arr, int_names)
            zone_labels.append(segment)

    df = df.with_columns(
        zone_label=pl.Series(zone_labels),
    )

    return df


def _determine_segment(
    lon: float,
    int_lons: np.ndarray,
    int_names: list[str],
) -> str:
    """
    Determine which backbone segment a longitude falls into.
    Returns format: "name_a→name_b" for the segment between consecutive intersections.
    """
    # Find which pair of consecutive intersections the longitude is between
    for i in range(len(int_lons) - 1):
        lon_a = int_lons[i]
        lon_b = int_lons[i + 1]
        if lon_a <= lon <= lon_b:
            return f"{int_names[i]}→{int_names[i+1]}"

    # If west of first intersection
    if lon < int_lons[0]:
        return f"west_of_{int_names[0]}"
    # If east of last intersection
    return f"east_of_{int_names[-1]}"


def label_trip_od(df: pl.DataFrame) -> pl.DataFrame:
    """
    For each trip, determine origin and destination intersections.

    A trip's origin = first intersection zone it enters.
    A trip's destination = last intersection zone it enters.

    Adds columns:
    - trip_origin: str — origin intersection name (or "unknown")
    - trip_destination: str — destination intersection name (or "unknown")
    """
    # Filter to pings that are in an intersection zone
    in_zone = df.filter(pl.col("in_intersection_zone"))

    # First and last intersection per trip
    trip_od = (
        in_zone.sort(["trip_id", "timestamp"])
        .group_by("trip_id", maintain_order=True)
        .agg(
            trip_origin=pl.col("nearest_intersection").first(),
            trip_destination=pl.col("nearest_intersection").last(),
        )
    )

    # Join back
    df = df.join(trip_od, on="trip_id", how="left")

    # Fill unknown for trips with no zone pings
    df = df.with_columns(
        trip_origin=pl.col("trip_origin").fill_null("unknown"),
        trip_destination=pl.col("trip_destination").fill_null("unknown"),
    )

    return df


def main():
    """Label intersections and OD for segmented data."""
    if not INPUT_SEGMENTED.exists():
        print("❌ Segmented data not found. Run segmentation.py first.")
        return

    print(f"Reading {INPUT_SEGMENTED}...")
    df = pl.read_parquet(INPUT_SEGMENTED)
    print(f"  {df.height:,} pings, {df['trip_id'].n_unique():,} trips")

    # Label intersection zones
    print(f"Labeling intersection zones (radius={INTERSECTION_ZONE_RADIUS_M}m)...")
    df = label_intersection_zones(df, INTERSECTION_ZONE_RADIUS_M)

    n_in_zone = df.filter(pl.col("in_intersection_zone")).height
    pct_in_zone = n_in_zone / df.height * 100
    print(f"  Pings in intersection zones: {n_in_zone:,} ({pct_in_zone:.1f}%)")

    # Zone distribution
    zone_counts = (
        df.filter(pl.col("in_intersection_zone"))
        .group_by("nearest_intersection")
        .len()
        .sort("nearest_intersection")
    )
    print(f"\n  Zone distribution:")
    for row in zone_counts.iter_rows():
        print(f"    {row[0]}: {row[1]:,} pings")

    # Label trip OD
    print("\nLabeling trip origin-destination...")
    df = label_trip_od(df)

    # OD summary
    od_trips = df.select("trip_id", "trip_origin", "trip_destination").unique()
    n_with_od = od_trips.filter(
        (pl.col("trip_origin") != "unknown") &
        (pl.col("trip_destination") != "unknown")
    ).height
    print(f"  Trips with known OD: {n_with_od:,} / {od_trips.height:,}")

    # Save
    OUTPUT_LABELED.parent.mkdir(parents=True, exist_ok=True)
    df.write_parquet(OUTPUT_LABELED, compression="zstd")
    size_mb = OUTPUT_LABELED.stat().st_size / 1024 / 1024
    print(f"\n✓ Saved: {OUTPUT_LABELED.resolve()} ({size_mb:.1f} MB)")


if __name__ == "__main__":
    main()
