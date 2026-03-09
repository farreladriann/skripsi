"""
Analisis 9: Spatial Coverage Evolution
========================================
Evolusi cakupan spasial per bulan dan keseluruhan (DuckDB engine).
"""

import duckdb
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import seaborn as sns
import pandas as pd
import os
import time

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_ROOT = os.path.join(BASE_DIR, '..', 'DataGPS_parquet')
OUTPUT_BASE = os.path.join(BASE_DIR, 'output_plots')
SUMMARY_FILE = os.path.join(BASE_DIR, 'hasil_spatial_evolution.csv')
GRID_RES = 0.01

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
TOTAL_POSSIBLE = int(((LAT_MAX - LAT_MIN) / GRID_RES) * ((LON_MAX - LON_MIN) / GRID_RES))

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


def process_coverage(con, month_name, parquet_file, out_dir):
    fpath = os.path.join(DATA_ROOT, parquet_file)
    if not os.path.exists(fpath):
        return None, None

    stats_row = con.execute(f"""
        SELECT COUNT(*) AS total,
               AVG(latitude) AS mean_lat, AVG(longitude) AS mean_lon,
               VAR_SAMP(latitude) AS var_lat, VAR_SAMP(longitude) AS var_lon
        FROM read_parquet('{fpath}')
        WHERE latitude BETWEEN {LAT_MIN} AND {LAT_MAX}
          AND longitude BETWEEN {LON_MIN} AND {LON_MAX}
    """).fetchone()
    total, mean_lat, mean_lon, var_lat, var_lon = stats_row
    if total == 0:
        return None, None

    var_lat = var_lat or 0
    var_lon = var_lon or 0
    spatial_spread = np.sqrt(var_lat + var_lon) * 111

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

    n_cells = len(grid_counts)
    coverage_pct = n_cells / TOTAL_POSSIBLE * 100

    os.makedirs(out_dir, exist_ok=True)

    fig, ax = plt.subplots(figsize=(12, 10))
    sc = ax.scatter(grid_counts['lon_grid'], grid_counts['lat_grid'],
                    c=grid_counts['count'], s=2, cmap='YlOrRd',
                    norm=mcolors.LogNorm(vmin=1, vmax=max(grid_counts['count'].max(), 2)),
                    alpha=0.7)
    fig.colorbar(sc, ax=ax, label='Data Points per Grid (~1km2)')
    ax.set_title(f'Cakupan Spasial - {month_name}\n{total:,} pts | {n_cells} cells ({coverage_pct:.1f}%)',
                 fontsize=13, fontweight='bold')
    ax.set_xlabel('Longitude'); ax.set_ylabel('Latitude')
    ax.set_xlim(LON_MIN, LON_MAX); ax.set_ylim(LAT_MIN, LAT_MAX); ax.set_aspect('equal')
    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, 'coverage_density.png'), bbox_inches='tight'); plt.close()

    result = {
        'Bulan': month_name, 'Total_Points': total, 'Grid_Cells': n_cells,
        'Coverage_Pct': coverage_pct, 'Centroid_Lat': mean_lat, 'Centroid_Lon': mean_lon,
        'Spatial_Spread_km': spatial_spread,
    }
    return result, grid_counts


print("=" * 60)
print("ANALISIS 9: SPATIAL COVERAGE EVOLUTION")
print("=" * 60)

start_time = time.time()
con = get_con()
all_results = []
all_grid_counts = {}

for month_name, pfile in DATA_FILES:
    print(f"\n[{month_name}] Memproses...", end=' ', flush=True)
    out_dir = os.path.join(OUTPUT_BASE, month_name)
    result, grid_counts = process_coverage(con, month_name, pfile, out_dir)
    if result is None:
        print("SKIP"); continue
    all_results.append(result)
    all_grid_counts[month_name] = grid_counts
    print(f"OK {result['Grid_Cells']} cells ({result['Coverage_Pct']:.1f}%)")

keseluruhan_dir = os.path.join(OUTPUT_BASE, 'Keseluruhan')
os.makedirs(keseluruhan_dir, exist_ok=True)

if all_results:
    months = [r['Bulan'] for r in all_results]
    x = range(len(months))

    # Small multiples (3x3)
    n_months = len(all_grid_counts)
    ncols = 3
    nrows = (n_months + ncols - 1) // ncols
    fig, axes = plt.subplots(nrows, ncols, figsize=(15, nrows * 4.5))
    axes_flat = axes.flatten()
    for i, (month_name, gc_df) in enumerate(all_grid_counts.items()):
        ax = axes_flat[i]
        sc = ax.scatter(gc_df['lon_grid'], gc_df['lat_grid'],
                        c=gc_df['count'], s=1, cmap='YlOrRd',
                        norm=mcolors.LogNorm(vmin=1, vmax=max(gc_df['count'].max(), 2)), alpha=0.7)
        ax.set_xlim(LON_MIN, LON_MAX); ax.set_ylim(LAT_MIN, LAT_MAX); ax.set_aspect('equal')
        info = next(r for r in all_results if r['Bulan'] == month_name)
        ax.set_title(f"{month_name}\n{info['Total_Points']:,.0f} pts | {info['Grid_Cells']} cells", fontsize=9, fontweight='bold')
        ax.tick_params(labelsize=6)
    for j in range(i + 1, len(axes_flat)):
        axes_flat[j].set_visible(False)
    fig.suptitle('Evolusi Cakupan Spasial per Bulan (Okt 2021-Jun 2022)', fontsize=14, fontweight='bold')
    plt.tight_layout()
    plt.savefig(os.path.join(keseluruhan_dir, 'small_multiples.png'), bbox_inches='tight'); plt.close()

    del all_grid_counts

    # Coverage trend
    fig, ax1 = plt.subplots(figsize=(12, 6))
    cells = [r['Grid_Cells'] for r in all_results]
    pcts = [r['Coverage_Pct'] for r in all_results]
    ax1.bar(x, cells, color='#4CAF50', alpha=0.7, label='Grid Cells')
    ax1.set_ylabel('Grid Cells (~1km2)', color='#4CAF50')
    ax1.set_xticks(x); ax1.set_xticklabels(months, rotation=45, ha='right')
    for i_val, (c, p) in enumerate(zip(cells, pcts)):
        ax1.text(i_val, c + max(cells)*0.01, f'{c}', ha='center', fontsize=8, fontweight='bold')
    ax2 = ax1.twinx()
    ax2.plot(x, pcts, 'o-', color='#FF5722', lw=2.5, ms=8, label='Coverage %')
    ax2.set_ylabel('Coverage %', color='#FF5722')
    fig.suptitle('Cakupan Spasial per Bulan', fontsize=14, fontweight='bold')
    lines1, l1 = ax1.get_legend_handles_labels()
    lines2, l2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1+lines2, l1+l2, loc='upper left')
    plt.tight_layout()
    plt.savefig(os.path.join(keseluruhan_dir, 'coverage_trend.png'), bbox_inches='tight'); plt.close()

    # Spatial spread trend
    fig, ax = plt.subplots(figsize=(12, 6))
    spreads = [r['Spatial_Spread_km'] for r in all_results]
    ax.plot(x, spreads, 'o-', color='#9C27B0', lw=2.5, ms=8)
    ax.fill_between(x, spreads, alpha=0.15, color='#9C27B0')
    ax.set_xticks(x); ax.set_xticklabels(months, rotation=45, ha='right')
    ax.set_ylabel('Spatial Spread (km)')
    ax.set_title('Tren Spatial Spread per Bulan', fontsize=14, fontweight='bold')
    for i_val, v in enumerate(spreads):
        ax.text(i_val, v+max(spreads)*0.01, f'{v:.1f}', ha='center', fontsize=9)
    plt.tight_layout()
    plt.savefig(os.path.join(keseluruhan_dir, 'spatial_spread.png'), bbox_inches='tight'); plt.close()

    # Data points per bulan
    fig, ax = plt.subplots(figsize=(12, 6))
    pts = [r['Total_Points'] for r in all_results]
    ax.bar(x, pts, color='#1976D2', alpha=0.8)
    ax.set_xticks(x); ax.set_xticklabels(months, rotation=45, ha='right')
    ax.set_ylabel('Data Points')
    ax.set_title('Data Points per Bulan', fontsize=14, fontweight='bold')
    for i_val, v in enumerate(pts):
        ax.text(i_val, v+max(pts)*0.01, f'{v:,.0f}', ha='center', fontsize=7, rotation=45)
    plt.tight_layout()
    plt.savefig(os.path.join(keseluruhan_dir, 'data_points_bulan.png'), bbox_inches='tight'); plt.close()

df_res = pd.DataFrame(all_results)
df_res.to_csv(SUMMARY_FILE, index=False)

elapsed = time.time() - start_time
with open(os.path.join(BASE_DIR, 'LAPORAN.md'), 'w') as f:
    f.write("# Laporan Analisis 9: Spatial Coverage Evolution\n")
    f.write("## Data: GPS Mobilitas DIY (Oktober 2021 - Juni 2022)\n\n")
    f.write("### Tujuan\n")
    f.write("Menganalisis evolusi cakupan spasial data GPS per bulan.\n\n")
    f.write("### Metodologi\n")
    f.write(f"- Grid resolution: {GRID_RES} deg (~1 km)\n")
    f.write(f"- Total possible grid cells: {TOTAL_POSSIBLE:,}\n")
    f.write("- DuckDB aggregasi grid untuk coverage dan spatial spread\n\n")
    f.write("### Hasil Per Bulan\n\n")
    f.write("| Bulan | Total Points | Grid Cells | Coverage % | Spread (km) |\n")
    f.write("|-------|-------------|------------|-----------|-------------|\n")
    for r in all_results:
        f.write(f"| {r['Bulan']} | {r['Total_Points']:,} | {r['Grid_Cells']:,} | {r['Coverage_Pct']:.1f}% | {r['Spatial_Spread_km']:.1f} |\n")
    f.write("\n### Hasil Keseluruhan\n\n")
    if all_results:
        total = sum(r['Total_Points'] for r in all_results)
        max_cov = max(all_results, key=lambda r: r['Coverage_Pct'])
        min_cov = min(all_results, key=lambda r: r['Coverage_Pct'])
        f.write(f"- **Total data points**: {total:,}\n")
        f.write(f"- **Coverage tertinggi**: {max_cov['Bulan']} ({max_cov['Coverage_Pct']:.1f}%)\n")
        f.write(f"- **Coverage terendah**: {min_cov['Bulan']} ({min_cov['Coverage_Pct']:.1f}%)\n")
        f.write(f"- **Rata-rata spread**: {np.mean([r['Spatial_Spread_km'] for r in all_results]):.1f} km\n")
    f.write("\n### Visualisasi\n")
    f.write("- Plot per bulan: `output_plots/{bulan}/`\n")
    f.write("- Small multiples: `output_plots/Keseluruhan/small_multiples.png`\n")
    f.write("- Coverage trend: `output_plots/Keseluruhan/coverage_trend.png`\n\n")
    f.write(f"*Waktu eksekusi: {elapsed:.1f} detik*\n")

con.close()
print(f"\n{'='*60}")
print(f"ANALISIS 9 SELESAI! ({elapsed:.1f} detik)")
print(f"{'='*60}")
