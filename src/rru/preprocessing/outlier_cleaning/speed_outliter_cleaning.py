import polars as pl
import numpy as np
from pathlib import Path
from src.rru.utils import drop_singleton_maids

# File Input & Output
INPUT_PARQUET = Path("./data/processed/gps_rru_collapsed.parquet")
OUTPUT_CLEANED = Path("./data/processed/gps_rru_speed_cleaned.parquet")

# Threshold Speed (contoh: 120 km/jam)
MAX_SPEED_KMH = 1000.0
MAX_SPEED_MS = MAX_SPEED_KMH * 1000 / 3600
R_EARTH_M = 6_371_008.8

def haversine_expr(lat1: pl.Expr, lon1: pl.Expr, lat2: pl.Expr, lon2: pl.Expr) -> pl.Expr:
    """Kalkulasi jarak Haversine dalam expression Polars."""
    lat1r = lat1 * np.pi / 180.0
    lat2r = lat2 * np.pi / 180.0
    dlat = (lat2 - lat1) * np.pi / 180.0
    dlon = (lon2 - lon1) * np.pi / 180.0
    
    a = (dlat / 2.0).sin() ** 2 + lat1r.cos() * lat2r.cos() * (dlon / 2.0).sin() ** 2
    return 2 * R_EARTH_M * a.sqrt().arcsin()

def filter_speed_outliers(df: pl.DataFrame) -> pl.DataFrame:
    # Urutkan berdasarkan Device dan Waktu
    df = df.sort(["maid", "timestamp"])

    df_speed = df.with_columns(
        time_diff = pl.col("timestamp").diff().over("maid"),
        dist_m = haversine_expr(
            pl.col("latitude").shift(1), pl.col("longitude").shift(1),
            pl.col("latitude"), pl.col("longitude")
        ).over("maid")
    ).with_columns(
        speed_ms = pl.col("dist_m") / pl.col("time_diff")
    )

    # Syarat Valid = Baris pertama (null) ATAU kecepatannya masuk akal (<= MAX_SPEED_MS)
    # Ini menghapus titik-titik lompatan GPS yang terlalu jauh dalam waktu terlalu singkat
    is_valid = pl.col("speed_ms").is_null() | (pl.col("speed_ms") <= MAX_SPEED_MS)
    
    df_clean = df_speed.filter(is_valid).drop(["time_diff", "dist_m", "speed_ms"])
    
    return df_clean

def main():
    if not INPUT_PARQUET.exists():
        print(f"File {INPUT_PARQUET} belum ada. Berhenti.")
        return

    print(f"Membaca {INPUT_PARQUET}...")
    df = pl.read_parquet(INPUT_PARQUET)
    
    before = df.height
    df_clean = filter_speed_outliers(df)
    
    
    after = df_clean.height
    
    print(f"\n--- Ringkasan Speed Outlier (Max: {MAX_SPEED_KMH} km/h) ---")
    print(f"Data awal: {before:,} baris")
    print(f"Data setelah pembersihan speed : {after:,} baris")
    print(f"Data dibuang: {before - after:,} baris")

    # Hapus kembali MAID yang hanya tersisa 1 titik akibat dropping outliers
    df_clean = drop_singleton_maids(df_clean, label="stage 1d speed_outlier")
    
    df_clean.write_parquet(OUTPUT_CLEANED, compression="zstd")
    print(f"\nTersimpan: {OUTPUT_CLEANED.resolve()}")

if __name__ == "__main__":
    main()