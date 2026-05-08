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