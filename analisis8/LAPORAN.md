# Laporan Analisis 8: Monthly Mobility Comparison
## Data: GPS Mobilitas DIY (Oktober 2021 - Juni 2022)

### Tujuan
Membandingkan metrik mobilitas (jarak, kecepatan, Rg) antar bulan.

### Metodologi
- Jarak: Haversine via DuckDB window functions (filter 0.05-200 km, speed <200 km/h)
- Kecepatan: jarak/waktu
- Rg: radius of gyration per user (min 5 data points)

### Hasil Per Bulan

| Bulan | Data Points | Users | Moves | Med Dist (km) | Med Speed (km/h) | Med Rg (km) |
|-------|-----------|-------|-------|---------------|-----------------|-------------|
| 2021_10_Oktober | 12,123,709 | 398,142 | 396,864 | 0.94 | 0.9 | 1.05 |
| 2021_11_November | 119,072,431 | 1,226,198 | 2,940,428 | 1.56 | 0.4 | 1.47 |
| 2021_12_Desember | 45,950,349 | 1,288,665 | 2,933,730 | 1.69 | 0.4 | 1.77 |
| 2022_01_Januari | 22,488,991 | 924,855 | 2,728,441 | 0.81 | 1.1 | 1.71 |
| 2022_02_Februari | 39,601,774 | 956,296 | 3,797,990 | 0.52 | 8.7 | 1.47 |
| 2022_03_Maret | 26,837,642 | 457,977 | 584,732 | 1.87 | 1.4 | 0.13 |
| 2022_04_April | 1,048,571 | 121,764 | 124,315 | 1.99 | 0.8 | 1.65 |
| 2022_05_Mei | 31,075,611 | 1,271,674 | 2,956,957 | 0.74 | 5.6 | 1.68 |
| 2022_06_Juni | 12,246,261 | 403,758 | 966,707 | 0.61 | 7.3 | 1.14 |

### Hasil Keseluruhan

- **Rata-rata median jarak**: 1.19 km
- **Rata-rata median kecepatan**: 2.9 km/h
- **Rata-rata median Rg**: 1.34 km

### Interpretasi Hasil

- Median jarak perpindahan antarbulan berada pada skala pendek, dengan rata-rata **1,19 km**. Ini menguatkan temuan bahwa sebagian besar pergerakan harian bersifat lokal.
- **April 2022** dan **Maret 2022** memiliki median jarak tertinggi, sedangkan **Februari 2022**, **Mei 2022**, dan **Juni 2022** menunjukkan median jarak yang lebih pendek.
- Median kecepatan menunjukkan variasi yang tajam, terutama **Februari 2022 (8,7 km/h)** dan **Juni 2022 (7,3 km/h)**. Nilai ini bisa mengindikasikan perpindahan yang lebih efisien atau efek interval waktu perekaman yang berbeda, sehingga interpretasinya perlu hati-hati.
- Median Rg bulanan umumnya berada di sekitar **1-2 km**, tetapi **Maret 2022** turun drastis ke **0,13 km**. Ini konsisten dengan indikasi mobilitas yang sangat terlokalisasi pada bulan tersebut.
- Selisih antara mean dan median pada jarak maupun kecepatan menunjukkan distribusi yang tidak simetris: mayoritas pergerakan pendek, namun ada sebagian kecil pergerakan yang jauh lebih besar dan cepat.
- Dalam konteks skripsi, analisis ini penting karena mempertemukan tiga dimensi mobilitas sekaligus: perpindahan antar titik, kecepatan, dan ruang gerak individu.

### Kesimpulan

- Mobilitas bulanan di DIY secara umum tetap bertumpu pada perpindahan jarak pendek, walaupun terdapat variasi intensitas dan efisiensi perpindahan antarbulan.
- Beberapa bulan memperlihatkan anomali yang kuat, terutama Maret 2022 untuk Rg yang sangat kecil dan Februari 2022 untuk median kecepatan yang tinggi.
- Perbandingan metrik mobilitas ini memberi gambaran komprehensif tentang perubahan perilaku gerak masyarakat dari waktu ke waktu.

### Visualisasi
- Plot per bulan: `output_plots/{bulan}/`
- Dashboard keseluruhan: `output_plots/Keseluruhan/dashboard_mobilitas.png`

*Waktu eksekusi: 93.2 detik*
