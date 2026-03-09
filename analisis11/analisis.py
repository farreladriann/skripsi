"""
Analisis 11: Daypart Spatial Shift & Urban Pulse
=================================================
Menganalisis redistribusi aktivitas GPS menurut pembagian waktu harian
untuk menangkap denyut kota dan pergeseran spasial intrahari.
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
SUMMARY_FILE = os.path.join(BASE_DIR, 'hasil_daypart_summary.csv')

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
DAYPART_ORDER = ['Dini Hari', 'Pagi', 'Siang', 'Sore', 'Malam']

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


def haversine_km(lat1, lon1, lat2, lon2):
    if any(pd.isna(v) for v in [lat1, lon1, lat2, lon2]):
        return np.nan
    radius = 6371.0
    lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = np.sin(dlat / 2.0) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2.0) ** 2
    return radius * 2.0 * np.arctan2(np.sqrt(a), np.sqrt(1.0 - a))


def process_daypart(con, month_name, parquet_file, out_dir):
    fpath = os.path.join(DATA_ROOT, parquet_file)
    if not os.path.exists(fpath):
        return None

    grid_counts = con.execute(f"""
        WITH base AS (
            SELECT CASE
                       WHEN HOUR(TO_TIMESTAMP(timestamp) + INTERVAL '7 hours') < 6 THEN 'Dini Hari'
                       WHEN HOUR(TO_TIMESTAMP(timestamp) + INTERVAL '7 hours') < 10 THEN 'Pagi'
                       WHEN HOUR(TO_TIMESTAMP(timestamp) + INTERVAL '7 hours') < 15 THEN 'Siang'
                       WHEN HOUR(TO_TIMESTAMP(timestamp) + INTERVAL '7 hours') < 19 THEN 'Sore'
                       ELSE 'Malam'
                   END AS daypart,
                   ROUND(latitude / {GRID_RES}) * {GRID_RES} AS lat_grid,
                   ROUND(longitude / {GRID_RES}) * {GRID_RES} AS lon_grid
            FROM read_parquet('{fpath}')
            WHERE latitude BETWEEN {LAT_MIN} AND {LAT_MAX}
              AND longitude BETWEEN {LON_MIN} AND {LON_MAX}
        )
        SELECT daypart, lat_grid, lon_grid, COUNT(*) AS cnt
        FROM base
        GROUP BY daypart, lat_grid, lon_grid
        ORDER BY daypart, cnt DESC
    """).fetchdf()

    if len(grid_counts) == 0:
        return None

    grid_counts['cell_id'] = grid_counts['lat_grid'].map(lambda x: f'{x:.2f}') + ',' + grid_counts['lon_grid'].map(lambda x: f'{x:.2f}')

    stats_rows = []
    for daypart in DAYPART_ORDER:
        subset = grid_counts[grid_counts['daypart'] == daypart].copy()
        if len(subset) == 0:
            stats_rows.append({
                'daypart': daypart,
                'points': 0,
                'active_cells': 0,
                'centroid_lat': np.nan,
                'centroid_lon': np.nan,
                'top_share': np.nan,
            })
            continue
        total_points = int(subset['cnt'].sum())
        centroid_lat = np.average(subset['lat_grid'], weights=subset['cnt'])
        centroid_lon = np.average(subset['lon_grid'], weights=subset['cnt'])
        top_share = float(subset['cnt'].max() / total_points)
        stats_rows.append({
            'daypart': daypart,
            'points': total_points,
            'active_cells': len(subset),
            'centroid_lat': centroid_lat,
            'centroid_lon': centroid_lon,
            'top_share': top_share,
        })

    daypart_stats = pd.DataFrame(stats_rows)
    os.makedirs(out_dir, exist_ok=True)

    fig, axes = plt.subplots(2, 1, figsize=(10, 8), sharex=True)
    colors = ['#283593', '#1565C0', '#00897B', '#FB8C00', '#8E24AA']
    axes[0].bar(daypart_stats['daypart'], daypart_stats['points'], color=colors)
    axes[0].set_title(f'Intensitas Aktivitas per Daypart - {month_name}', fontsize=13, fontweight='bold')
    axes[0].set_ylabel('Jumlah Points')
    axes[1].bar(daypart_stats['daypart'], daypart_stats['top_share'], color=colors)
    axes[1].set_ylabel('Top hotspot share')
    axes[1].set_xlabel('Daypart')
    plt.xticks(rotation=0)
    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, 'daypart_counts_dan_konsentrasi.png'), bbox_inches='tight')
    plt.close()

    fig, ax = plt.subplots(figsize=(11, 9))
    ax.scatter(grid_counts['lon_grid'], grid_counts['lat_grid'], s=2, c='lightgray', alpha=0.18)
    valid_centroids = daypart_stats.dropna(subset=['centroid_lat', 'centroid_lon']).reset_index(drop=True)
    for idx, (_, row) in enumerate(valid_centroids.iterrows()):
        ax.scatter(row['centroid_lon'], row['centroid_lat'], s=80, color=colors[idx], edgecolors='black', zorder=5)
        ax.text(row['centroid_lon'] + 0.004, row['centroid_lat'] + 0.004, row['daypart'], fontsize=9, weight='bold')
        if idx > 0:
            prev = valid_centroids.iloc[idx - 1]
            ax.annotate(
                '',
                xy=(row['centroid_lon'], row['centroid_lat']),
                xytext=(prev['centroid_lon'], prev['centroid_lat']),
                arrowprops=dict(arrowstyle='->', color='#37474F', lw=1.5),
            )
    ax.set_xlim(LON_MIN, LON_MAX)
    ax.set_ylim(LAT_MIN, LAT_MAX)
    ax.set_aspect('equal')
    ax.set_title(f'Trajektori Centroid Aktivitas Intrahari - {month_name}', fontsize=13, fontweight='bold')
    ax.set_xlabel('Longitude')
    ax.set_ylabel('Latitude')
    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, 'centroid_trajectory.png'), bbox_inches='tight')
    plt.close()

    top_cells = grid_counts.groupby('cell_id')['cnt'].sum().nlargest(12).index.tolist()
    heat_df = grid_counts[grid_counts['cell_id'].isin(top_cells)].pivot_table(
        index='daypart',
        columns='cell_id',
        values='cnt',
        fill_value=0,
    )
    heat_df = heat_df.reindex(DAYPART_ORDER, fill_value=0)
    fig, ax = plt.subplots(figsize=(12, 5))
    sns.heatmap(heat_df, cmap='YlOrRd', ax=ax, cbar_kws={'label': 'Jumlah Points'})
    ax.set_title(f'Hotspot Utama per Daypart - {month_name}', fontsize=13, fontweight='bold')
    ax.set_xlabel('Grid utama')
    ax.set_ylabel('Daypart')
    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, 'heatmap_hotspot_daypart.png'), bbox_inches='tight')
    plt.close()

    centroid_pairs = []
    for left in DAYPART_ORDER:
        for right in DAYPART_ORDER:
            if left >= right:
                continue
            row_l = daypart_stats[daypart_stats['daypart'] == left].iloc[0]
            row_r = daypart_stats[daypart_stats['daypart'] == right].iloc[0]
            centroid_pairs.append(haversine_km(row_l['centroid_lat'], row_l['centroid_lon'], row_r['centroid_lat'], row_r['centroid_lon']))

    pagi = daypart_stats[daypart_stats['daypart'] == 'Pagi'].iloc[0]
    malam = daypart_stats[daypart_stats['daypart'] == 'Malam'].iloc[0]
    dini = daypart_stats[daypart_stats['daypart'] == 'Dini Hari'].iloc[0]
    siang = daypart_stats[daypart_stats['daypart'] == 'Siang'].iloc[0]

    summary = {
        'Bulan': month_name,
        'Total_Points': int(daypart_stats['points'].sum()),
        'Dominant_Daypart': daypart_stats.sort_values('points', ascending=False).iloc[0]['daypart'],
        'Mean_Top_Share': float(daypart_stats['top_share'].fillna(0).mean()),
        'Pagi_Malam_Shift_km': float(haversine_km(pagi['centroid_lat'], pagi['centroid_lon'], malam['centroid_lat'], malam['centroid_lon'])),
        'Dini_Siang_Shift_km': float(haversine_km(dini['centroid_lat'], dini['centroid_lon'], siang['centroid_lat'], siang['centroid_lon'])),
        'Max_Centroid_Shift_km': float(np.nanmax(centroid_pairs) if centroid_pairs else 0.0),
    }

    return summary, daypart_stats.assign(Bulan=month_name)


print('=' * 60)
print('ANALISIS 11: DAYPART SPATIAL SHIFT & URBAN PULSE')
print('=' * 60)

start_time = time.time()
con = get_con()
all_results = []
all_dayparts = []

for month_name, pfile in DATA_FILES:
    print(f"\n[{month_name}] Memproses...", end=' ', flush=True)
    out_dir = os.path.join(OUTPUT_BASE, month_name)
    out = process_daypart(con, month_name, pfile, out_dir)
    if out is None:
        print('SKIP')
        continue
    result, daypart_stats = out
    all_results.append(result)
    all_dayparts.append(daypart_stats)
    print(
        f"OK dominant={result['Dominant_Daypart']} | "
        f"pagi-malam shift={result['Pagi_Malam_Shift_km']:.2f} km"
    )

keseluruhan_dir = os.path.join(OUTPUT_BASE, 'Keseluruhan')
os.makedirs(keseluruhan_dir, exist_ok=True)

combined_dayparts = pd.DataFrame()
if all_dayparts:
    combined_dayparts = pd.concat(all_dayparts, ignore_index=True)

if len(combined_dayparts) > 0:
    heat_points = combined_dayparts.pivot_table(index='Bulan', columns='daypart', values='points', fill_value=0)
    heat_points = heat_points[DAYPART_ORDER]
    fig, ax = plt.subplots(figsize=(10, 6))
    sns.heatmap(heat_points, cmap='Blues', ax=ax, cbar_kws={'label': 'Jumlah Points'})
    ax.set_title('Heatmap Intensitas Aktivitas per Bulan x Daypart', fontsize=14, fontweight='bold')
    ax.set_xlabel('Daypart')
    ax.set_ylabel('Bulan')
    plt.tight_layout()
    plt.savefig(os.path.join(keseluruhan_dir, 'heatmap_bulan_daypart.png'), bbox_inches='tight')
    plt.close()

    fig, ax = plt.subplots(figsize=(12, 6))
    months = [r['Bulan'] for r in all_results]
    pagi_malam = [r['Pagi_Malam_Shift_km'] for r in all_results]
    dini_siang = [r['Dini_Siang_Shift_km'] for r in all_results]
    max_shift = [r['Max_Centroid_Shift_km'] for r in all_results]
    ax.plot(range(len(months)), pagi_malam, 'o-', label='Pagi -> Malam', color='#1565C0', lw=2)
    ax.plot(range(len(months)), dini_siang, 'o-', label='Dini Hari -> Siang', color='#FB8C00', lw=2)
    ax.plot(range(len(months)), max_shift, 'o--', label='Maks antar-daypart', color='#6A1B9A', lw=2)
    ax.set_xticks(range(len(months)))
    ax.set_xticklabels(months, rotation=45, ha='right')
    ax.set_ylabel('Jarak centroid (km)')
    ax.set_title('Tren Pergeseran Spasial Intrahari', fontsize=14, fontweight='bold')
    ax.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(keseluruhan_dir, 'tren_shift_intrahari.png'), bbox_inches='tight')
    plt.close()

    fig, ax = plt.subplots(figsize=(12, 6))
    mean_top_share = combined_dayparts.groupby('daypart')['top_share'].mean().reindex(DAYPART_ORDER)
    ax.bar(mean_top_share.index, mean_top_share.values, color=['#283593', '#1565C0', '#00897B', '#FB8C00', '#8E24AA'])
    ax.set_ylabel('Rata-rata top hotspot share')
    ax.set_title('Rata-rata Konsentrasi Spasial per Daypart', fontsize=14, fontweight='bold')
    plt.tight_layout()
    plt.savefig(os.path.join(keseluruhan_dir, 'rata_konsentrasi_per_daypart.png'), bbox_inches='tight')
    plt.close()

df_res = pd.DataFrame(all_results)
df_res.to_csv(SUMMARY_FILE, index=False)

elapsed = time.time() - start_time
with open(os.path.join(BASE_DIR, 'LAPORAN.md'), 'w', encoding='utf-8') as f:
    f.write('# Laporan Analisis 11: Daypart Spatial Shift & Urban Pulse\n')
    f.write('## Data: GPS Mobilitas DIY (Oktober 2021 - Juni 2022)\n\n')
    f.write('### Tujuan\n')
    f.write('Mengidentifikasi bagaimana pusat aktivitas dan konsentrasi ruang berubah sepanjang hari untuk menangkap denyut spasial kota.\n\n')
    f.write('### Metodologi\n')
    f.write('- Timestamp dikonversi ke WIB (UTC+7)\n')
    f.write(f"- Grid spasial: {GRID_RES:.2f} derajat\n")
    f.write('- Daypart: Dini Hari (00-05), Pagi (06-09), Siang (10-14), Sore (15-18), Malam (19-23)\n')
    f.write('- Untuk tiap daypart dihitung intensitas titik, jumlah sel aktif, centroid berbobot, dan dominasi hotspot utama\n')
    f.write('- Pergeseran spasial diukur dengan jarak Haversine antar-centroid daypart\n\n')
    f.write('### Hasil Per Bulan\n\n')
    f.write('| Bulan | Total Points | Daypart Dominan | Mean Top Share | Pagi->Malam Shift | Dini->Siang Shift | Shift Maksimum |\n')
    f.write('|-------|--------------|-----------------|----------------|-------------------|-------------------|----------------|\n')
    for r in all_results:
        f.write(
            f"| {r['Bulan']} | {r['Total_Points']:,} | {r['Dominant_Daypart']} | {r['Mean_Top_Share']:.3f} | "
            f"{r['Pagi_Malam_Shift_km']:.2f} km | {r['Dini_Siang_Shift_km']:.2f} km | {r['Max_Centroid_Shift_km']:.2f} km |\n"
        )
    f.write('\n### Hasil Keseluruhan\n\n')
    if all_results:
        df_rank = pd.DataFrame(all_results)
        most_shift = df_rank.sort_values('Max_Centroid_Shift_km', ascending=False).iloc[0]
        least_shift = df_rank.sort_values('Max_Centroid_Shift_km', ascending=True).iloc[0]
        dominant_overall = combined_dayparts.groupby('daypart')['points'].sum().sort_values(ascending=False).index[0]
        f.write(f"- **Daypart paling dominan secara keseluruhan**: {dominant_overall}\n")
        f.write(f"- **Bulan dengan pergeseran centroid terbesar**: {most_shift['Bulan']} ({most_shift['Max_Centroid_Shift_km']:.2f} km)\n")
        f.write(f"- **Bulan dengan pergeseran centroid terkecil**: {least_shift['Bulan']} ({least_shift['Max_Centroid_Shift_km']:.2f} km)\n")
    f.write('\n### Kesimpulan\n\n')
    if all_results:
        f.write('- Aktivitas mobilitas tidak hanya berubah volumenya, tetapi juga berpindah pusat ruangnya sepanjang hari. Ini menandakan adanya ritme intrahari yang kuat pada wilayah DIY.\n')
        f.write('- Pergeseran centroid yang besar mengindikasikan perpindahan terstruktur antara zona aktivitas berbeda, misalnya dari area hunian menuju pusat kegiatan siang hari lalu kembali ke area malam.\n')
        f.write('- Top hotspot share membantu membaca apakah aktivitas pada suatu daypart terkonsentrasi pada sedikit titik atau tersebar ke banyak lokasi.\n')
        f.write('- Analisis ini penting untuk skripsi karena menghubungkan dimensi waktu dan ruang secara langsung, bukan hanya melihat jumlah aktivitas atau hotspot secara terpisah.\n')
    f.write('\n### Visualisasi\n')
    f.write('- Plot per bulan: `output_plots/{bulan}/`\n')
    f.write('- Plot keseluruhan: `output_plots/Keseluruhan/`\n\n')
    f.write(f'*Waktu eksekusi: {elapsed:.1f} detik*\n')

con.close()
print(f"\n{'=' * 60}")
print(f'ANALISIS 11 SELESAI! ({elapsed:.1f} detik)')
print(f"{'=' * 60}")