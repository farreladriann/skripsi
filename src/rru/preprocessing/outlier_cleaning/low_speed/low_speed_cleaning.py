import pandas as pd
from pathlib import Path
import sys

# Import fungsi dari file sebelahnya
from src.rru.preprocessing.outlier_cleaning.low_speed.low_speed_check import calculate_consecutive_speed

INPUT_PATH = Path("./data/processed/gps_rru_collapsed.parquet")
OUTPUT_PATH = Path("./data/processed/gps_rru_cleaned_lowspeed.parquet")

# Threshold ini di-set ke 5.0 km/jam sesuai modifikasi dari pengamatan Anda
MIN_SPEED_MAX_THRESHOLD = 5.0 

def drop_low_speed_maids(df: pd.DataFrame, min_speed_kmh: float) -> pd.DataFrame:
    """
    Menghapus MAID yang selalu berjalan sangat lambat atau diam 
    (nilai kecepatan maksimalnya di bawah min_speed_kmh).
    """
    print(f"Menghitung metrik antar-ping untuk {len(df):,} baris data...")
    # Hitung kecepatan menggunakan fungsi dari low_speed_check.py
    df_metrics = calculate_consecutive_speed(df)
    
    print(f"Mencari MAID yang tidak pernah melampaui batas kecepatan {min_speed_kmh} km/jam...")
    
    # Kelompokkan berdasarkan maid, cari max_speed-nya
    maid_max_speed = df_metrics.groupby('maid')['speed_kmh'].max()
    
    # Filter valid MAIDs
    valid_maids_list = maid_max_speed[maid_max_speed >= min_speed_kmh].index
    
    # Filter dataset utama berdasarkan MAID yang valid
    df_cleaned = df_metrics[df_metrics['maid'].isin(valid_maids_list)].copy()
    
    # Hapus kolom bantuan yang ditambahkan oleh calculate_consecutive_speed agar footprint kembali seperti aslinya
    df_cleaned = df_cleaned.drop(columns=['time_diff_hours', 'distance_km', 'speed_kmh'])
    
    # Kalkulasi statisik hasil cleaning
    n_maids_before = df['maid'].nunique()
    n_maids_after = len(valid_maids_list)
    n_dropped_maids = n_maids_before - n_maids_after
    
    print(f"\n--- Ringkasan Pembersihan Low Speed (Non-Vehicles) ---")
    print(f"MAID terhapus   : {n_dropped_maids:,} (dari {n_maids_before:,} MAID)")
    print(f"Baris terhapus  : {len(df) - len(df_cleaned):,} baris")
    print(f"Sisa Data MAID  : {n_maids_after:,} MAID")
    print(f"Sisa Data Baris : {len(df_cleaned):,} baris\n")
    
    return df_cleaned

def main():
    if not INPUT_PATH.exists():
        print(f"ERROR: File {INPUT_PATH} tidak ditemukan.")
        print("Jalankan / pastikan script collapse_bilocation.py telah terselesaikan.")
        return
        
    print(f"Membaca data: {INPUT_PATH.resolve()}")
    df = pd.read_parquet(INPUT_PATH)
    
    # Cek & samakan tipe timestamp menjadi datetime seperti yang dibutuhkan low_speed_check.py
    if not pd.api.types.is_datetime64_any_dtype(df['timestamp']):
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s')

    # Proses Drop Low Speed
    df_cleaned = drop_low_speed_maids(df, min_speed_kmh=MIN_SPEED_MAX_THRESHOLD)
    
    print(f"Menyimpan data hasil pembersihan ke {OUTPUT_PATH.resolve()}...")
    
    # Simpan kembali format parquet dengan kompresi zstd
    df_cleaned.to_parquet(OUTPUT_PATH, compression="zstd")
    print("Pemrosesan Selesai.")

if __name__ == "__main__":
    main()