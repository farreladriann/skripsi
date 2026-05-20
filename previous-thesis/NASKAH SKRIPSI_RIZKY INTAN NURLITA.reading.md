# Ringkasan Pembacaan — NASKAH SKRIPSI Rizky Intan Nurlita

## Identitas dokumen
- **Jenis**: naskah skripsi.
- **Judul yang terbaca**: *Analisis Spatial Time-Series Data untuk Identifikasi Pola Kecepatan dan Arus Lalu Lintas di Jalan Malioboro Berbasis Active Mobile Positioning Data*.
- **Topik utama**: analisis kecepatan dan arus lalu lintas Jalan Malioboro menggunakan Active MPD/GPS, path reconstruction, dan validasi terhadap data pembanding.
- **Kata kunci kerja**: Active MPD, GPS, preprocessing, map matching, KDTree, HMM, path reconstruction, speed, traffic flow, Google Maps, Dinas Perhubungan DIY.

## Inti penelitian
Skripsi ini menganalisis pola kecepatan dan arus lalu lintas di Jalan Malioboro berdasarkan Active MPD. Tujuan utamanya adalah merekonstruksi lintasan pengguna, menghitung pola kecepatan/arus, lalu membandingkan hasilnya dengan ground truth atau data pembanding seperti Google Maps dan Dinas Perhubungan DIY.

Dokumen ini penting untuk skripsi RRU karena menggunakan jenis data yang sangat dekat: Active MPD berbasis GPS dari perangkat bergerak, dengan karakter sparse/noisy dan kebutuhan preprocessing yang kuat.

## Data dan fitur
Teks menyebut fitur MPD aktif seperti:
- `maid` sebagai ID unik pengguna/perangkat;
- latitude dan longitude;
- timestamp;
- atribut turunan seperti durasi, jarak, kecepatan, dan bearing pada tahap hasil.

Data pembanding yang digunakan:
- riwayat kecepatan lalu lintas Google Maps;
- survei arus lalu lintas Dinas Perhubungan DIY.

## Alur metodologi yang dibaca
Tahapan penting dalam Bab III/Bab IV:
1. **Mengumpulkan data** Active MPD dan data jaringan jalan.
2. **Preprocessing data**
   - memilih atribut relevan;
   - menghapus duplikasi;
   - mengonversi timestamp;
   - memastikan data sesuai area dan urutan waktu.
3. **Mengeliminasi stay locations**
   - menghapus titik diam yang tidak merepresentasikan pergerakan lalu lintas.
4. **Mengeliminasi titik jarak >20 meter dari ruas jalan**
   - menggunakan buffer Shapely 20 meter di sekitar jaringan jalan;
   - alasan: GPS tidak selalu akurat dan error perekaman dapat berada pada rentang sekitar 10–20 meter.
5. **Map matching dengan KDTree**
   - titik GPS dicocokkan ke ruas jalan terdekat secara efisien.
6. **Immobility filter**
   - mengurangi titik yang bertumpuk/diam setelah map matching.
7. **Menyesuaikan titik dengan arah jalur jalan**
   - penting pada jaringan jalan dengan arah tertentu.
8. **Split trajectory berdasarkan waktu observasi**
   - membagi lintasan berdasarkan gap observasi.
9. **Path reconstruction**
   - menggunakan pendekatan jalur terpendek/A* untuk mengisi lintasan antar titik.
10. **Interpolasi waktu**
   - memberi estimasi waktu pada titik hasil rekonstruksi.
11. **Perhitungan kecepatan dan arus lalu lintas**
   - dilakukan pada lintasan yang memenuhi kriteria.
12. **Validasi/komparasi**
   - membandingkan kecepatan dengan Google Maps;
   - membandingkan arus dengan data Dinas Perhubungan DIY;
   - memakai DTW dan korelasi Pearson.

## Angka preprocessing penting
Tabel implementasi preprocessing menunjukkan reduksi besar:
- Titik awal preprocessing: **2.195.131** titik GPS (100%).
- Setelah eliminasi stay locations: **342.123** titik (15,58%).
- Setelah eliminasi titik >20 m dari jalan: **340.744** titik (15,52%).
- Setelah map matching KDTree: **340.744** titik (15,52%).
- Setelah immobility filter: **229.826** titik (10,46%).
- Setelah penyesuaian arah jalur: **229.826** titik (10,46%).

Tabel perubahan tahap lanjutan juga menyebut:
- split trajectory: **175.964** titik dan **30.482** trajectory;
- rekonstruksi rute: **4.231.096** titik dan **29.058** trajectory;
- lingkup Jalan Malioboro: **200.254** titik dan **5.354** trajectory;
- perhitungan kecepatan: **2.316** trajectory memenuhi kriteria.

## Temuan penting
- Mayoritas data mentah dapat berupa titik diam/stay atau titik yang tidak langsung berguna untuk analisis lalu lintas, sehingga preprocessing sangat menentukan hasil.
- Buffer 20 meter dipakai untuk menjaga titik yang masih mungkin terkait jaringan jalan dengan mempertimbangkan error GPS.
- Analisis menunjukkan perbedaan pola weekday dan weekend di Malioboro.
- Hasil dibandingkan dengan data Google Maps dan Dinas Perhubungan DIY; secara umum disebut cukup selaras, terutama pada hari kerja, meskipun ada outlier/variabilitas.

## Relevansi untuk skripsi RRU
Ini adalah rujukan lokal paling penting untuk justifikasi preprocessing RRU.

Yang dapat diadopsi:
- penjelasan bahwa Active MPD/GPS mengandung noise dan sparse sampling;
- kebutuhan deduplikasi, pengurutan waktu, filtering spasial terhadap jaringan jalan;
- penggunaan ambang **20 meter** sebagai toleransi konservatif terhadap error GPS;
- penggunaan MAID sebagai unit pengguna/perangkat teramati;
- pentingnya menghindari klaim terlalu kuat jika validasi ground truth tidak dilakukan.

Yang tidak perlu diadopsi penuh:
- path reconstruction lengkap dengan HMM/A*/interpolasi jika tujuan RRU hanya baseline koridor;
- estimasi arus/volume aktual jika RRU tidak punya data ground truth Dishub/traffic count;
- turning movement aktual jika sampling rendah tidak cukup untuk memvalidasi belokan geometris.

## Implikasi metodologis untuk RRU
- Ambang 20 m di RRU dapat dijustifikasi dengan dua hal:
  1. rujukan lokal Nurlita bahwa error GPS dapat berada sekitar 10–20 m;
  2. sensitivitas lokal RRU terhadap jarak titik-ke-jaringan.
- RRU sebaiknya memakai istilah **kendaraan terindikasi/teramati** dan **OD zona teramati**, bukan volume lalu lintas aktual.
- Jika Bab III RRU memakai R-tree/nearest road filtering, jelaskan bahwa ini adalah seleksi spasial konservatif, bukan map matching lintasan penuh.
- Untuk intensitas simpang, gunakan **rata-rata MAID unik harian dari agregasi harian teramati**, bukan membagi total MAID unik dengan jumlah hari.

## Keterbatasan jika dijadikan rujukan
- Studi Malioboro punya validasi eksternal; RRU belum tentu punya ground truth sebanding.
- Karakter Jalan Malioboro berbeda dari Ring Road Utara: Malioboro lebih turistik/perkotaan pusat, RRU adalah koridor arterials/ring road.
- Metode path reconstruction Malioboro lebih kompleks daripada kebutuhan RRU; mengadopsi istilahnya tanpa menjalankan metodenya dapat membuat klaim terlalu kuat.
