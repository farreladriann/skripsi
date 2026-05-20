# Ringkasan Pembacaan — Comparison of Hidden Markov Model and KD-Tree in GPS Data-Based Map Matching Process

## Identitas dokumen
- **Jenis**: paper konferensi IEEE ICITEE 2024.
- **Topik utama**: perbandingan algoritma map matching berbasis Hidden Markov Model (HMM) dan KD-Tree pada data GPS.
- **Kata kunci kerja**: GPS data, map matching, HMM, KD-Tree, Dynamic Time Warping (DTW), noise, sparsity/reduksi data.

## Inti penelitian
Paper ini membahas masalah utama pada data GPS/MPD: koordinat mentah mengandung noise dan tidak selalu tepat berada pada jaringan jalan. Untuk menghasilkan lintasan yang lebih masuk akal, data perlu dicocokkan ke jaringan jalan melalui proses map matching.

Studi membandingkan dua pendekatan:
- **HMM**: memodelkan kemungkinan posisi titik GPS pada ruas jalan dan transisi antar-ruas menggunakan struktur jaringan jalan.
- **KD-Tree**: mencari ruas/titik jaringan jalan terdekat secara efisien sebagai pendekatan nearest-neighbor.

Evaluasi dilakukan dengan membandingkan hasil map matching terhadap ground truth memakai **Dynamic Time Warping (DTW)** dan similarity score.

## Data dan eksperimen
- Menggunakan lebih dari satu kategori data GPS, termasuk data perjalanan penulis dan dataset Newson et al.
- Eksperimen juga mencakup **random data reduction** untuk melihat dampak berkurangnya titik GPS terhadap akurasi.
- Data hasil map matching dibandingkan dengan ground truth rute.

## Temuan penting
- HMM menghasilkan tingkat akurasi/similarity lebih tinggi daripada KD-Tree pada kategori data yang diuji.
- Dalam teks paper, HMM disebut berada sekitar **80%**, sedangkan KD-Tree sekitar **55%** untuk kategori yang diuji.
- Pada dataset Newson, HMM unggul sekitar **20%**; pada dataset penulis yang lebih sedikit titik GPS-nya, selisihnya sekitar **30%**.
- Reduksi data ke 75% dan 50% tetap menunjukkan HMM lebih unggul daripada KD-Tree.
- Akurasi sangat dipengaruhi oleh jumlah/kerapatan titik GPS yang tersedia.

## Relevansi untuk skripsi RRU
- Menguatkan argumen bahwa data GPS/Active MPD perlu diperlakukan sebagai data noisy dan perlu proses penyelarasan/penyaringan terhadap jaringan jalan.
- Memberi dasar bahwa map matching penuh seperti HMM lebih akurat untuk rekonstruksi rute, tetapi lebih kompleks.
- Untuk skripsi RRU, pendekatan yang lebih sederhana seperti R-tree/nearest-edge filtering masih masuk akal **jika klaimnya dibatasi** pada seleksi titik dekat koridor dan bukan rekonstruksi lintasan aktual penuh.
- Jika skripsi tidak melakukan validasi ground truth rute, sebaiknya tidak mengklaim “rute sebenarnya”, “turning movement aktual”, atau “volume lalu lintas aktual”.

## Catatan metodologis untuk RRU
- Gunakan paper ini untuk menjelaskan trade-off:
  - HMM lebih kuat untuk map matching lintasan penuh.
  - KD-Tree/R-tree/nearest-neighbor lebih ringan dan cocok untuk filtering spasial awal.
- Karena tujuan RRU adalah baseline spatiotemporal koridor, bukan rekonstruksi rute door-to-door, pendekatan sederhana lebih robust selama hasil dibahas sebagai **indikator kendaraan teramati**.
- Paper ini mendukung kebutuhan analisis sensitivitas ambang jarak karena jumlah dan kepadatan titik memengaruhi hasil.

## Keterbatasan jika dijadikan rujukan
- Studi berfokus pada map matching dan evaluasi rute dengan ground truth, sedangkan skripsi RRU berfokus pada OD zona persimpangan dan intensitas koridor.
- Hasil akurasi HMM tidak otomatis berlaku untuk dataset RRU tanpa ground truth rute.
- Jangan memakai angka 80%/55% sebagai akurasi metode RRU; gunakan hanya sebagai bukti umum bahwa metode map matching berbeda menghasilkan kualitas berbeda.
