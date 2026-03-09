# Laporan Analisis 3: Spatial Hotspot & Density Clustering
## Data: GPS Mobilitas DIY (Oktober 2021 - Juni 2022)

### Tujuan
Mengidentifikasi lokasi-lokasi hotspot aktivitas GPS menggunakan grid-based clustering.

### Metodologi
- Grid resolution: 0.005 deg (~500m)
- Hotspot = grid cells dengan density di atas persentil 95
- DuckDB aggregasi grid + scatter density map + top 10 bar chart

### Hasil Per Bulan

| Bulan | Total Data | Grid Cells | Hotspots | Lokasi Terpadat | Count |
|-------|-----------|------------|----------|-----------------|-------|
| 2021_10_Oktober | 12,123,709 | 7,717 | 386 | (-7.805, 110.365) | 172,801.0 |
| 2021_11_November | 119,072,431 | 9,243 | 463 | (-7.805, 110.365) | 2,376,970.0 |
| 2021_12_Desember | 45,950,349 | 7,909 | 396 | (-7.700, 110.300) | 2,593,947.0 |
| 2022_01_Januari | 22,488,991 | 8,149 | 408 | (-7.805, 110.365) | 603,068.0 |
| 2022_02_Februari | 39,601,774 | 8,434 | 422 | (-7.805, 110.365) | 1,364,295.0 |
| 2022_03_Maret | 26,837,642 | 6,889 | 345 | (-7.805, 110.365) | 3,562,421.0 |
| 2022_04_April | 1,048,571 | 5,576 | 279 | (-7.805, 110.365) | 91,379.0 |
| 2022_05_Mei | 31,075,611 | 8,554 | 428 | (-7.770, 110.410) | 4,490,955.0 |
| 2022_06_Juni | 12,246,261 | 7,486 | 375 | (-7.805, 110.365) | 1,295,760.0 |

### Hasil Keseluruhan

- **Total data points (9 bulan)**: 310,445,339
- **Lokasi terpadat**: (-7.805, 110.365) - 11,783,334.0 points
- **Total grid cells terisi**: 9,969

### Interpretasi Hasil

- Jumlah grid terisi per bulan berada pada rentang **5.576 sampai 9.243** sel, yang menunjukkan cakupan spasial cukup luas tetapi tetap memiliki konsentrasi kuat pada simpul-simpul tertentu.
- Hotspot bulanan berkisar **279 sampai 463** sel. Artinya, hanya sebagian kecil grid yang benar-benar menjadi pusat intensitas tinggi.
- Koordinat **(-7.805, 110.365)** muncul sebagai lokasi terpadat pada sebagian besar bulan. Ini mengindikasikan adanya pusat aktivitas yang sangat stabil dan dominan secara konsisten.
- Ada pengecualian penting pada **Desember 2021** dengan hotspot utama **(-7.700, 110.300)** dan **Mei 2022** dengan hotspot utama **(-7.770, 110.410)**. Pergeseran ini menunjukkan bahwa struktur ruang mobilitas tidak sepenuhnya statis.
- **Maret 2022** dan **Mei 2022** menunjukkan count hotspot tertinggi pada lokasi puncak, yang berarti konsentrasi aktivitas pada titik tertentu sangat kuat pada dua bulan tersebut.
- Dalam konteks skripsi, analisis ini memperlihatkan bahwa pergerakan masyarakat tidak tersebar merata di DIY, melainkan tertarik ke koridor dan simpul aktivitas tertentu yang berulang dari waktu ke waktu.

### Kesimpulan

- Struktur mobilitas GPS di DIY membentuk hotspot yang jelas dan berulang, dengan satu inti utama yang muncul sangat konsisten pada banyak bulan.
- Meskipun ada inti yang stabil, beberapa bulan memperlihatkan perpindahan hotspot utama, menandakan adanya dinamika spasial musiman atau kontekstual.
- Analisis hotspot ini penting karena memberi bukti bahwa distribusi aktivitas mobilitas bersifat terkonsentrasi dan dapat dipetakan secara eksplisit.

### Visualisasi
- Plot per bulan: `output_plots/{bulan}/`
- Plot keseluruhan: `output_plots/Keseluruhan/`

*Waktu eksekusi: 29.7 detik*
