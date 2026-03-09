"""
Analisis 10: Mobility Regularity & Spatial Entropy
===================================================
Mengukur regularitas mobilitas pengguna melalui entropi spasial per bulan
dan keseluruhan menggunakan DuckDB.
"""

import os
import time

import duckdb
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_ROOT = os.path.join(BASE_DIR, '..', 'DataGPS_parquet')
OUTPUT_BASE = os.path.join(BASE_DIR, 'output_plots')
SUMMARY_FILE = os.path.join(BASE_DIR, 'hasil_entropy_summary.csv')

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
MIN_POINTS = 20
ROUTINE_THRESHOLD = 0.35
EXPLORER_THRESHOLD = 0.80
TOP1_ROUTINE_SHARE = 0.50

sns.set_theme(style='whitegrid', font_scale=1.05)
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


def process_entropy(con, month_name, parquet_file, out_dir):
    fpath = os.path.join(DATA_ROOT, parquet_file)
    if not os.path.exists(fpath):
        return None

    user_metrics = con.execute(f"""
        WITH user_visits AS (
            SELECT maid,
                   ROUND(latitude / {GRID_RES}) * {GRID_RES} AS lat_grid,
                   ROUND(longitude / {GRID_RES}) * {GRID_RES} AS lon_grid,
                   COUNT(*) AS cnt
            FROM read_parquet('{fpath}')
            WHERE latitude BETWEEN {LAT_MIN} AND {LAT_MAX}
              AND longitude BETWEEN {LON_MIN} AND {LON_MAX}
            GROUP BY maid, lat_grid, lon_grid
        ),
        user_totals AS (
            SELECT maid,
                   SUM(cnt) AS total_points,
                   COUNT(*) AS n_locations,
                   MAX(cnt) AS top1_cnt
            FROM user_visits
            GROUP BY maid
            HAVING SUM(cnt) >= {MIN_POINTS}
        ),
        user_entropy AS (
            SELECT v.maid,
                   t.total_points,
                   t.n_locations,
                   t.top1_cnt,
                   -SUM((v.cnt * 1.0 / t.total_points) * LN(v.cnt * 1.0 / t.total_points)) AS entropy
            FROM user_visits v
            JOIN user_totals t USING (maid)
            GROUP BY v.maid, t.total_points, t.n_locations, t.top1_cnt
        )
        SELECT maid,
               total_points,
               n_locations,
               entropy,
               CASE WHEN n_locations > 1 THEN entropy / LN(n_locations) ELSE 0 END AS normalized_entropy,
               top1_cnt * 1.0 / total_points AS top1_share
        FROM user_entropy
        ORDER BY maid
    """).fetchdf()

    if len(user_metrics) == 0:
        return None

    os.makedirs(out_dir, exist_ok=True)

    user_metrics['routine_flag'] = user_metrics['normalized_entropy'] < ROUTINE_THRESHOLD
    user_metrics['explorer_flag'] = user_metrics['normalized_entropy'] >= EXPLORER_THRESHOLD
    user_metrics['top1_routine_flag'] = user_metrics['top1_share'] >= TOP1_ROUTINE_SHARE

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.hist(user_metrics['normalized_entropy'], bins=40, color='#1565C0', alpha=0.75, edgecolor='white')
    ax.axvline(ROUTINE_THRESHOLD, color='#D81B60', linestyle='--', label=f'Routine < {ROUTINE_THRESHOLD:.2f}')
    ax.axvline(EXPLORER_THRESHOLD, color='#2E7D32', linestyle='--', label=f'Explorer >= {EXPLORER_THRESHOLD:.2f}')
    ax.set_title(f'Distribusi Normalized Entropy - {month_name}', fontsize=13, fontweight='bold')
    ax.set_xlabel('Normalized Entropy (0-1)')
    ax.set_ylabel('Jumlah Users')
    ax.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, 'distribusi_normalized_entropy.png'), bbox_inches='tight')
    plt.close()

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.hist(user_metrics['top1_share'], bins=40, color='#FB8C00', alpha=0.75, edgecolor='white')
    ax.axvline(TOP1_ROUTINE_SHARE, color='#6A1B9A', linestyle='--', label=f'Top-1 share >= {TOP1_ROUTINE_SHARE:.2f}')
    ax.set_title(f'Distribusi Dominasi Lokasi Utama - {month_name}', fontsize=13, fontweight='bold')
    ax.set_xlabel('Porsi kunjungan pada lokasi utama')
    ax.set_ylabel('Jumlah Users')
    ax.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, 'distribusi_top1_share.png'), bbox_inches='tight')
    plt.close()

    sample_size = min(15000, len(user_metrics))
    sample_df = user_metrics.sample(sample_size, random_state=42) if len(user_metrics) > sample_size else user_metrics
    fig, ax = plt.subplots(figsize=(10, 6))
    sc = ax.scatter(
        sample_df['n_locations'],
        sample_df['normalized_entropy'],
        c=sample_df['top1_share'],
        cmap='viridis',
        s=12,
        alpha=0.45,
    )
    ax.set_xscale('log')
    ax.set_title(f'Keragaman Lokasi vs Entropy - {month_name}', fontsize=13, fontweight='bold')
    ax.set_xlabel('Jumlah lokasi unik (log scale)')
    ax.set_ylabel('Normalized Entropy')
    fig.colorbar(sc, ax=ax, label='Top-1 Share')
    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, 'scatter_lokasi_vs_entropy.png'), bbox_inches='tight')
    plt.close()

    summary = {
        'Bulan': month_name,
        'Users_Analyzed': len(user_metrics),
        'Median_Entropy': float(user_metrics['entropy'].median()),
        'Median_Normalized_Entropy': float(user_metrics['normalized_entropy'].median()),
        'Mean_Normalized_Entropy': float(user_metrics['normalized_entropy'].mean()),
        'Median_Top1_Share': float(user_metrics['top1_share'].median()),
        'Median_Locations': float(user_metrics['n_locations'].median()),
        'Routine_Pct': float(user_metrics['routine_flag'].mean() * 100),
        'Explorer_Pct': float(user_metrics['explorer_flag'].mean() * 100),
        'Top1_Routine_Pct': float(user_metrics['top1_routine_flag'].mean() * 100),
    }

    return summary, user_metrics[['normalized_entropy', 'top1_share', 'n_locations']]


print('=' * 60)
print('ANALISIS 10: MOBILITY REGULARITY & SPATIAL ENTROPY')
print('=' * 60)

start_time = time.time()
con = get_con()
all_results = []
all_metrics = []

for month_name, pfile in DATA_FILES:
    print(f"\n[{month_name}] Memproses...", end=' ', flush=True)
    out_dir = os.path.join(OUTPUT_BASE, month_name)
    out = process_entropy(con, month_name, pfile, out_dir)
    if out is None:
        print('SKIP')
        continue
    result, metrics = out
    metrics = metrics.assign(Bulan=month_name)
    all_results.append(result)
    all_metrics.append(metrics)
    print(
        f"OK median Hn={result['Median_Normalized_Entropy']:.3f} | "
        f"routine={result['Routine_Pct']:.1f}%"
    )

keseluruhan_dir = os.path.join(OUTPUT_BASE, 'Keseluruhan')
os.makedirs(keseluruhan_dir, exist_ok=True)

combined_metrics = pd.DataFrame()
if all_metrics:
    combined_metrics = pd.concat(all_metrics, ignore_index=True)

if len(combined_metrics) > 0:
    fig, axes = plt.subplots(2, 1, figsize=(12, 9), sharex=True)
    months = [r['Bulan'] for r in all_results]
    med_entropy = [r['Median_Normalized_Entropy'] for r in all_results]
    med_top1 = [r['Median_Top1_Share'] for r in all_results]
    axes[0].plot(range(len(months)), med_entropy, 'o-', color='#1565C0', lw=2)
    axes[0].axhline(ROUTINE_THRESHOLD, color='#D81B60', linestyle='--', alpha=0.7)
    axes[0].axhline(EXPLORER_THRESHOLD, color='#2E7D32', linestyle='--', alpha=0.7)
    axes[0].set_ylabel('Median Normalized Entropy')
    axes[0].set_title('Tren Regularitas Mobilitas per Bulan', fontsize=14, fontweight='bold')
    axes[1].plot(range(len(months)), med_top1, 'o-', color='#FB8C00', lw=2)
    axes[1].axhline(TOP1_ROUTINE_SHARE, color='#6A1B9A', linestyle='--', alpha=0.7)
    axes[1].set_ylabel('Median Top-1 Share')
    axes[1].set_xticks(range(len(months)))
    axes[1].set_xticklabels(months, rotation=45, ha='right')
    plt.tight_layout()
    plt.savefig(os.path.join(keseluruhan_dir, 'tren_entropy_dan_top1.png'), bbox_inches='tight')
    plt.close()

    fig, ax = plt.subplots(figsize=(12, 6))
    sns.boxplot(data=combined_metrics, x='Bulan', y='normalized_entropy', ax=ax, color='#90CAF9', showfliers=False)
    ax.axhline(ROUTINE_THRESHOLD, color='#D81B60', linestyle='--', alpha=0.7)
    ax.axhline(EXPLORER_THRESHOLD, color='#2E7D32', linestyle='--', alpha=0.7)
    ax.set_title('Sebaran Normalized Entropy per Bulan', fontsize=14, fontweight='bold')
    ax.set_xlabel('Bulan')
    ax.set_ylabel('Normalized Entropy')
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    plt.savefig(os.path.join(keseluruhan_dir, 'boxplot_entropy_per_bulan.png'), bbox_inches='tight')
    plt.close()

    fig, ax = plt.subplots(figsize=(12, 6))
    routine_vals = [r['Routine_Pct'] for r in all_results]
    explorer_vals = [r['Explorer_Pct'] for r in all_results]
    intermediate_vals = [max(0.0, 100.0 - rt - ex) for rt, ex in zip(routine_vals, explorer_vals)]
    ax.bar(range(len(months)), routine_vals, label='Routine', color='#D81B60')
    ax.bar(range(len(months)), intermediate_vals, bottom=routine_vals, label='Menengah', color='#90CAF9')
    ax.bar(
        range(len(months)),
        explorer_vals,
        bottom=np.array(routine_vals) + np.array(intermediate_vals),
        label='Explorer',
        color='#2E7D32',
    )
    ax.set_xticks(range(len(months)))
    ax.set_xticklabels(months, rotation=45, ha='right')
    ax.set_ylabel('Persentase Users')
    ax.set_title('Komposisi Routine vs Explorer per Bulan', fontsize=14, fontweight='bold')
    ax.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(keseluruhan_dir, 'komposisi_routine_explorer.png'), bbox_inches='tight')
    plt.close()

df_res = pd.DataFrame(all_results)
df_res.to_csv(SUMMARY_FILE, index=False)

elapsed = time.time() - start_time
with open(os.path.join(BASE_DIR, 'LAPORAN.md'), 'w', encoding='utf-8') as f:
    f.write('# Laporan Analisis 10: Mobility Regularity & Spatial Entropy\n')
    f.write('## Data: GPS Mobilitas DIY (Oktober 2021 - Juni 2022)\n\n')
    f.write('### Tujuan\n')
    f.write('Mengukur seberapa rutin atau eksploratif perilaku mobilitas pengguna dari distribusi kunjungan spasial pada grid lokasi.\n\n')
    f.write('### Metodologi\n')
    f.write(f'- Grid spasial: {GRID_RES:.2f} derajat (sekitar 1 km)\n')
    f.write(f'- Minimal {MIN_POINTS} titik GPS per user agar pola mobilitas cukup stabil\n')
    f.write('- Entropy spasial dihitung dari proporsi kunjungan user ke setiap grid\n')
    f.write('- Normalized entropy = entropy / ln(jumlah lokasi unik), bernilai 0 sampai 1\n')
    f.write(f'- User rutin: normalized entropy < {ROUTINE_THRESHOLD:.2f}\n')
    f.write(f'- User eksploratif: normalized entropy >= {EXPLORER_THRESHOLD:.2f}\n')
    f.write(f'- Top-1 share digunakan untuk melihat dominasi satu lokasi utama (ambang {TOP1_ROUTINE_SHARE:.2f})\n\n')
    f.write('### Hasil Per Bulan\n\n')
    f.write('| Bulan | Users Dianalisis | Median Hn | Mean Hn | Median Top-1 Share | Median Lokasi | Routine | Explorer | Dominan 1 Lokasi |\n')
    f.write('|-------|------------------|-----------|---------|--------------------|---------------|---------|----------|------------------|\n')
    for r in all_results:
        f.write(
            f"| {r['Bulan']} | {r['Users_Analyzed']:,} | {r['Median_Normalized_Entropy']:.3f} | "
            f"{r['Mean_Normalized_Entropy']:.3f} | {r['Median_Top1_Share']:.3f} | {r['Median_Locations']:.0f} | "
            f"{r['Routine_Pct']:.1f}% | {r['Explorer_Pct']:.1f}% | {r['Top1_Routine_Pct']:.1f}% |\n"
        )
    f.write('\n### Hasil Keseluruhan\n\n')
    if len(combined_metrics) > 0:
        f.write(f"- **Total user-month dianalisis**: {len(combined_metrics):,}\n")
        f.write(f"- **Median normalized entropy keseluruhan**: {combined_metrics['normalized_entropy'].median():.3f}\n")
        f.write(f"- **Median top-1 share keseluruhan**: {combined_metrics['top1_share'].median():.3f}\n")
        f.write(f"- **Median jumlah lokasi unik**: {combined_metrics['n_locations'].median():.0f}\n")
    f.write('\n### Kesimpulan\n\n')
    if all_results:
        df_rank = pd.DataFrame(all_results)
        most_routine = df_rank.sort_values(['Median_Normalized_Entropy', 'Median_Top1_Share'], ascending=[True, False]).iloc[0]
        most_explorative = df_rank.sort_values(['Median_Normalized_Entropy', 'Explorer_Pct'], ascending=[False, False]).iloc[0]
        f.write(
            f"- Mobilitas paling rutin muncul pada **{most_routine['Bulan']}**, ditandai median normalized entropy {most_routine['Median_Normalized_Entropy']:.3f} dan top-1 share {most_routine['Median_Top1_Share']:.3f}.\n"
        )
        f.write(
            f"- Mobilitas paling eksploratif muncul pada **{most_explorative['Bulan']}**, dengan median normalized entropy {most_explorative['Median_Normalized_Entropy']:.3f} dan persentase explorer {most_explorative['Explorer_Pct']:.1f}%.\n"
        )
        f.write('- Secara umum, entropy yang tidak terlalu tinggi bersama top-1 share yang besar menunjukkan banyak pengguna masih bertumpu pada sedikit lokasi inti, seperti rumah, area kerja, atau koridor aktivitas rutin.\n')
        f.write('- Analisis ini penting untuk skripsi karena menjelaskan tidak hanya seberapa jauh orang bergerak, tetapi juga seberapa stabil pola ruang yang mereka ulang dari waktu ke waktu.\n')
    f.write('\n### Visualisasi\n')
    f.write('- Plot per bulan: `output_plots/{bulan}/`\n')
    f.write('- Plot keseluruhan: `output_plots/Keseluruhan/`\n\n')
    f.write(f'*Waktu eksekusi: {elapsed:.1f} detik*\n')

con.close()
print(f"\n{'=' * 60}")
print(f'ANALISIS 10 SELESAI! ({elapsed:.1f} detik)')
print(f"{'=' * 60}")