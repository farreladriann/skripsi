# Laporan Analisis 2: Temporal Activity Pattern
## Data: GPS Mobilitas DIY (Oktober 2021 - Juni 2022)

### Tujuan
Menganalisis pola aktivitas temporal pengguna GPS: distribusi per jam, per hari, weekday vs weekend.

### Metodologi
- Konversi timestamp Unix ke WIB (UTC+7) via DuckDB
- Heatmap jam x hari, line chart per jam, bar chart per hari, time series harian
- Analisis per bulan dan perbandingan keseluruhan

### Hasil Per Bulan

| Bulan | Total Data | Users Unik | Peak Hour | Avg Weekday | Avg Weekend | Rasio WD/WE |
|-------|-----------|------------|-----------|-------------|-------------|-------------|
| 2021_10_Oktober | 12,123,709 | 398,142 | 19:00 | 976,323 | 3,621,046 | 0.27x |
| 2021_11_November | 119,072,431 | 1,226,198 | 19:00 | 17,269,406 | 16,362,700 | 1.06x |
| 2021_12_Desember | 45,950,349 | 1,288,665 | 20:00 | 6,835,038 | 5,887,580 | 1.16x |
| 2022_01_Januari | 22,488,993 | 924,855 | 20:00 | 3,168,863 | 3,322,338 | 0.95x |
| 2022_02_Februari | 39,601,777 | 956,296 | 23:00 | 5,560,533 | 5,899,556 | 0.94x |
| 2022_03_Maret | 26,837,642 | 457,977 | 08:00 | 3,872,108 | 3,738,552 | 1.04x |
| 2022_04_April | 1,048,571 | 121,764 | 19:00 | 150,681 | 147,582 | 1.02x |
| 2022_05_Mei | 31,075,618 | 1,271,675 | 18:00 | 4,400,930 | 4,535,485 | 0.97x |
| 2022_06_Juni | 12,246,261 | 403,758 | 20:00 | 1,683,504 | 1,914,370 | 0.88x |

### Hasil Keseluruhan

- **Total data points**: 310,445,351
- **Peak hour paling umum**: 19:00 WIB
- **Rata-rata rasio weekday/weekend**: 0.92x

### Interpretasi Hasil

- Jam puncak paling sering berada pada **19:00-20:00 WIB**, sehingga aktivitas GPS cenderung memuncak pada periode sore hingga malam. Ini konsisten dengan mobilitas pulang, aktivitas malam, atau penggunaan perangkat yang tinggi di luar jam kerja inti.
- Ada deviasi yang menarik pada **Februari 2022 (23:00)** dan **Maret 2022 (08:00)**. Februari menunjukkan pergeseran puncak sangat malam, sedangkan Maret menunjukkan dominasi pagi hari yang jauh lebih kuat daripada bulan lain.
- Secara umum rasio weekday/weekend mendekati 1.0, tetapi rata-rata keseluruhan **0.92x** menunjukkan aktivitas akhir pekan sedikit lebih tinggi daripada hari kerja. Ini berarti pola mobilitas tidak sepenuhnya berorientasi komuter kerja formal.
- **Oktober 2021** memiliki rasio yang sangat rendah (**0.27x**) karena data hanya mencakup 10 hari, sehingga hasil bulan ini perlu dibaca dengan lebih hati-hati dibanding bulan lain.
- Dalam konteks skripsi, analisis temporal ini memperlihatkan bahwa struktur mobilitas tidak homogen sepanjang waktu. Ada ritme harian dan mingguan yang dapat dipakai untuk membaca kapan sistem perkotaan paling aktif.

### Kesimpulan

- Mobilitas GPS di DIY menunjukkan ritme temporal yang jelas, dengan dominasi aktivitas pada sore hingga malam hari.
- Perbedaan weekday dan weekend tidak terlalu tajam, yang mengindikasikan bahwa aktivitas masyarakat tersebar cukup merata antara hari kerja dan akhir pekan.
- Variasi jam puncak antarbulan menandakan adanya dinamika temporal yang penting untuk dibaca bersama analisis spasial, bukan hanya sebagai statistik pelengkap.

### Visualisasi
- Plot per bulan: `output_plots/{bulan}/`
- Perbandingan keseluruhan: `output_plots/Keseluruhan/`

*Waktu eksekusi: 151.0 detik*
