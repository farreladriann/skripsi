# Ringkasan Pembacaan — From GPS to Maps: Path Reconstruction Techniques for Understanding People Mobility with Low-Sampling-Rate Data

## Identitas dokumen
- **Jenis**: paper konferensi IEEE ICICyTA 2023.
- **Topik utama**: rekonstruksi lintasan dari data GPS berfrekuensi rendah.
- **Kata kunci kerja**: low-sampling-rate GPS, KD-Tree, map matching, road network graph, immobility filter, path reconstruction, time interpolation.

## Inti penelitian
Paper ini membahas cara merekonstruksi jalur perjalanan dari data GPS yang interval pencuplikan waktunya rendah/tidak rapat. Data seperti ini tidak selalu menangkap detail lintasan aktual, sehingga diperlukan proses preprocessing, pencocokan ke jaringan jalan, dan rekonstruksi jalur antar titik.

## Alur metodologi yang dibaca
Tahapan utama yang muncul dalam teks:
1. **Preprocessing data GPS**
   - pemilihan kolom relevan seperti `maid`, latitude, longitude, timestamp;
   - penghapusan duplikasi;
   - konversi timestamp ke format datetime;
   - pengurutan data.
2. **Pengolahan jaringan jalan**
   - jaringan jalan direpresentasikan sebagai graph;
   - titik/ruas jalan menjadi node/edge untuk mendukung pencarian jalur.
3. **Map matching dengan KD-Tree**
   - titik GPS disejajarkan dengan ruas/titik jaringan jalan terdekat.
4. **Immobility filtering**
   - titik yang menunjukkan kondisi diam berulang dikompresi/dikurangi agar tidak membebani komputasi.
5. **Path reconstruction**
   - jalur antar titik yang telah disejajarkan diperkirakan menggunakan shortest path/A*.
6. **Time interpolation**
   - timestamp untuk titik tambahan hasil rekonstruksi diperkirakan dari selisih waktu antar titik asli.

## Temuan/kontribusi penting
- Data GPS low-sampling-rate tetap dapat digunakan untuk memahami mobilitas jika diberi preprocessing dan rekonstruksi lintasan yang tepat.
- Masalah utama low-sampling-rate adalah ketidakpastian jalur di antara dua titik observasi.
- Pendekatan graph + map matching + interpolasi waktu membantu membuat lintasan lebih masuk akal untuk analisis mobilitas.

## Relevansi untuk skripsi RRU
- Menguatkan bahwa Active MPD/GPS yang sparse perlu diproses hati-hati sebelum dianalisis.
- Memberi dasar literatur untuk tahapan: hapus duplikasi, konversi waktu, urutkan per MAID, filter titik diam, dan seleksi terhadap jaringan jalan.
- Menjadi rujukan bahwa rekonstruksi jalur penuh membutuhkan langkah tambahan seperti graph shortest path dan interpolasi waktu.
- Untuk skripsi RRU yang dibuat lebih sederhana, paper ini justru membantu menegaskan batasan: skripsi tidak perlu mengklaim path reconstruction penuh jika tidak menjalankan alur lengkap tersebut.

## Implikasi metodologis untuk RRU
- RRU sebaiknya memakai istilah **seleksi titik koridor / identifikasi zona pertama-terakhir yang teramati**, bukan “rekonstruksi rute aktual”.
- Jika ada pembahasan keterbatasan, sebutkan bahwa low-sampling-rate membatasi akurasi lintasan di antara dua titik GPS.
- Analisis OD zona berbasis persimpangan pertama/terakhir lebih sederhana dan robust dibanding mencoba menebak semua ruas yang dilewati.

## Keterbatasan jika dijadikan rujukan
- Paper ini fokus pada path reconstruction, sedangkan skripsi RRU fokus pada baseline koridor dan OD zona.
- Tanpa ground truth lintasan RRU, metode RRU tidak boleh mengklaim validitas lintasan aktual seperti studi path reconstruction.
