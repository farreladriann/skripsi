# Ringkasan Pembacaan — Identification of Non-Vehicle and Vehicle Density at Intersections Based on GPS Data

## Identitas dokumen
- **Jenis**: paper konferensi IEEE ICITCOM 2024.
- **Topik utama**: identifikasi kepadatan kendaraan dan non-kendaraan di simpang Titik Nol Yogyakarta berbasis data GPS.
- **Kata kunci kerja**: GPS data, vehicle, non-vehicle, intersection, rule-based classification, density.

## Inti penelitian
Paper ini menguji apakah data GPS dari pengguna layanan telekomunikasi yang mengaktifkan lokasi dapat dipakai untuk membedakan aktivitas kendaraan dan non-kendaraan di kawasan simpang padat. Lokasi kajian adalah **Simpang/Titik Nol Yogyakarta**, dipilih karena kepadatan aktivitas, nilai historis, dan posisinya sebagai area pusat/turis.

## Data dan cakupan
- Data GPS/MPD aktif dari pengguna telekomunikasi.
- Periode data: **November 2021 sampai Januari 2022**.
- Aktivitas dibagi menjadi:
  - siang: 06.00–17.59 WIB;
  - malam: 18.00–05.59 WIB.
- Simpang dimodelkan dengan geometri dari Google Earth/KML.

## Alur metodologi yang dibaca
1. **Raw GPS** dikumpulkan untuk area Titik Nol Yogyakarta.
2. **Preprocessing** dilakukan sebelum rule-based classification, termasuk spatial join, data cleaning/filtering, dan penggabungan data lokasi dengan atribut pengguna/titik.
3. **Definisi area simpang** memakai panjang/ruang pengamatan sekitar simpang.
4. **Rule-based classification** membagi pengguna GPS menjadi vehicle dan non-vehicle.
5. **Visualisasi/komparasi** dilakukan per bulan dan siang/malam.

## Aturan klasifikasi penting
Teks paper menyebut pengguna GPS di simpang dikategorikan sebagai **non-vehicle** jika memenuhi aturan seperti:
- kecepatan antara **0,36–5 km/jam**;
- jarak sekitar **11 meter**;
- waktu tunggu **1 menit atau lebih dari 2,56 menit**.

Jika tidak memenuhi kriteria tersebut, pengguna dikategorikan sebagai vehicle.

## Hasil yang dibaca
Tabel hasil membandingkan vehicle dan non-vehicle pada November 2021–Januari 2022:
- November 2021:
  - vehicle siang 1.789, malam 1.062;
  - non-vehicle siang 2.016, malam 1.472;
  - total 5.409.
- Desember 2021:
  - vehicle siang 1.588, malam 1.064;
  - non-vehicle siang 1.390, malam 1.022;
  - total 4.405.
- Januari 2022:
  - vehicle siang 875, malam 499;
  - non-vehicle siang 880, malam 678;
  - total 2.520.

Paper mengaitkan tingginya kepadatan November 2021 dengan kegiatan/event di Yogyakarta, dan penurunan Desember–Januari dengan pembatasan mobilitas akibat pandemi COVID-19.

## Relevansi untuk skripsi RRU
- Sangat relevan untuk topik **intensitas simpang** berbasis GPS/MPD.
- Menunjukkan bahwa analisis simpang dapat dilakukan dengan geometri area simpang dan agregasi titik/pengguna GPS.
- Memberi contoh penggunaan rule-based classification berbasis kecepatan/durasi/jarak.
- Namun, skripsi RRU sebaiknya tidak mengambil klasifikasi vehicle vs non-vehicle secara langsung kecuali ada validasi/aturan yang benar-benar sesuai dengan data RRU.

## Implikasi metodologis untuk RRU
- Untuk RRU, lebih robust memakai istilah **MAID unik teramati di zona simpang** daripada “kepadatan kendaraan aktual”.
- Jika memakai intensitas simpang, hitung sebagai indikator observasi MPD: jumlah ping, MAID unik, rerata harian MAID unik, bukan volume kendaraan total.
- Paper ini mendukung analisis berbasis simpang, tetapi juga memperlihatkan bahwa klasifikasi perilaku di simpang sangat bergantung pada aturan parameter.

## Keterbatasan jika dijadikan rujukan
- Rule-based classification tampak sederhana dan sensitif terhadap ambang kecepatan, jarak, dan waktu tunggu.
- Tidak cukup untuk mengklaim volume lalu lintas aktual tanpa ground truth atau kalibrasi.
- Konteks Titik Nol berbeda dari Ring Road Utara: Titik Nol mengandung campuran pejalan kaki/turis tinggi, sedangkan RRU lebih koridor kendaraan.
