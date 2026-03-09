"""
Script untuk mengkonversi semua CSV di DataGPS, DataMPD, dan PeopleGraph
ke format Parquet yang lebih efisien (storage + query speed).

Hasil disimpan di DataGPS_parquet/, DataMPD_parquet/, dan PeopleGraph_parquet/.
Struktur folder dan file dipertahankan sama seperti CSV sumber.

Keuntungan Parquet vs CSV:
- Kompresi ~3-10x lebih kecil (zstd compression)
- Columnar format → hanya baca kolom yang diperlukan
- Tipe data native (int, float) → tidak perlu parsing string
- Predicate pushdown → filter tanpa baca seluruh file
"""

import os
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import time

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# ==========================================
# 1. KONVERSI DataGPS (per file, struktur folder sama)
# ==========================================
GPS_SRC = os.path.join(BASE_DIR, 'DataGPS')
GPS_DST = os.path.join(BASE_DIR, 'DataGPS_parquet')
os.makedirs(GPS_DST, exist_ok=True)

# List semua file CSV sumber (path relatif terhadap GPS_SRC)
gps_csv_files = [
    '2021Oktober/Oktober2021.csv',
    *[f'2021November/November2021_part{i}.csv' for i in range(1, 8)],
    *[f'2021Desember/Desember2021_part{i}.csv' for i in range(1, 4)],
    *[f'2022Januari/Januari2022_part{i}.csv' for i in range(1, 3)],
    *[f'2022Februari/Februari2022_part{i}.csv' for i in range(1, 3)],
    *[f'2022Maret/Maret2022_part{i}.csv' for i in range(1, 3)],
    '2022April/April2022.csv',
    *[f'2022Mei/Mei2022_part{i}.csv' for i in range(1, 3)],
    '2022Juni/Juni2022.csv',
]

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

total_csv_bytes = 0
total_pq_bytes = 0

for csv_rel_path in gps_csv_files:
    t0 = time.time()
    fpath = os.path.join(GPS_SRC, csv_rel_path)
    
    # Buat path output dengan struktur folder yang sama, ganti ekstensi .csv → .parquet
    parquet_rel_path = os.path.splitext(csv_rel_path)[0] + '.parquet'
    out_path = os.path.join(GPS_DST, parquet_rel_path)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    
    if not os.path.exists(fpath):
        print(f"  [WARN] File tidak ditemukan: {csv_rel_path}")
        continue
    
    csv_size = os.path.getsize(fpath)
    total_csv_bytes += csv_size
    
    if os.path.exists(out_path):
        print(f"  [SKIP] {parquet_rel_path} sudah ada")
        total_pq_bytes += os.path.getsize(out_path)
        continue
    
    print(f"\n  [{csv_rel_path}] Mengkonversi...", flush=True)
    
    writer = None
    file_rows = 0
    
    for chunk in pd.read_csv(fpath, chunksize=CHUNK_SIZE,
                              dtype={'maid': str, 'latitude': str, 
                                     'longitude': str, 'timestamp': str}):
        # Konversi tipe data
        chunk['latitude'] = pd.to_numeric(chunk['latitude'], errors='coerce').astype('float32')
        chunk['longitude'] = pd.to_numeric(chunk['longitude'], errors='coerce').astype('float32')
        chunk['timestamp'] = pd.to_numeric(chunk['timestamp'], errors='coerce').astype('Int64')
        chunk = chunk.dropna(subset=['latitude', 'longitude', 'timestamp'])
        chunk['timestamp'] = chunk['timestamp'].astype('int64')
        
        table = pa.Table.from_pandas(chunk, schema=GPS_SCHEMA, preserve_index=False)
        
        if writer is None:
            writer = pq.ParquetWriter(out_path, GPS_SCHEMA, compression='zstd')
        
        writer.write_table(table)
        file_rows += len(chunk)
    
    if writer is not None:
        writer.close()
    
    pq_size = os.path.getsize(out_path) if os.path.exists(out_path) else 0
    total_pq_bytes += pq_size
    
    elapsed = time.time() - t0
    ratio = csv_size / pq_size if pq_size > 0 else 0
    print(f"    → {file_rows:,} baris | CSV: {csv_size/1e6:.0f} MB → Parquet: {pq_size/1e6:.0f} MB ({ratio:.1f}x kompresi) | {elapsed:.1f}s")


# ==========================================
# 2. KONVERSI PeopleGraph
# ==========================================
PG_SRC = os.path.join(GPS_SRC, 'PeopleGraph', 'people_graph.csv')
PG_DST = os.path.join(BASE_DIR, 'PeopleGraph_parquet')
os.makedirs(PG_DST, exist_ok=True)
pg_out = os.path.join(PG_DST, 'people_graph.parquet')

if os.path.exists(pg_out):
    print(f"\n  [SKIP] people_graph.parquet sudah ada")
    total_pq_bytes += os.path.getsize(pg_out)
    total_csv_bytes += os.path.getsize(PG_SRC)
else:
    print(f"\n  [PeopleGraph] Mengkonversi...", flush=True)
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
    
    # Konversi ke kategorikal (hemat memori untuk kolom low-cardinality)
    for col in ['gender', 'country', 'income', 'province', 'kabupaten', 'kecamatan', 'kelurahan']:
        if col in df_pg.columns:
            df_pg[col] = df_pg[col].astype('category')
    
    # Simpan dictionary encoding otomatis di Parquet
    table = pa.Table.from_pandas(df_pg, preserve_index=False)
    pq.write_table(table, pg_out, compression='zstd',
                   use_dictionary=['gender', 'country', 'income', 'province', 
                                   'kabupaten', 'kecamatan', 'kelurahan'])
    
    pg_pq_size = os.path.getsize(pg_out)
    total_csv_bytes += pg_csv_size
    total_pq_bytes += pg_pq_size
    
    elapsed = time.time() - t0
    ratio = pg_csv_size / pg_pq_size if pg_pq_size > 0 else 0
    print(f"    → {len(df_pg):,} baris | CSV: {pg_csv_size/1e6:.0f} MB → Parquet: {pg_pq_size/1e6:.0f} MB ({ratio:.1f}x kompresi) | {elapsed:.1f}s")


# ==========================================
# 3. KONVERSI DataMPD
# ==========================================
MPD_SRC = os.path.join(BASE_DIR, 'DataMPD', 'mpd_sample_small.csv')
MPD_DST = os.path.join(BASE_DIR, 'DataMPD_parquet')
os.makedirs(MPD_DST, exist_ok=True)
mpd_out = os.path.join(MPD_DST, 'mpd_sample_small.parquet')

if os.path.exists(mpd_out):
    print(f"\n  [SKIP] mpd_sample_small.parquet sudah ada")
    total_pq_bytes += os.path.getsize(mpd_out)
    total_csv_bytes += os.path.getsize(MPD_SRC)
else:
    print(f"\n  [DataMPD] Mengkonversi...", flush=True)
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
print(f"  - {PG_DST}/")
print(f"  - {MPD_DST}/")
print("\nSelesai!")
