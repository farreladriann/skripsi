import polars as pl
import numpy as np
from pathlib import Path
from src.rru.utils import haversine_m

OUTPUT_CANDIDATES = Path("./data/interim/gps_rru_candidates.parquet")

def aggregate_per_key(df: pl.DataFrame,
                     keys: tuple[str, ...] = ("maid", "timestamp")) -> pl.DataFrame:
    """Per (maid, ts): n_pings + bbox lat/lon (untuk hitung spread)."""
    return (
        df.lazy()
        .group_by(list(keys))
        .agg(
            n_pings=pl.len(),
            lat_min=pl.col("latitude").min(),
            lat_max=pl.col("latitude").max(),
            lon_min=pl.col("longitude").min(),
            lon_max=pl.col("longitude").max(),
        )
        .collect()
    )


def add_bbox_spread_column(per_key: pl.DataFrame) -> pl.DataFrame:
    """spread_m = max diagonal of bbox in meters (upper bound on max pairwise dist)."""
    lat_min = per_key["lat_min"].to_numpy()
    lat_max = per_key["lat_max"].to_numpy()
    lon_min = per_key["lon_min"].to_numpy()
    lon_max = per_key["lon_max"].to_numpy()
    diag_a = haversine_m(lat_min, lon_min, lat_max, lon_max)
    diag_b = haversine_m(lat_min, lon_max, lat_max, lon_min)
    return per_key.with_columns(pl.Series("spread_m", np.maximum(diag_a, diag_b)))


def report_bilocation_prevalence(per_key: pl.DataFrame, n_total_rows: int) -> None:
    """Ringkasan satu blok: prevalence bilocation + ringkasan spread."""
    n_keys = per_key.height
    bilocation = per_key.filter(pl.col("n_pings") > 1)
    n_bilocation = bilocation.height
    n_rows_bilocation = int(bilocation["n_pings"].sum()) if n_bilocation else 0
    pct_keys = n_bilocation / n_keys
    pct_rows = n_rows_bilocation / n_total_rows

    print(f"Bilocation: {n_bilocation:,} / {n_keys:,} keys ({pct_keys:.4%}) | "
          f"{n_rows_bilocation:,} / {n_total_rows:,} rows ({pct_rows:.4%})")

    if "spread_m" in bilocation.columns and n_bilocation:
        spread = bilocation["spread_m"].to_numpy()
        print(f"Spread (m): median={np.median(spread):.1f}  "
              f"p95={np.percentile(spread, 95):.1f}  "
              f"p99={np.percentile(spread, 99):.1f}  "
              f"max={spread.max():.1f}")
        
def main():
    df_candidates_lazy = pl.scan_parquet(OUTPUT_CANDIDATES)
    df_candidates = df_candidates_lazy.collect()
    per_key = aggregate_per_key(df_candidates)
    bilocation = add_bbox_spread_column(per_key.filter(pl.col("n_pings") > 1))
    report_bilocation_prevalence(
        per_key.with_columns(pl.lit(0.0).alias("spread_m")).update(bilocation, on=["maid", "timestamp"]),
        n_total_rows=df_candidates.height,
    )

if __name__ == "__main__":
    main()