"""
Analisis 6: Radius of Gyration & Home Detection
=================================================
Rg dan deteksi rumah per bulan dan keseluruhan (DuckDB engine).
"""

import duckdb
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy import stats as sp_stats
import seaborn as sns
import pandas as pd
import os
import time

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_ROOT = os.path.join(BASE_DIR, '..', 'DataGPS_parquet')
OUTPUT_BASE = os.path.join(BASE_DIR, 'output_plots')
SUMMARY_FILE = os.path.join(BASE_DIR, 'hasil_gyration_summary.csv')

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
RG_BINS = [0, 0.5, 2, 5, 10, np.inf]
RG_LABELS = ['Statis (<0.5)', 'Lokal (0.5-2)', 'Kota (2-5)', 'Regional (5-10)', 'Jauh (>10)']

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


def process_rg_home(con, month_name, parquet_file, out_dir):
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
    if total == 0:
        return None

    # Rg via DuckDB variance-based computation
    rg_data = con.execute(f"""
        SELECT maid, COUNT(*) AS n_points,
               AVG(latitude) AS mean_lat, AVG(longitude) AS mean_lon,
               AVG(latitude * latitude) AS lat_sq_mean,
               AVG(longitude * longitude) AS lon_sq_mean
        FROM read_parquet('{fpath}')
        WHERE latitude BETWEEN {LAT_MIN} AND {LAT_MAX}
          AND longitude BETWEEN {LON_MIN} AND {LON_MAX}
        GROUP BY maid HAVING n_points >= 10
    """).fetchdf()

    if len(rg_data) == 0:
        return None

    var_lat = np.maximum(0, rg_data['lat_sq_mean'] - rg_data['mean_lat']**2)
    var_lon = np.maximum(0, rg_data['lon_sq_mean'] - rg_data['mean_lon']**2)
    cos_lat = np.cos(np.radians(rg_data['mean_lat']))
    rg_data['rg_km'] = np.sqrt(var_lat * 111**2 + var_lon * (111 * cos_lat)**2)

    median_rg = rg_data['rg_km'].median()
    mean_rg = rg_data['rg_km'].mean()

    os.makedirs(out_dir, exist_ok=True)

    # Plot Rg distribution
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    rg_vals = rg_data['rg_km'].values

    axes[0].hist(rg_vals, bins=80, color='#1976D2', alpha=0.7, density=True, edgecolor='white')
    axes[0].axvline(median_rg, color='red', ls='--', label=f'Median: {median_rg:.2f} km')
    axes[0].set_title('Distribusi Rg (Linear)'); axes[0].set_xlabel('Rg (km)'); axes[0].set_ylabel('Density')
    axes[0].set_xlim(0, np.percentile(rg_vals, 95)); axes[0].legend()

    rg_pos = rg_vals[rg_vals > 0.01]
    if len(rg_pos) > 50:
        counts, edges = np.histogram(rg_pos, bins=50, density=True)
        centers = (edges[:-1]+edges[1:])/2; mask = counts > 0
        x, y = centers[mask], counts[mask]
        axes[1].scatter(x, y, c='#1976D2', s=20, alpha=0.7)
        try:
            sl, ic, rv, _, _ = sp_stats.linregress(np.log10(x), np.log10(y))
            yf = 10**(ic + sl*np.log10(x))
            axes[1].plot(x, yf, 'r--', lw=2, label=f'a={-sl:.2f} (R2={rv**2:.3f})')
            axes[1].legend()
        except Exception:
            pass
        axes[1].set_xscale('log'); axes[1].set_yscale('log')
    axes[1].set_title('Distribusi Rg (Log-Log)'); axes[1].set_xlabel('Rg (km)')
    fig.suptitle(f'Radius of Gyration - {month_name}', fontsize=13, fontweight='bold')
    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, 'distribusi_rg.png'), bbox_inches='tight'); plt.close()

    # Kategorisasi
    rg_data['category'] = pd.cut(rg_data['rg_km'], bins=RG_BINS, labels=RG_LABELS)
    cat_counts = rg_data['category'].value_counts().reindex(RG_LABELS, fill_value=0)

    colors = ['#4CAF50', '#8BC34A', '#FF9800', '#F44336', '#9C27B0']
    fig, ax = plt.subplots(figsize=(10, 5))
    bars = ax.bar(range(len(cat_counts)), cat_counts.values, color=colors, edgecolor='white')
    ax.set_xticks(range(len(cat_counts))); ax.set_xticklabels(cat_counts.index, rotation=20, ha='right')
    ax.set_ylabel('Jumlah Users')
    ax.set_title(f'Kategorisasi Mobilitas - {month_name}', fontsize=13, fontweight='bold')
    for bar, val in zip(bars, cat_counts.values):
        pct = val/len(rg_data)*100
        ax.text(bar.get_x()+bar.get_width()/2, bar.get_height()+max(cat_counts.values)*0.01,
                f'{val:,}\n({pct:.1f}%)', ha='center', fontsize=8, fontweight='bold')
    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, 'kategorisasi_mobilitas.png'), bbox_inches='tight'); plt.close()

    # Home detection via DuckDB
    home_locs = con.execute(f"""
        WITH night_visits AS (
            SELECT maid,
                   ROUND(latitude, 3) AS lat, ROUND(longitude, 3) AS lon,
                   COUNT(*) AS visits
            FROM read_parquet('{fpath}')
            WHERE latitude BETWEEN {LAT_MIN} AND {LAT_MAX}
              AND longitude BETWEEN {LON_MIN} AND {LON_MAX}
              AND (HOUR(TO_TIMESTAMP(timestamp) + INTERVAL '7 hours') >= 20
                   OR HOUR(TO_TIMESTAMP(timestamp) + INTERVAL '7 hours') < 6)
            GROUP BY maid, lat, lon
        ),
        ranked AS (
            SELECT *, ROW_NUMBER() OVER (PARTITION BY maid ORDER BY visits DESC) AS rn
            FROM night_visits WHERE visits >= 3
        )
        SELECT maid, lat AS latitude, lon AS longitude, visits FROM ranked WHERE rn = 1
    """).fetchdf()
    n_homes = len(home_locs)

    if n_homes > 0:
        # Sample background points
        bg = con.execute(f"""
            SELECT longitude, latitude FROM read_parquet('{fpath}')
            WHERE latitude BETWEEN {LAT_MIN} AND {LAT_MAX}
              AND longitude BETWEEN {LON_MIN} AND {LON_MAX}
            USING SAMPLE 30000
        """).fetchdf()

        fig, ax = plt.subplots(figsize=(12, 10))
        ax.scatter(bg['longitude'], bg['latitude'], s=0.1, c='lightgray', alpha=0.3)
        ax.scatter(home_locs['longitude'], home_locs['latitude'], s=3, c='#E53935', alpha=0.6,
                   label=f'Rumah (n={n_homes:,})')
        ax.set_title(f'Estimasi Lokasi Rumah - {month_name}', fontsize=13, fontweight='bold')
        ax.set_xlim(LON_MIN, LON_MAX); ax.set_ylim(LAT_MIN, LAT_MAX); ax.set_aspect('equal')
        ax.legend(markerscale=5)
        plt.tight_layout()
        plt.savefig(os.path.join(out_dir, 'home_locations.png'), bbox_inches='tight'); plt.close()

    cat_dict = {label: int(cat_counts.get(label, 0)) for label in RG_LABELS}
    return {
        'Bulan': month_name, 'Total_Rows': total, 'Users': n_users,
        'Users_Rg': len(rg_data), 'Median_Rg': median_rg, 'Mean_Rg': mean_rg,
        'Homes_Detected': n_homes, **cat_dict,
    }, rg_data[['maid', 'rg_km']]


print("=" * 60)
print("ANALISIS 6: RADIUS OF GYRATION & HOME DETECTION")
print("=" * 60)

start_time = time.time()
con = get_con()
all_results = []
all_rg = []

for month_name, pfile in DATA_FILES:
    print(f"\n[{month_name}] Memproses...", end=' ', flush=True)
    out_dir = os.path.join(OUTPUT_BASE, month_name)
    out = process_rg_home(con, month_name, pfile, out_dir)
    if out is None:
        print("SKIP"); continue
    result, rg_data = out
    all_results.append(result)
    all_rg.append(rg_data)
    print(f"OK Rg median={result['Median_Rg']:.2f} km | {result['Homes_Detected']} rumah")

keseluruhan_dir = os.path.join(OUTPUT_BASE, 'Keseluruhan')
os.makedirs(keseluruhan_dir, exist_ok=True)

median_all = 0.0
if all_rg:
    combined_rg = pd.concat(all_rg, ignore_index=True)
    rg_all = combined_rg['rg_km'].values
    median_all = float(np.median(rg_all))

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.hist(rg_all, bins=100, color='#1976D2', alpha=0.7, density=True, edgecolor='white')
    ax.axvline(median_all, color='red', ls='--', label=f'Median: {median_all:.2f} km')
    ax.set_title('Distribusi Rg Keseluruhan (9 Bulan)', fontsize=14, fontweight='bold')
    ax.set_xlabel('Rg (km)'); ax.set_ylabel('Density')
    ax.set_xlim(0, np.percentile(rg_all, 95)); ax.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(keseluruhan_dir, 'rg_keseluruhan.png'), bbox_inches='tight'); plt.close()

    fig, ax = plt.subplots(figsize=(12, 6))
    months = [r['Bulan'] for r in all_results]
    med_rgs = [r['Median_Rg'] for r in all_results]
    ax.plot(range(len(months)), med_rgs, 'o-', color='#4CAF50', lw=2, ms=8)
    ax.set_xticks(range(len(months))); ax.set_xticklabels(months, rotation=45, ha='right')
    ax.set_ylabel('Median Rg (km)')
    ax.set_title('Tren Median Rg per Bulan', fontsize=14, fontweight='bold')
    plt.tight_layout()
    plt.savefig(os.path.join(keseluruhan_dir, 'tren_rg.png'), bbox_inches='tight'); plt.close()

    fig, ax = plt.subplots(figsize=(14, 7))
    bottom = np.zeros(len(all_results))
    colors = ['#4CAF50', '#8BC34A', '#FF9800', '#F44336', '#9C27B0']
    for label, color in zip(RG_LABELS, colors):
        vals = [r[label] for r in all_results]
        ax.bar(range(len(months)), vals, bottom=bottom, color=color, label=label, edgecolor='white')
        bottom += np.array(vals)
    ax.set_xticks(range(len(months))); ax.set_xticklabels(months, rotation=45, ha='right')
    ax.set_ylabel('Jumlah Users')
    ax.set_title('Kategorisasi Mobilitas per Bulan', fontsize=14, fontweight='bold')
    ax.legend(loc='upper left', fontsize=8)
    plt.tight_layout()
    plt.savefig(os.path.join(keseluruhan_dir, 'kategorisasi_per_bulan.png'), bbox_inches='tight'); plt.close()

df_res = pd.DataFrame(all_results)
df_res.to_csv(SUMMARY_FILE, index=False)
if all_rg:
    combined_rg.to_csv(os.path.join(BASE_DIR, 'hasil_rg_data.csv'), index=False)

elapsed = time.time() - start_time
with open(os.path.join(BASE_DIR, 'LAPORAN.md'), 'w') as f:
    f.write("# Laporan Analisis 6: Radius of Gyration & Home Detection\n")
    f.write("## Data: GPS Mobilitas DIY (Oktober 2021 - Juni 2022)\n\n")
    f.write("### Tujuan\n")
    f.write("Menghitung Radius of Gyration (Rg) dan mendeteksi lokasi rumah pengguna.\n\n")
    f.write("### Metodologi\n")
    f.write("- Rg = sqrt(mean((ri - r_cm)^2)) dalam km (DuckDB variance aggregation)\n")
    f.write("- Min 10 data points per user\n")
    f.write("- Home detection: jam malam (20:00-06:00 WIB), min 3 kunjungan\n")
    f.write(f"- Kategori: {', '.join(RG_LABELS)}\n\n")
    f.write("### Hasil Per Bulan\n\n")
    f.write("| Bulan | Users Rg | Median Rg | Mean Rg | Rumah Terdeteksi |\n")
    f.write("|-------|----------|-----------|---------|------------------|\n")
    for r in all_results:
        f.write(f"| {r['Bulan']} | {r['Users_Rg']:,} | {r['Median_Rg']:.3f} km | {r['Mean_Rg']:.3f} km | {r['Homes_Detected']:,} |\n")
    f.write("\n### Kategorisasi Per Bulan\n\n")
    f.write("| Bulan | " + " | ".join(RG_LABELS) + " |\n")
    f.write("|-------" + "|---" * len(RG_LABELS) + "|\n")
    for r in all_results:
        vals = " | ".join([f"{r[l]:,}" for l in RG_LABELS])
        f.write(f"| {r['Bulan']} | {vals} |\n")
    f.write("\n### Hasil Keseluruhan\n\n")
    if all_results:
        total_users = sum(r['Users_Rg'] for r in all_results)
        f.write(f"- **Total users dianalisis**: {total_users:,}\n")
        f.write(f"- **Median Rg keseluruhan**: {median_all:.3f} km\n")
        total_homes = sum(r['Homes_Detected'] for r in all_results)
        f.write(f"- **Total rumah terdeteksi**: {total_homes:,}\n")
    f.write("\n### Visualisasi\n")
    f.write("- Plot per bulan: `output_plots/{bulan}/`\n")
    f.write("- Plot keseluruhan: `output_plots/Keseluruhan/`\n\n")
    f.write(f"*Waktu eksekusi: {elapsed:.1f} detik*\n")

con.close()
print(f"\n{'='*60}")
print(f"ANALISIS 6 SELESAI! ({elapsed:.1f} detik)")
print(f"{'='*60}")
