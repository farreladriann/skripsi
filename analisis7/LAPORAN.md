# Laporan Analisis 7: Monthly Trend Analysis
## Data: GPS Mobilitas DIY (Oktober 2021 - Juni 2022)

### Tujuan
Menganalisis tren aktivitas GPS secara bulanan.

### Metodologi
- DuckDB aggregasi per hari dan per jam
- Per bulan: daily trend + hourly distribution
- Keseluruhan: perbandingan tren antar bulan

### Hasil Per Bulan

| Bulan | Total Points | Users Unik | Peak Hour | Avg Daily Points | Avg Daily Users | Hari Data |
|-------|-------------|------------|-----------|-----------------|-----------------|----------|
| 2021_10_Oktober | 12,123,709 | 398,142 | 19:00 | 1,212,371 | 68,031 | 10 |
| 2021_11_November | 119,072,431 | 1,226,198 | 19:00 | 3,841,046 | 120,502 | 31 |
| 2021_12_Desember | 45,950,349 | 1,288,665 | 20:00 | 1,435,948 | 130,690 | 32 |
| 2022_01_Januari | 22,488,993 | 924,855 | 20:00 | 702,781 | 86,804 | 32 |
| 2022_02_Februari | 39,601,777 | 956,296 | 23:00 | 1,365,579 | 82,161 | 29 |
| 2022_03_Maret | 26,837,642 | 457,977 | 08:00 | 838,676 | 30,767 | 32 |
| 2022_04_April | 1,048,571 | 121,764 | 19:00 | 33,825 | 7,481 | 31 |
| 2022_05_Mei | 31,075,618 | 1,271,675 | 18:00 | 971,113 | 83,442 | 32 |
| 2022_06_Juni | 12,246,261 | 403,758 | 20:00 | 1,530,783 | 85,132 | 8 |

### Hasil Keseluruhan

- **Total data points**: 310,445,351
- **Bulan terbanyak**: 2021_11_November (119,072,431)
- **Bulan tersedikit**: 2022_04_April (1,048,571)
- **Rata-rata users/bulan**: 783,259

### Interpretasi Hasil

- Volume data bulanan sangat tidak seragam. **November 2021** menjadi bulan paling padat, sedangkan **April 2022** paling rendah. Ini berarti perbandingan antarb­ulan perlu selalu dibaca bersama konteks ukuran data.
- **Oktober 2021** hanya memiliki **10 hari data**, dan **Juni 2022** hanya **8 hari data**, sehingga rata-rata harian kedua bulan ini tidak sepenuhnya sebanding dengan bulan penuh.
- Jam puncak kembali menegaskan dominasi sore-malam pada banyak bulan, tetapi ada anomali menarik pada **Maret 2022 (08:00)** dan **Mei 2022 (18:00)**. Ini menandakan ritme harian bulanan memang dapat berubah.
- Rata-rata user harian tertinggi muncul pada **Desember 2021**, sedangkan rata-rata point harian tertinggi sangat dipengaruhi oleh **November 2021**. Dengan kata lain, bulan dengan data point paling banyak tidak selalu identik dengan intensitas aktivitas pengguna per hari yang paling merata.
- Dalam konteks skripsi, analisis tren bulanan ini penting untuk membedakan perubahan yang berasal dari volume data, jumlah pengguna, dan ritme waktu, sehingga pembacaan hasil analisis lain tidak terlepas dari konteks temporal bulanan.

### Kesimpulan

- Aktivitas GPS di DIY berfluktuasi cukup besar antarbulan, baik dari sisi total titik data maupun jumlah pengguna unik.
- Puncak aktivitas umumnya terjadi pada sore hingga malam, tetapi beberapa bulan menunjukkan pergeseran ritme yang cukup jelas.
- Analisis tren bulanan berfungsi sebagai konteks dasar untuk membaca apakah perubahan pada analisis spasial dan mobilitas lain berasal dari perilaku pengguna atau dari perbedaan intensitas data.

### Visualisasi
- Plot per bulan: `output_plots/{bulan}/`
- Plot keseluruhan: `output_plots/Keseluruhan/`

*Waktu eksekusi: 75.5 detik*
