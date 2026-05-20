# Ringkasan Pembacaan — How Does Rainfall Affect Mobility Across Yogyakarta Regions?

## Identitas dokumen
- **Jenis**: paper konferensi ACM AICCC 2025.
- **Topik utama**: dampak hujan terhadap mobilitas wilayah di Daerah Istimewa Yogyakarta menggunakan Active MPD.
- **Kata kunci kerja**: Active Mobile Positioning Data, rainfall, trajectory splitting, OD construction, mobility network, network indicators.

## Inti penelitian
Paper ini menggunakan Active MPD untuk melihat perubahan pola mobilitas pada hari hujan dan tidak hujan di DIY. Data lokasi GPS dari perangkat bergerak digabungkan dengan data curah hujan harian, lalu dianalisis melalui karakteristik perjalanan dan indikator jaringan mobilitas.

## Data dan cakupan
- Dataset utama berupa Active MPD di DIY.
- Periode data: **November 2021 sampai Mei 2022**.
- Teks menyebut sekitar **297,6 juta GPS records**.
- Data hujan harian diperoleh dari Visual Crossing Weather API.

## Alur metodologi yang dibaca
1. **Initial preprocessing**
   - konversi timestamp UNIX ke datetime;
   - penghapusan duplikasi;
   - pengurutan berdasarkan `maid` dan timestamp.
2. **Outlier removal**
   - titik dengan kecepatan tidak masuk akal/spatial anomaly dihapus;
   - ambang maksimum yang disebut: **120 km/jam**.
3. **Trajectory splitting**
   - perjalanan dipisahkan berdasarkan konsep stay location;
   - stay location didefinisikan sebagai berhenti lebih dari **30 menit** dalam radius **200 meter**.
4. **OD construction**
   - titik awal dan akhir trajectory dijadikan origin dan destination;
   - OD dipakai sebagai unit analisis mobilitas.
5. **Rainy vs non-rainy classification**
   - hari diklasifikasikan hujan jika curah hujan > 5 mm, dan tidak hujan jika ≤ 5 mm.
6. **Analisis indikator mobilitas**
   - jumlah user unik, jumlah trip, durasi, jarak, trip harian;
   - indikator jaringan seperti node degree, node strength, closeness centrality, network density, coefficient of variation.

## Temuan penting
- Hari hujan cenderung memiliki rata-rata trip harian, jarak, dan durasi yang lebih rendah dibanding hari tidak hujan.
- Dampak hujan tidak homogen secara spasial: wilayah urban seperti Kota Yogyakarta dan Sleman selatan relatif lebih resilien, sedangkan Gunungkidul dan Kulon Progo lebih rentan terhadap penurunan konektivitas/aksesibilitas.
- Paper menekankan MPD dapat digunakan untuk monitoring dinamika mobilitas, tetapi interpretasinya tetap berbasis sampel observasional.

## Relevansi untuk skripsi RRU
- Menguatkan struktur metodologi OD berbasis titik awal-akhir trajectory.
- Memberi rujukan bahwa preprocessing dasar seperti deduplikasi, konversi timestamp, pengurutan per MAID, outlier speed, dan trajectory splitting merupakan praktik wajar pada Active MPD.
- Menguatkan penggunaan indikator agregat dan jaringan sebagai baseline, bukan klaim kausal/volume aktual.
- Berguna untuk Bab II/Bab III sebagai contoh penelitian MPD di Yogyakarta dengan skala besar dan preprocessing eksplisit.

## Implikasi untuk RRU
- Untuk RRU, OD zona persimpangan pertama/terakhir sejalan dengan pendekatan OD construction, tetapi skala zonanya lebih spesifik pada simpang koridor.
- Karena RRU tidak menganalisis hujan, bagian rainfall tidak perlu dibawa terlalu jauh; cukup ambil aspek preprocessing dan OD/network logic.
- Gunakan bahasa konservatif: hasil RRU menunjukkan pola perjalanan kendaraan terindikasi di koridor, bukan keseluruhan mobilitas penduduk atau volume lalu lintas.

## Keterbatasan jika dijadikan rujukan
- Unit analisis paper ini wilayah administrasi/grid mobilitas, bukan koridor jalan spesifik.
- Paper memproses stay location dan OD untuk mobilitas umum, sedangkan RRU fokus pada kendaraan terindikasi dalam koridor.
