import os
import math
import duckdb

def get_con(base_dir: str) -> duckdb.DuckDBPyConnection:
    """Buat koneksi DuckDB dengan konfigurasi standar (4 GB RAM, 4 threads)."""
    con = duckdb.connect()
    tmp = os.path.join(base_dir, ".", ".duckdb_tmp")
    os.makedirs(tmp, exist_ok=True)
    con.execute(f"SET temp_directory='{tmp}'")
    con.execute("SET memory_limit='4GB'")
    con.execute("SET preserve_insertion_order=false")
    con.execute("SET threads=4")
    return con

# Fungsi haversine (meter)
def haversine_m(lat1, lon1, lat2, lon2):
    R = 6371000.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlmb = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlmb / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))