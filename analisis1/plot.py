import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# GANTI NAMA FILE DENGAN YANG ANDA PUNYA
# Gunakan file Oktober yang tadi error
filename = './Data GPS/2022April/April2022.csv'

print(f"--- MEMULAI ANALISIS SEDERHANA: {filename} ---")

# 1. LOAD DATA
# Kita batasi 1 juta baris dulu biar cepat untuk testing. 
# Hapus parameter 'nrows=1000000' jika ingin load semua (bisa makan RAM besar).
df = pd.read_csv(filename, nrows=1000000)

print(f"Data dimuat. Jumlah baris sampel: {len(df):,}")

# 2. FIX TIMESTAMP (BAGIAN KRUSIAL)
print("Memperbaiki format timestamp...")
# Paksa jadi angka. Yang error jadi NaT/NaN
df['timestamp'] = pd.to_numeric(df['timestamp'], errors='coerce')

# Buang baris yang timestamp-nya rusak
df = df.dropna(subset=['timestamp'])

# Konversi ke datetime
df['datetime'] = pd.to_datetime(df['timestamp'], unit='s')
print("Timestamp berhasil diperbaiki.")

# 3. FIX KOORDINAT
# Paksa latitude/longitude jadi angka (jaga-jaga ada header nyasar)
df['latitude'] = pd.to_numeric(df['latitude'], errors='coerce')
df['longitude'] = pd.to_numeric(df['longitude'], errors='coerce')
df = df.dropna(subset=['latitude', 'longitude'])

# 4. STATISTIK DASAR
print("\n--- STATISTIK DATA ---")
print(f"Total User Unik (MAID) : {df['maid'].nunique():,}")
print(f"Awal Data              : {df['datetime'].min()}")
print(f"Akhir Data             : {df['datetime'].max()}")
print(f"Durasi                 : {df['datetime'].max() - df['datetime'].min()}")

print("\n--- RENTANG LOKASI (BOUNDING BOX) ---")
print(f"Latitude  : {df['latitude'].min()} s/d {df['latitude'].max()}")
print(f"Longitude : {df['longitude'].min()} s/d {df['longitude'].max()}")

# 5. VISUALISASI PETA (SCATTER PLOT)
print("\nMembuat plot peta...")
plt.figure(figsize=(10, 8))

# Plot titik-titik (gunakan s=0.1 agar titiknya kecil dan terlihat seperti peta)
plt.scatter(df['longitude'], df['latitude'], s=0.1, alpha=0.5, c='blue')

plt.title(f"Visualisasi Sebaran Data GPS (Sampel {len(df):,} titik)")
plt.xlabel("Longitude")
plt.ylabel("Latitude")
plt.grid(True, alpha=0.3)

# Fokuskan tampilan ke area Jogja (opsional, sesuaikan jika perlu)
# Batas kasar DIY: Lat -8.2 s/d -7.5, Long 110.0 s/d 110.8
plt.xlim(110.0, 110.9)
plt.ylim(-8.25, -7.5)

plt.show()

print("Selesai.")