import polars as pl
from pathlib import Path
from .bilocation_check import add_bbox_spread_column
from src.rru.preprocessing.interim.rtree import find_edge_candidates_chunked, build_edge_spatial_index
from src.rru.utils import drop_singleton_maids
from src.rru.paths import RRU_WITH_INTERSECTION_CLEAN_GEOJSON
import geopandas as gpd
from configs import MAX_DIST_METERS

EPSG_WGS84 = 4326
EPSG_UTM49S = 32749
MAX_SPREAD_M = 10.0
OUTPUT_CANDIDATES = Path("./data/interim/gps_rru_candidates.parquet")
GEOJSON_EDGES = RRU_WITH_INTERSECTION_CLEAN_GEOJSON
OUTPUT_COLLAPSED = Path("./data/processed/gps_rru_collapsed.parquet")

def collapse_bilocation(
    df: pl.DataFrame,
    group_keys: tuple[str, ...] = ("maid", "timestamp"),
    max_spread_m: float = MAX_SPREAD_M,
) -> tuple[pl.DataFrame, pl.DataFrame]:
    keys = list(group_keys)

    aggregated = (
        df.group_by(keys, maintain_order=True)
        .agg(
            latitude=pl.col("latitude").median(),
            longitude=pl.col("longitude").median(),
            n_points_collapsed=pl.len(),
            lat_min=pl.col("latitude").min(),
            lat_max=pl.col("latitude").max(),
            lon_min=pl.col("longitude").min(),
            lon_max=pl.col("longitude").max(),
        )
        .pipe(add_bbox_spread_column)
        .sort(keys)
    )

    bbox_cols = ["lat_min", "lat_max", "lon_min", "lon_max"]
    is_tight  = pl.col("spread_m") < max_spread_m

    kept    = aggregated.filter(is_tight).drop(bbox_cols)
    dropped = aggregated.filter(~is_tight).drop(bbox_cols)
    return kept, dropped

def main():
    GROUP_KEYS = ("maid", "timestamp")
    df_candidates_lazy = pl.scan_parquet(OUTPUT_CANDIDATES)
    df_candidates = df_candidates_lazy.collect()
    before = df_candidates.height
    df_collapsed_points, df_dropped_points = collapse_bilocation(df_candidates, GROUP_KEYS)
    
    print("Membaca geojson network rru...")
    rru_edges = gpd.read_file(GEOJSON_EDGES)
    edge_index = build_edge_spatial_index(rru_edges, target_epsg=EPSG_UTM49S)

    print("Mencari titik edge candidates pada data bilocation...")
    df_candidates_collapsed = find_edge_candidates_chunked(
        df_collapsed_points.select(list(GROUP_KEYS) + ["latitude", "longitude"]),
        edge_index,
        source_epsg=EPSG_WGS84,
        max_distance_m=MAX_DIST_METERS,
        chunk_size=1_000_000,
        sort_keys=list(GROUP_KEYS),
    ).join(
        df_collapsed_points.select(list(GROUP_KEYS) + ["n_points_collapsed"]),
        on=list(GROUP_KEYS),
        how="left",
    )
    
    n_dropped_groups = df_dropped_points.height
    n_dropped_raw_rows = df_dropped_points["n_points_collapsed"].sum() if n_dropped_groups > 0 else 0
    n_compressed_rows = before - df_collapsed_points.height - n_dropped_raw_rows

    print(f"\n--- Ringkasan Collapse Bilocation ---")
    print(f"Data awal: {before:,} baris")
    print(f"Data setelah dilebur/dikompresi: {df_collapsed_points.height:,} baris kejadian unik")
    print(f"Data duplikat yang disusutkan menjadi 1: {n_compressed_rows:,} baris")
    print(f"Ditolak sepenuhnya (spread di atas {MAX_SPREAD_M}m): {n_dropped_groups:,} kejadian ({n_dropped_raw_rows:,} baris orisinal)")

    df_candidates_collapsed = drop_singleton_maids(df_candidates_collapsed, label="stage 1c")
    df_candidates_collapsed.write_parquet(OUTPUT_COLLAPSED, compression="zstd")
    
    print(f"Data berhasil disave ke {OUTPUT_COLLAPSED.resolve()}")

if __name__ == "__main__":
    main()