# Laporan Analisis 5: Demographic-Mobility Correlation
## Data: GPS + PeopleGraph DIY (Oktober 2021 - Juni 2022)

### Tujuan
Mengkorelasikan data demografi (gender, income, lokasi) dengan pola mobilitas.

### Metodologi
- Hitung mobility radius per user via DuckDB (std koordinat x 111 km)
- Join GPS metrics dengan PeopleGraph (gender, income, kabupaten)
- Boxplot per kategori demografi per bulan dan keseluruhan

### Hasil Per Bulan

| Bulan | Users GPS | Matched | Median Radius (km) | Mean Radius (km) |
|-------|-----------|---------|--------------------|------------------|
| 2021_10_Oktober | 398,142 | 66,213 | 0.15 | 1.45 |
| 2021_11_November | 1,226,198 | 221,390 | 1.06 | 2.36 |
| 2021_12_Desember | 1,288,665 | 233,854 | 1.49 | 2.88 |
| 2022_01_Januari | 924,855 | 171,534 | 1.17 | 2.52 |
| 2022_02_Februari | 956,296 | 175,154 | 0.73 | 2.17 |
| 2022_03_Maret | 457,977 | 66,440 | 0.00 | 1.37 |
| 2022_04_April | 121,764 | 6,932 | 0.09 | 1.92 |
| 2022_05_Mei | 1,271,675 | 165,924 | 0.00 | 1.89 |
| 2022_06_Juni | 403,758 | 72,058 | 0.19 | 1.64 |

### Gender Analysis

| Bulan | Male (n) | Male Median | Female (n) | Female Median |
|-------|----------|-------------|------------|---------------|
| 2021_10_Oktober | 33,670 | 0.23 km | 7,899 | 0.09 km |
| 2021_11_November | 105,482 | 1.15 km | 25,845 | 0.98 km |
| 2021_12_Desember | 109,031 | 1.64 km | 28,627 | 1.50 km |
| 2022_01_Januari | 80,525 | 1.32 km | 18,970 | 1.04 km |
| 2022_02_Februari | 72,569 | 0.93 km | 19,110 | 0.41 km |
| 2022_03_Maret | 19,850 | 0.00 km | 8,626 | 0.00 km |
| 2022_04_April | 2,239 | 0.00 km | 799 | 0.00 km |
| 2022_05_Mei | 66,950 | 0.00 km | 16,069 | 0.00 km |
| 2022_06_Juni | 29,786 | 0.18 km | 7,791 | 0.06 km |

### Hasil Keseluruhan

- **Total matched users**: 1,179,499
- **Rata-rata median radius**: 0.54 km

### Interpretasi Hasil

- Hanya sebagian dari user GPS yang berhasil dipadankan dengan PeopleGraph, sehingga hasil ini harus dibaca sebagai gambaran pada **subset user yang matched**, bukan seluruh populasi GPS.
- Median radius mobilitas matched users cenderung rendah, bahkan **0,00 km** pada **Maret 2022** dan **Mei 2022**. Ini mengindikasikan banyak user pada subset tersebut sangat terkonsentrasi pada satu area dominan.
- Pada bulan-bulan dengan median radius lebih besar, seperti **Desember 2021 (1,49 km)** dan **Januari 2022 (1,17 km)**, terlihat adanya ekspansi mobilitas yang lebih luas pada user yang teridentifikasi secara demografis.
- Median radius pengguna **male** umumnya lebih tinggi daripada **female** pada bulan-bulan ketika keduanya memiliki jumlah sampel memadai. Namun, selisih ini perlu dibaca hati-hati karena distribusi sampel gender tidak seimbang.
- Nilai mean radius yang jauh di atas median menunjukkan distribusi mobilitas demografis bersifat miring ke kanan: sebagian besar user relatif lokal, tetapi ada sebagian kecil user dengan radius jauh lebih besar.
- Untuk konteks skripsi, analisis ini berguna sebagai penghubung antara perilaku mobilitas dan atribut sosial, meskipun kekuatan kesimpulannya tetap bergantung pada kualitas dan representativitas data join demografis.

### Kesimpulan

- Mobilitas pada subset user yang berhasil dicocokkan dengan PeopleGraph cenderung lokal, dengan radius median yang relatif kecil.
- Ada indikasi perbedaan mobilitas menurut gender, tetapi hasil ini lebih tepat dibaca sebagai kecenderungan awal daripada kesimpulan final yang mutlak.
- Analisis demografi-mobilitas memperkaya skripsi karena membuka jalur interpretasi sosial atas pola spatiotemporal yang teramati pada data GPS.

### Visualisasi
- Plot per bulan: `output_plots/{bulan}/`
- Plot keseluruhan: `output_plots/Keseluruhan/`

*Waktu eksekusi: 15.0 detik*
