"""
Analisis 7: Monthly Trend Analysis
====================================
Tren aktivitas bulanan per bulan dan keseluruhan (DuckDB engine).
"""

import duckdb
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import seaborn as sns
import pandas as pd
import os
import time

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_ROOT = os.path.join(BASE_DIR, '..', 'DataGPS_parquet')
OUTPUT_BASE = os.path.join(BASE_DIR, 'output_plots')
SUMMARY_FILE = os.path.join(BASE_DIR, 'hasil_monthly_trend.csv')

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


def process_monthly_trend(con, month_name, parquet_file, out_dir):
    fpath = os.path.join(DATA_ROOT, parquet_file)
    if not os.path.exists(fpath):
        return None

    stats_row = con.execute(f"""
        SELECT COUNT(*) AS total, COUNT(DISTINCT maid) AS n_users
        FROM read_parquet('{fpath}')
    """).fetchone()
    total, n_users = stats_row
    if total == 0:
        return None

    hourly_df = con.execute(f"""
        SELECT HOUR(TO_TIMESTAMP(timestamp) + INTERVAL '7 hours') AS h, COUNT(*) AS cnt
        FROM read_parquet('{fpath}')
        GROUP BY h ORDER BY h
    """).fetchdf()

    daily_df = con.execute(f"""
        SELECT CAST(TO_TIMESTAMP(timestamp) + INTERVAL '7 hours' AS DATE) AS dt,
               COUNT(*) AS points, COUNT(DISTINCT maid) AS users
        FROM read_parquet('{fpath}')
        GROUP BY dt ORDER BY dt
    """).fetchdf()
    daily_df['dt'] = pd.to_datetime(daily_df['dt'])

    hourly = np.zeros(24, dtype=int)
    for _, row in hourly_df.iterrows():
        hourly[int(row['h'])] = int(row['cnt'])
    peak_hour = int(np.argmax(hourly))

    os.makedirs(out_dir, exist_ok=True)

    # Daily trend (dual axis)
    fig, ax1 = plt.subplots(figsize=(14, 6))
    ax1.bar(daily_df['dt'], daily_df['points'], color='#1976D2', alpha=0.6, label='Data Points')
    ax1.set_ylabel('Data Points', color='#1976D2')
    ax1.xaxis.set_major_formatter(mdates.DateFormatter('%d %b'))
    ax1.xaxis.set_major_locator(mdates.DayLocator(interval=3))
    plt.xticks(rotation=45, ha='right')
    ax2 = ax1.twinx()
    ax2.plot(daily_df['dt'], daily_df['users'], 'o-', color='#E91E63', lw=2, ms=4, label='Users')
    ax2.set_ylabel('Unique Users', color='#E91E63')
    fig.suptitle(f'Trend Harian - {month_name}', fontsize=13, fontweight='bold')
    lines1, l1 = ax1.get_legend_handles_labels()
    lines2, l2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1+lines2, l1+l2, loc='upper left')
    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, 'trend_harian.png'), bbox_inches='tight'); plt.close()

    # Hourly pattern
    fig, ax = plt.subplots(figsize=(12, 5))
    ax.bar(range(24), hourly, color='#4CAF50', alpha=0.8, edgecolor='white')
    ax.set_xticks(range(24)); ax.set_xticklabels([f'{h:02d}' for h in range(24)])
    ax.set_title(f'Distribusi per Jam - {month_name}', fontsize=13, fontweight='bold')
    ax.set_xlabel('Jam (WIB)'); ax.set_ylabel('Jumlah Data Points')
    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, 'distribusi_jam.png'), bbox_inches='tight'); plt.close()

    return {
        'Bulan': month_name, 'Total_Points': total, 'Unique_Users': n_users,
        'Peak_Hour': peak_hour, 'Peak_Count': int(hourly[peak_hour]),
        'Avg_Daily_Points': float(daily_df['points'].mean()),
        'Avg_Daily_Users': float(daily_df['users'].mean()),
        'N_Days': len(daily_df),
    }


print("=" * 60)
print("ANALISIS 7: MONTHLY TREND ANALYSIS")
print("=" * 60)

start_time = time.time()
con = get_con()
all_results = []

for month_name, pfile in DATA_FILES:
    print(f"\n[{month_name}] Memproses...", end=' ', flush=True)
    out_dir = os.path.join(OUTPUT_BASE, month_name)
    result = process_monthly_trend(con, month_name, pfile, out_dir)
    if result is None:
        print("SKIP"); continue
    all_results.append(result)
    print(f"OK {result['Total_Points']:,} pts, {result['Unique_Users']:,} users")

keseluruhan_dir = os.path.join(OUTPUT_BASE, 'Keseluruhan')
os.makedirs(keseluruhan_dir, exist_ok=True)

if all_results:
    months = [r['Bulan'] for r in all_results]
    x = range(len(months))

    fig, ax1 = plt.subplots(figsize=(14, 7))
    pts = [r['Total_Points'] for r in all_results]
    users = [r['Unique_Users'] for r in all_results]
    ax1.bar(x, pts, color='#1976D2', alpha=0.7, label='Data Points')
    ax1.set_ylabel('Data Points', color='#1976D2')
    ax1.set_xticks(x); ax1.set_xticklabels(months, rotation=45, ha='right')
    for i, v in enumerate(pts):
        ax1.text(i, v+max(pts)*0.01, f'{v:,.0f}', ha='center', fontsize=7, rotation=45)
    ax2 = ax1.twinx()
    ax2.plot(x, users, 'o-', color='#E91E63', lw=2.5, ms=8, label='Users')
    ax2.set_ylabel('Unique Users', color='#E91E63')
    fig.suptitle('Tren Aktivitas GPS Bulanan - DIY (Okt 2021-Jun 2022)', fontsize=14, fontweight='bold')
    lines1, l1 = ax1.get_legend_handles_labels()
    lines2, l2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1+lines2, l1+l2, loc='upper left')
    plt.tight_layout()
    plt.savefig(os.path.join(keseluruhan_dir, 'tren_bulanan.png'), bbox_inches='tight'); plt.close()

    fig, ax = plt.subplots(figsize=(12, 6))
    ax.plot(x, users, 'o-', color='#4CAF50', lw=2.5, ms=8)
    ax.fill_between(x, users, alpha=0.15, color='#4CAF50')
    ax.set_xticks(x); ax.set_xticklabels(months, rotation=45, ha='right')
    ax.set_ylabel('Unique Users')
    ax.set_title('Tren Users Unik per Bulan', fontsize=14, fontweight='bold')
    for i, u in enumerate(users):
        ax.text(i, u+max(users)*0.02, f'{u:,}', ha='center', fontsize=9)
    plt.tight_layout()
    plt.savefig(os.path.join(keseluruhan_dir, 'tren_users.png'), bbox_inches='tight'); plt.close()

    fig, ax = plt.subplots(figsize=(12, 6))
    avg_daily = [r['Avg_Daily_Points'] for r in all_results]
    ax.bar(x, avg_daily, color='#FF9800', alpha=0.8)
    ax.set_xticks(x); ax.set_xticklabels(months, rotation=45, ha='right')
    ax.set_ylabel('Rata-rata Data Points/Hari')
    ax.set_title('Rata-rata Aktivitas Harian per Bulan', fontsize=14, fontweight='bold')
    for i, v in enumerate(avg_daily):
        ax.text(i, v+max(avg_daily)*0.01, f'{v:,.0f}', ha='center', fontsize=8)
    plt.tight_layout()
    plt.savefig(os.path.join(keseluruhan_dir, 'avg_daily.png'), bbox_inches='tight'); plt.close()

df_res = pd.DataFrame(all_results)
df_res.to_csv(SUMMARY_FILE, index=False)

elapsed = time.time() - start_time
with open(os.path.join(BASE_DIR, 'LAPORAN.md'), 'w') as f:
    f.write("# Laporan Analisis 7: Monthly Trend Analysis\n")
    f.write("## Data: GPS Mobilitas DIY (Oktober 2021 - Juni 2022)\n\n")
    f.write("### Tujuan\n")
    f.write("Menganalisis tren aktivitas GPS secara bulanan.\n\n")
    f.write("### Metodologi\n")
    f.write("- DuckDB aggregasi per hari dan per jam\n")
    f.write("- Per bulan: daily trend + hourly distribution\n")
    f.write("- Keseluruhan: perbandingan tren antar bulan\n\n")
    f.write("### Hasil Per Bulan\n\n")
    f.write("| Bulan | Total Points | Users Unik | Peak Hour | Avg Daily Points | Avg Daily Users | Hari Data |\n")
    f.write("|-------|-------------|------------|-----------|-----------------|-----------------|----------|\n")
    for r in all_results:
        f.write(f"| {r['Bulan']} | {r['Total_Points']:,} | {r['Unique_Users']:,} | {r['Peak_Hour']:02d}:00 | {r['Avg_Daily_Points']:,.0f} | {r['Avg_Daily_Users']:,.0f} | {r['N_Days']} |\n")
    f.write("\n### Hasil Keseluruhan\n\n")
    if all_results:
        total = sum(r['Total_Points'] for r in all_results)
        max_month = max(all_results, key=lambda r: r['Total_Points'])
        min_month = min(all_results, key=lambda r: r['Total_Points'])
        f.write(f"- **Total data points**: {total:,}\n")
        f.write(f"- **Bulan terbanyak**: {max_month['Bulan']} ({max_month['Total_Points']:,})\n")
        f.write(f"- **Bulan tersedikit**: {min_month['Bulan']} ({min_month['Total_Points']:,})\n")
        f.write(f"- **Rata-rata users/bulan**: {np.mean([r['Unique_Users'] for r in all_results]):,.0f}\n")
    f.write("\n### Visualisasi\n")
    f.write("- Plot per bulan: `output_plots/{bulan}/`\n")
    f.write("- Plot keseluruhan: `output_plots/Keseluruhan/`\n\n")
    f.write(f"*Waktu eksekusi: {elapsed:.1f} detik*\n")

con.close()
print(f"\n{'='*60}")
print(f"ANALISIS 7 SELESAI! ({elapsed:.1f} detik)")
print(f"{'='*60}")
