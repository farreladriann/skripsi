# Laporan Analisis 4: Origin-Destination Mobility Flow
## Data: GPS Mobilitas DIY (Oktober 2021 - Juni 2022)

### Tujuan
Menganalisis pola pergerakan origin-destination menggunakan grid zoning.

### Metodologi
- Grid 10x10 zona di wilayah DIY (DuckDB zone assignment)
- Origin = titik pertama per hari, Destination = titik terakhir
- Filter: min 3 data points per user per hari

### Hasil Per Bulan

| Bulan | Total Data | OD Pairs | Bergerak | %Bergerak | Median Jarak | Rute Terpopuler | Flow |
|-------|-----------|----------|----------|-----------|-------------|-----------------|------|
| 2021_10_Oktober | 12,123,709 | 343,616 | 27,010 | 7.9% | 7.00 km | 5_4->6_4 | 1504 |
| 2021_11_November | 119,072,431 | 2,248,164 | 180,740 | 8.0% | 7.31 km | 7_4->6_4 | 11825 |
| 2021_12_Desember | 45,950,349 | 2,295,635 | 195,484 | 8.5% | 10.20 km | 6_4->7_4 | 9793 |
| 2022_01_Januari | 22,488,991 | 1,251,368 | 119,882 | 9.6% | 8.94 km | 7_4->6_4 | 7353 |
| 2022_02_Februari | 39,601,774 | 1,289,559 | 135,196 | 10.5% | 9.15 km | 7_4->6_4 | 9950 |
| 2022_03_Maret | 26,837,642 | 604,847 | 51,589 | 8.5% | 9.82 km | 7_4->6_4 | 7433 |
| 2022_04_April | 1,048,571 | 76,814 | 11,773 | 15.3% | 9.70 km | 7_4->6_4 | 1219 |
| 2022_05_Mei | 31,075,611 | 1,263,814 | 125,232 | 9.9% | 9.82 km | 7_4->6_4 | 9318 |
| 2022_06_Juni | 12,246,261 | 400,876 | 39,227 | 9.8% | 9.04 km | 6_4->7_4 | 3230 |

### Hasil Keseluruhan

- **Total OD trips (9 bulan)**: 886,133
- **Rata-rata median jarak**: 9.00 km
- **Rute terpopuler keseluruhan**: 7_4->6_4 (61128 trips)

### Interpretasi Hasil

- Dari seluruh pasangan origin-destination harian, proporsi yang benar-benar berpindah zona hanya sekitar **7,9% sampai 15,3%**. Ini berarti mayoritas user-day tetap memulai dan mengakhiri aktivitas di zona yang sama.
- Median jarak OD relatif stabil pada kisaran **7,00 sampai 10,20 km**, sehingga ketika perpindahan antarzona terjadi, skalanya cenderung menengah dan cukup konsisten antarbulan.
- Rute **7_4->6_4** dan kebalikannya **6_4->7_4** mendominasi banyak bulan. Ini menandakan ada koridor mobilitas utama yang berulang, kemungkinan menghubungkan dua zona aktivitas inti.
- **April 2022** memiliki persentase bergerak tertinggi (**15,3%**), tetapi ukuran datanya juga paling kecil. Karena itu, bulan ini layak dibaca sebagai sinyal perubahan, bukan langsung dianggap pola dominan jangka panjang.
- Dalam konteks skripsi, analisis OD menunjukkan bahwa mobilitas harian masyarakat DIY bersifat selektif: tidak semua orang berpindah jauh setiap hari, tetapi ada arus tertentu yang berulang dan membentuk tulang punggung pergerakan wilayah.

### Kesimpulan

- Pola OD DIY didominasi perjalanan harian yang berawal dan berakhir dalam zona yang sama, dengan hanya sebagian kecil perjalanan yang benar-benar berpindah zona.
- Ketika perpindahan terjadi, jaraknya cenderung berada pada skala menengah sekitar 9 km.
- Adanya rute yang sangat konsisten antarbulan menunjukkan keberadaan koridor mobilitas utama yang layak dibahas lebih lanjut dalam narasi spasial skripsi.

### Visualisasi
- Plot per bulan: `output_plots/{bulan}/`
- Plot keseluruhan: `output_plots/Keseluruhan/`

*Waktu eksekusi: 65.1 detik*
