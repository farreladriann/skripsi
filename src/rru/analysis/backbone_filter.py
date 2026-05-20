"""
Backbone Analytical Filter — derive an RRU backbone-only dataset.

The thesis preprocessing first identifies motor-vehicle trajectories interacting
with the full RRU fishbone network (backbone + north/south branch links at each
intersection). This module then builds the OD analysis dataset by:

1. taking the motor-vehicle-only pings produced by fishbone preprocessing,
2. matching those pings to the RRU backbone-only network,
3. retaining only pings close enough to a backbone edge,
4. segmenting the retained backbone pings into trips, and
5. labeling the six RRU intersections as OD zones.

This keeps density/turning movement grounded in the full intersection fishbone
while ensuring OD matrix results represent vehicles that actually
traverse the RRU backbone.
"""

from pathlib import Path

import geopandas as gpd
import polars as pl

from configs import MAX_DIST_METERS
from src.rru.preprocessing.interim.rtree import (
    EPSG_UTM49S,
    EPSG_WGS84,
    build_edge_spatial_index,
    find_edge_candidates_chunked,
)
from src.rru.preprocessing.mapmatching.map_matching import (
    _parse_edge_nodes,
    assign_nearest_edge,
)
from src.rru.preprocessing.traj_segmentation.segmentation import (
    DEFAULT_GAP_SECONDS,
    MIN_PINGS_PER_TRIP,
    segment_trips,
    summarize_trips,
)
from src.rru.analysis.intersection_labeling import (
    INTERSECTION_ZONE_RADIUS_M,
    label_intersection_zones,
    label_trip_od,
)
from src.rru.paths import RRU_BACKBONE_CLEAN_GEOJSON

INPUT_VEHICLE_ONLY = Path("./data/processed/gps_rru_vehicle_only.parquet")
BACKBONE_GEOJSON = RRU_BACKBONE_CLEAN_GEOJSON
OUTPUT_DIR = Path("./data/matched/backbone")
OUTPUT_CANDIDATES = OUTPUT_DIR / "gps_rru_candidates.parquet"
OUTPUT_MATCHED = OUTPUT_DIR / "gps_rru_matched.parquet"
OUTPUT_SEGMENTED = OUTPUT_DIR / "gps_rru_segmented.parquet"
OUTPUT_LABELED = OUTPUT_DIR / "gps_rru_labeled.parquet"
OUTPUT_TRIP_SUMMARY = OUTPUT_DIR / "trip_summary.parquet"


def _read_vehicle_pings() -> pl.DataFrame:
    if not INPUT_VEHICLE_ONLY.exists():
        raise FileNotFoundError(
            f"{INPUT_VEHICLE_ONLY} not found. Run the fishbone preprocessing first."
        )
    df = pl.read_parquet(INPUT_VEHICLE_ONLY)
    if df["timestamp"].dtype != pl.Int64:
        df = df.with_columns(pl.col("timestamp").dt.epoch("s").alias("timestamp"))
    if "__index_level_0__" in df.columns:
        df = df.drop("__index_level_0__")
    return df


def main():
    """Generate backbone-only matched, segmented, and labeled datasets."""
    if not BACKBONE_GEOJSON.exists():
        raise FileNotFoundError(
            f"{BACKBONE_GEOJSON} not found. Build the RRU backbone network first."
        )

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print(f"Reading vehicle-only fishbone preprocessing output: {INPUT_VEHICLE_ONLY}...")
    df = _read_vehicle_pings()
    print(f"  Input: {df.height:,} pings, {df['maid'].n_unique():,} MAIDs")

    print(f"Reading backbone network: {BACKBONE_GEOJSON}...")
    backbone_edges = gpd.read_file(BACKBONE_GEOJSON)
    edge_index = build_edge_spatial_index(backbone_edges, target_epsg=EPSG_UTM49S)
    print(f"  Backbone edges: {len(edge_index[1]):,}")

    print(f"Finding backbone edge candidates within {MAX_DIST_METERS} m...")
    candidates = find_edge_candidates_chunked(
        df,
        edge_index,
        source_epsg=EPSG_WGS84,
        max_distance_m=MAX_DIST_METERS,
        chunk_size=2_000_000,
        sort_keys=["maid", "timestamp"],
    )
    print(
        f"  Retained on backbone: {candidates.height:,} pings "
        f"({candidates.height / df.height * 100:.1f}%)"
    )
    print(f"  Backbone MAIDs: {candidates['maid'].n_unique():,}")
    candidates.write_parquet(OUTPUT_CANDIDATES, compression="zstd")
    print(f"✓ Candidates saved: {OUTPUT_CANDIDATES}")

    print("Assigning nearest backbone edge...")
    matched = assign_nearest_edge(candidates)
    matched = _parse_edge_nodes(matched).sort(["maid", "timestamp"])
    matched.write_parquet(OUTPUT_MATCHED, compression="zstd")
    print(f"✓ Matched saved: {OUTPUT_MATCHED}")

    print(
        f"Segmenting backbone trips (gap={DEFAULT_GAP_SECONDS}s, "
        f"min_pings={MIN_PINGS_PER_TRIP})..."
    )
    segmented = segment_trips(matched, DEFAULT_GAP_SECONDS, MIN_PINGS_PER_TRIP)
    segmented.write_parquet(OUTPUT_SEGMENTED, compression="zstd")
    trip_summary = summarize_trips(segmented)
    trip_summary.write_parquet(OUTPUT_TRIP_SUMMARY, compression="zstd")
    print(
        f"✓ Segmented saved: {OUTPUT_SEGMENTED} "
        f"({segmented['trip_id'].n_unique():,} trips)"
    )

    print(f"Labeling backbone intersection zones (radius={INTERSECTION_ZONE_RADIUS_M} m)...")
    labeled = label_intersection_zones(segmented, INTERSECTION_ZONE_RADIUS_M)
    labeled = label_trip_od(labeled)
    labeled.write_parquet(OUTPUT_LABELED, compression="zstd")
    od_trips = labeled.select("trip_id", "trip_origin", "trip_destination").unique()
    n_known_od = od_trips.filter(
        (pl.col("trip_origin") != "unknown")
        & (pl.col("trip_destination") != "unknown")
    ).height
    print(f"✓ Labeled saved: {OUTPUT_LABELED}")
    print(f"  Trips with known OD: {n_known_od:,} / {od_trips.height:,}")


if __name__ == "__main__":
    main()
