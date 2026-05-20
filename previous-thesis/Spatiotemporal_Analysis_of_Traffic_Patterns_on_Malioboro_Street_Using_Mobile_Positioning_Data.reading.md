# Ringkasan Pembacaan — Spatiotemporal Analysis of Traffic Patterns on Malioboro Street Using Mobile Positioning Data

## Identitas dokumen
- **Jenis**: paper konferensi IEEE ICITEE 2025.
- **Topik utama**: analisis spatiotemporal pola lalu lintas Jalan Malioboro menggunakan Active MPD.
- **Kata kunci kerja**: Active MPD, GPS, preprocessing, stay location removal, KDTree, HMM, Viterbi, path reconstruction, speed, flow, validation.

## Inti penelitian
Paper ini merupakan versi ringkas/paper dari studi Active MPD Malioboro. Fokusnya adalah menggunakan GPS time series dari Active MPD untuk menganalisis kecepatan dan flow lalu lintas di Jalan Malioboro, lalu membandingkan hasil dengan data pembanding seperti Google Maps dan survei resmi.

## Data dan cakupan
- Data Active MPD dari salah satu perusahaan telekomunikasi Indonesia.
- Periode data yang terbaca: **Januari–Februari 2022**.
- Teks menyebut sekitar **2,2 juta** titik GPS mentah.
- Setelah preprocessing, data berkurang menjadi **229.826** entri berkualitas.
- Rekonstruksi menghasilkan **2.316 trajectory** pengguna untuk analisis.

## Catatan akurasi GPS
Paper menyebut Active MPD/GPS berbasis smartphone dengan A-GPS:
- akurasi tipikal **5–10 meter** pada kondisi optimal;
- dapat menjadi sekitar **10–30 meter** pada kawasan urban padat;
- temporal granularity relatif rendah karena interval antar-record yang lebar.

Catatan ini sangat penting untuk justifikasi toleransi spasial RRU.

## Alur metodologi yang dibaca
1. **Data acquisition** dari Active MPD.
2. **Preprocessing**
   - filtering radius dari area target;
   - penghapusan duplikasi;
   - pengurutan kronologis.
3. **Eliminating stay locations**
   - menggunakan MovingPandas `StopSplitter()`;
   - threshold yang disebut: **200 meter** dan **30 menit**.
4. **Eliminating outliers distant from road network**
   - titik lebih dari **20 meter** dari ruas jalan dihapus;
   - memakai buffer Shapely agar hanya titik terkait pergerakan di jalan yang dipertahankan.
5. **Map matching dengan KDTree**
   - titik GPS dikoreksi/dicocokkan ke segmen jalan terdekat.
6. **Adjusting points to road direction**
   - titik disesuaikan dengan arah jalan.
7. **Trajectory segmentation**
   - data disegmentasi berdasarkan gap observasi **10 menit** memakai MovingPandas `ObservationGapSplitter()`.
8. **Path reconstruction**
   - memakai PyTrack, HMM, dan Viterbi untuk rekonstruksi lintasan kendaraan.
9. **Speed and flow calculation**
   - menghitung kecepatan dan flow di polygon Jalan Malioboro.
10. **Validation**
   - membandingkan dengan Google Maps dan survei resmi menggunakan DTW dan Pearson correlation.

## Angka preprocessing penting
Tabel hasil preprocessing:
- Preprocessing awal: **2.195.131** titik (100%).
- Setelah stay location removal: **342.123** titik (15,58%).
- Setelah filter jarak >20 m dari jaringan jalan: **340.744** titik (15,52%).
- Setelah map matching KDTree: **340.744** titik (15,52%).
- Setelah penyesuaian arah jalan: **229.826** titik (10,46%).

## Temuan penting
- Weekday menunjukkan rata-rata kecepatan lebih tinggi dan pola flow lebih teratur daripada weekend.
- Teks paper menyebut rata-rata kecepatan weekday sekitar **15,54 km/jam**, sedangkan weekend sekitar **12,88 km/jam**.
- Validasi dengan DTW dan Pearson menunjukkan kesesuaian sedang-kuat pada beberapa aspek, antara lain weekday flow **r = 0,79** dan weekend speed **r = 0,63**.

## Relevansi untuk skripsi RRU
- Sangat relevan untuk menyatakan bahwa Active MPD perlu preprocessing ketat sebelum dipakai untuk analisis lalu lintas.
- Memberi rujukan eksplisit untuk:
  - akurasi GPS/A-GPS 5–10 m optimal dan 10–30 m di urban padat;
  - filter titik lebih dari 20 m dari jaringan jalan;
  - stay location removal;
  - segmentation berdasarkan observation gap;
  - perlunya validasi jika ingin mengklaim speed/flow.

## Implikasi metodologis untuk RRU
- Ambang 20 m pada RRU dapat dijelaskan sebagai toleransi terhadap error posisi Active MPD, bukan angka arbitrer.
- Karena RRU tidak melakukan rekonstruksi HMM/Viterbi penuh dan tidak punya validasi flow eksternal, klaim harus lebih sederhana:
  - “intensitas MAID/ping teramati”; bukan “arus lalu lintas aktual”;
  - “OD zona persimpangan pertama/terakhir teramati”; bukan “rute aktual”;
  - “pola OD zona eksploratif”; bukan “turning movement terverifikasi”.

## Keterbatasan jika dijadikan rujukan
- Paper Malioboro memiliki ground truth pembanding; RRU harus hati-hati jika tidak punya data pembanding setara.
- Karakter Malioboro berbeda dari RRU, terutama pada fungsi jalan, kepadatan wisata, dan geometri satu arah.
- Jangan menyalin metode HMM/Viterbi jika pipeline RRU hanya melakukan filtering dan agregasi zona.
