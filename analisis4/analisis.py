"""
Analisis 4: Origin-Destination Mobility Flow
==============================================
Analisis pola OD per bulan dan keseluruhan (DuckDB engine).
"""

import duckdb
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import os
import time

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_ROOT = os.path.join(BASE_DIR, '..', 'DataGPS_parquet')
OUTPUT_BASE = os.path.join(BASE_DIR, 'output_plots')
SUMMARY_FILE = os.path.join(BASE_DIR, 'hasil_od_summary.csv')

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
GRID_SIZE = 10
LAT_STEP = (LAT_MAX - LAT_MIN) / GRID_SIZE
LON_STEP = (LON_MAX - LON_MIN) / GRID_SIZE

lat_bins = np.linspace(LAT_MIN, LAT_MAX, GRID_SIZE + 1)
lon_bins = np.linspace(LON_MIN, LON_MAX, GRID_SIZE + 1)

sns.set_theme(style='whitegrid', font_scale=1.1)
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


def haversine_vec(lat1, lon1, lat2, lon2):
    R = 6371
    phi1, phi2 = np.radians(lat1), np.radians(lat2)
    dphi = np.radians(lat2 - lat1)
    dlam = np.radians(lon2 - lon1)
    a = np.sin(dphi/2)**2 + np.cos(phi1)*np.cos(phi2)*np.sin(dlam/2)**2
    return R * 2 * np.arctan2(np.sqrt(a), np.sqrt(1-a))


def process_od(con, month_name, parquet_file, out_dir):
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

    od = con.execute(f"""
        WITH zoned AS (
            SELECT maid, latitude, longitude, timestamp,
                CAST(TO_TIMESTAMP(timestamp) + INTERVAL '7 hours' AS DATE) AS day_date,
                LEAST(GREATEST(CAST(FLOOR((latitude - ({LAT_MIN})) / {LAT_STEP}) AS INT), 0), {GRID_SIZE-1}) AS lat_zone,
                LEAST(GREATEST(CAST(FLOOR((longitude - ({LON_MIN})) / {LON_STEP}) AS INT), 0), {GRID_SIZE-1}) AS lon_zone
            FROM read_parquet('{fpath}')
            WHERE latitude BETWEEN {LAT_MIN} AND {LAT_MAX}
              AND longitude BETWEEN {LON_MIN} AND {LON_MAX}
        ),
        zoned2 AS (
            SELECT *, CONCAT(CAST(lat_zone AS VARCHAR), '_', CAST(lon_zone AS VARCHAR)) AS zone
            FROM zoned
        )
        SELECT maid, day_date,
               ARG_MIN(zone, timestamp) AS origin_zone,
               ARG_MAX(zone, timestamp) AS dest_zone,
               ARG_MIN(latitude, timestamp) AS origin_lat,
               ARG_MIN(longitude, timestamp) AS origin_lon,
               ARG_MAX(latitude, timestamp) AS dest_lat,
               ARG_MAX(longitude, timestamp) AS dest_lon,
               COUNT(*) AS n_points
        FROM zoned2
        GROUP BY maid, day_date
        HAVING n_points >= 3
    """).fetchdf()

    if len(od) == 0:
        return None

    od_moving = od[od['origin_zone'] != od['dest_zone']].copy()
    os.makedirs(out_dir, exist_ok=True)

    # OD Matrix
    od_matrix = od_moving.groupby(['origin_zone', 'dest_zone']).size().reset_index(name='flow')
    od_matrix = od_matrix.sort_values('flow', ascending=False)

    # Heatmap top zones
    top_o = od_matrix.groupby('origin_zone')['flow'].sum().nlargest(8).index.tolist()
    top_d = od_matrix.groupby('dest_zone')['flow'].sum().nlargest(8).index.tolist()
    top_zones = list(set(top_o + top_d))[:10]
    od_top = od_moving[od_moving['origin_zone'].isin(top_zones) & od_moving['dest_zone'].isin(top_zones)]
    pivot = od_top.groupby(['origin_zone', 'dest_zone']).size().unstack(fill_value=0)
    if len(pivot) > 0:
        fig, ax = plt.subplots(figsize=(10, 8))
        sns.heatmap(pivot, cmap='Blues', annot=True, fmt='d', linewidths=0.5, ax=ax)
        ax.set_title(f'OD Matrix (Top Zones) - {month_name}', fontsize=13, fontweight='bold')
        ax.set_xlabel('Destination'); ax.set_ylabel('Origin')
        plt.tight_layout()
        plt.savefig(os.path.join(out_dir, 'od_matrix.png'), bbox_inches='tight'); plt.close()

    # Flow lines top 20
    top20 = od_matrix.head(20)
    if len(top20) > 0:
        fig, ax = plt.subplots(figsize=(12, 10))
        max_flow = top20['flow'].max()
        for _, row in top20.iterrows():
            parts_o = row['origin_zone'].split('_')
            parts_d = row['dest_zone'].split('_')
            oi, oj = int(parts_o[0]), int(parts_o[1])
            di, dj = int(parts_d[0]), int(parts_d[1])
            o_lat = (lat_bins[oi]+lat_bins[min(oi+1,GRID_SIZE)])/2
            o_lon = (lon_bins[oj]+lon_bins[min(oj+1,GRID_SIZE)])/2
            d_lat = (lat_bins[di]+lat_bins[min(di+1,GRID_SIZE)])/2
            d_lon = (lon_bins[dj]+lon_bins[min(dj+1,GRID_SIZE)])/2
            lw = max(1, (row['flow']/max_flow)*8)
            ax.annotate('', xy=(d_lon, d_lat), xytext=(o_lon, o_lat),
                        arrowprops=dict(arrowstyle='->', color='#E53935', lw=lw, alpha=0.7))
            ax.text((o_lon+d_lon)/2, (o_lat+d_lat)/2, str(row['flow']), fontsize=6, ha='center',
                    bbox=dict(boxstyle='round,pad=0.2', facecolor='white', alpha=0.8))
        ax.set_title(f'Top 20 Rute - {month_name}', fontsize=13, fontweight='bold')
        ax.set_xlim(LON_MIN, LON_MAX); ax.set_ylim(LAT_MIN, LAT_MAX); ax.set_aspect('equal')
        plt.tight_layout()
        plt.savefig(os.path.join(out_dir, 'flow_lines.png'), bbox_inches='tight'); plt.close()

    # Distance distribution
    median_dist = mean_dist = 0
    if len(od_moving) > 0:
        od_moving['dist_km'] = haversine_vec(
            od_moving['origin_lat'].values, od_moving['origin_lon'].values,
            od_moving['dest_lat'].values, od_moving['dest_lon'].values)
        fig, ax = plt.subplots(figsize=(10, 5))
        ax.hist(od_moving['dist_km'], bins=60, color='#1976D2', alpha=0.7, edgecolor='white')
        med = od_moving['dist_km'].median()
        ax.axvline(med, color='red', ls='--', label=f'Median: {med:.2f} km')
        ax.set_title(f'Distribusi Jarak OD - {month_name}', fontsize=13, fontweight='bold')
        ax.set_xlabel('Jarak (km)'); ax.set_ylabel('Frekuensi'); ax.legend()
        plt.tight_layout()
        plt.savefig(os.path.join(out_dir, 'distribusi_jarak_od.png'), bbox_inches='tight'); plt.close()
        median_dist = float(med)
        mean_dist = float(od_moving['dist_km'].mean())

    top_route = od_matrix.iloc[0] if len(od_matrix) > 0 else None
    return {
        'Bulan': month_name, 'Total_Rows': total, 'OD_Pairs': len(od),
        'OD_Moving': len(od_moving), 'Pct_Moving': len(od_moving)/max(len(od),1)*100,
        'Median_Dist_km': median_dist, 'Mean_Dist_km': mean_dist,
        'Top_Route': f"{top_route['origin_zone']}->{top_route['dest_zone']}" if top_route is not None else '',
        'Top_Flow': int(top_route['flow']) if top_route is not None else 0,
    }, od_matrix


print("=" * 60)
print("ANALISIS 4: ORIGIN-DESTINATION MOBILITY FLOW")
print("=" * 60)

start_time = time.time()
con = get_con()
all_results = []
all_od = []

for month_name, pfile in DATA_FILES:
    print(f"\n[{month_name}] Memproses...", end=' ', flush=True)
    out_dir = os.path.join(OUTPUT_BASE, month_name)
    out = process_od(con, month_name, pfile, out_dir)
    if out is None:
        print("SKIP"); continue
    result, od_mat = out
    all_results.append(result)
    all_od.append(od_mat)
    print(f"OK {result['OD_Moving']:,} trips | Top: {result['Top_Route']} ({result['Top_Flow']})")

keseluruhan_dir = os.path.join(OUTPUT_BASE, 'Keseluruhan')
os.makedirs(keseluruhan_dir, exist_ok=True)

if all_od:
    combined_od = pd.concat(all_od)
    combined_od = combined_od.groupby(['origin_zone', 'dest_zone'])['flow'].sum().reset_index()
    combined_od = combined_od.sort_values('flow', ascending=False)

    fig, ax = plt.subplots(figsize=(12, 6))
    months = [r['Bulan'] for r in all_results]
    od_counts = [r['OD_Moving'] for r in all_results]
    ax.bar(range(len(months)), od_counts, color='#1976D2', alpha=0.8)
    ax.set_xticks(range(len(months))); ax.set_xticklabels(months, rotation=45, ha='right')
    ax.set_ylabel('Jumlah OD Trips')
    ax.set_title('Jumlah OD Trips per Bulan', fontsize=14, fontweight='bold')
    for i, v in enumerate(od_counts):
        ax.text(i, v+max(od_counts)*0.01, f'{v:,}', ha='center', fontsize=8)
    plt.tight_layout()
    plt.savefig(os.path.join(keseluruhan_dir, 'od_trips_per_bulan.png'), bbox_inches='tight'); plt.close()

    fig, ax = plt.subplots(figsize=(12, 6))
    med_dists = [r['Median_Dist_km'] for r in all_results]
    ax.plot(range(len(months)), med_dists, 'o-', color='#E91E63', lw=2, ms=8)
    ax.set_xticks(range(len(months))); ax.set_xticklabels(months, rotation=45, ha='right')
    ax.set_ylabel('Median Jarak OD (km)')
    ax.set_title('Tren Median Jarak OD per Bulan', fontsize=14, fontweight='bold')
    plt.tight_layout()
    plt.savefig(os.path.join(keseluruhan_dir, 'tren_jarak_od.png'), bbox_inches='tight'); plt.close()

df_res = pd.DataFrame(all_results)
df_res.to_csv(SUMMARY_FILE, index=False)

elapsed = time.time() - start_time
with open(os.path.join(BASE_DIR, 'LAPORAN.md'), 'w') as f:
    f.write("# Laporan Analisis 4: Origin-Destination Mobility Flow\n")
    f.write("## Data: GPS Mobilitas DIY (Oktober 2021 - Juni 2022)\n\n")
    f.write("### Tujuan\n")
    f.write("Menganalisis pola pergerakan origin-destination menggunakan grid zoning.\n\n")
    f.write("### Metodologi\n")
    f.write(f"- Grid {GRID_SIZE}x{GRID_SIZE} zona di wilayah DIY (DuckDB zone assignment)\n")
    f.write("- Origin = titik pertama per hari, Destination = titik terakhir\n")
    f.write("- Filter: min 3 data points per user per hari\n\n")
    f.write("### Hasil Per Bulan\n\n")
    f.write("| Bulan | Total Data | OD Pairs | Bergerak | %Bergerak | Median Jarak | Rute Terpopuler | Flow |\n")
    f.write("|-------|-----------|----------|----------|-----------|-------------|-----------------|------|\n")
    for r in all_results:
        f.write(f"| {r['Bulan']} | {r['Total_Rows']:,} | {r['OD_Pairs']:,} | {r['OD_Moving']:,} | {r['Pct_Moving']:.1f}% | {r['Median_Dist_km']:.2f} km | {r['Top_Route']} | {r['Top_Flow']} |\n")
    f.write("\n### Hasil Keseluruhan\n\n")
    if all_results:
        total_trips = sum(r['OD_Moving'] for r in all_results)
        avg_dist = np.mean([r['Median_Dist_km'] for r in all_results])
        f.write(f"- **Total OD trips (9 bulan)**: {total_trips:,}\n")
        f.write(f"- **Rata-rata median jarak**: {avg_dist:.2f} km\n")
        if all_od:
            top = combined_od.iloc[0]
            f.write(f"- **Rute terpopuler keseluruhan**: {top['origin_zone']}->{top['dest_zone']} ({top['flow']} trips)\n")
    f.write("\n### Visualisasi\n")
    f.write("- Plot per bulan: `output_plots/{bulan}/`\n")
    f.write("- Plot keseluruhan: `output_plots/Keseluruhan/`\n\n")
    f.write(f"*Waktu eksekusi: {elapsed:.1f} detik*\n")

con.close()
print(f"\n{'='*60}")
print(f"ANALISIS 4 SELESAI! ({elapsed:.1f} detik)")
print(f"{'='*60}")
