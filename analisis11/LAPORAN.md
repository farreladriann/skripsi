# Laporan Analisis 11: Daypart Spatial Shift & Urban Pulse
## Data: GPS Mobilitas DIY (Oktober 2021 - Juni 2022)

### Tujuan
Mengidentifikasi bagaimana pusat aktivitas dan konsentrasi ruang berubah sepanjang hari untuk menangkap denyut spasial kota.

### Metodologi
- Timestamp dikonversi ke WIB (UTC+7)
- Grid spasial: 0.01 derajat
- Daypart: Dini Hari (00-05), Pagi (06-09), Siang (10-14), Sore (15-18), Malam (19-23)
- Untuk tiap daypart dihitung intensitas titik, jumlah sel aktif, centroid berbobot, dan dominasi hotspot utama
- Pergeseran spasial diukur dengan jarak Haversine antar-centroid daypart

### Hasil Per Bulan

| Bulan | Total Points | Daypart Dominan | Mean Top Share | Pagi->Malam Shift | Dini->Siang Shift | Shift Maksimum |
|-------|--------------|-----------------|----------------|-------------------|-------------------|----------------|
| 2021_10_Oktober | 12,123,709 | Malam | 0.027 | 1.17 km | 0.16 km | 1.42 km |
| 2021_11_November | 119,072,431 | Malam | 0.031 | 1.00 km | 0.62 km | 1.09 km |
| 2021_12_Desember | 45,950,349 | Dini Hari | 0.057 | 0.26 km | 0.32 km | 0.38 km |
| 2022_01_Januari | 22,488,991 | Dini Hari | 0.035 | 0.52 km | 0.37 km | 0.59 km |
| 2022_02_Februari | 39,601,774 | Malam | 0.051 | 0.62 km | 0.13 km | 0.81 km |
| 2022_03_Maret | 26,837,642 | Dini Hari | 0.145 | 1.50 km | 0.95 km | 1.70 km |
| 2022_04_April | 1,048,571 | Malam | 0.097 | 0.78 km | 0.54 km | 0.78 km |
| 2022_05_Mei | 31,075,611 | Malam | 0.136 | 0.25 km | 0.40 km | 0.49 km |
| 2022_06_Juni | 12,246,261 | Malam | 0.100 | 0.46 km | 0.23 km | 0.51 km |

### Hasil Keseluruhan

- **Daypart paling dominan secara keseluruhan**: Malam
- **Bulan dengan pergeseran centroid terbesar**: 2022_03_Maret (1.70 km)
- **Bulan dengan pergeseran centroid terkecil**: 2021_12_Desember (0.38 km)

### Interpretasi Hasil

- Dominasi **Malam** sebagai daypart utama pada sebagian besar bulan menunjukkan bahwa intensitas aktivitas GPS cenderung paling tinggi setelah sore hari. Ini bisa terkait dengan akumulasi mobilitas pulang, aktivitas malam, atau perilaku penggunaan perangkat yang tetap aktif pada malam hari.
- Pada **Desember 2021**, **Januari 2022**, dan **Maret 2022**, daypart dominan bergeser ke **Dini Hari**. Pergeseran ini penting karena menunjukkan bahwa ritme intrahari tidak selalu konstan dari bulan ke bulan.
- **Maret 2022** memiliki pergeseran centroid paling besar, baik untuk lintasan **Pagi ke Malam** maupun shift maksimum antar-daypart. Ini menandakan redistribusi ruang aktivitas intrahari pada bulan tersebut jauh lebih kuat daripada bulan lainnya.
- Sebaliknya, **Desember 2021** memiliki shift centroid paling kecil. Artinya, meskipun aktivitas tinggi, pusat ruang aktivitas antardaypart relatif berdekatan dan tidak banyak berpindah.
- Nilai **mean top share** yang meningkat pada beberapa bulan, terutama **Maret, April, Mei, dan Juni 2022**, menunjukkan bahwa aktivitas per daypart pada bulan-bulan tersebut lebih terkonsentrasi pada sedikit lokasi utama.
- Dalam konteks skripsi, analisis ini menjelaskan dimensi **denyut kota**. Ruang aktivitas DIY tidak hanya penting secara bulanan, tetapi juga bergerak secara sistematis di dalam satu hari, sehingga interpretasi mobilitas menjadi lebih kaya daripada sekadar hitungan volume atau hotspot statis.

### Kesimpulan

- Aktivitas mobilitas tidak hanya berubah volumenya, tetapi juga berpindah pusat ruangnya sepanjang hari. Ini menandakan adanya ritme intrahari yang kuat pada wilayah DIY.
- Pergeseran centroid yang besar mengindikasikan perpindahan terstruktur antara zona aktivitas berbeda, misalnya dari area hunian menuju pusat kegiatan siang hari lalu kembali ke area malam.
- Top hotspot share membantu membaca apakah aktivitas pada suatu daypart terkonsentrasi pada sedikit titik atau tersebar ke banyak lokasi.
- Analisis ini penting untuk skripsi karena menghubungkan dimensi waktu dan ruang secara langsung, bukan hanya melihat jumlah aktivitas atau hotspot secara terpisah.

### Visualisasi
- Plot per bulan: `output_plots/{bulan}/`
- Plot keseluruhan: `output_plots/Keseluruhan/`

*Waktu eksekusi: 57.1 detik*
