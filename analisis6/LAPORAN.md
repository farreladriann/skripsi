# Laporan Analisis 6: Radius of Gyration & Home Detection
## Data: GPS Mobilitas DIY (Oktober 2021 - Juni 2022)

### Tujuan
Menghitung Radius of Gyration (Rg) dan mendeteksi lokasi rumah pengguna.

### Metodologi
- Rg = sqrt(mean((ri - r_cm)^2)) dalam km (DuckDB variance aggregation)
- Min 10 data points per user
- Home detection: jam malam (20:00-06:00 WIB), min 3 kunjungan
- Kategori: Statis (<0.5), Lokal (0.5-2), Kota (2-5), Regional (5-10), Jauh (>10)

### Hasil Per Bulan

| Bulan | Users Rg | Median Rg | Mean Rg | Rumah Terdeteksi |
|-------|----------|-----------|---------|------------------|
| 2021_10_Oktober | 103,793 | 1.092 km | 1.787 km | 129,620 |
| 2021_11_November | 500,251 | 1.550 km | 2.530 km | 544,179 |
| 2021_12_Desember | 432,413 | 2.056 km | 3.288 km | 579,834 |
| 2022_01_Januari | 254,635 | 1.871 km | 3.052 km | 355,561 |
| 2022_02_Februari | 278,532 | 1.637 km | 2.673 km | 350,274 |
| 2022_03_Maret | 150,430 | 0.416 km | 1.721 km | 110,005 |
| 2022_04_April | 11,400 | 1.806 km | 2.566 km | 17,502 |
| 2022_05_Mei | 286,629 | 1.675 km | 2.822 km | 428,116 |
| 2022_06_Juni | 129,922 | 1.235 km | 2.015 km | 157,973 |

### Kategorisasi Per Bulan

| Bulan | Statis (<0.5) | Lokal (0.5-2) | Kota (2-5) | Regional (5-10) | Jauh (>10) |
|-------|---|---|---|---|---|
| 2021_10_Oktober | 24,381 | 40,380 | 17,580 | 5,740 | 2,762 |
| 2021_11_November | 100,485 | 161,311 | 120,413 | 48,938 | 23,437 |
| 2021_12_Desember | 58,937 | 129,531 | 131,711 | 61,536 | 28,125 |
| 2022_01_Januari | 33,641 | 87,401 | 72,862 | 31,969 | 14,909 |
| 2022_02_Februari | 56,737 | 93,686 | 66,795 | 29,170 | 14,241 |
| 2022_03_Maret | 52,520 | 33,818 | 29,018 | 8,428 | 3,323 |
| 2022_04_April | 2,109 | 3,644 | 3,134 | 968 | 384 |
| 2022_05_Mei | 26,121 | 150,673 | 55,715 | 26,830 | 14,173 |
| 2022_06_Juni | 28,893 | 45,020 | 25,608 | 8,159 | 4,434 |

### Hasil Keseluruhan

- **Total users dianalisis**: 2,148,005
- **Median Rg keseluruhan**: 1.675 km
- **Total rumah terdeteksi**: 2,673,064

### Interpretasi Hasil

- Median Radius of Gyration keseluruhan sebesar **1,675 km** menunjukkan mobilitas tipikal pengguna berada pada skala lokal, bukan mobilitas jarak jauh.
- **Desember 2021** memiliki median Rg tertinggi (**2,056 km**), sedangkan **Maret 2022** terendah (**0,416 km**). Perubahan ini menunjukkan intensitas eksplorasi ruang tidak konstan antarbulan.
- Kategori **Lokal (0,5-2 km)** mendominasi banyak bulan, yang berarti sebagian besar pengguna beraktivitas dalam jangkauan spasial yang relatif terbatas di sekitar pusat aktivitasnya.
- Porsi kategori **Kota (2-5 km)** dan **Regional (5-10 km)** tetap cukup besar pada beberapa bulan seperti November, Desember, Januari, dan Februari, menandakan adanya kelompok pengguna yang jauh lebih mobile.
- Jumlah rumah terdeteksi cukup besar di semua bulan. Ini menunjukkan data malam hari cukup kuat untuk mengestimasi lokasi rumah, sehingga analisis berikutnya seperti commuting atau regularitas memiliki basis spasial yang lebih masuk akal.
- Dalam konteks skripsi, Rg sangat penting karena memberikan ukuran kompak tentang luas ruang aktivitas individu, sedangkan home detection memberi jangkar spasial untuk membaca pola mobilitas lebih lanjut.

### Kesimpulan

- Mobilitas pengguna GPS di DIY secara umum bersifat lokal, dengan median ruang gerak sekitar 1 sampai 2 km.
- Terdapat variasi antarb­ulan yang cukup nyata, sehingga ruang gerak masyarakat berubah menurut konteks waktu, bukan konstan sepanjang periode observasi.
- Radius of Gyration dan home detection menjadi fondasi kuat untuk menjelaskan intensitas mobilitas individu secara lebih interpretatif dalam skripsi.

### Visualisasi
- Plot per bulan: `output_plots/{bulan}/`
- Plot keseluruhan: `output_plots/Keseluruhan/`

*Waktu eksekusi: 87.4 detik*
