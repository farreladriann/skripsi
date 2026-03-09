"""
Analisis 8: Monthly Mobility Comparison
=========================================
Perbandingan metrik mobilitas per bulan dan keseluruhan (DuckDB engine).
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
SUMMARY_FILE = os.path.join(BASE_DIR, 'hasil_monthly_mobility.csv')

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


def process_mobility(con, month_name, parquet_file, out_dir):
    fpath = os.path.join(DATA_ROOT, parquet_file)
    if not os.path.exists(fpath):
        return None

    stats_row = con.execute(f"""
        SELECT COUNT(*) AS total, COUNT(DISTINCT maid) AS n_users
        FROM read_parquet('{fpath}')
        WHERE latitude BETWEEN {LAT_MIN} AND {LAT_MAX}
          AND longitude BETWEEN {LON_MIN} AND {LON_MAX}
    """).fetchone()
    total, n_users = stats_row
    if total < 100:
        return None

    # Rg per user
    rg_df = con.execute(f"""
        SELECT
            SQRT(
                GREATEST(AVG(latitude*latitude) - POWER(AVG(latitude),2), 0) * 111*111 +
                GREATEST(AVG(longitude*longitude) - POWER(AVG(longitude),2), 0) *
                    POWER(111*COS(RADIANS(AVG(latitude))), 2)
            ) AS rg_km
        FROM read_parquet('{fpath}')
        WHERE latitude BETWEEN {LAT_MIN} AND {LAT_MAX}
          AND longitude BETWEEN {LON_MIN} AND {LON_MAX}
        GROUP BY maid HAVING COUNT(*) >= 5
    """).fetchnumpy()['rg_km']

    # Distance and speed via window functions (chunked for large files)
    n_chunks = max(1, total // 10_000_000)
    all_dist = []
    all_speed = []
    for ci in range(n_chunks):
        chunk_filter = f"AND HASH(maid) % {n_chunks} = {ci}" if n_chunks > 1 else ""
        move_data = con.execute(f"""
            WITH shifted AS (
                SELECT latitude, longitude, timestamp,
                       LAG(latitude)  OVER w AS prev_lat,
                       LAG(longitude) OVER w AS prev_lon,
                       LAG(timestamp) OVER w AS prev_ts
                FROM read_parquet('{fpath}')
                WHERE latitude BETWEEN {LAT_MIN} AND {LAT_MAX}
                  AND longitude BETWEEN {LON_MIN} AND {LON_MAX}
                  {chunk_filter}
                WINDOW w AS (PARTITION BY maid ORDER BY timestamp)
            ),
            dists AS (
                SELECT
                    6371.0 * 2.0 * ASIN(SQRT(
                        POWER(SIN(RADIANS(latitude - prev_lat) / 2.0), 2) +
                        COS(RADIANS(prev_lat)) * COS(RADIANS(latitude)) *
                        POWER(SIN(RADIANS(longitude - prev_lon) / 2.0), 2)
                    )) AS dist_km,
                    (timestamp - prev_ts) / 3600.0 AS dt_h
                FROM shifted
                WHERE prev_lat IS NOT NULL AND (timestamp - prev_ts) > 0
            )
            SELECT dist_km, dist_km / dt_h AS speed_kmh
            FROM dists
            WHERE dist_km > 0.05 AND dist_km < 200 AND dt_h > 0
              AND (dist_km / dt_h) < 200
        """).fetchnumpy()
        all_dist.append(move_data['dist_km'])
        all_speed.append(move_data['speed_kmh'])

    v_dist = np.concatenate(all_dist) if all_dist else np.array([], dtype=np.float64)
    v_speed = np.concatenate(all_speed) if all_speed else np.array([], dtype=np.float64)

    os.makedirs(out_dir, exist_ok=True)

    # 1. Distance distribution
    if len(v_dist) > 0:
        fig, ax = plt.subplots(figsize=(10, 5))
        ax.hist(v_dist[v_dist < np.percentile(v_dist, 95)], bins=60, color='#1976D2', alpha=0.7, edgecolor='white')
        med = np.median(v_dist)
        ax.axvline(med, color='red', ls='--', label=f'Median: {med:.2f} km')
        ax.set_title(f'Distribusi Jarak Perpindahan - {month_name}', fontsize=13, fontweight='bold')
        ax.set_xlabel('Jarak (km)'); ax.set_ylabel('Frekuensi'); ax.legend()
        plt.tight_layout()
        plt.savefig(os.path.join(out_dir, 'distribusi_jarak.png'), bbox_inches='tight'); plt.close()

    # 2. Speed distribution
    if len(v_speed) > 0:
        fig, ax = plt.subplots(figsize=(10, 5))
        ax.hist(v_speed[v_speed < np.percentile(v_speed, 95)], bins=60, color='#4CAF50', alpha=0.7, edgecolor='white')
        med_s = np.median(v_speed)
        ax.axvline(med_s, color='red', ls='--', label=f'Median: {med_s:.1f} km/h')
        ax.set_title(f'Distribusi Kecepatan - {month_name}', fontsize=13, fontweight='bold')
        ax.set_xlabel('Kecepatan (km/h)'); ax.set_ylabel('Frekuensi'); ax.legend()
        plt.tight_layout()
        plt.savefig(os.path.join(out_dir, 'distribusi_kecepatan.png'), bbox_inches='tight'); plt.close()

    # 3. Rg distribution
    if len(rg_df) > 10:
        fig, ax = plt.subplots(figsize=(10, 5))
        rg_plot = rg_df[rg_df < np.percentile(rg_df, 95)]
        ax.hist(rg_plot, bins=50, color='#FF9800', alpha=0.7, edgecolor='white')
        ax.axvline(np.median(rg_df), color='red', ls='--', label=f'Median: {np.median(rg_df):.2f} km')
        ax.set_title(f'Distribusi Radius of Gyration - {month_name}', fontsize=13, fontweight='bold')
        ax.set_xlabel('Rg (km)'); ax.set_ylabel('Frekuensi'); ax.legend()
        plt.tight_layout()
        plt.savefig(os.path.join(out_dir, 'distribusi_rg.png'), bbox_inches='tight'); plt.close()

    return {
        'Bulan': month_name, 'Total_Points': total, 'Users': n_users,
        'Valid_Moves': len(v_dist),
        'Median_Dist_km': float(np.median(v_dist)) if len(v_dist) > 0 else 0,
        'Mean_Dist_km': float(np.mean(v_dist)) if len(v_dist) > 0 else 0,
        'Median_Speed_kmh': float(np.median(v_speed)) if len(v_speed) > 0 else 0,
        'Mean_Speed_kmh': float(np.mean(v_speed)) if len(v_speed) > 0 else 0,
        'Median_Rg_km': float(np.median(rg_df)),
        'Mean_Rg_km': float(np.mean(rg_df)),
        'Users_Rg': len(rg_df),
    }


print("=" * 60)
print("ANALISIS 8: MONTHLY MOBILITY COMPARISON")
print("=" * 60)

start_time = time.time()
con = get_con()
all_results = []

for month_name, pfile in DATA_FILES:
    print(f"\n[{month_name}] Memproses...", end=' ', flush=True)
    out_dir = os.path.join(OUTPUT_BASE, month_name)
    result = process_mobility(con, month_name, pfile, out_dir)
    if result is None:
        print("SKIP"); continue
    all_results.append(result)
    print(f"OK dist={result['Median_Dist_km']:.2f}km speed={result['Median_Speed_kmh']:.1f}km/h Rg={result['Median_Rg_km']:.2f}km")

keseluruhan_dir = os.path.join(OUTPUT_BASE, 'Keseluruhan')
os.makedirs(keseluruhan_dir, exist_ok=True)

if all_results:
    months = [r['Bulan'] for r in all_results]
    x = range(len(months))

    # Dashboard 4-panel
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    axes[0,0].plot(x, [r['Median_Dist_km'] for r in all_results], 'o-', color='#1976D2', lw=2, ms=8, label='Median')
    axes[0,0].plot(x, [r['Mean_Dist_km'] for r in all_results], 's--', color='#64B5F6', lw=1.5, ms=6, label='Mean')
    axes[0,0].set_title('Jarak Perpindahan per Bulan'); axes[0,0].set_ylabel('km'); axes[0,0].legend()
    axes[0,0].set_xticks(x); axes[0,0].set_xticklabels(months, rotation=45, ha='right', fontsize=8)

    axes[0,1].plot(x, [r['Median_Speed_kmh'] for r in all_results], 'o-', color='#4CAF50', lw=2, ms=8, label='Median')
    axes[0,1].plot(x, [r['Mean_Speed_kmh'] for r in all_results], 's--', color='#81C784', lw=1.5, ms=6, label='Mean')
    axes[0,1].set_title('Kecepatan per Bulan'); axes[0,1].set_ylabel('km/h'); axes[0,1].legend()
    axes[0,1].set_xticks(x); axes[0,1].set_xticklabels(months, rotation=45, ha='right', fontsize=8)

    axes[1,0].plot(x, [r['Median_Rg_km'] for r in all_results], 'o-', color='#FF9800', lw=2, ms=8, label='Median')
    axes[1,0].plot(x, [r['Mean_Rg_km'] for r in all_results], 's--', color='#FFB74D', lw=1.5, ms=6, label='Mean')
    axes[1,0].set_title('Radius of Gyration per Bulan'); axes[1,0].set_ylabel('km'); axes[1,0].legend()
    axes[1,0].set_xticks(x); axes[1,0].set_xticklabels(months, rotation=45, ha='right', fontsize=8)

    tp = [r['Total_Points'] for r in all_results]
    axes[1,1].bar(x, tp, color='#9C27B0', alpha=0.7)
    axes[1,1].set_title('Volume Data per Bulan'); axes[1,1].set_ylabel('Data Points')
    axes[1,1].set_xticks(x); axes[1,1].set_xticklabels(months, rotation=45, ha='right', fontsize=8)
    for i, v in enumerate(tp):
        axes[1,1].text(i, v+max(tp)*0.01, f'{v:,.0f}', ha='center', fontsize=7)

    fig.suptitle('Dashboard Mobilitas Bulanan - DIY (Okt 2021-Jun 2022)', fontsize=15, fontweight='bold')
    plt.tight_layout()
    plt.savefig(os.path.join(keseluruhan_dir, 'dashboard_mobilitas.png'), bbox_inches='tight'); plt.close()

    for metric, label, color in [
        ('Median_Dist_km', 'Median Jarak (km)', '#1976D2'),
        ('Median_Speed_kmh', 'Median Kecepatan (km/h)', '#4CAF50'),
        ('Median_Rg_km', 'Median Rg (km)', '#FF9800')]:
        fig, ax = plt.subplots(figsize=(12, 6))
        vals = [r[metric] for r in all_results]
        ax.plot(x, vals, 'o-', color=color, lw=2.5, ms=10)
        ax.fill_between(x, vals, alpha=0.15, color=color)
        ax.set_xticks(x); ax.set_xticklabels(months, rotation=45, ha='right')
        ax.set_ylabel(label)
        ax.set_title(f'Tren {label} per Bulan', fontsize=14, fontweight='bold')
        for i, v in enumerate(vals):
            ax.text(i, v+max(vals)*0.02, f'{v:.2f}', ha='center', fontsize=9)
        plt.tight_layout()
        fname = metric.lower().replace(' ', '_')
        plt.savefig(os.path.join(keseluruhan_dir, f'tren_{fname}.png'), bbox_inches='tight'); plt.close()

df_res = pd.DataFrame(all_results)
df_res.to_csv(SUMMARY_FILE, index=False)

elapsed = time.time() - start_time
with open(os.path.join(BASE_DIR, 'LAPORAN.md'), 'w') as f:
    f.write("# Laporan Analisis 8: Monthly Mobility Comparison\n")
    f.write("## Data: GPS Mobilitas DIY (Oktober 2021 - Juni 2022)\n\n")
    f.write("### Tujuan\n")
    f.write("Membandingkan metrik mobilitas (jarak, kecepatan, Rg) antar bulan.\n\n")
    f.write("### Metodologi\n")
    f.write("- Jarak: Haversine via DuckDB window functions (filter 0.05-200 km, speed <200 km/h)\n")
    f.write("- Kecepatan: jarak/waktu\n")
    f.write("- Rg: radius of gyration per user (min 5 data points)\n\n")
    f.write("### Hasil Per Bulan\n\n")
    f.write("| Bulan | Data Points | Users | Moves | Med Dist (km) | Med Speed (km/h) | Med Rg (km) |\n")
    f.write("|-------|-----------|-------|-------|---------------|-----------------|-------------|\n")
    for r in all_results:
        f.write(f"| {r['Bulan']} | {r['Total_Points']:,} | {r['Users']:,} | {r['Valid_Moves']:,} | {r['Median_Dist_km']:.2f} | {r['Median_Speed_kmh']:.1f} | {r['Median_Rg_km']:.2f} |\n")
    f.write("\n### Hasil Keseluruhan\n\n")
    if all_results:
        f.write(f"- **Rata-rata median jarak**: {np.mean([r['Median_Dist_km'] for r in all_results]):.2f} km\n")
        f.write(f"- **Rata-rata median kecepatan**: {np.mean([r['Median_Speed_kmh'] for r in all_results]):.1f} km/h\n")
        f.write(f"- **Rata-rata median Rg**: {np.mean([r['Median_Rg_km'] for r in all_results]):.2f} km\n")
    f.write("\n### Visualisasi\n")
    f.write("- Plot per bulan: `output_plots/{bulan}/`\n")
    f.write("- Dashboard keseluruhan: `output_plots/Keseluruhan/dashboard_mobilitas.png`\n\n")
    f.write(f"*Waktu eksekusi: {elapsed:.1f} detik*\n")

con.close()
print(f"\n{'='*60}")
print(f"ANALISIS 8 SELESAI! ({elapsed:.1f} detik)")
print(f"{'='*60}")
