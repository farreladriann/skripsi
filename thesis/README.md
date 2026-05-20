# Manuskrip Skripsi

Direktori ini berisi naskah LaTeX aktif untuk skripsi:

> Analisis Baseline Spatiotemporal Perjalanan Kendaraan pada Koridor Ring Road Utara Berbasis MPD Aktif

## Struktur penting

- `main.tex`: berkas utama kompilasi.
- `contents/chapter-1` s.d. `contents/chapter-5`: isi bab utama.
- `contents/abstract`: intisari dan abstract.
- `references.bib`: daftar pustaka BibTeX.
- Gambar utama dirujuk dari `../results/figures/...`.

## Kompilasi

Jalankan dari direktori `thesis/`:

```bash
pdflatex -interaction=nonstopmode main.tex
bibtex main
pdflatex -interaction=nonstopmode main.tex
pdflatex -interaction=nonstopmode main.tex
```

Setelah kompilasi, periksa log:

```bash
grep -E 'Citation.*undefined|Reference.*undefined|LaTeX Error' main.log
```

## Catatan ruang lingkup

Naskah aktif tidak memasukkan analisis catchment area atau estimasi lokasi rumah. Analisis utama dibatasi pada OD zona persimpangan, indikator intensitas persimpangan berbasis MAID/ping, sparsitas ping per trip, dan pola OD zona eksploratif. Semua keluaran diposisikan sebagai indikator berbasis sampel MPD aktif, bukan volume lalu lintas aktual.
