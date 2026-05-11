import polars as pl
import numpy as np
import matplotlib.pyplot as plt
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

def plot_bilocation_spread(bilocation_df: pl.DataFrame, start_threshold: float = 0.1, max_threshold: float = 10.0, step: float = 0.1):
    """
    Menampilkan grafik jumlah keseluruhan ping (n_pings) yang event bilocation-nya
    memiliki sebaran (spread_m) di bawah atau sama dengan threshold tertentu.
    """
    thresholds = np.arange(start_threshold, max_threshold + step, step)
    counts = []
    
    for th in thresholds:
        # Filter ping yang berada dalam interval (th - step, th] (non-kumulatif)
        lower_bound = round(th - step, 5)
        count = bilocation_df.filter(
            (pl.col("spread_m") > lower_bound) & (pl.col("spread_m") <= th)
        )["n_pings"].sum()
        counts.append(count if count is not None else 0)
        
    plt.figure(figsize=(10, 6))
    plt.bar(thresholds, counts, width=step*0.8, color='#d62728', alpha=0.7)
    
    plt.title('Distribusi Jumlah Ping Bilocation per Interval Spread (m)')
    plt.xlabel('Spread Interval (m)')
    plt.ylabel('Jumlah Ping (Total n_pings)')
    plt.grid(True, linestyle='--', alpha=0.7)
    
    # Atur ticks X agar rapi
    step_ticks = max(1.0, max_threshold // 10)
    plt.xlim(left=max(0, start_threshold - step))
    
    # Supaya tick di x axis lebih rapi 
    # (misal kalau start=0.1, tick kita pakai bulat saja kecuali sangat kecil)
    ticks_range = np.arange(round(start_threshold), max_threshold + step_ticks, step_ticks)
    if len(ticks_range) == 0 or ticks_range[0] > start_threshold:
        ticks_range = np.insert(ticks_range, 0, start_threshold)
    plt.xticks(ticks_range)
    
    plt.tight_layout()
    plt.show()

def main():
    df_candidates_lazy = pl.scan_parquet(OUTPUT_CANDIDATES)
    df_candidates = df_candidates_lazy.collect()
    per_key = aggregate_per_key(df_candidates)
    bilocation = add_bbox_spread_column(per_key.filter(pl.col("n_pings") > 1))
    report_bilocation_prevalence(
        per_key.with_columns(pl.lit(0.0).alias("spread_m")).update(bilocation, on=["maid", "timestamp"]),
        n_total_rows=df_candidates.height,
    )
    
    # Menampilkan plot
    plot_bilocation_spread(bilocation, start_threshold=5.0, max_threshold=20.0, step=0.2)

if __name__ == "__main__":
    main()