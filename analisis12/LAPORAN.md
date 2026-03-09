# Laporan Analisis 12: Hotspot Persistence & Turnover
## Data: GPS Mobilitas DIY (Oktober 2021 - Juni 2022)

### Tujuan
Menilai apakah hotspot aktivitas GPS bersifat stabil antarbulan atau sering berganti, sehingga dapat dibedakan pusat aktivitas inti dan hotspot temporer.

### Metodologi
- Grid spasial: 0.01 derajat
- Hotspot bulanan = grid di atas persentil 0.98 distribusi kepadatan bulanan
- Kemiripan antarbulan diukur menggunakan indeks Jaccard
- Retained hotspot = persentase hotspot bulan lalu yang tetap muncul
- Persistent core = hotspot yang aktif minimal 5 bulan

### Hasil Per Bulan

| Bulan | Grid Cells | Hotspot Cells | Threshold Count | Share Points di Hotspot | Jaccard vs Prev | Retained Prev | Hotspot Baru |
|-------|------------|---------------|-----------------|-------------------------|-----------------|---------------|--------------|
| 2021_10_Oktober | 2,474 | 50 | 50740.1 | 34.91% | - | - | - |
| 2021_11_November | 2,640 | 53 | 475727.8 | 36.10% | 0.689 | 84.0% | 20.8% |
| 2021_12_Desember | 2,448 | 49 | 155953.1 | 46.00% | 0.308 | 45.3% | 51.0% |
| 2022_01_Januari | 2,483 | 50 | 82774.5 | 35.74% | 0.597 | 75.5% | 26.0% |
| 2022_02_Februari | 2,527 | 51 | 152516.7 | 38.28% | 0.485 | 66.0% | 35.3% |
| 2022_03_Maret | 2,302 | 47 | 92777.8 | 48.54% | 0.441 | 58.8% | 36.2% |
| 2022_04_April | 2,005 | 41 | 4522.9 | 48.02% | 0.492 | 61.7% | 29.3% |
| 2022_05_Mei | 2,544 | 51 | 114634.9 | 48.81% | 0.394 | 63.4% | 49.0% |
| 2022_06_Juni | 2,373 | 48 | 41455.5 | 45.57% | 0.707 | 80.4% | 14.6% |

### Hasil Keseluruhan

- **Jumlah hotspot unik lintas semua bulan**: 122
- **Ukuran persistent core**: 36 sel hotspot
- **Overlap tertinggi dengan bulan sebelumnya**: 2022_06_Juni (0.707)
- **Overlap terendah dengan bulan sebelumnya**: 2021_12_Desember (0.308)

### Interpretasi Hasil

- Dari **122 hotspot unik** lintas periode, hanya **36** yang tergolong **persistent core**. Artinya, tidak semua hotspot memiliki sifat permanen; hanya sebagian yang benar-benar membentuk inti aktivitas ruang DIY.
- Nilai Jaccard antarbulan memperlihatkan tingkat kestabilan yang bervariasi. **Juni 2022** memiliki overlap tertinggi dengan bulan sebelumnya, sehingga struktur hotspot pada akhir periode terlihat lebih stabil. Sebaliknya, **Desember 2021** memiliki overlap terendah, yang menandakan adanya perombakan pola hotspot cukup besar dibanding November.
- Persentase hotspot baru per bulan berkisar dari **14,6% sampai 51,0%**. Ini menunjukkan bahwa selain ada hotspot inti yang bertahan, selalu ada bagian struktur hotspot yang bersifat temporer atau kontekstual.
- Share points yang berada pada hotspot bulanan berada di kisaran **34,9% sampai 48,8%**, sehingga proporsi aktivitas yang sangat besar memang terkonsentrasi pada sel-sel puncak. Dengan kata lain, hotspot bukan sekadar fenomena pinggiran, tetapi benar-benar menyerap bagian penting dari total aktivitas GPS.
- Bulan-bulan seperti **Maret, April, dan Mei 2022** memiliki share points di hotspot yang relatif tinggi, yang menunjukkan konsentrasi aktivitas spasial lebih tajam pada periode tersebut.
- Dalam konteks skripsi, analisis ini sangat penting karena mengubah pembahasan hotspot dari yang semula hanya deskriptif per bulan menjadi pembahasan tentang **stabilitas dan perubahan struktur ruang** antarperiode.

### Kesimpulan

- Tidak semua hotspot memiliki sifat yang sama. Sebagian sel muncul berulang kali dan membentuk inti aktivitas spasial, sementara sebagian lain hanya muncul sesaat mengikuti dinamika bulanan.
- Nilai Jaccard yang tinggi menandakan struktur ruang aktivitas relatif stabil, sedangkan nilai yang rendah menunjukkan turnover hotspot yang besar.
- Persistent core penting untuk mengidentifikasi pusat aktivitas yang konsisten dari waktu ke waktu, misalnya pusat kota, koridor utama, atau simpul kegiatan harian.
- Analisis ini memperkaya skripsi karena tidak hanya memetakan hotspot per bulan, tetapi juga menjelaskan kontinuitas dan perubahan spasial antarperiode.

### Visualisasi
- Plot per bulan: `output_plots/{bulan}/`
- Plot keseluruhan: `output_plots/Keseluruhan/`

*Waktu eksekusi: 21.0 detik*
