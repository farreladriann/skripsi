# Ringkasan 3 Analisis Spatiotemporal Tambahan

## Konteks

Analisis ini disusun untuk memperkuat deskripsi skripsi yang masih terlalu umum. Fokusnya bukan hanya membuktikan bahwa data GPS dapat dianalisis, tetapi menunjukkan bahwa data tersebut mampu menjelaskan:

- seberapa rutin pola gerak pengguna dari waktu ke waktu,
- bagaimana pusat aktivitas berpindah sepanjang hari,
- dan seberapa stabil hotspot spasial antarbulan.

Semua analisis menggunakan data Parquet pada `DataGPS_parquet/` yang sudah dibersihkan dan diurutkan.

## Analisis 10: Mobility Regularity & Spatial Entropy

Folder: `analisis10/`

### Inti Temuan Analisis 10

- Total user-month yang memenuhi syarat analisis mencapai **1.346.348**.
- **Median normalized entropy keseluruhan = 0,456**, sehingga secara umum mobilitas pengguna tidak sepenuhnya acak, tetapi juga tidak sepenuhnya tersebar luas.
- **Median top-1 share keseluruhan = 0,853**. Artinya, pada user tipikal, sekitar 85,3% titik GPS terkonsentrasi pada satu lokasi utama.
- Bulan **paling rutin** adalah **Maret 2022** dengan median normalized entropy **0,000** dan median top-1 share **1,000**.
- Bulan **paling eksploratif** adalah **Desember 2021** dengan median normalized entropy **0,581** dan persentase user eksploratif **23,0%**.

### Interpretasi Analisis 10

Temuan ini menunjukkan bahwa mobilitas di DIY didominasi oleh pola kunjungan berulang pada sedikit lokasi inti. Dalam konteks skripsi, ini berarti struktur mobilitas masyarakat tidak hanya dapat dilihat dari jarak perjalanan, tetapi juga dari kestabilan ruang aktivitas yang mereka ulang.

## Analisis 11: Daypart Spatial Shift & Urban Pulse

Folder: `analisis11/`

### Inti Temuan Analisis 11

- Daypart yang paling dominan secara keseluruhan adalah **Malam**.
- Pergeseran pusat aktivitas paling besar terjadi pada **Maret 2022**, dengan **shift maksimum 1,70 km** antar-daypart.
- Pergeseran paling kecil terjadi pada **Desember 2021**, hanya **0,38 km**.
- Pada beberapa bulan, daypart dominan berpindah dari **Malam** ke **Dini Hari**, menandakan perubahan ritme aktivitas intrahari yang cukup jelas.
- Rata-rata top hotspot share per daypart cenderung lebih tinggi pada bulan-bulan dengan aktivitas lebih terkonsentrasi, misalnya Maret, April, dan Mei 2022.

### Interpretasi Analisis 11

Analisis ini memperlihatkan bahwa pola mobilitas DIY memiliki ritme intrahari yang nyata. Pusat aktivitas tidak diam pada satu lokasi, melainkan bergerak mengikuti pembagian waktu harian. Ini memberi nilai tambah metodologis karena menggabungkan dimensi waktu dan ruang secara langsung.

## Analisis 12: Hotspot Persistence & Turnover

Folder: `analisis12/`

### Inti Temuan Analisis 12

- Dari seluruh periode, terdapat **122 hotspot unik**.
- Sebanyak **36 sel hotspot** tergolong **persistent core**, yaitu tetap aktif minimal 5 bulan.
- Overlap hotspot tertinggi dengan bulan sebelumnya terjadi pada **Juni 2022** dengan **Jaccard 0,707**.
- Overlap terendah terjadi pada **Desember 2021** dengan **Jaccard 0,308**.
- Share points yang jatuh pada hotspot bulanan berkisar sekitar **34,9% sampai 48,8%**, sehingga proporsi besar aktivitas memang tertarik ke simpul spasial tertentu.

### Interpretasi Analisis 12

Hasil ini menunjukkan adanya dua lapisan struktur ruang: hotspot inti yang stabil dan hotspot temporer yang berubah menurut bulan. Untuk skripsi, ini penting karena membuktikan bahwa analisis hotspot tidak cukup dilakukan per bulan saja; dinamika persistensi antarperiode juga perlu dibaca.

## Sintesis untuk Narasi Skripsi

Jika tiga analisis ini dirangkai, maka narasi yang muncul adalah sebagai berikut:

- Mobilitas di DIY cenderung **rutin**, dengan sebagian besar pengguna bertumpu pada sedikit lokasi utama.
- Meskipun rutin, pusat aktivitas tetap mengalami **pergeseran intrahari** yang terukur, sehingga ada denyut spasial harian yang kuat.
- Pada skala bulanan, sebagian hotspot tetap **persisten**, tetapi sebagian lain mengalami **turnover**, menandakan bahwa struktur mobilitas mengandung elemen stabil dan dinamis sekaligus.

Dengan demikian, data GPS ini layak digunakan untuk eksplorasi big data spatiotemporal karena mampu mengungkap pola perilaku mobilitas yang tidak terlihat dari agregasi statistik biasa.

## File Utama

- `analisis10/LAPORAN.md`
- `analisis11/LAPORAN.md`
- `analisis12/LAPORAN.md`
- `analisis10/hasil_entropy_summary.csv`
- `analisis11/hasil_daypart_summary.csv`
- `analisis12/hasil_hotspot_persistence_summary.csv`

## Visualisasi Keseluruhan

- `analisis10/output_plots/Keseluruhan/`
- `analisis11/output_plots/Keseluruhan/`
- `analisis12/output_plots/Keseluruhan/`
