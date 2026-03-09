"""
Script untuk mengkonversi semua CSV di DataGPS, DataMPD, dan PeopleGraph
ke format Parquet yang lebih efisien (storage + query speed).

Hasil disimpan di DataGPS_parquet/, DataMPD_parquet/, dan PeopleGraph_parquet/.
Setiap bulan digabung menjadi satu file Parquet (menghilangkan part-files).

Keuntungan Parquet vs CSV:
- Kompresi ~3-10x lebih kecil (zstd compression)
- Columnar format → hanya baca kolom yang diperlukan
- Tipe data native (int, float) → tidak perlu parsing string
- Predicate pushdown → filter tanpa baca seluruh file
"""

import os
import logging
import pandas as pd
import duckdb
import pyarrow as pa
import pyarrow.parquet as pq
import time

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# ==========================================
# SETUP LOGGING
# ==========================================
LOG_DIR = os.path.join(BASE_DIR, 'log')
os.makedirs(LOG_DIR, exist_ok=True)
log_file = os.path.join(LOG_DIR, 'convert_to_parquet.log')

logger = logging.getLogger('convert_to_parquet')
logger.setLevel(logging.INFO)
fh = logging.FileHandler(log_file, mode='w', encoding='utf-8')
fh.setFormatter(logging.Formatter('%(asctime)s [%(levelname)s] %(message)s', datefmt='%Y-%m-%d %H:%M:%S'))
logger.addHandler(fh)

# Temp dir untuk DuckDB spill-to-disk saat sorting
DUCKDB_TEMP = os.path.join(BASE_DIR, '.duckdb_tmp')
os.makedirs(DUCKDB_TEMP, exist_ok=True)

def duckdb_low_mem():
    """Buat koneksi DuckDB dengan limit RAM 2 GB, spill ke disk."""
    con = duckdb.connect()
    con.execute(f"SET temp_directory='{DUCKDB_TEMP}'")
    con.execute("SET memory_limit='2GB'")
    return con

# ==========================================
# 1. KONVERSI DataGPS (per bulan, gabung parts)
# ==========================================
GPS_SRC = os.path.join(BASE_DIR, 'DataGPS')
GPS_DST = os.path.join(BASE_DIR, 'DataGPS_parquet')
os.makedirs(GPS_DST, exist_ok=True)

# Mapping: nama output → list file CSV sumber
gps_files = {
    '2021_10_Oktober': ['2021Oktober/Oktober2021.csv'],
    '2021_11_November': [f'2021November/November2021_part{i}.csv' for i in range(1, 8)],
    '2021_12_Desember': [f'2021Desember/Desember2021_part{i}.csv' for i in range(1, 4)],
    '2022_01_Januari': [f'2022Januari/Januari2022_part{i}.csv' for i in range(1, 3)],
    '2022_02_Februari': [f'2022Februari/Februari2022_part{i}.csv' for i in range(1, 3)],
    '2022_03_Maret': [f'2022Maret/Maret2022_part{i}.csv' for i in range(1, 3)],
    '2022_04_April': ['2022April/April2022.csv'],
    '2022_05_Mei': [f'2022Mei/Mei2022_part{i}.csv' for i in range(1, 3)],
    '2022_06_Juni': ['2022Juni/Juni2022.csv'],
}

GPS_SCHEMA = pa.schema([
    ('maid', pa.string()),
    ('latitude', pa.float32()),
    ('longitude', pa.float32()),
    ('timestamp', pa.int64()),
])

CHUNK_SIZE = 500_000

print("=" * 60)
print("KONVERSI CSV → PARQUET")
print("=" * 60)
logger.info("Mulai konversi CSV → Parquet")

total_csv_bytes = 0
total_pq_bytes = 0

for month_name, csv_list in gps_files.items():
    t0 = time.time()
    out_path = os.path.join(GPS_DST, f'{month_name}.parquet')
    
    if os.path.exists(out_path):
        print(f"  [SKIP] {month_name}.parquet sudah ada")
        logger.info(f"[SKIP] {month_name}.parquet sudah ada")
        total_pq_bytes += os.path.getsize(out_path)
        for cf in csv_list:
            fp = os.path.join(GPS_SRC, cf)
            if os.path.exists(fp):
                total_csv_bytes += os.path.getsize(fp)
        continue
    
    print(f"\n  [{month_name}] Mengkonversi {len(csv_list)} file CSV...", flush=True)
    logger.info(f"[{month_name}] Mulai konversi {len(csv_list)} file CSV")
    
    writer = None
    total_rows = 0
    month_csv_bytes = 0
    rows_dropped = 0
    
    for csv_file in csv_list:
        fpath = os.path.join(GPS_SRC, csv_file)
        if not os.path.exists(fpath):
            print(f"    [WARN] File tidak ditemukan: {csv_file}")
            logger.warning(f"[{month_name}] File tidak ditemukan: {csv_file}")
            continue
        
        month_csv_bytes += os.path.getsize(fpath)
        
        for chunk in pd.read_csv(fpath, chunksize=CHUNK_SIZE,
                                  dtype={'maid': str, 'latitude': str, 
                                         'longitude': str, 'timestamp': str}):
            # Konversi tipe data
            chunk['latitude'] = pd.to_numeric(chunk['latitude'], errors='coerce').astype('float32')
            chunk['longitude'] = pd.to_numeric(chunk['longitude'], errors='coerce').astype('float32')
            chunk['timestamp'] = pd.to_numeric(chunk['timestamp'], errors='coerce').astype('Int64')
            before_drop = len(chunk)
            chunk = chunk.dropna(subset=['latitude', 'longitude', 'timestamp'])
            rows_dropped += before_drop - len(chunk)
            chunk['timestamp'] = chunk['timestamp'].astype('int64')
            
            table = pa.Table.from_pandas(chunk, schema=GPS_SCHEMA, preserve_index=False)
            
            if writer is None:
                writer = pq.ParquetWriter(out_path, GPS_SCHEMA, compression='zstd')
            
            writer.write_table(table)
            total_rows += len(chunk)
    
    if writer is not None:
        writer.close()
    
    if rows_dropped > 0:
        logger.info(f"[{month_name}] Dropped {rows_dropped:,} baris dengan NaN (latitude/longitude/timestamp)")
    
    # Sorting berdasarkan maid lalu timestamp (DuckDB out-of-core, hemat RAM)
    if os.path.exists(out_path):
        logger.info(f"[{month_name}] Sorting berdasarkan maid, timestamp (out-of-core)...")
        print(f"    Sorting berdasarkan maid, timestamp...", flush=True)
        t_sort = time.time()
        tmp_sorted = out_path + '.sorting.tmp'
        con = duckdb_low_mem()
        con.execute("""
            COPY (SELECT * FROM read_parquet($1) ORDER BY maid, timestamp)
            TO $2 (FORMAT PARQUET, COMPRESSION ZSTD)
        """, [out_path, tmp_sorted])
        con.close()
        os.replace(tmp_sorted, out_path)
        logger.info(f"[{month_name}] Sorting selesai dalam {time.time() - t_sort:.1f}s")
    
    pq_size = os.path.getsize(out_path) if os.path.exists(out_path) else 0
    total_csv_bytes += month_csv_bytes
    total_pq_bytes += pq_size
    
    elapsed = time.time() - t0
    ratio = month_csv_bytes / pq_size if pq_size > 0 else 0
    print(f"    → {total_rows:,} baris | CSV: {month_csv_bytes/1e6:.0f} MB → Parquet: {pq_size/1e6:.0f} MB ({ratio:.1f}x kompresi) | {elapsed:.1f}s")
    logger.info(f"[{month_name}] {total_rows:,} baris | CSV: {month_csv_bytes/1e6:.0f} MB → Parquet: {pq_size/1e6:.0f} MB ({ratio:.1f}x) | {elapsed:.1f}s")


# ==========================================
# 2. KONVERSI PeopleGraph
# ==========================================
PG_SRC = os.path.join(GPS_SRC, 'PeopleGraph', 'people_graph.csv')
pg_out = os.path.join(GPS_DST, 'people_graph.parquet')

if os.path.exists(pg_out):
    print(f"\n  [SKIP] people_graph.parquet sudah ada")
    logger.info(f"[SKIP] people_graph.parquet sudah ada")
    total_pq_bytes += os.path.getsize(pg_out)
    total_csv_bytes += os.path.getsize(PG_SRC)
else:
    print(f"\n  [PeopleGraph] Mengkonversi...", flush=True)
    logger.info("[PeopleGraph] Mulai konversi")
    t0 = time.time()
    pg_csv_size = os.path.getsize(PG_SRC)
    
    pg_cols = ['maid', 'gender', 'col3', 'col4', 'country', 'geohash', 'income',
               'province', 'kabupaten', 'kecamatan', 'kelurahan']
    
    # PeopleGraph tidak punya header
    df_pg = pd.read_csv(PG_SRC, header=None, names=pg_cols, quotechar='"',
                         na_values=['\\N'], dtype=str)
    
    # Hapus kolom kosong / tidak berguna
    df_pg = df_pg.drop(columns=['col3', 'col4'], errors='ignore')

    # Hapus baris duplikat
    before = len(df_pg)
    df_pg = df_pg.drop_duplicates()
    after = len(df_pg)
    if before > after:
        print(f"    Hapus {before - after:,} baris duplikat ({before:,} → {after:,})")
        logger.info(f"[PeopleGraph] Hapus {before - after:,} baris duplikat ({before:,} → {after:,})")
    
    # Konversi ke kategorikal (hemat memori untuk kolom low-cardinality)
    for col in ['gender', 'country', 'income', 'province', 'kabupaten', 'kecamatan', 'kelurahan']:
        if col in df_pg.columns:
            df_pg[col] = df_pg[col].astype('category')
    
    # Simpan ke Parquet (tanpa sort dulu)
    table = pa.Table.from_pandas(df_pg, preserve_index=False)
    n_rows_pg = len(df_pg)
    del df_pg  # bebaskan RAM sebelum sort
    pq.write_table(table, pg_out, compression='zstd',
                   use_dictionary=['gender', 'country', 'income', 'province', 
                                   'kabupaten', 'kecamatan', 'kelurahan'])
    del table
    
    # Sorting berdasarkan maid (DuckDB out-of-core, hemat RAM)
    logger.info("[PeopleGraph] Sorting berdasarkan maid (out-of-core)...")
    print(f"    Sorting berdasarkan maid...", flush=True)
    pg_tmp = pg_out + '.sorting.tmp'
    con = duckdb_low_mem()
    con.execute("""
        COPY (SELECT * FROM read_parquet($1) ORDER BY maid)
        TO $2 (FORMAT PARQUET, COMPRESSION ZSTD)
    """, [pg_out, pg_tmp])
    con.close()
    os.replace(pg_tmp, pg_out)
    logger.info("[PeopleGraph] Sorting selesai")
    
    pg_pq_size = os.path.getsize(pg_out)
    total_csv_bytes += pg_csv_size
    total_pq_bytes += pg_pq_size
    
    elapsed = time.time() - t0
    ratio = pg_csv_size / pg_pq_size if pg_pq_size > 0 else 0
    print(f"    → {n_rows_pg:,} baris | CSV: {pg_csv_size/1e6:.0f} MB → Parquet: {pg_pq_size/1e6:.0f} MB ({ratio:.1f}x kompresi) | {elapsed:.1f}s")
    logger.info(f"[PeopleGraph] {n_rows_pg:,} baris | CSV: {pg_csv_size/1e6:.0f} MB → Parquet: {pg_pq_size/1e6:.0f} MB ({ratio:.1f}x) | {elapsed:.1f}s")


# ==========================================
# 3. KONVERSI DataMPD
# ==========================================
MPD_SRC = os.path.join(BASE_DIR, 'DataMPD', 'mpd_sample_small.csv')
MPD_DST = os.path.join(BASE_DIR, 'DataMPD_parquet')
os.makedirs(MPD_DST, exist_ok=True)
mpd_out = os.path.join(MPD_DST, 'mpd_sample_small.parquet')

if os.path.exists(mpd_out):
    print(f"\n  [SKIP] mpd_sample_small.parquet sudah ada")
    logger.info("[SKIP] mpd_sample_small.parquet sudah ada")
    total_pq_bytes += os.path.getsize(mpd_out)
    total_csv_bytes += os.path.getsize(MPD_SRC)
else:
    print(f"\n  [DataMPD] Mengkonversi...", flush=True)
    logger.info("[DataMPD] Mulai konversi")
    t0 = time.time()
    mpd_csv_size = os.path.getsize(MPD_SRC)
    
    df_mpd = pd.read_csv(MPD_SRC, na_values=['\\N'])
    
    table = pa.Table.from_pandas(df_mpd, preserve_index=False)
    pq.write_table(table, mpd_out, compression='zstd')
    
    mpd_pq_size = os.path.getsize(mpd_out)
    total_csv_bytes += mpd_csv_size
    total_pq_bytes += mpd_pq_size
    
    elapsed = time.time() - t0
    ratio = mpd_csv_size / mpd_pq_size if mpd_pq_size > 0 else 0
    print(f"    → {len(df_mpd):,} baris | CSV: {mpd_csv_size/1e6:.1f} MB → Parquet: {mpd_pq_size/1e6:.1f} MB ({ratio:.1f}x kompresi) | {elapsed:.1f}s")
    logger.info(f"[DataMPD] {len(df_mpd):,} baris | CSV: {mpd_csv_size/1e6:.1f} MB → Parquet: {mpd_pq_size/1e6:.1f} MB ({ratio:.1f}x) | {elapsed:.1f}s")


# ==========================================
# RINGKASAN
# ==========================================
print("\n" + "=" * 60)
print("RINGKASAN KONVERSI")
print("=" * 60)
print(f"  Total CSV  : {total_csv_bytes/1e9:.2f} GB")
print(f"  Total Parquet: {total_pq_bytes/1e9:.2f} GB")
if total_pq_bytes > 0:
    print(f"  Rasio kompresi: {total_csv_bytes/total_pq_bytes:.1f}x lebih kecil")
    print(f"  Hemat: {(total_csv_bytes - total_pq_bytes)/1e9:.2f} GB ({(1 - total_pq_bytes/total_csv_bytes)*100:.0f}%)")
print("=" * 60)
print("\nFile Parquet tersedia di:")
print(f"  - {GPS_DST}/")
print(f"  - {MPD_DST}/")
logger.info(f"Ringkasan: CSV {total_csv_bytes/1e9:.2f} GB → Parquet {total_pq_bytes/1e9:.2f} GB")
logger.info("Selesai!")
print(f"\nLog tersimpan di: {log_file}")
print("\nSelesai!")

