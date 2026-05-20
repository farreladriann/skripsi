#!/usr/bin/env python3
"""Run R-tree max-distance threshold sensitivity for the RRU preprocessing.

This script summarizes point retention, MAID retention, candidate-count
statistics, minimum point-to-edge distances, and all point-edge candidate-pair
percentiles for one or more max-distance thresholds.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import geopandas as gpd
import numpy as np
import polars as pl
import shapely
from pyproj import Transformer

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.rru.paths import RRU_WITH_INTERSECTION_CLEAN_GEOJSON
from src.rru.preprocessing.interim.rtree import EPSG_UTM49S, EPSG_WGS84, build_edge_spatial_index
INPUT_PINGS = PROJECT_ROOT / "data" / "interim" / "output_bbox.parquet"
OUTPUT_DIR = PROJECT_ROOT / "results" / "rtree_threshold_sensitivity"
SUMMARY_CSV = OUTPUT_DIR / "rtree_threshold_min_distance_percentiles.csv"
PAIR_CSV = OUTPUT_DIR / "rtree_threshold_candidate_pair_distance_percentiles.csv"
POINTS_WITHIN_50M = OUTPUT_DIR / "rtree_points_within_50m_min_distance.parquet"

QUANTILES = [0, 1, 5, 10, 25, 50, 75, 90, 95, 99, 100]


def percentile_dict(prefix: str, values: np.ndarray) -> dict[str, float]:
    if values.size == 0:
        return {f"{prefix}_p{q:02d}_m": float("nan") for q in QUANTILES}
    percentiles = np.percentile(values.astype(np.float64, copy=False), QUANTILES)
    return {f"{prefix}_p{q:02d}_m": float(v) for q, v in zip(QUANTILES, percentiles, strict=True)}


def count_percentiles(values: np.ndarray) -> tuple[float, float, int]:
    if values.size == 0:
        return float("nan"), float("nan"), 0
    p50, p90 = np.percentile(values.astype(np.float64, copy=False), [50, 90])
    return float(p50), float(p90), int(values.max())


def run_threshold(
    df: pl.DataFrame,
    edge_index: tuple,
    threshold: float,
    *,
    chunk_size: int,
) -> tuple[dict[str, float | int], dict[str, float | int], pl.DataFrame | None]:
    tree, geometries, edge_keys, crs_epsg = edge_index
    transformer = Transformer.from_crs(EPSG_WGS84, crs_epsg, always_xy=True)

    candidate_count_chunks: list[np.ndarray] = []
    min_dist_chunks: list[np.ndarray] = []
    pair_dist_chunks: list[np.ndarray] = []
    maid_chunks: list[pl.Series] = []

    total_rows = df.height
    for offset in range(0, total_rows, chunk_size):
        chunk = df.slice(offset, chunk_size)
        x, y = transformer.transform(
            chunk["longitude"].to_numpy(),
            chunk["latitude"].to_numpy(),
        )
        pts = shapely.points(x, y)
        pt_idx, edge_idx = tree.query(pts, predicate="dwithin", distance=threshold)

        if pt_idx.size == 0:
            print(f"    chunk {offset:,}-{min(offset + chunk_size, total_rows):,}: 0 retained pings")
            continue

        dists = shapely.distance(pts[pt_idx], geometries[edge_idx]).astype(np.float32, copy=False)
        order = np.argsort(pt_idx, kind="stable")
        pt_sorted = pt_idx[order]
        dists_sorted = dists[order]
        unique_pts, starts, counts = np.unique(pt_sorted, return_index=True, return_counts=True)
        min_dists = np.minimum.reduceat(dists_sorted, starts).astype(np.float32, copy=False)

        candidate_count_chunks.append(counts.astype(np.uint16, copy=False))
        min_dist_chunks.append(min_dists)
        pair_dist_chunks.append(dists)
        maid_chunks.append(chunk["maid"].gather(pl.Series(unique_pts.astype(np.int64))))

        print(
            f"    chunk {offset:,}-{min(offset + chunk_size, total_rows):,}: "
            f"{unique_pts.size:,} retained pings, {dists.size:,} candidate pairs"
        )

    if not min_dist_chunks:
        empty_summary = {
            "max_dist_m": int(threshold) if threshold.is_integer() else threshold,
            "input_pings": df.height,
            "input_maids": df["maid"].n_unique(),
            "rtree_pings_raw": 0,
            "rtree_maids_raw": 0,
            "rtree_ping_retention_raw_pct": 0.0,
            "rtree_maids_retention_raw_pct": 0.0,
            "pings_after_drop_singleton": 0,
            "maids_after_drop_singleton": 0,
            "ping_retention_after_drop_singleton_pct": 0.0,
            "maids_retention_after_drop_singleton_pct": 0.0,
            "singleton_pings_dropped": 0,
            "singleton_maids_dropped": 0,
            "avg_candidates_per_ping_raw": float("nan"),
            "p50_candidates_per_ping_raw": float("nan"),
            "p90_candidates_per_ping_raw": float("nan"),
            "max_candidates_per_ping_raw": 0,
            **percentile_dict("min_dist", np.array([], dtype=np.float32)),
            **percentile_dict("min_dist", np.array([], dtype=np.float32)),
        }
        return empty_summary, {
            "max_dist_m": int(threshold) if threshold.is_integer() else threshold,
            "candidate_point_edge_pairs": 0,
            **percentile_dict("candidate_pair_dist", np.array([], dtype=np.float32)),
        }, None

    candidate_counts = np.concatenate(candidate_count_chunks)
    min_dists = np.concatenate(min_dist_chunks)
    pair_dists = np.concatenate(pair_dist_chunks)
    maids = pl.concat(maid_chunks, rechunk=True)

    retained = pl.DataFrame(
        {
            "maid": maids,
            "candidate_count": candidate_counts,
            "min_dist_m": min_dists,
        }
    )

    raw_pings = retained.height
    raw_maids = retained["maid"].n_unique()
    retained_after = retained.filter(pl.len().over("maid") >= 2)
    after_pings = retained_after.height
    after_maids = retained_after["maid"].n_unique()
    p50_count, p90_count, max_count = count_percentiles(candidate_counts)

    max_dist_value = int(threshold) if float(threshold).is_integer() else threshold
    summary = {
        "max_dist_m": max_dist_value,
        "input_pings": df.height,
        "input_maids": df["maid"].n_unique(),
        "rtree_pings_raw": raw_pings,
        "rtree_maids_raw": raw_maids,
        "rtree_ping_retention_raw_pct": raw_pings / df.height * 100,
        "rtree_maids_retention_raw_pct": raw_maids / df["maid"].n_unique() * 100,
        "pings_after_drop_singleton": after_pings,
        "maids_after_drop_singleton": after_maids,
        "ping_retention_after_drop_singleton_pct": after_pings / df.height * 100,
        "maids_retention_after_drop_singleton_pct": after_maids / df["maid"].n_unique() * 100,
        "singleton_pings_dropped": raw_pings - after_pings,
        "singleton_maids_dropped": raw_maids - after_maids,
        "avg_candidates_per_ping_raw": pair_dists.size / raw_pings,
        "p50_candidates_per_ping_raw": p50_count,
        "p90_candidates_per_ping_raw": p90_count,
        "max_candidates_per_ping_raw": max_count,
        **percentile_dict("min_dist", min_dists),
        **percentile_dict("min_dist", retained_after["min_dist_m"].to_numpy()),
    }

    # Rename duplicated min_dist keys from the two percentile blocks to match the
    # historical CSV schema.
    raw_percentiles = percentile_dict("min_dist", min_dists)
    after_percentiles = percentile_dict("min_dist", retained_after["min_dist_m"].to_numpy())
    for q in QUANTILES:
        summary[f"min_dist_p{q:02d}_m_raw"] = raw_percentiles[f"min_dist_p{q:02d}_m"]
        summary[f"min_dist_p{q:02d}_m_after_drop_singleton"] = after_percentiles[f"min_dist_p{q:02d}_m"]
    for q in QUANTILES:
        summary.pop(f"min_dist_p{q:02d}_m", None)

    pair_summary = {
        "max_dist_m": max_dist_value,
        "candidate_point_edge_pairs": int(pair_dists.size),
        **percentile_dict("candidate_pair_dist", pair_dists),
    }

    points_50 = None
    if threshold == 50:
        points_50 = retained.select("maid", "candidate_count", "min_dist_m")

    return summary, pair_summary, points_50


def combine_with_existing(path: Path, new_df: pl.DataFrame) -> pl.DataFrame:
    if path.exists():
        old = pl.read_csv(path)
        combined = pl.concat([old, new_df], how="diagonal_relaxed")
        return combined.unique(subset=["max_dist_m"], keep="last").sort("max_dist_m")
    return new_df.sort("max_dist_m")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--thresholds", nargs="+", type=float, required=True)
    parser.add_argument("--chunk-size", type=int, default=2_000_000)
    args = parser.parse_args()

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print(f"Reading input pings: {INPUT_PINGS}")
    df = pl.read_parquet(INPUT_PINGS).select(["maid", "latitude", "longitude"])
    input_maids = df["maid"].n_unique()
    print(f"Input: {df.height:,} pings, {input_maids:,} MAIDs")

    print(f"Reading clean RRU network: {RRU_WITH_INTERSECTION_CLEAN_GEOJSON}")
    edges = gpd.read_file(RRU_WITH_INTERSECTION_CLEAN_GEOJSON)
    edge_index = build_edge_spatial_index(edges, EPSG_UTM49S)
    print(f"R-tree edges: {len(edge_index[1]):,}")

    summaries = []
    pair_summaries = []
    for threshold in args.thresholds:
        print(f"\n=== max_dist_m={threshold:g} ===")
        summary, pair_summary, points_50 = run_threshold(
            df, edge_index, threshold, chunk_size=args.chunk_size
        )
        summaries.append(summary)
        pair_summaries.append(pair_summary)
        if points_50 is not None:
            points_50.write_parquet(POINTS_WITHIN_50M, compression="zstd")
            print(f"Saved 50 m point-level distances: {POINTS_WITHIN_50M}")
        print(
            f"  raw retained: {summary['rtree_pings_raw']:,} pings "
            f"({summary['rtree_ping_retention_raw_pct']:.3f}%), "
            f"{summary['rtree_maids_raw']:,} MAIDs"
        )
        print(
            f"  after singleton drop: {summary['pings_after_drop_singleton']:,} pings "
            f"({summary['ping_retention_after_drop_singleton_pct']:.3f}%), "
            f"{summary['maids_after_drop_singleton']:,} MAIDs"
        )
        print(
            f"  candidate pairs: {pair_summary['candidate_point_edge_pairs']:,}, "
            f"min-dist median raw: {summary['min_dist_p50_m_raw']:.2f} m"
        )

    summary_df = pl.DataFrame(summaries)
    pair_df = pl.DataFrame(pair_summaries)
    combined_summary = combine_with_existing(SUMMARY_CSV, summary_df)
    combined_pairs = combine_with_existing(PAIR_CSV, pair_df)
    combined_summary.write_csv(SUMMARY_CSV)
    combined_pairs.write_csv(PAIR_CSV)
    print(f"\nWrote: {SUMMARY_CSV}")
    print(f"Wrote: {PAIR_CSV}")


if __name__ == "__main__":
    main()
