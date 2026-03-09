# Laporan Analisis 1: Power-Law & Lévy Flight
## Data: GPS Mobilitas DIY (Oktober 2021 – Juni 2022)

### Tujuan
Mendiagnosis apakah distribusi jarak lompatan pengguna mengikuti pola Fat Tailed (Lévy Flight) atau Thin Tailed.

### Metodologi
- Menghitung jarak Haversine antar titik GPS berurutan per pengguna
- Filter noise (<0.1 km) dan teleportasi (>1000 km/jam)
- Regresi linear pada histogram log-log untuk estimasi eksponen α
- α < 1.0: SUPER FAT | 1.0 ≤ α ≤ 2.0: FAT TAILED | α > 2.0: Thin Tailed

### Hasil Per Bulan

| Bulan | Total Baris | Pergerakan Valid | Alpha (α) | R² | Diagnosis |
|-------|-------------|------------------|-----------|----|-----------|

### Hasil Keseluruhan


### Visualisasi
- Plot per bulan: `output_plots/per_bulan/{bulan}/`
- Plot keseluruhan: `output_plots/keseluruhan/`
- Perbandingan alpha: `output_plots/keseluruhan/perbandingan_alpha.png`

*Waktu eksekusi: 0.3 detik*
