# Repo Cleanup Manifest

Tanggal: 2026-05-20

## Tujuan

Merapikan struktur `Github/skripsi` agar jalur kerja utama jelas, file besar/sumber pihak lain tidak ikut ter-upload ke GitHub, dan artefak final mudah ditemukan.

## Struktur aktif

- `thesis/` — sumber LaTeX skripsi aktif.
- `src/rru/` — package Python utama.
- `scripts/` — entrypoint CLI dan utilitas pipeline.
- `results/` — output analisis/figure/ringkasan yang dapat diregenerasi.
- `deliverables/` — artefak yang siap dikirim/dibaca manusia.
- `previous-thesis/` — ringkasan pembacaan skripsi/paper terdahulu; PDF lokal tidak di-track.
- `references/` — metadata/catatan literatur; PDF lokal tidak di-track.
- `archive/` — arsip lokal/scratch, di-ignore oleh Git.

## Perubahan cleanup

- Menambahkan aturan `.gitignore` untuk:
  - `archive/`
  - `previous-thesis/*.pdf`
  - `previous-thesis/_extracted_text/`
  - `references/*.pdf`
  - `references/**/*.pdf`
  - `results/**/*.parquet`
- Menghapus PDF sumber dari tracking Git dengan `git rm --cached`, tanpa menghapus file lokal.
- Memindahkan `thesis-dont-change/` ke `archive/local-only/thesis-dont-change/` sebagai arsip lokal.
- Memindahkan duplikat `deliverables/skripsi_rru_backbone_updated.pdf` ke `archive/duplicates/` karena salinan identik sudah ada di `deliverables/pdf/`.
- Membersihkan cache lokal seperti `__pycache__`, `.DS_Store`, file swap, dan artefak build LaTeX.

## Catatan penting

- PDF `previous-thesis/NASKAH SKRIPSI_RIZKY INTAN NURLITA.pdf` tetap ada lokal, tetapi sudah di-ignore dan tidak lagi ada di tree terbaru GitHub.
- Penghapusan dengan `git rm --cached` hanya menghapus dari Git tracking, bukan dari disk lokal.
- Jika ingin menghapus PDF dari seluruh riwayat commit GitHub, perlu proses terpisah: rewrite history / purge.

## Validasi yang harus dilakukan setelah cleanup

1. `git check-ignore` untuk memastikan PDF sumber dan ekstraksi teks penuh di-ignore.
2. Build LaTeX dari `thesis/main.tex`.
3. Cek placeholder/citation warning di PDF/log.
4. Cek `git status` agar hanya file yang memang diinginkan yang akan di-track.
