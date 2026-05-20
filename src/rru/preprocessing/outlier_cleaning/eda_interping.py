import polars as pl
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from pathlib import Path

# Tambahkan direktori root ke sys.path agar rru import berfungsi jika dijalankan langsung
from src.rru.utils import calculate_inter_ping_metrics

def plot_interping_eda(df: pl.DataFrame, save_path: str = None):
    """
    Menghasilkan 4 grafik EDA terbaik untuk analisis inter-ping pergerakan GPS.
    """
    print("Mempersiapkan visualisasi EDA Inter-ping...")
    
    # 1. Filter baris dengan valid inter-ping (bukan baris pertama dari trip MAID)
    valid_df = df.filter(pl.col("dt_seconds").is_not_null())
    
    # Konversi ke NumPy array untuk eksekusi plotting matplotlib yang cepat
    dt = valid_df["dt_seconds"].to_numpy()
    dist = valid_df["dist_meters"].to_numpy()
    speed = valid_df["speed_kmh"].to_numpy()

    # Setup layout kanvas
    sns.set_theme(style="whitegrid")
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    
    # --- PLOT 1: Waktu Antar Ping (Time Gap) ---
    ax = axes[0, 0]
    dt_safe = np.clip(dt, 1, None) # Hindari log(0)
    bins_dt = np.logspace(0, np.log10(dt_safe.max() + 1), 60)
    ax.hist(dt_safe, bins=bins_dt, color='#3498db', edgecolor='black')
    ax.set_xscale('log')
    ax.set_yscale('log') # Log Y agar frekuensi tinggi tidak menutup yang rendah
    ax.set_title("1. Distribusi Waktu Antar-Ping (dt_seconds)", fontsize=14, fontweight='bold')
    ax.set_xlabel("Waktu (Detik) - Log Scale")
    ax.set_ylabel("Frekuensi (Log Scale)")

    # --- PLOT 2: Jarak Antar Ping (Distance Gap) ---
    ax = axes[0, 1]
    dist_safe = np.clip(dist, 0.1, None) # Hindari log(0)
    bins_dist = np.logspace(-1, np.log10(dist_safe.max() + 1), 60)
    ax.hist(dist_safe, bins=bins_dist, color='#2ecc71', edgecolor='black')
    ax.set_xscale('log')
    ax.set_yscale('log')
    ax.set_title("2. Distribusi Jarak Antar-Ping (dist_meters)", fontsize=14, fontweight='bold')
    ax.set_xlabel("Jarak (Meter) - Log Scale")
    ax.set_ylabel("Frekuensi (Log Scale)")

    # --- PLOT 3: Distribusi Kecepatan (Speeding Profiling) ---
    ax = axes[1, 0]
    # Kita clip di 200 km/h agar fokus ke variasi kecepatan lalu lintas & anomali normal
    speed_clip = np.clip(speed, 0, 200) 
    ax.hist(speed_clip, bins=50, color='#e74c3c', edgecolor='black')
    ax.set_title("3. Profil Kecepatan Kendaraan (speed_kmh)", fontsize=14, fontweight='bold')
    ax.set_xlabel("Kecepatan (km/h) - Dibatasi max 200 km/h di plot")
    ax.set_ylabel("Frekuensi")
    
    # Tambahkan garis vertikal statistik (Median, 90th percentile)
    ax.axvline(np.nanmedian(speed), color='blue', linestyle='dashed', linewidth=2, label=f'Median: {np.nanmedian(speed):.1f} km/h')
    ax.axvline(np.nanpercentile(speed, 90), color='k', linestyle='dashed', linewidth=2, label=f'P90: {np.nanpercentile(speed, 90):.1f} km/h')
    ax.legend()

    # --- PLOT 4: Hexbin Waktu vs Jarak (Korelasi) ---
    ax = axes[1, 1]
    # Filter data-data rasional: max waktu 2 jam, max jarak 15 km
    mask = (dt_safe > 0) & (dist_safe > 0) & (dt_safe < 7200) & (dist_safe < 15000)
    hb = ax.hexbin(
        dt_safe[mask], dist_safe[mask], 
        gridsize=45, cmap='magma', mincnt=1, xscale='log', bins='log'
    )
    ax.set_title("4. Hubungan Selisih Waktu & Jarak Tempuh", fontsize=14, fontweight='bold')
    ax.set_xlabel("Waktu (Detik) - Log Scale")
    ax.set_ylabel("Jarak (Meter)")
    cb = fig.colorbar(hb, ax=ax)
    cb.set_label('Log10(Count)')

    # Styling akhir
    plt.tight_layout()
    if save_path:
        # Buat foldernya kalau belum ada
        Path(save_path).parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"Visualisasi disimpan di: {save_path}")
    
    plt.show()

if __name__ == "__main__":
    # Path dapat disesuaikan dengan file output dari proses bilocation
    INPUT_PATH = Path("data/processed/gps_rru_cleaned_lowspeed.parquet") # <<< SESUAIKAN JIKA PERLU
    OUTPUT_IMG = Path("results/eda_interping_dashboard.png")
    
    if INPUT_PATH.exists():
        print(f"Membaca data: {INPUT_PATH}")
        # Lazily load and limit for very massive datasets if needed, or eager
        df_bilocation = pl.read_parquet(INPUT_PATH)
        
        # Hitung metrik inter-ping. Jika sudah dihitung di proses sebelumnya, tahap ini bisa diskip.
        print("Menghitung dt, dist, dan speed...")
        df_metrics = calculate_inter_ping_metrics(df_bilocation)
        
        plot_interping_eda(df_metrics, save_path=OUTPUT_IMG)
    else:
        print(f"File {INPUT_PATH} tidak ditemukan! Pastikan jalur merujuk ke data berformat parquet yang sesuai.")