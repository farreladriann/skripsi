"""
Map Matching Module — Nearest-edge assignment with candidate scoring.

Assigns each GPS ping to its closest road edge from the fishbone network.
Uses pre-computed R-tree candidate edges from the preprocessing pipeline.

Algorithm: Geometric point-to-curve matching (Quddus et al., 2007 taxonomy).

Design rationale grounded in literature:
1. Quddus et al. (2007, Transport. Res. Part C) classify map matching into
   geometric, topological, probabilistic, and advanced. Geometric methods
   are sufficient when the road network has LOW TOPOLOGICAL COMPLEXITY —
   which our fishbone structure (1 backbone + 6 branches) satisfies.
2. Newson & Krumm (2009, ACM SIGSPATIAL) showed HMM map matching is
   effective at <30s sampling intervals but DEGRADES SIGNIFICANTLY at
   higher intervals. Our data has median inter-ping gaps of minutes to
   hours, where HMM transition probabilities add little value.
3. The fishbone network has at most 2-3 candidate edges per point, so the
   topological ambiguity that HMM resolves (parallel roads, complex grids)
   is minimal. Geometric proximity is a strong enough signal.
4. R-tree spatial indexing already computes candidate edges with distances
   during preprocessing — this is the emission probability component.

References:
- Quddus, M.A., Ochieng, W.Y., Noland, R.B. (2007). Current map-matching
  algorithms for transport applications. Transportation Research Part C, 15(5).
- Newson, P., Krumm, J. (2009). Hidden Markov Map Matching Through Noise
  and Sparseness. ACM SIGSPATIAL GIS.
"""

import polars as pl
from pathlib import Path

from configs import intersections

# ── File paths ──────────────────────────────────────────────────────
INPUT_COLLAPSED = Path("./data/processed/gps_rru_collapsed.parquet")
INPUT_LOWSPEED = Path("./data/processed/gps_rru_cleaned_lowspeed.parquet")
INPUT_VEHICLE_ONLY = Path("./data/processed/gps_rru_vehicle_only.parquet")
OUTPUT_MATCHED = Path("./data/matched/gps_rru_matched.parquet")


def assign_nearest_edge(df: pl.DataFrame) -> pl.DataFrame:
    """
    Assign each GPS ping to its nearest candidate road edge.

    The input DataFrame must have columns:
    - candidate_edge_keys: List[str] — edge identifiers (u_v format)
    - candidate_dists: List[float] — distances to each candidate edge (meters)

    Returns the DataFrame with added columns:
    - matched_edge: str — the edge key with minimum distance
    - matched_dist: float — distance to the matched edge (meters)
    """
    return df.with_columns(
        matched_edge=pl.col("candidate_edge_keys").list.get(0),
        matched_dist=pl.col("candidate_dists").list.get(0),
    )


def _parse_edge_nodes(df: pl.DataFrame) -> pl.DataFrame:
    """Extract u and v node IDs from the matched_edge key (format: u_v)."""
    return df.with_columns(
        matched_u=pl.col("matched_edge").str.split("_").list.get(0),
        matched_v=pl.col("matched_edge").str.split("_").list.get(1),
    )


def main():
    """Run map matching on the cleaned low-speed dataset."""
    # Select input: prefer journal-based motor-vehicle filtered data.
    # Fallbacks are kept only for backwards compatibility with older runs.
    if INPUT_VEHICLE_ONLY.exists():
        input_path = INPUT_VEHICLE_ONLY
    elif INPUT_LOWSPEED.exists():
        input_path = INPUT_LOWSPEED
    elif INPUT_COLLAPSED.exists():
        input_path = INPUT_COLLAPSED
    else:
        print("❌ No processed data found. Run preprocessing pipeline first.")
        return

    print(f"Reading {input_path}...")
    df = pl.read_parquet(input_path)
    print(f"  {df.height:,} pings, {df['maid'].n_unique():,} MAIDs")

    # Handle timestamp format: convert datetime to unix if needed
    if df["timestamp"].dtype != pl.Int64:
        df = df.with_columns(
            pl.col("timestamp").dt.epoch("s").alias("timestamp")
        )

    # Drop index column if present
    if "__index_level_0__" in df.columns:
        df = df.drop("__index_level_0__")

    # Assign nearest edge
    print("Assigning nearest edge to each ping...")
    df_matched = assign_nearest_edge(df)

    # Parse edge node IDs
    df_matched = _parse_edge_nodes(df_matched)

    # Sort by MAID and timestamp for downstream trajectory processing
    df_matched = df_matched.sort(["maid", "timestamp"])

    # Summary
    n_edges = df_matched["matched_edge"].n_unique()
    avg_dist = df_matched["matched_dist"].mean()
    print(f"\n--- Map Matching Summary ---")
    print(f"  Pings matched: {df_matched.height:,}")
    print(f"  Unique MAIDs: {df_matched['maid'].n_unique():,}")
    print(f"  Unique edges used: {n_edges:,}")
    print(f"  Avg match distance: {avg_dist:.1f} m")
    print(f"  Match distance P50: {df_matched['matched_dist'].median():.1f} m")
    print(f"  Match distance P90: {df_matched['matched_dist'].quantile(0.9):.1f} m")
    print(f"  Match distance P99: {df_matched['matched_dist'].quantile(0.99):.1f} m")

    # Save
    OUTPUT_MATCHED.parent.mkdir(parents=True, exist_ok=True)
    df_matched.write_parquet(OUTPUT_MATCHED, compression="zstd")
    size_mb = OUTPUT_MATCHED.stat().st_size / 1024 / 1024
    print(f"\n✓ Saved: {OUTPUT_MATCHED.resolve()} ({size_mb:.1f} MB)")


if __name__ == "__main__":
    main()
