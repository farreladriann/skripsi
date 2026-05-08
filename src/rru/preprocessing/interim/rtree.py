from pathlib import Path
import geopandas as gpd
import numpy as np
import polars as pl
import shapely
from pyproj import Transformer
from shapely.strtree import STRtree

from src.rru.utils import drop_singleton_maids
from configs import MAX_DIST_METERS

PROCESSED_DIR = Path("./data")
OUTPUT_BBOX = PROCESSED_DIR / "interim" / "output_bbox.parquet"
OUTPUT_CANDIDATES = PROCESSED_DIR / "interim" / "gps_rru_candidates.parquet"
GEOJSON_EDGES = PROCESSED_DIR / "external" / "rru_with_intersections.geojson"
EPSG_WGS84 = 4326
EPSG_UTM49S = 32749

def build_edge_spatial_index(
    edges_gdf: gpd.GeoDataFrame,
    target_epsg: int,
) -> tuple[STRtree, np.ndarray, np.ndarray, int]:
    """Reproject `edges_gdf` ke `target_epsg` (meter-based) dan bangun R-tree.
    Returns:
        (tree, geometries, edge_keys, crs_epsg)
    """
    edges_proj = edges_gdf.to_crs(epsg=target_epsg).reset_index()
    geoms = edges_proj.geometry.to_numpy()
    edge_keys = (
        edges_proj["u"].astype(str) + "_" + edges_proj["v"].astype(str)
    ).to_numpy()

    shapely.prepare(geoms)
    tree = STRtree(geoms)
    return tree, geoms, edge_keys, target_epsg


def find_edge_candidates(
    points_df: pl.DataFrame,
    edge_index: tuple[STRtree, np.ndarray, np.ndarray, int],
    *,
    source_epsg: int,
    max_distance_m: float,
    lon_col: str = "longitude",
    lat_col: str = "latitude",
    sort_keys: list[str] | None = None,
) -> pl.DataFrame:
    """Tambahkan kolom kandidat edge ke setiap titik di `points_df`.
    Hanya titik yang punya >= 1 kandidat dalam `max_distance_m` yang di-keep.
    """
    tree, geometries, edge_keys, crs_epsg = edge_index
    transformer = Transformer.from_crs(source_epsg, crs_epsg, always_xy=True)
    x, y = transformer.transform(
        points_df[lon_col].to_numpy(),
        points_df[lat_col].to_numpy(),
    )
    pts = shapely.points(x, y)

    pt_idx, edge_idx = tree.query(pts, predicate="dwithin",
                                  distance=max_distance_m)
    dists = shapely.distance(pts[pt_idx], geometries[edge_idx])

    per_point = (
        pl.DataFrame({
            "row_idx": pt_idx,
            "edge_key": edge_keys[edge_idx],
            "dist": np.round(dists, 2),
        })
        .sort(["row_idx", "dist"])
        .group_by("row_idx", maintain_order=True)
        .agg(
            candidate_edge_keys=pl.col("edge_key"),
            candidate_dists=pl.col("dist"),
        )
    )

    result = (
        points_df.with_row_index("row_idx")
        .with_columns(pl.col("row_idx").cast(pl.Int64))
        .join(per_point, on="row_idx", how="inner")
        .drop("row_idx")
    )
    return result.sort(sort_keys) if sort_keys else result


def find_edge_candidates_chunked(
    points_df: pl.DataFrame,
    edge_index: tuple[STRtree, np.ndarray, np.ndarray, int],
    *,
    source_epsg: int,
    max_distance_m: float,
    chunk_size: int = 2_000_000,
    lon_col: str = "longitude",
    lat_col: str = "latitude",
    sort_keys: list[str] | None = None,
) -> pl.DataFrame:
    """Implementasi pemrosesan chunked untuk find_edge_candidates guna menghindari OOM."""
    total_rows = points_df.height
    processed_chunks = []
    
    for offset in range(0, total_rows, chunk_size):
        chunk = points_df.slice(offset, chunk_size)
        chunk_candidates = find_edge_candidates(
            chunk,
            edge_index,
            source_epsg=source_epsg,
            max_distance_m=max_distance_m,
            lon_col=lon_col,
            lat_col=lat_col,
            sort_keys=None 
        )
        processed_chunks.append(chunk_candidates)

    df_candidates = pl.concat(processed_chunks)
    if sort_keys:
        df_candidates = df_candidates.sort(sort_keys)
    return df_candidates

def main():
    rru_edges = gpd.read_file(GEOJSON_EDGES)
    edge_index = build_edge_spatial_index(rru_edges, target_epsg=EPSG_UTM49S)
    print(f"R-tree: {len(edge_index[1])} edge")
    
    df_bb_lazy = pl.scan_parquet(OUTPUT_BBOX)
    df_bb = df_bb_lazy.collect() 
    print(f"Total baris yang akan diproses: {df_bb.height:,}")
    
    df_candidates = find_edge_candidates_chunked(
        df_bb,
        edge_index,
        source_epsg=EPSG_WGS84,
        max_distance_m=MAX_DIST_METERS,
        chunk_size=2_000_000,
        sort_keys=["maid", "timestamp"]
    )

    n_drop = df_bb.height - df_candidates.height
    print(f"Lolos filter (>=1 edge <={MAX_DIST_METERS}m): {df_candidates.height:,}")
    print(f"Drop (0 kandidat)                     : {n_drop:,}")

    df_candidates = drop_singleton_maids(df_candidates, label="stage 1b")
    df_candidates.write_parquet(OUTPUT_CANDIDATES, compression="zstd")

    size_mb = OUTPUT_CANDIDATES.stat().st_size / 1024 / 1024
    print(f"\nTersimpan: {OUTPUT_CANDIDATES.resolve()} ({size_mb:.1f} MB)")

if __name__ == "__main__":
    main()
