# Catatan Jurnal: Trajectory Data Preprocessing: Methods and Models

**File:** `references/electronics-14-04694.pdf`  
**Artikel:** Li, P.; Tian, Z.; Yang, Y.; Lin, Y. (2025). *Trajectory Data Preprocessing: Methods and Models*. Electronics, 14, 4694. https://doi.org/10.3390/electronics14234694  
**Jenis:** Systematic review / literature review  
**Cakupan:** 138 studi tentang preprocessing data trajektori.

## Inti Artikel

Artikel ini merangkum pipeline preprocessing data trajektori GPS/sensor sebelum data dipakai untuk trajectory mining, transport analysis, visualization, atau location-based services. Empat pilar utama yang dibahas:

1. **Data cleaning**
   - Menghapus outlier/duplikasi.
   - Mengisi data hilang / interpolasi.
   - Smoothing noise.
   - Menyamakan timestamp, koordinat, dan format data.

2. **Trajectory compression**
   - Mengurangi volume data dan biaya komputasi.
   - Metode umum: line simplification, road-network constrained compression, semantic compression.
   - Penting untuk dataset besar karena data GPS mentah sering redundan.

3. **Trajectory segmentation**
   - Memecah trajektori menjadi unit bermakna.
   - Bisa berdasarkan waktu, jarak, kecepatan, perubahan arah, stop/move, transport mode, atau konteks semantik.
   - Kategori metode: supervised, unsupervised, semi-supervised.

4. **Map matching**
   - Mencocokkan titik GPS ke jaringan jalan.
   - Tujuan: memperbaiki error GPS, drift, multipath, atau sampling jarang supaya rute sesuai jalan aktual.
   - Kategori metode: geometric, topology-based, probabilistic/statistical, dan advanced/deep learning.

## Poin Penting untuk Skripsi RRU

### 1. Pembenaran pipeline preprocessing
Artikel ini mendukung urutan kerja skripsi:

`raw GPS → cleaning/outlier filtering → segmentation/trip processing → map matching → analisis OD/density/catchment/turning movement`

Karena artikel menekankan bahwa kualitas preprocessing sangat mempengaruhi validitas hasil analisis lanjutan.

### 2. Data cleaning relevan dengan outlier speed
Untuk data MPD/GPS, error bisa muncul karena:

- noise GPS,
- titik lompat jauh,
- timestamp tidak konsisten,
- sampling interval tidak merata,
- duplikasi titik.

Metode yang disebut artikel:

- mean/median filter untuk noise lokal,
- Kalman filter untuk smoothing berbasis model gerak,
- particle filter untuk gerak nonlinear/non-Gaussian,
- machine-learning-based cleaning untuk pola historis.

Untuk skripsi ini, bagian ini bisa dipakai sebagai landasan teori bahwa filtering kecepatan/outlier diperlukan sebelum map matching dan analisis jaringan.

### 3. Map matching adalah tahap kunci untuk analisis berbasis jalan
Artikel menyatakan map matching diperlukan karena raw GPS dapat menyimpang dari jalan aktual. Ini relevan langsung untuk skripsi karena analisis RRU membutuhkan identifikasi apakah kendaraan melewati backbone/intersection tertentu.

Ringkasan tipe map matching:

- **Geometric-based:** mudah dan cepat, menggunakan jarak/angle/shape similarity; cocok jika sampling rapat dan error kecil, tetapi lemah di simpang/overpass/low-frequency data.
- **Topology-based:** mempertimbangkan konektivitas jaringan jalan; lebih baik untuk lingkungan kompleks seperti simpang dan bundaran, tetapi membutuhkan data jaringan yang akurat.
- **Probability/statistics-based:** memakai confidence interval, candidate road, likelihood, HMM/MHT/CRF; lebih robust untuk noise dan sampling jarang, tetapi lebih kompleks.
- **Advanced model:** HMM, FMM, IVMM, deep learning; lebih kuat pada data noisy/low-frequency namun butuh komputasi dan/atau data latih.

Untuk skripsi ini, HMM/FMM-style map matching paling nyambung sebagai pembenaran karena data mobile/GPS kemungkinan sampling tidak selalu tinggi dan posisi bisa noisy.

### 4. Relevan untuk masalah jaringan jalan RRU dua carriageway
Artikel menekankan bahwa kualitas road network dan topologi jalan mempengaruhi akurasi map matching. Ini mendukung keputusan menjaga representasi jaringan jalan yang benar:

- tidak asal collapse semua jalan dua arah menjadi satu centerline,
- perlu membedakan carriageway one-way pada jalan terbagi,
- perlu hati-hati pada bundaran, simpang, flyover, underpass, dan jalan paralel.

Ini cocok dengan pekerjaan `rru_with_intersections-one-way-true.py`, terutama saat membedakan jalan surface vs flyover/tunnel di Jombor/Kentungan.

### 5. Evaluasi metode
Artikel menyarankan evaluasi preprocessing berdasarkan:

- sampling rate berbeda,
- noise/outlier berbeda,
- road-network density berbeda,
- akurasi dan running time untuk map matching,
- compression ratio dan SED untuk compression.

Untuk skripsi, yang paling relevan adalah:

- melaporkan jumlah titik/trip sebelum dan sesudah cleaning,
- melaporkan jumlah titik/trip berhasil match,
- memvisualisasikan hasil map matching di jaringan RRU,
- melakukan sanity check terhadap simpang/bundaran/flyover.

## Kutipan/Parafrase yang Bisa Dipakai

- Raw trajectory data sering mengandung error, noise, inkonsistensi, dan redundansi; preprocessing diperlukan agar hasil analisis lebih akurat dan reliabel.
- Preprocessing trajectory umumnya mencakup data cleaning, compression, segmentation, dan map matching.
- Map matching bertujuan mengoreksi titik trajektori ke jaringan jalan aktual dan penting untuk analisis transportasi berbasis rute/jalan.
- Geometric/topological methods cepat dan cocok untuk sampling tinggi, tetapi probabilistic/HMM-based methods lebih robust untuk data noisy atau low-frequency.

## Potensi Penempatan di Skripsi

- **Bab II / Landasan Teori:** definisi trajectory preprocessing, cleaning, segmentation, map matching.
- **Bab III / Metodologi:** justifikasi pipeline preprocessing data GPS sebelum OD matrix, density, catchment, dan turning movement.
- **Bab III / Map Matching:** pembenaran penggunaan jaringan jalan OSM dan pentingnya representasi topologi jalan.
- **Bab IV / Validasi:** mendukung perlunya visual validation dan pemeriksaan kualitas hasil matching.

## Catatan Kritis

- Artikel ini adalah review umum, bukan studi kasus RRU/Yogyakarta.
- Tidak memberikan parameter langsung untuk threshold speed, buffer GPS, atau metode spesifik yang harus dipakai.
- Beberapa bagian bersifat sangat luas; gunakan sebagai landasan teori/pembenaran metodologis, bukan sebagai sumber parameter numerik utama.
- Karena terbit 2025, cocok untuk menyatakan perkembangan terbaru, tetapi tetap perlu dipadukan dengan referensi klasik map matching seperti Newson & Krumm (HMM) jika metode matching dibahas mendalam.
