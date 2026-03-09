# Laporan Analisis 10: Mobility Regularity & Spatial Entropy
## Data: GPS Mobilitas DIY (Oktober 2021 - Juni 2022)

### Tujuan
Mengukur seberapa rutin atau eksploratif perilaku mobilitas pengguna dari distribusi kunjungan spasial pada grid lokasi.

### Metodologi
- Grid spasial: 0.01 derajat (sekitar 1 km)
- Minimal 20 titik GPS per user agar pola mobilitas cukup stabil
- Entropy spasial dihitung dari proporsi kunjungan user ke setiap grid
- Normalized entropy = entropy / ln(jumlah lokasi unik), bernilai 0 sampai 1
- User rutin: normalized entropy < 0.35
- User eksploratif: normalized entropy >= 0.80
- Top-1 share digunakan untuk melihat dominasi satu lokasi utama (ambang 0.50)

### Hasil Per Bulan

| Bulan | Users Dianalisis | Median Hn | Mean Hn | Median Top-1 Share | Median Lokasi | Routine | Explorer | Dominan 1 Lokasi |
|-------|------------------|-----------|---------|--------------------|---------------|---------|----------|------------------|
| 2021_10_Oktober | 63,166 | 0.222 | 0.336 | 0.959 | 2 | 55.8% | 15.1% | 93.0% |
| 2021_11_November | 348,346 | 0.465 | 0.424 | 0.848 | 2 | 43.8% | 19.9% | 86.4% |
| 2021_12_Desember | 269,308 | 0.581 | 0.500 | 0.767 | 3 | 33.2% | 23.0% | 84.0% |
| 2022_01_Januari | 153,220 | 0.573 | 0.498 | 0.756 | 3 | 32.9% | 20.8% | 81.3% |
| 2022_02_Februari | 166,928 | 0.489 | 0.444 | 0.822 | 2 | 40.9% | 19.8% | 85.1% |
| 2022_03_Maret | 96,536 | 0.000 | 0.269 | 1.000 | 1 | 65.6% | 14.2% | 94.8% |
| 2022_04_April | 6,386 | 0.405 | 0.396 | 0.855 | 2 | 46.9% | 18.1% | 86.4% |
| 2022_05_Mei | 159,842 | 0.257 | 0.348 | 0.949 | 2 | 53.9% | 15.8% | 87.0% |
| 2022_06_Juni | 82,616 | 0.229 | 0.343 | 0.957 | 2 | 55.1% | 16.2% | 90.0% |

### Hasil Keseluruhan

- **Total user-month dianalisis**: 1,346,348
- **Median normalized entropy keseluruhan**: 0.456
- **Median top-1 share keseluruhan**: 0.853
- **Median jumlah lokasi unik**: 2

### Interpretasi Hasil

- Nilai median normalized entropy keseluruhan sebesar **0,456** menunjukkan bahwa mobilitas pengguna DIY tidak sepenuhnya acak, tetapi juga tidak sepenuhnya tersebar merata ke banyak lokasi. Dengan kata lain, pola mobilitas didominasi oleh struktur yang cukup teratur.
- Median **top-1 share 0,853** berarti lebih dari 85% titik GPS pengguna tipikal terkonsentrasi pada satu lokasi utama. Ini menguatkan dugaan bahwa banyak pengguna beraktivitas berulang pada lokasi inti seperti rumah, area kerja, atau simpul kegiatan harian.
- **Maret 2022** menjadi bulan paling rutin dengan median entropy **0,000**, median lokasi unik **1**, dan top-1 share **1,000**. Secara substantif, bulan ini memperlihatkan pemusatan aktivitas yang ekstrem pada satu lokasi dominan.
- **Desember 2021** dan **Januari 2022** menunjukkan entropy tertinggi. Ini mengindikasikan ruang aktivitas lebih tersebar dan jumlah lokasi yang dikunjungi pengguna lebih banyak dibanding bulan lain.
- Persentase user rutin berada pada kisaran **32,9% sampai 65,6%**, sedangkan user eksploratif berada pada kisaran **14,2% sampai 23,0%**. Artinya, dalam setiap bulan, kelompok pengguna rutin selalu lebih dominan daripada kelompok yang benar-benar eksploratif.
- Dalam konteks skripsi, analisis ini penting karena menjelaskan dimensi **regularitas spasial** mobilitas. Jadi, pembahasan tidak berhenti pada seberapa jauh orang bergerak, tetapi juga pada seberapa konsisten mereka mengulangi pola ruang yang sama.

### Kesimpulan

- Mobilitas paling rutin muncul pada **2022_03_Maret**, ditandai median normalized entropy 0.000 dan top-1 share 1.000.
- Mobilitas paling eksploratif muncul pada **2021_12_Desember**, dengan median normalized entropy 0.581 dan persentase explorer 23.0%.
- Secara umum, entropy yang tidak terlalu tinggi bersama top-1 share yang besar menunjukkan banyak pengguna masih bertumpu pada sedikit lokasi inti, seperti rumah, area kerja, atau koridor aktivitas rutin.
- Analisis ini penting untuk skripsi karena menjelaskan tidak hanya seberapa jauh orang bergerak, tetapi juga seberapa stabil pola ruang yang mereka ulang dari waktu ke waktu.

### Visualisasi
- Plot per bulan: `output_plots/{bulan}/`
- Plot keseluruhan: `output_plots/Keseluruhan/`

*Waktu eksekusi: 37.9 detik*
