# Laporan Analisis 9: Spatial Coverage Evolution
## Data: GPS Mobilitas DIY (Oktober 2021 - Juni 2022)

### Tujuan
Menganalisis evolusi cakupan spasial data GPS per bulan.

### Metodologi
- Grid resolution: 0.01 deg (~1 km)
- Total possible grid cells: 5,524
- DuckDB aggregasi grid untuk coverage dan spatial spread

### Hasil Per Bulan

| Bulan | Total Points | Grid Cells | Coverage % | Spread (km) |
|-------|-------------|------------|-----------|-------------|
| 2021_10_Oktober | 12,123,709 | 2,474 | 44.8% | 13.9 |
| 2021_11_November | 119,072,431 | 2,640 | 47.8% | 14.1 |
| 2021_12_Desember | 45,950,349 | 2,448 | 44.3% | 14.5 |
| 2022_01_Januari | 22,488,991 | 2,483 | 44.9% | 13.8 |
| 2022_02_Februari | 39,601,774 | 2,527 | 45.7% | 12.9 |
| 2022_03_Maret | 26,837,642 | 2,302 | 41.7% | 13.0 |
| 2022_04_April | 1,048,571 | 2,005 | 36.3% | 13.6 |
| 2022_05_Mei | 31,075,611 | 2,544 | 46.1% | 11.9 |
| 2022_06_Juni | 12,246,261 | 2,373 | 43.0% | 12.7 |

### Hasil Keseluruhan

- **Total data points**: 310,445,339
- **Coverage tertinggi**: 2021_11_November (47.8%)
- **Coverage terendah**: 2022_04_April (36.3%)
- **Rata-rata spread**: 13.4 km

### Interpretasi Hasil

- Coverage spasial bulanan relatif stabil pada kisaran **41% sampai 48%** untuk sebagian besar bulan, yang berarti hampir separuh grid potensial di DIY terisi aktivitas GPS pada bulan-bulan normal.
- **November 2021** memiliki coverage tertinggi, sedangkan **April 2022** turun jauh menjadi **36,3%**. Ini menandakan bulan April memiliki penyusutan cakupan spasial yang cukup nyata.
- Spatial spread berada di kisaran **11,9 sampai 14,5 km**, dengan nilai tertinggi pada **Desember 2021** dan terendah pada **Mei 2022**. Jadi, luas cakupan dan intensitas ekspansi ruang tidak selalu bergerak searah.
- Koordinat centroid bulanan sangat dekat satu sama lain, berada di sekitar **(-7.80, 110.37)**. Ini mengindikasikan pusat gravitasi mobilitas DIY relatif stabil, meskipun cakupan dan intensitas sebarannya berubah.
- Dalam konteks skripsi, analisis ini penting untuk menunjukkan bahwa perubahan mobilitas tidak selalu berarti pusat aktivitas berpindah drastis; sering kali yang berubah adalah luas jangkauan dan kepadatan sebaran di sekitar pusat yang sama.

### Kesimpulan

- Cakupan spasial mobilitas GPS di DIY cukup luas dan relatif stabil pada sebagian besar bulan, meskipun ada kontraksi yang jelas pada April 2022.
- Pusat gravitasi aktivitas bulanan cenderung tetap, tetapi tingkat penyebaran ruangnya berubah antarperiode.
- Analisis evolusi cakupan spasial ini melengkapi hotspot dan OD karena menjelaskan apakah perubahan mobilitas terjadi sebagai ekspansi wilayah, kontraksi wilayah, atau hanya redistribusi di pusat yang sama.

### Visualisasi
- Plot per bulan: `output_plots/{bulan}/`
- Small multiples: `output_plots/Keseluruhan/small_multiples.png`
- Coverage trend: `output_plots/Keseluruhan/coverage_trend.png`

*Waktu eksekusi: 14.2 detik*
