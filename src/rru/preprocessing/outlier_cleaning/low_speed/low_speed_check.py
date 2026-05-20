import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

def calculate_consecutive_speed(df: pd.DataFrame) -> pd.DataFrame:
    """
    Menghitung jarak dan kecepatan (km/h) antar ping berturut-turut untuk setiap MAID.
    Diasumsikan df memiliki kolom: 'maid', 'latitude', 'longitude', 'timestamp' (datetime).
    """
    # Pastikan data terurut berdasarkan MAID dan waktu
    df = df.sort_values(by=['maid', 'timestamp']).copy()
    
    # Hitung selisih waktu dalam jam
    df['time_diff_hours'] = df.groupby('maid')['timestamp'].diff().dt.total_seconds() / 3600.0
    
    # Vectorized Haversine distance
    lat1 = np.radians(df['latitude'])
    lon1 = np.radians(df['longitude'])
    lat2 = np.radians(df.groupby('maid')['latitude'].shift(1))
    lon2 = np.radians(df.groupby('maid')['longitude'].shift(1))
    
    dlat = lat1 - lat2
    dlon = lon1 - lon2
    a = np.sin(dlat / 2)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2)**2
    c = 2 * np.arcsin(np.sqrt(a))
    r = 6371.0 # Radius bumi dalam km
    
    df['distance_km'] = c * r
    
    # Hitung kecepatan (km/h)
    df['speed_kmh'] = df['distance_km'] / df['time_diff_hours']
    
    return df

def plot_low_speed_maids(df: pd.DataFrame, max_threshold: int = 20, step: float = 1.0):
    """
    Menganalisis tipe MAID yang kemungkinan besar "Bukan Kendaraan" (misal: diam atau berjalan kaki) 
    yaitu ketika MAID tersebut memilik kecepatan maksimal keseluruhan di bawah suatu threshold.
    """
    if 'speed_kmh' not in df.columns:
        print("Menghitung kecepatan antar ping...")
        df = calculate_consecutive_speed(df)
        
    # Cari nilai maksimum speed untuk setiap MAID
    # MAID yang nilai max speed-nya sangat rendah menandakan tidak pernah bergerak cepat
    max_speed_per_maid = df.groupby('maid')['speed_kmh'].max()
    
    thresholds = np.arange(step, max_threshold + step, step)
    counts = []
    
    for th in thresholds:
        # Hitung jumlah MAID yang nilai maksimal kecepatannya < th
        count = (max_speed_per_maid < th).sum()
        counts.append(count)
        
    # Membuat visualisasi grafik
    plt.figure(figsize=(10, 6))
    plt.plot(thresholds, counts, marker='o', linestyle='-', color='#1f77b4')
    
    plt.title('Jumlah MAID dengan Seluruh Ping di Bawah Ambang Kecepatan Tertentu')
    plt.xlabel('Speed Threshold (km/h)')
    plt.ylabel('Jumlah MAID (Max Speed < Threshold)')
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.xticks(np.arange(0, max_threshold + 1, step if max_threshold <= 20 else max_threshold // 10))
    
    # Tambahkan label jumlah di atas titik
    for i, count in enumerate(counts):
        plt.text(thresholds[i], count + (max(counts)*0.01), str(count), 
                 ha='center', va='bottom', fontsize=8, alpha=0.8)
                 
    plt.tight_layout()
    plt.show()
    
    return max_speed_per_maid, thresholds, counts

if __name__ == "__main__":
    OUTPUT_COLLAPSED = Path("./data/processed/gps_rru_collapsed.parquet")
    print(f"Membaca data dari {OUTPUT_COLLAPSED} ...")
    
    df_gps = pd.read_parquet(OUTPUT_COLLAPSED)
    
    if not pd.api.types.is_datetime64_any_dtype(df_gps['timestamp']):
        df_gps['timestamp'] = pd.to_datetime(df_gps['timestamp'], unit='s')
        
    print(f"Data berhasil dimuat. Total rows: {len(df_gps)}. Menyiapkan plot grafik...")
    plot_low_speed_maids(df_gps, max_threshold=20, step=0.5)
