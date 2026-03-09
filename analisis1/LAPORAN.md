# Laporan Analisis 1: Power-Law & Levy Flight
## Data: GPS Mobilitas DIY (Oktober 2021 - Juni 2022)

### Tujuan
Mendiagnosis apakah distribusi jarak lompatan pengguna mengikuti pola Fat Tailed (Levy Flight) atau Thin Tailed.

### Metodologi
- Menghitung jarak Haversine antar titik GPS berurutan per pengguna (DuckDB window functions)
- Filter noise (<0.1 km) dan teleportasi (>1000 km/jam)
- Regresi linear pada histogram log-log untuk estimasi eksponen alpha
- alpha < 1.0: SUPER FAT | 1.0 <= alpha <= 2.0: FAT TAILED | alpha > 2.0: Thin Tailed

### Hasil Per Bulan

| Bulan | Total Baris | Pergerakan Valid | Alpha | R2 | Diagnosis |
|-------|-------------|------------------|-------|----|-----------|
| 2021_10_Oktober | 12,123,709 | 374,528 | 2.89 | 0.759 | Thin Tailed (Aman) |
| 2021_11_November | 119,072,431 | 2,833,783 | 3.20 | 0.769 | Thin Tailed (Aman) |
| 2021_12_Desember | 45,950,349 | 2,842,159 | 2.92 | 0.734 | Thin Tailed (Aman) |
| 2022_01_Januari | 22,488,993 | 2,526,862 | 3.08 | 0.759 | Thin Tailed (Aman) |
| 2022_02_Februari | 39,601,777 | 3,342,075 | 3.04 | 0.789 | Thin Tailed (Aman) |
| 2022_03_Maret | 26,837,642 | 551,544 | 3.06 | 0.775 | Thin Tailed (Aman) |
| 2022_04_April | 1,048,571 | 115,104 | 2.65 | 0.799 | Thin Tailed (Aman) |
| 2022_05_Mei | 31,075,618 | 2,779,346 | 2.98 | 0.781 | Thin Tailed (Aman) |
| 2022_06_Juni | 12,246,261 | 918,931 | 3.05 | 0.795 | Thin Tailed (Aman) |

### Hasil Keseluruhan

- **Total jump lengths gabungan**: 16,284,332
- **Alpha keseluruhan**: 3.54
- **R2**: 0.722
- **Diagnosis**: Thin Tailed (Aman)

### Interpretasi Hasil

- Seluruh bulan menghasilkan nilai alpha di atas 2, sehingga distribusi jarak lompatan cenderung **thin tailed**. Ini menunjukkan pergerakan ekstrem jarak jauh relatif jarang dibandingkan pergerakan jarak pendek hingga menengah.
- Nilai alpha tertinggi muncul pada **November 2021 (3.20)**, yang menandakan pola lompatan paling terkonsentrasi pada jarak pendek. Nilai terendah muncul pada **April 2022 (2.65)**, namun tetap berada pada rezim thin tailed.
- Jumlah pergerakan valid paling besar terdapat pada **Februari 2022 (3,34 juta)**, sedangkan yang paling kecil pada **April 2022 (115 ribu)**. Artinya, kekuatan inferensi per bulan juga dipengaruhi oleh banyaknya transisi yang lolos filter.
- Nilai $R^2$ yang berada di kisaran 0,73 sampai 0,80 menunjukkan pendekatan power-law log-log cukup informatif, tetapi tidak berarti seluruh mobilitas benar-benar mengikuti hukum pangkat sempurna.
- Dalam konteks skripsi, hasil ini penting karena memberi indikasi bahwa mobilitas GPS di DIY lebih banyak dibentuk oleh rutinitas lokal dan regional, bukan didominasi perjalanan sangat jauh yang sporadis.

### Kesimpulan

- Pola jarak perpindahan di DIY selama Oktober 2021 sampai Juni 2022 secara konsisten bersifat **thin tailed**.
- Mobilitas masyarakat lebih banyak terjadi pada rentang perpindahan pendek hingga menengah, sehingga struktur pergerakan terlihat relatif terkendali dan tidak didominasi lompatan ekstrem.
- Analisis ini melengkapi studi spatiotemporal karena memberi dasar statistik tentang karakter dasar perpindahan sebelum dibahas lebih jauh lewat hotspot, OD, atau regularitas mobilitas.

### Visualisasi
- Plot per bulan: `output_plots/{bulan}/`
- Plot keseluruhan: `output_plots/Keseluruhan/`

*Waktu eksekusi: 72.5 detik*
