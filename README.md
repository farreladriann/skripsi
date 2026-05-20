# Skripsi — Analisis Spatiotemporal Mobilitas GPS pada Jalan Ring Road Utara Yogyakarta

Repository ini berisi kode, konfigurasi, dokumen, dan artefak pendukung untuk analisis mobilitas GPS/MPD pada koridor Jalan Ring Road Utara (RRU) Yogyakarta.

## Struktur repository

```text
skripsi/
├── src/                         # Package Python utama (`rru`)
│   └── rru/
│       ├── preprocessing/       # BBox, outlier cleaning, transport-mode filter, map matching, segmentasi
│       ├── network/             # Pembuatan/validasi jaringan RRU
│       ├── analysis/            # OD zona, intensitas persimpangan, pola OD zona eksploratif, backbone filter
│       ├── viz/                 # Visualisasi hasil
│       └── utils.py
├── scripts/                     # Entrypoint dan utility yang dijalankan dari CLI
│   ├── run_pipeline.py          # Pipeline utama end-to-end
│   ├── network/                 # Builder/QA jaringan
│   ├── maps/                    # Pembuatan peta HTML/PNG
│   └── figures/                 # Pembuatan figure pendukung
├── data/                        # Data lokal besar; di-ignore oleh Git
│   ├── raw/                     # Data mentah
│   ├── external/                # Data eksternal/cache OSM
│   ├── interim/                 # Hasil antara
│   ├── matched/                 # Hasil map matching/labeling
│   └── processed/               # Data final/bersih
│       └── network/             # Network clean hasil kurasi QGIS
├── results/                     # Output analisis yang dapat diregenerasi
├── deliverables/                # Artefak untuk dikirim/dibaca manusia
│   ├── maps/                    # Peta review/interaktif
│   └── pdf/                     # PDF final/preview
├── thesis/                      # Manuskrip LaTeX skripsi aktif
├── notebooks/                   # Notebook eksplorasi/EDA
├── references/                  # Metadata/catatan rujukan; PDF lokal di-ignore
├── previous-thesis/             # Ringkasan skripsi/paper pembanding; PDF lokal di-ignore
├── project-description/         # Catatan desain riset, tujuan, metodologi
├── tests/                       # Test Python
└── archive/                     # Arsip lokal/scratch lama; di-ignore oleh Git
```

Catatan: folder LaTeX aktif saat ini adalah `thesis/`. Folder/template lama tidak digunakan sebagai sumber naskah utama.

## Data penting

Data besar tidak dimasukkan ke Git. `.gitignore` meng-ignore `data/`, `.venv/`, cache, arsip lokal, PDF sumber literatur/skripsi terdahulu, hasil ekstraksi teks penuh, dan artefak build LaTeX.

PDF sumber di `references/` dan `previous-thesis/` disimpan lokal saja. Yang boleh masuk Git adalah catatan/metadata yang ringan seperti `.md`, `.json`, `.bib`, `.csv`, dan ringkasan pembacaan (`*.reading.md`). Hal ini mencegah naskah skripsi/paper pihak lain ikut ter-upload ke GitHub.

Network hasil kurasi QGIS yang dipakai sebagai rujukan manual/final disimpan di:

```text
data/processed/network/rru_backbone_clean.geojson
data/processed/network/rru_with_intersection_clean.geojson
```

Duplikat lama mungkin masih ada di `data/external/` atau `data/processed/` untuk kompatibilitas script lama. Untuk pengembangan berikutnya, gunakan lokasi `data/processed/network/` sebagai sumber authoritative.

## Setup environment

Repository ini memakai Python 3.13 dan `uv`.

```bash
uv sync
```

Jika memakai virtualenv yang sudah ada:

```bash
source .venv/bin/activate
```

## Menjalankan pipeline utama

Dari root repository:

```bash
uv run python scripts/run_pipeline.py
```

Atau dengan venv lokal:

```bash
.venv/bin/python scripts/run_pipeline.py
```

## Script pendukung

Network:

```bash
.venv/bin/python scripts/network/build_backbone_network.py
.venv/bin/python scripts/network/build_network_variants.py
.venv/bin/python scripts/network/qa_network_selection.py
```

Maps:

```bash
.venv/bin/python scripts/maps/make_rru_with_intersections_buffer_map.py
.venv/bin/python scripts/maps/make_rru_with_intersections_one_way_true_buffer_map.py
.venv/bin/python scripts/maps/make_sleman_major_roads_map.py
```

Figures:

```bash
.venv/bin/python scripts/figures/plot_interping.py
```

## Output utama

- Hasil analisis: `results/`
- Peta dan review manual: `deliverables/maps/`
- PDF deliverable: `deliverables/pdf/`
- Manuskrip LaTeX: `thesis/main.tex`
- PDF LaTeX terkini: `thesis/main.pdf`

## Konvensi kerja

1. Data mentah tetap di `data/raw/` dan tidak diedit langsung.
2. Hasil antara yang dapat diregenerasi masuk ke `data/interim/`, `data/matched/`, atau `results/`.
3. Data hasil kurasi manual/final masuk ke `data/processed/`, khusus network ke `data/processed/network/`.
4. Script CLI yang reusable masuk ke `scripts/`; logika utama tetap di `src/rru/`.
5. Notebook hanya untuk eksplorasi. Alur final harus bisa dijalankan via script/pipeline.
6. File scratch/eksperimen lama masuk ke `archive/`, bukan root atau folder pipeline utama. `archive/` bersifat lokal dan tidak di-upload ke GitHub.
7. PDF referensi/skripsi terdahulu tidak di-track. Simpan file PDF lokal, lalu catat hasil bacaan di `.md`/`.reading.md` agar tetap aman untuk GitHub.
