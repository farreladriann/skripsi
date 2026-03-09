"""
Analisis 3: Spatial Hotspot & Density Clustering
==================================================
Identifikasi hotspot per bulan dan keseluruhan (DuckDB engine).
"""

import duckdb
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import pandas as pd
import os
import time

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_ROOT = os.path.join(BASE_DIR, '..', 'DataGPS_parquet')
OUTPUT_BASE = os.path.join(BASE_DIR, 'output_plots')
SUMMARY_FILE = os.path.join(BASE_DIR, 'hasil_hotspot_summary.csv')

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
GRID_RES = 0.005
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


def process_hotspot(con, month_name, parquet_file, out_dir):
    fpath = os.path.join(DATA_ROOT, parquet_file)
    if not os.path.exists(fpath):
        return None

    total = con.execute(f"""
        SELECT COUNT(*) FROM read_parquet('{fpath}')
        WHERE latitude BETWEEN {LAT_MIN} AND {LAT_MAX}
          AND longitude BETWEEN {LON_MIN} AND {LON_MAX}
    """).fetchone()[0]
    if total == 0:
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

    os.makedirs(out_dir, exist_ok=True)

    # 1. Density scatter (using grid counts instead of raw hexbin)
    fig, ax = plt.subplots(figsize=(12, 10))
    sc = ax.scatter(grid_counts['lon_grid'], grid_counts['lat_grid'],
                    c=grid_counts['count'], s=2, cmap='YlOrRd',
                    norm=mcolors.LogNorm(vmin=1, vmax=grid_counts['count'].max()), alpha=0.7)
    fig.colorbar(sc, ax=ax, label='Data Points (log)')
    ax.set_title(f'Density Map GPS - {month_name}', fontsize=13, fontweight='bold')
    ax.set_xlabel('Longitude'); ax.set_ylabel('Latitude')
    ax.set_xlim(LON_MIN, LON_MAX); ax.set_ylim(LAT_MIN, LAT_MAX); ax.set_aspect('equal')
    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, 'density_map.png'), bbox_inches='tight'); plt.close()

    # 2. Hotspots (95th percentile)
    threshold = grid_counts['count'].quantile(0.95)
    hotspots = grid_counts[grid_counts['count'] >= threshold].copy()
    n_hotspots = len(hotspots)

    fig, ax = plt.subplots(figsize=(12, 10))
    ax.scatter(grid_counts['lon_grid'], grid_counts['lat_grid'], s=0.3, c='lightgray', alpha=0.3)
    sc = ax.scatter(hotspots['lon_grid'], hotspots['lat_grid'], s=hotspots['count']*2,
                    c=hotspots['count'], cmap='YlOrRd', alpha=0.7, edgecolors='black', lw=0.3)
    fig.colorbar(sc, ax=ax, label='Data Points per Grid')
    ax.set_title(f'Hotspots ({n_hotspots} lokasi) - {month_name}', fontsize=13, fontweight='bold')
    ax.set_xlabel('Longitude'); ax.set_ylabel('Latitude')
    ax.set_xlim(LON_MIN, LON_MAX); ax.set_ylim(LAT_MIN, LAT_MAX); ax.set_aspect('equal')
    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, 'spatial_hotspots.png'), bbox_inches='tight'); plt.close()

    # 3. Top 10
    top10 = hotspots.head(10)
    fig, ax = plt.subplots(figsize=(12, 6))
    bars = ax.barh(range(len(top10)), top10['count'],
                   color=plt.cm.YlOrRd(np.linspace(0.3, 0.9, len(top10))))
    ax.set_yticks(range(len(top10)))
    ax.set_yticklabels([f"({lat:.3f}, {lon:.3f})" for lat, lon in zip(top10['lat_grid'], top10['lon_grid'])])
    ax.set_xlabel('Jumlah Data Points')
    ax.set_title(f'Top 10 Lokasi Terpadat - {month_name}', fontsize=13, fontweight='bold')
    ax.invert_yaxis()
    for bar, val in zip(bars, top10['count']):
        ax.text(bar.get_width()+max(top10['count'])*0.01, bar.get_y()+bar.get_height()/2,
                f'{val:,}', ha='left', va='center', fontsize=9, fontweight='bold')
    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, 'top10_hotspots.png'), bbox_inches='tight'); plt.close()

    top1 = top10.iloc[0]
    return {
        'Bulan': month_name, 'Total_Rows': total, 'Grid_Cells': len(grid_counts),
        'Hotspots': n_hotspots, 'Top1_Lat': top1['lat_grid'], 'Top1_Lon': top1['lon_grid'],
        'Top1_Count': top1['count'],
    }, grid_counts


print("=" * 60)
print("ANALISIS 3: SPATIAL HOTSPOT & DENSITY CLUSTERING")
print("=" * 60)

start_time = time.time()
con = get_con()
all_results = []
all_grids = []

for month_name, pfile in DATA_FILES:
    print(f"\n[{month_name}] Memproses...", end=' ', flush=True)
    out_dir = os.path.join(OUTPUT_BASE, month_name)
    out = process_hotspot(con, month_name, pfile, out_dir)
    if out is None:
        print("SKIP"); continue
    result, grid_counts = out
    all_results.append(result)
    all_grids.append((month_name, grid_counts))
    print(f"OK {result['Hotspots']} hotspots | Top: ({result['Top1_Lat']:.3f}, {result['Top1_Lon']:.3f})")

keseluruhan_dir = os.path.join(OUTPUT_BASE, 'Keseluruhan')
os.makedirs(keseluruhan_dir, exist_ok=True)

if all_grids:
    combined = pd.concat([gc.assign(bulan=name) for name, gc in all_grids])
    combined_agg = combined.groupby(['lat_grid', 'lon_grid'])['count'].sum().reset_index()
    combined_agg = combined_agg.sort_values('count', ascending=False)

    fig, ax = plt.subplots(figsize=(12, 10))
    sc = ax.scatter(combined_agg['lon_grid'], combined_agg['lat_grid'],
                    s=1, c=combined_agg['count'], cmap='YlOrRd',
                    norm=mcolors.LogNorm(vmin=1, vmax=combined_agg['count'].max()), alpha=0.7)
    fig.colorbar(sc, ax=ax, label='Total Data Points (9 bulan)')
    ax.set_title('Density Map Keseluruhan - Okt 2021-Jun 2022', fontsize=14, fontweight='bold')
    ax.set_xlabel('Longitude'); ax.set_ylabel('Latitude')
    ax.set_xlim(LON_MIN, LON_MAX); ax.set_ylim(LAT_MIN, LAT_MAX); ax.set_aspect('equal')
    plt.tight_layout()
    plt.savefig(os.path.join(keseluruhan_dir, 'density_keseluruhan.png'), bbox_inches='tight'); plt.close()

    fig, ax = plt.subplots(figsize=(12, 6))
    months = [r['Bulan'] for r in all_results]
    hotspot_counts = [r['Hotspots'] for r in all_results]
    ax.bar(range(len(months)), hotspot_counts, color='#E53935', alpha=0.8)
    ax.set_xticks(range(len(months))); ax.set_xticklabels(months, rotation=45, ha='right')
    ax.set_ylabel('Jumlah Hotspot Cells')
    ax.set_title('Jumlah Hotspot per Bulan', fontsize=14, fontweight='bold')
    for i, v in enumerate(hotspot_counts):
        ax.text(i, v+max(hotspot_counts)*0.01, str(v), ha='center', fontsize=9, fontweight='bold')
    plt.tight_layout()
    plt.savefig(os.path.join(keseluruhan_dir, 'perbandingan_hotspot.png'), bbox_inches='tight'); plt.close()

    top10_all = combined_agg.head(10)
    fig, ax = plt.subplots(figsize=(12, 6))
    bars = ax.barh(range(len(top10_all)), top10_all['count'],
                   color=plt.cm.YlOrRd(np.linspace(0.3, 0.9, len(top10_all))))
    ax.set_yticks(range(len(top10_all)))
    ax.set_yticklabels([f"({lat:.3f}, {lon:.3f})" for lat, lon in
                        zip(top10_all['lat_grid'], top10_all['lon_grid'])])
    ax.set_xlabel('Total Data Points (9 Bulan)')
    ax.set_title('Top 10 Lokasi Terpadat - Keseluruhan', fontsize=14, fontweight='bold')
    ax.invert_yaxis(); plt.tight_layout()
    plt.savefig(os.path.join(keseluruhan_dir, 'top10_keseluruhan.png'), bbox_inches='tight'); plt.close()

df_res = pd.DataFrame(all_results)
df_res.to_csv(SUMMARY_FILE, index=False)

elapsed = time.time() - start_time
with open(os.path.join(BASE_DIR, 'LAPORAN.md'), 'w') as f:
    f.write("# Laporan Analisis 3: Spatial Hotspot & Density Clustering\n")
    f.write("## Data: GPS Mobilitas DIY (Oktober 2021 - Juni 2022)\n\n")
    f.write("### Tujuan\n")
    f.write("Mengidentifikasi lokasi-lokasi hotspot aktivitas GPS menggunakan grid-based clustering.\n\n")
    f.write("### Metodologi\n")
    f.write(f"- Grid resolution: {GRID_RES} deg (~500m)\n")
    f.write("- Hotspot = grid cells dengan density di atas persentil 95\n")
    f.write("- DuckDB aggregasi grid + scatter density map + top 10 bar chart\n\n")
    f.write("### Hasil Per Bulan\n\n")
    f.write("| Bulan | Total Data | Grid Cells | Hotspots | Lokasi Terpadat | Count |\n")
    f.write("|-------|-----------|------------|----------|-----------------|-------|\n")
    for r in all_results:
        f.write(f"| {r['Bulan']} | {r['Total_Rows']:,} | {r['Grid_Cells']:,} | {r['Hotspots']} | ({r['Top1_Lat']:.3f}, {r['Top1_Lon']:.3f}) | {r['Top1_Count']:,} |\n")
    f.write("\n### Hasil Keseluruhan\n\n")
    if all_results:
        total = sum(r['Total_Rows'] for r in all_results)
        f.write(f"- **Total data points (9 bulan)**: {total:,}\n")
        if all_grids:
            top = combined_agg.iloc[0]
            f.write(f"- **Lokasi terpadat**: ({top['lat_grid']:.3f}, {top['lon_grid']:.3f}) - {top['count']:,} points\n")
            f.write(f"- **Total grid cells terisi**: {len(combined_agg):,}\n")
    f.write("\n### Visualisasi\n")
    f.write("- Plot per bulan: `output_plots/{bulan}/`\n")
    f.write("- Plot keseluruhan: `output_plots/Keseluruhan/`\n\n")
    f.write(f"*Waktu eksekusi: {elapsed:.1f} detik*\n")

con.close()
print(f"\n{'='*60}")
print(f"ANALISIS 3 SELESAI! ({elapsed:.1f} detik)")
print(f"{'='*60}")
