"""
Shared utilities untuk seluruh skrip analisis skripsi.
=====================================================
Modul ini berisi konstanta, konfigurasi, dan fungsi pembantu yang
digunakan secara identik di analisis 1–12.
"""

import os

import duckdb
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

# ---------------------------------------------------------------------------
# Konstanta Wilayah DIY
# ---------------------------------------------------------------------------
LAT_MIN = -8.2
LAT_MAX = -7.55
LON_MIN = 110.0
LON_MAX = 110.85

# ---------------------------------------------------------------------------
# Daftar File Data Bulanan (Oktober 2021 – Juni 2022)
# ---------------------------------------------------------------------------
DATA_FILES: list[tuple[str, str]] = [
    ("2021_10_Oktober", "2021_10_Oktober.parquet"),
    ("2021_11_November", "2021_11_November.parquet"),
    ("2021_12_Desember", "2021_12_Desember.parquet"),
    ("2022_01_Januari", "2022_01_Januari.parquet"),
    ("2022_02_Februari", "2022_02_Februari.parquet"),
    ("2022_03_Maret", "2022_03_Maret.parquet"),
    ("2022_04_April", "2022_04_April.parquet"),
    ("2022_05_Mei", "2022_05_Mei.parquet"),
    ("2022_06_Juni", "2022_06_Juni.parquet"),
]


# ---------------------------------------------------------------------------
# DuckDB Connection Helper
# ---------------------------------------------------------------------------
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


# ---------------------------------------------------------------------------
# Matplotlib Setup
# ---------------------------------------------------------------------------
def setup_matplotlib(dpi: int = 150) -> None:
    """Konfigurasi matplotlib untuk rendering non-interaktif."""
    plt.rcParams["figure.dpi"] = dpi
