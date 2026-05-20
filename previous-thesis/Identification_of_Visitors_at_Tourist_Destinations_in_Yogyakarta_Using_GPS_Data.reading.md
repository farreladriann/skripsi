# Ringkasan Pembacaan — Identification of Visitors at Tourist Destinations in Yogyakarta Using GPS Data

## Identitas dokumen
- **Jenis**: paper konferensi IEEE ICITCOM 2024.
- **Topik utama**: identifikasi wisatawan/pengunjung pada destinasi wisata di Yogyakarta menggunakan data GPS.
- **Kata kunci kerja**: GPS data, tourism, visitor profiling, tourist vs resident, home location, rule-based classification, reverse geocoding.

## Inti penelitian
Paper ini menggunakan data GPS dari operator telekomunikasi untuk membedakan aktivitas wisatawan domestik, penduduk biasa, pekerja di area wisata, dan pengunjung kasual pada beberapa destinasi wisata di DIY. Masalah utamanya adalah data GPS dari operator masih mencampur wisatawan dengan non-wisatawan, sehingga diperlukan profiling berbasis aturan.

## Data dan cakupan
- Periode data: **November 2021 sampai Februari 2022**.
- Data berasal dari pengguna ponsel yang mengaktifkan layanan lokasi.
- Lokasi wisata yang dibaca dalam teks meliputi:
  - Pantai Baron;
  - Candi Prambanan;
  - Gembira Loka;
  - Glagah;
  - Pantai Parangtritis.
- Periode masih berada dalam konteks pembatasan COVID-19 sehingga mobilitas penduduk dapat terpengaruh.

## Alur metodologi yang dibaca
1. **Data preparation**
   - menghapus data duplikat;
   - memberi label waktu/kondisi;
   - mengubah tipe field untuk kebutuhan analisis.
2. **Reverse geocoding dan integrasi geometri**
   - koordinat GPS dikonversi menjadi informasi lokasi administratif;
   - data GPS digabungkan dengan polygon kecamatan/administrasi DIY.
3. **Home location detection**
   - lokasi rumah diperkirakan dari titik yang sering muncul pada malam hari;
   - rentang malam yang disebut: sekitar **22.00–04.00**.
4. **Temporal-spatial threshold**
   - studi menyebut konsep radius **200 meter** dan durasi **20 menit** untuk mendeteksi aktivitas/stationarity.
5. **Administrative alignment**
   - jika lokasi rumah dan lokasi wisata berada pada sub-district yang sama, pengguna dikategorikan sebagai resident;
   - jika berbeda, pengguna dapat dikategorikan sebagai tourist.
6. **Klasifikasi kategori pengunjung**
   - tourist: individu dari kecamatan berbeda yang berada di lokasi wisata;
   - working resident: menghabiskan sekitar 40 jam/minggu di lokasi wisata;
   - visitor: menghabiskan rata-rata sekitar 3,3 jam di lokasi wisata;
   - ordinary resident: tidak masuk kategori sebelumnya.
7. **Priority destination analysis**
   - menggunakan first visit dan frekuensi UID untuk melihat destinasi yang diprioritaskan.

## Temuan penting
- Gembira Loka dan Parangtritis disebut sebagai destinasi utama/priority destination untuk first-time visitors.
- Paper menampilkan variasi komposisi pengunjung antar destinasi dan bulan.
- Studi menyimpulkan rule-based approach dapat membedakan wisatawan, pekerja/residen, pengunjung, dan penduduk biasa dari data GPS low-sampling-rate.

## Relevansi untuk skripsi RRU
- Relevan sebagai contoh bahwa data GPS/MPD perlu preprocessing, deduplikasi, penggabungan spasial, dan klasifikasi berbasis aturan jika ingin menafsirkan perilaku pengguna.
- Sangat berguna sebagai **pembanding keputusan metodologis**: skripsi RRU sengaja tidak mengambil estimasi rumah/catchment karena itu menambah asumsi kuat dan risiko bias.
- Mendukung pemilihan pendekatan RRU yang lebih sederhana: zona persimpangan pertama/terakhir teramati, bukan asal/tujuan rumah sebenarnya.

## Implikasi metodologis untuk RRU
- Jangan memasukkan home location/catchment jika fokus skripsi adalah koridor RRU; metode itu cocok untuk studi pariwisata/residensi, bukan wajib untuk analisis koridor.
- Jika ada pembahasan OD, gunakan istilah **OD zona teramati** bukan asal/tujuan aktual penduduk.
- Paper ini bisa dipakai untuk menjelaskan bahwa inferensi identitas/peran pengguna membutuhkan aturan tambahan; karena RRU tidak memvalidasi peran pengguna, klaim harus dibatasi.

## Keterbatasan jika dijadikan rujukan
- Fokusnya pariwisata, bukan lalu lintas koridor.
- Estimasi rumah dan kategori pengunjung sensitif terhadap threshold waktu/spasial dan kualitas data.
- Tidak cocok dijadikan dasar langsung untuk mengklaim kendaraan RRU berasal dari/tujuan ke wilayah rumah tertentu.
