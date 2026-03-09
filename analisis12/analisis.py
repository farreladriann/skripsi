"""
Analisis 12: Hotspot Persistence & Turnover
============================================
Menganalisis kestabilan hotspot antarbulan untuk membedakan pusat aktivitas
yang persisten dan hotspot yang temporer.
"""

import os
import time

import duckdb
import matplotlib
matplotlib.use('Agg')
import matplotlib.colors as mcolors
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_ROOT = os.path.join(BASE_DIR, '..', 'DataGPS_parquet')
OUTPUT_BASE = os.path.join(BASE_DIR, 'output_plots')
SUMMARY_FILE = os.path.join(BASE_DIR, 'hasil_hotspot_persistence_summary.csv')

DATA_FILES = [
    ('2021_10_Oktober', '2021_10_Oktober.parquet'),
    ('2021_11_November', '2021_11_November.parquet'),
    ('2021_12_Desember', '2021_12_Desember.parquet'),
    ('2022_01_Januari', '2022_01_Januari.parquet'),
    ('2022_02_Februari', '2022_02_Februari.parquet'),
    ('2022_03_Maret', '2022_03_Maret.parquet'),
    ('2022_04_April', '2022_04_April.parquet'),
    ('2022_05_Mei', '2022_05_Mei.parquet'),
    ('2022_06_Juni', '2022_06_Juni.parquet'),
]

LAT_MIN, LAT_MAX = -8.2, -7.55
LON_MIN, LON_MAX = 110.0, 110.85
GRID_RES = 0.01
HOTSPOT_QUANTILE = 0.98
PERSISTENT_MONTHS = 5

sns.set_theme(style='whitegrid', font_scale=1.0)
plt.rcParams['figure.dpi'] = 150


def get_con():
    con = duckdb.connect()
    tmp = os.path.join(BASE_DIR, '..', '.duckdb_tmp')
    os.makedirs(tmp, exist_ok=True)
    con.execute(f"SET temp_directory='{tmp}'")
    con.execute("SET memory_limit='4GB'")
    con.execute("SET preserve_insertion_order=false")
    con.execute("SET threads=4")
    return con


def process_hotspots(con, month_name, parquet_file, out_dir):
    fpath = os.path.join(DATA_ROOT, parquet_file)
    if not os.path.exists(fpath):
        return None

    grid_counts = con.execute(f"""
        SELECT ROUND(latitude / {GRID_RES}) * {GRID_RES} AS lat_grid,
               ROUND(longitude / {GRID_RES}) * {GRID_RES} AS lon_grid,
               COUNT(*) AS count
        FROM read_parquet('{fpath}')
        WHERE latitude BETWEEN {LAT_MIN} AND {LAT_MAX}
          AND longitude BETWEEN {LON_MIN} AND {LON_MAX}
        GROUP BY lat_grid, lon_grid
        ORDER BY count DESC
    """).fetchdf()

    if len(grid_counts) == 0:
        return None

    grid_counts['cell_id'] = grid_counts['lat_grid'].map(lambda x: f'{x:.2f}') + ',' + grid_counts['lon_grid'].map(lambda x: f'{x:.2f}')
    threshold = float(grid_counts['count'].quantile(HOTSPOT_QUANTILE))
    hotspots = grid_counts[grid_counts['count'] >= threshold].copy().sort_values('count', ascending=False)
    if len(hotspots) < 10:
        hotspots = grid_counts.nlargest(min(10, len(grid_counts)), 'count').copy()

    os.makedirs(out_dir, exist_ok=True)

    fig, ax = plt.subplots(figsize=(11, 9))
    ax.scatter(grid_counts['lon_grid'], grid_counts['lat_grid'], s=3, c='lightgray', alpha=0.22)
    sc = ax.scatter(
        hotspots['lon_grid'],
        hotspots['lat_grid'],
        s=np.clip(hotspots['count'] / hotspots['count'].max() * 240, 30, 240),
        c=hotspots['count'],
        cmap='YlOrRd',
        alpha=0.85,
        edgecolors='black',
        linewidths=0.3,
    )
    fig.colorbar(sc, ax=ax, label='Jumlah points hotspot')
    ax.set_xlim(LON_MIN, LON_MAX)
    ax.set_ylim(LAT_MIN, LAT_MAX)
    ax.set_aspect('equal')
    ax.set_title(f'Hotspot Persentil Tinggi - {month_name}', fontsize=13, fontweight='bold')
    ax.set_xlabel('Longitude')
    ax.set_ylabel('Latitude')
    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, 'hotspot_map.png'), bbox_inches='tight')
    plt.close()

    top10 = hotspots.head(10)
    fig, ax = plt.subplots(figsize=(10, 5))
    bars = ax.barh(range(len(top10)), top10['count'], color=plt.cm.YlOrRd(np.linspace(0.35, 0.9, len(top10))))
    ax.set_yticks(range(len(top10)))
    ax.set_yticklabels(top10['cell_id'])
    ax.set_xlabel('Jumlah points')
    ax.set_title(f'Top 10 Hotspot - {month_name}', fontsize=13, fontweight='bold')
    ax.invert_yaxis()
    for bar, value in zip(bars, top10['count']):
        ax.text(bar.get_width() + top10['count'].max() * 0.01, bar.get_y() + bar.get_height() / 2, f'{int(value):,}', va='center', fontsize=8)
    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, 'top10_hotspot.png'), bbox_inches='tight')
    plt.close()

    result = {
        'Bulan': month_name,
        'Grid_Cells': len(grid_counts),
        'Hotspot_Cells': len(hotspots),
        'Threshold_Count': threshold,
        'Hotspot_Point_Share': float(hotspots['count'].sum() / grid_counts['count'].sum() * 100),
    }
    return result, hotspots[['cell_id', 'lat_grid', 'lon_grid', 'count']]


def jaccard(left, right):
    union = left | right
    if not union:
        return np.nan
    return len(left & right) / len(union)


print('=' * 60)
print('ANALISIS 12: HOTSPOT PERSISTENCE & TURNOVER')
print('=' * 60)

start_time = time.time()
con = get_con()
all_results = []
all_hotspots = []
hotspot_sets = {}
prev_set = set()

for month_name, pfile in DATA_FILES:
    print(f"\n[{month_name}] Memproses...", end=' ', flush=True)
    out_dir = os.path.join(OUTPUT_BASE, month_name)
    out = process_hotspots(con, month_name, pfile, out_dir)
    if out is None:
        print('SKIP')
        continue
    result, hotspots = out
    current_set = set(hotspots['cell_id'])
    retained = len(current_set & prev_set)
    result['Prev_Jaccard'] = float(jaccard(prev_set, current_set)) if prev_set else np.nan
    result['Retained_From_Prev_Pct'] = float((retained / len(prev_set) * 100) if prev_set else np.nan)
    result['New_Hotspot_Pct'] = float(((len(current_set - prev_set) / len(current_set)) * 100) if prev_set and current_set else np.nan)
    all_results.append(result)
    all_hotspots.append(hotspots.assign(Bulan=month_name))
    hotspot_sets[month_name] = current_set
    prev_set = current_set
    prev_jaccard_text = '-' if pd.isna(result['Prev_Jaccard']) else f"{result['Prev_Jaccard']:.3f}"
    print(f"OK hotspots={result['Hotspot_Cells']} | jaccard_prev={prev_jaccard_text}")

keseluruhan_dir = os.path.join(OUTPUT_BASE, 'Keseluruhan')
os.makedirs(keseluruhan_dir, exist_ok=True)

combined_hotspots = pd.DataFrame()
if all_hotspots:
    combined_hotspots = pd.concat(all_hotspots, ignore_index=True)

if len(combined_hotspots) > 0:
    presence = combined_hotspots.groupby('cell_id').agg(
        months_active=('Bulan', 'nunique'),
        total_count=('count', 'sum'),
        lat_grid=('lat_grid', 'first'),
        lon_grid=('lon_grid', 'first'),
    ).reset_index()
    persistent_core = presence[presence['months_active'] >= PERSISTENT_MONTHS].copy()

    fig, ax = plt.subplots(figsize=(11, 9))
    sc = ax.scatter(
        presence['lon_grid'],
        presence['lat_grid'],
        c=presence['months_active'],
        s=np.clip(presence['total_count'] / presence['total_count'].max() * 220, 30, 220),
        cmap='YlOrRd',
        norm=mcolors.Normalize(vmin=1, vmax=max(presence['months_active'].max(), 2)),
        alpha=0.8,
        edgecolors='black',
        linewidths=0.25,
    )
    fig.colorbar(sc, ax=ax, label='Jumlah bulan aktif sebagai hotspot')
    ax.set_xlim(LON_MIN, LON_MAX)
    ax.set_ylim(LAT_MIN, LAT_MAX)
    ax.set_aspect('equal')
    ax.set_title('Peta Persistensi Hotspot Keseluruhan', fontsize=14, fontweight='bold')
    ax.set_xlabel('Longitude')
    ax.set_ylabel('Latitude')
    plt.tight_layout()
    plt.savefig(os.path.join(keseluruhan_dir, 'persistence_map.png'), bbox_inches='tight')
    plt.close()

    months = list(hotspot_sets.keys())
    jaccard_matrix = pd.DataFrame(index=months, columns=months, dtype=float)
    for left in months:
        for right in months:
            jaccard_matrix.loc[left, right] = jaccard(hotspot_sets[left], hotspot_sets[right])
    fig, ax = plt.subplots(figsize=(9, 7))
    sns.heatmap(jaccard_matrix, cmap='Blues', annot=True, fmt='.2f', ax=ax, vmin=0, vmax=1)
    ax.set_title('Kemiripan Hotspot Antarbulan (Jaccard)', fontsize=14, fontweight='bold')
    plt.tight_layout()
    plt.savefig(os.path.join(keseluruhan_dir, 'heatmap_jaccard.png'), bbox_inches='tight')
    plt.close()

    fig, ax = plt.subplots(figsize=(12, 6))
    hotspot_counts = [r['Hotspot_Cells'] for r in all_results]
    prev_jaccard_vals = [r['Prev_Jaccard'] for r in all_results]
    ax.bar(range(len(months)), hotspot_counts, color='#FB8C00', alpha=0.75, label='Jumlah hotspot')
    ax2 = ax.twinx()
    ax2.plot(range(len(months)), prev_jaccard_vals, 'o-', color='#1565C0', lw=2, label='Jaccard vs bulan sebelumnya')
    ax.set_xticks(range(len(months)))
    ax.set_xticklabels(months, rotation=45, ha='right')
    ax.set_ylabel('Jumlah hotspot')
    ax2.set_ylabel('Jaccard overlap')
    ax.set_title('Turnover Hotspot Antarbulan', fontsize=14, fontweight='bold')
    lines1, labels1 = ax.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax.legend(lines1 + lines2, labels1 + labels2, loc='upper left')
    plt.tight_layout()
    plt.savefig(os.path.join(keseluruhan_dir, 'tren_turnover_hotspot.png'), bbox_inches='tight')
    plt.close()

    top_persistent = presence.sort_values(['months_active', 'total_count'], ascending=[False, False]).head(12)
    fig, ax = plt.subplots(figsize=(10, 6))
    bars = ax.barh(range(len(top_persistent)), top_persistent['months_active'], color='#8E24AA')
    ax.set_yticks(range(len(top_persistent)))
    ax.set_yticklabels(top_persistent['cell_id'])
    ax.set_xlabel('Jumlah bulan aktif')
    ax.set_title('Hotspot Paling Persisten', fontsize=14, fontweight='bold')
    ax.invert_yaxis()
    for bar, count in zip(bars, top_persistent['months_active']):
        ax.text(bar.get_width() + 0.05, bar.get_y() + bar.get_height() / 2, f'{int(count)} bulan', va='center', fontsize=8)
    plt.tight_layout()
    plt.savefig(os.path.join(keseluruhan_dir, 'top_persistent_hotspots.png'), bbox_inches='tight')
    plt.close()

df_res = pd.DataFrame(all_results)
df_res.to_csv(SUMMARY_FILE, index=False)

elapsed = time.time() - start_time
with open(os.path.join(BASE_DIR, 'LAPORAN.md'), 'w', encoding='utf-8') as f:
    f.write('# Laporan Analisis 12: Hotspot Persistence & Turnover\n')
    f.write('## Data: GPS Mobilitas DIY (Oktober 2021 - Juni 2022)\n\n')
    f.write('### Tujuan\n')
    f.write('Menilai apakah hotspot aktivitas GPS bersifat stabil antarbulan atau sering berganti, sehingga dapat dibedakan pusat aktivitas inti dan hotspot temporer.\n\n')
    f.write('### Metodologi\n')
    f.write(f'- Grid spasial: {GRID_RES:.2f} derajat\n')
    f.write(f'- Hotspot bulanan = grid di atas persentil {HOTSPOT_QUANTILE:.2f} distribusi kepadatan bulanan\n')
    f.write('- Kemiripan antarbulan diukur menggunakan indeks Jaccard\n')
    f.write('- Retained hotspot = persentase hotspot bulan lalu yang tetap muncul\n')
    f.write(f'- Persistent core = hotspot yang aktif minimal {PERSISTENT_MONTHS} bulan\n\n')
    f.write('### Hasil Per Bulan\n\n')
    f.write('| Bulan | Grid Cells | Hotspot Cells | Threshold Count | Share Points di Hotspot | Jaccard vs Prev | Retained Prev | Hotspot Baru |\n')
    f.write('|-------|------------|---------------|-----------------|-------------------------|-----------------|---------------|--------------|\n')
    for r in all_results:
        prev_jaccard = '-' if pd.isna(r['Prev_Jaccard']) else f"{r['Prev_Jaccard']:.3f}"
        retained = '-' if pd.isna(r['Retained_From_Prev_Pct']) else f"{r['Retained_From_Prev_Pct']:.1f}%"
        new_share = '-' if pd.isna(r['New_Hotspot_Pct']) else f"{r['New_Hotspot_Pct']:.1f}%"
        f.write(
            f"| {r['Bulan']} | {r['Grid_Cells']:,} | {r['Hotspot_Cells']:,} | {r['Threshold_Count']:.1f} | "
            f"{r['Hotspot_Point_Share']:.2f}% | {prev_jaccard} | {retained} | {new_share} |\n"
        )
    f.write('\n### Hasil Keseluruhan\n\n')
    if len(combined_hotspots) > 0:
        max_jaccard_row = df_res.dropna(subset=['Prev_Jaccard']).sort_values('Prev_Jaccard', ascending=False).iloc[0]
        min_jaccard_row = df_res.dropna(subset=['Prev_Jaccard']).sort_values('Prev_Jaccard', ascending=True).iloc[0]
        f.write(f"- **Jumlah hotspot unik lintas semua bulan**: {presence['cell_id'].nunique():,}\n")
        f.write(f"- **Ukuran persistent core**: {len(persistent_core):,} sel hotspot\n")
        f.write(f"- **Overlap tertinggi dengan bulan sebelumnya**: {max_jaccard_row['Bulan']} ({max_jaccard_row['Prev_Jaccard']:.3f})\n")
        f.write(f"- **Overlap terendah dengan bulan sebelumnya**: {min_jaccard_row['Bulan']} ({min_jaccard_row['Prev_Jaccard']:.3f})\n")
    f.write('\n### Kesimpulan\n\n')
    if len(combined_hotspots) > 0:
        f.write('- Tidak semua hotspot memiliki sifat yang sama. Sebagian sel muncul berulang kali dan membentuk inti aktivitas spasial, sementara sebagian lain hanya muncul sesaat mengikuti dinamika bulanan.\n')
        f.write('- Nilai Jaccard yang tinggi menandakan struktur ruang aktivitas relatif stabil, sedangkan nilai yang rendah menunjukkan turnover hotspot yang besar.\n')
        f.write('- Persistent core penting untuk mengidentifikasi pusat aktivitas yang konsisten dari waktu ke waktu, misalnya pusat kota, koridor utama, atau simpul kegiatan harian.\n')
        f.write('- Analisis ini memperkaya skripsi karena tidak hanya memetakan hotspot per bulan, tetapi juga menjelaskan kontinuitas dan perubahan spasial antarperiode.\n')
    f.write('\n### Visualisasi\n')
    f.write('- Plot per bulan: `output_plots/{bulan}/`\n')
    f.write('- Plot keseluruhan: `output_plots/Keseluruhan/`\n\n')
    f.write(f'*Waktu eksekusi: {elapsed:.1f} detik*\n')

con.close()
print(f"\n{'=' * 60}")
print(f'ANALISIS 12 SELESAI! ({elapsed:.1f} detik)')
print(f"{'=' * 60}")