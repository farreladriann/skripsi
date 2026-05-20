import numpy as np
import polars as pl

R_EARTH_M = 6_371_008.8  # WGS84 mean Earth radius

def haversine_m(lat1, lon1, lat2, lon2):
    """Jarak Haversine dalam meter. Vectorized (numpy) & scalar keduanya OK."""
    lat1r = np.radians(lat1)
    lat2r = np.radians(lat2)
    dlat = lat2r - lat1r
    dlon = np.radians(np.asarray(lon2) - np.asarray(lon1))
    a = np.sin(dlat / 2) ** 2 + np.cos(lat1r) * np.cos(lat2r) * np.sin(dlon / 2) ** 2
    return 2 * R_EARTH_M * np.arcsin(np.sqrt(a))

def drop_singleton_maids(df: pl.DataFrame, *, min_pings: int = 2,
                         label: str = "") -> pl.DataFrame:
    """Drop MAID yang punya < `min_pings` ping. Print summary perubahan."""
    before_maids = df["maid"].n_unique()
    before_pings = df.height

    df_out = df.filter(pl.len().over("maid") >= min_pings)

    after_maids = df_out["maid"].n_unique()
    after_pings = df_out.height

    prefix = f"[{label}] " if label else ""
    print(f"{prefix}drop singleton MAID (< {min_pings} ping): "
          f"{before_maids - after_maids:,} maid "
          f"({before_pings - after_pings:,} ping)")
    print(f"{prefix}sisa: {after_maids:,} maid, {after_pings:,} ping")
    return df_out

import math

def calculate_inter_ping_metrics(
    df: pl.DataFrame, 
    maid_col: str = "maid",
    time_col: str = "timestamp", 
    lat_col: str = "latitude", 
    lon_col: str = "longitude"
) -> pl.DataFrame:
    """
    Menghitung metrik antar-ping (inter-ping) berturut-turut untuk setiap MAID.
    Kolom yang ditambahkan:
    - dt_seconds: Selisih waktu dengan ping sebelumnya (detik)
    - dist_meters: Jarak Haversine dengan ping sebelumnya (meter)
    - speed_kmh: Kecepatan antara dua ping (km/jam)
    """
    
    # 1. Pastikan data terurut berdasarkan MAID dan Waktu
    df = df.sort([maid_col, time_col])
    
    # 2. Persiapan formula Haversine (Pure Polars Expression untuk performa maksimal)
    lat1 = pl.col(lat_col)
    lon1 = pl.col(lon_col)
    lat2 = pl.col(lat_col).shift(1).over(maid_col)
    lon2 = pl.col(lon_col).shift(1).over(maid_col)
    
    # Konversi ke radian
    to_rad = math.pi / 180.0
    lat1_rad = lat1 * to_rad
    lat2_rad = lat2 * to_rad
    dlat_rad = (lat2 - lat1) * to_rad
    dlon_rad = (lon2 - lon1) * to_rad
    
    a = (dlat_rad / 2).sin()**2 + lat1_rad.cos() * lat2_rad.cos() * (dlon_rad / 2).sin()**2
    c = 2 * a.sqrt().arcsin()
    dist_expr = R_EARTH_M * c
    
    # 3. Ekspresi selisih waktu (dt) 
    # Cek tipe timestamp: jika datetime, hitung selisih detik. Jika integer (unix epoch), langsung kurangi.
    if df[time_col].dtype in [pl.Int64, pl.Float64, pl.Int32, pl.Float32]:
        dt_expr = pl.col(time_col) - pl.col(time_col).shift(1).over(maid_col)
    else:
        # Asumsi tipe adalah Datetime, dikonversi total detiknya
        dt_expr = (pl.col(time_col) - pl.col(time_col).shift(1).over(maid_col)).dt.total_seconds()

    # 4. Terapkan perhitungan ke DataFrame
    df = df.with_columns([
        dt_expr.alias("dt_seconds"),
        dist_expr.alias("dist_meters")
    ])
    
    # 5. Hitung Kecepatan (km/h) = (meter / 1000) / (detik / 3600) -> (meter / detik) * 3.6
    # fill_nan dan fill_null untuk menangani pembagian dengan dt_seconds = 0
    df = df.with_columns(
        pl.when(pl.col("dt_seconds") > 0)
        .then((pl.col("dist_meters") / pl.col("dt_seconds")) * 3.6)
        .otherwise(0.0) # Jika ping terjadi di detik yang sama, set speed 0
        .alias("speed_kmh")
    )
    
    return df