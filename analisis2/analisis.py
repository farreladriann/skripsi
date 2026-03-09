"""
Analisis 2: Temporal Activity Pattern Analysis
================================================
Pola aktivitas temporal per bulan dan keseluruhan (DuckDB engine).
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
SUMMARY_FILE = os.path.join(BASE_DIR, 'hasil_temporal_summary.csv')

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


def process_temporal(con, month_name, parquet_file, out_dir):
    fpath = os.path.join(DATA_ROOT, parquet_file)
    if not os.path.exists(fpath):
        return None

    stats_row = con.execute(f"""
        SELECT COUNT(*) AS total, COUNT(DISTINCT maid) AS n_users
        FROM read_parquet('{fpath}')
    """).fetchone()
    total, n_users = stats_row

    # Hour x Day-of-week heatmap data
    heat_df = con.execute(f"""
        SELECT
            HOUR(TO_TIMESTAMP(timestamp) + INTERVAL '7 hours') AS h,
            ISODOW(CAST(TO_TIMESTAMP(timestamp) + INTERVAL '7 hours' AS DATE)) - 1 AS dow,
            COUNT(*) AS cnt
        FROM read_parquet('{fpath}')
        GROUP BY h, dow ORDER BY h, dow
    """).fetchdf()

    # Hourly counts
    hourly_df = con.execute(f"""
        SELECT HOUR(TO_TIMESTAMP(timestamp) + INTERVAL '7 hours') AS h, COUNT(*) AS cnt
        FROM read_parquet('{fpath}')
        GROUP BY h ORDER BY h
    """).fetchdf()

    # Day-of-week counts
    dow_df = con.execute(f"""
        SELECT ISODOW(CAST(TO_TIMESTAMP(timestamp) + INTERVAL '7 hours' AS DATE)) - 1 AS dow,
               COUNT(*) AS cnt
        FROM read_parquet('{fpath}')
        GROUP BY dow ORDER BY dow
    """).fetchdf()

    # Daily time series
    daily_df = con.execute(f"""
        SELECT CAST(TO_TIMESTAMP(timestamp) + INTERVAL '7 hours' AS DATE) AS dt, COUNT(*) AS cnt
        FROM read_parquet('{fpath}')
        GROUP BY dt ORDER BY dt
    """).fetchdf()
    daily_df['dt'] = pd.to_datetime(daily_df['dt'])

    os.makedirs(out_dir, exist_ok=True)

    # Build hourly array (24 elements)
    hourly_counts = np.zeros(24, dtype=int)
    for _, row in hourly_df.iterrows():
        hourly_counts[int(row['h'])] = int(row['cnt'])
    peak_hour = int(np.argmax(hourly_counts))
    peak_count = int(hourly_counts[peak_hour])

    # Build dow array (7 elements, 0=Mon to 6=Sun)
    dow_counts = np.zeros(7, dtype=int)
    for _, row in dow_df.iterrows():
        dow_counts[int(row['dow'])] = int(row['cnt'])

    # 1. Heatmap jam x hari
    pivot = heat_df.pivot_table(index='h', columns='dow', values='cnt', fill_value=0)
    pivot = pivot.reindex(index=range(24), columns=range(7), fill_value=0)
    day_labels = ['Sen', 'Sel', 'Rab', 'Kam', 'Jum', 'Sab', 'Min']

    fig, ax = plt.subplots(figsize=(10, 7))
    sns.heatmap(pivot, cmap='YlOrRd', annot=False, linewidths=0.5, ax=ax,
                xticklabels=day_labels, cbar_kws={'label': 'Jumlah Data Points'})
    ax.set_title(f'Heatmap Aktivitas GPS - {month_name}', fontsize=13, fontweight='bold')
    ax.set_xlabel('Hari'); ax.set_ylabel('Jam (WIB)')
    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, 'heatmap_jam_hari.png'), bbox_inches='tight'); plt.close()

    # 2. Line chart pola per jam
    fig, ax = plt.subplots(figsize=(12, 6))
    ax.plot(range(24), hourly_counts, 'o-', color='#2196F3', lw=2, ms=8)
    ax.fill_between(range(24), hourly_counts, alpha=0.15, color='#2196F3')
    ax.set_title(f'Pola Aktivitas per Jam - {month_name}', fontsize=13, fontweight='bold')
    ax.set_xlabel('Jam (WIB)'); ax.set_ylabel('Jumlah Data Points')
    ax.set_xticks(range(24)); ax.set_xticklabels([f'{h:02d}' for h in range(24)])
    ax.annotate(f'Peak: {peak_count:,}\n({peak_hour:02d}:00)',
                xy=(peak_hour, peak_count), xytext=(peak_hour+2, peak_count*1.05),
                arrowprops=dict(arrowstyle='->', color='red'), fontsize=10, color='red', fontweight='bold')
    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, 'pola_per_jam.png'), bbox_inches='tight'); plt.close()

    # 3. Bar chart weekday vs weekend
    day_names = ['Senin', 'Selasa', 'Rabu', 'Kamis', 'Jumat', 'Sabtu', 'Minggu']
    colors = ['#4CAF50']*5 + ['#FF9800']*2
    fig, ax = plt.subplots(figsize=(10, 6))
    bars = ax.bar(day_names, dow_counts, color=colors, edgecolor='white', lw=1.5)
    for bar, val in zip(bars, dow_counts):
        ax.text(bar.get_x()+bar.get_width()/2, bar.get_height()+max(dow_counts)*0.01,
                f'{val:,}', ha='center', va='bottom', fontsize=9, fontweight='bold')
    ax.set_title(f'Aktivitas per Hari - {month_name}', fontsize=13, fontweight='bold')
    ax.set_ylabel('Jumlah Data Points')
    from matplotlib.patches import Patch
    ax.legend(handles=[Patch(facecolor='#4CAF50', label='Weekday'), Patch(facecolor='#FF9800', label='Weekend')])
    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, 'aktivitas_per_hari.png'), bbox_inches='tight'); plt.close()

    # 4. Time series harian
    fig, ax = plt.subplots(figsize=(14, 5))
    ax.bar(daily_df['dt'], daily_df['cnt'], color='#2196F3', alpha=0.7)
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%d %b'))
    ax.xaxis.set_major_locator(mdates.DayLocator(interval=3))
    ax.set_title(f'Time Series Harian - {month_name}', fontsize=13, fontweight='bold')
    ax.set_ylabel('Jumlah Data Points')
    plt.xticks(rotation=45, ha='right'); plt.tight_layout()
    plt.savefig(os.path.join(out_dir, 'time_series_harian.png'), bbox_inches='tight'); plt.close()

    wd_avg = float(dow_counts[:5].mean())
    we_avg = float(dow_counts[5:].mean())
    return {
        'Bulan': month_name, 'Total_Rows': total, 'Unique_Users': n_users,
        'Peak_Hour': peak_hour, 'Peak_Count': peak_count,
        'Avg_Weekday': wd_avg, 'Avg_Weekend': we_avg,
        'Rasio_WD_WE': wd_avg / we_avg if we_avg > 0 else 0,
        'Hourly_Counts': hourly_counts.tolist(),
    }


print("=" * 60)
print("ANALISIS 2: TEMPORAL ACTIVITY PATTERN")
print("=" * 60)

start_time = time.time()
con = get_con()
all_results = []
all_hourly = []

for month_name, pfile in DATA_FILES:
    print(f"\n[{month_name}] Memproses...", end=' ', flush=True)
    out_dir = os.path.join(OUTPUT_BASE, month_name)
    result = process_temporal(con, month_name, pfile, out_dir)
    if result is None:
        print("SKIP"); continue
    all_hourly.append((month_name, result['Hourly_Counts']))
    hc = result.pop('Hourly_Counts')
    all_results.append(result)
    print(f"OK Peak={result['Peak_Hour']:02d}:00 | {result['Total_Rows']:,} rows")

keseluruhan_dir = os.path.join(OUTPUT_BASE, 'Keseluruhan')
os.makedirs(keseluruhan_dir, exist_ok=True)

if all_hourly:
    fig, ax = plt.subplots(figsize=(14, 7))
    cmap = plt.cm.viridis(np.linspace(0, 1, len(all_hourly)))
    for (name, hc), color in zip(all_hourly, cmap):
        ax.plot(range(24), hc, 'o-', color=color, lw=1.5, ms=4, label=name, alpha=0.8)
    ax.set_title('Perbandingan Pola Aktivitas per Jam - Semua Bulan', fontsize=14, fontweight='bold')
    ax.set_xlabel('Jam (WIB)'); ax.set_ylabel('Jumlah Data Points')
    ax.set_xticks(range(24)); ax.legend(fontsize=8, ncol=3)
    plt.tight_layout()
    plt.savefig(os.path.join(keseluruhan_dir, 'perbandingan_pola_jam.png'), bbox_inches='tight'); plt.close()

    hourly_matrix = np.array([hc for _, hc in all_hourly])
    month_labels = [n for n, _ in all_hourly]
    fig, ax = plt.subplots(figsize=(14, 7))
    sns.heatmap(hourly_matrix, cmap='YlOrRd', annot=False, ax=ax,
                xticklabels=[f'{h:02d}' for h in range(24)], yticklabels=month_labels,
                cbar_kws={'label': 'Jumlah Data Points'})
    ax.set_title('Heatmap Aktivitas per Jam x Bulan', fontsize=14, fontweight='bold')
    ax.set_xlabel('Jam (WIB)'); ax.set_ylabel('Bulan')
    plt.tight_layout()
    plt.savefig(os.path.join(keseluruhan_dir, 'heatmap_bulan_jam.png'), bbox_inches='tight'); plt.close()

    fig, ax = plt.subplots(figsize=(12, 6))
    months = [r['Bulan'] for r in all_results]
    totals = [r['Total_Rows'] for r in all_results]
    peaks = [r['Peak_Hour'] for r in all_results]
    ax.bar(range(len(months)), totals, color='#1976D2', alpha=0.7)
    ax.set_xticks(range(len(months))); ax.set_xticklabels(months, rotation=45, ha='right')
    ax.set_ylabel('Total Data Points')
    ax.set_title('Total Data Points per Bulan', fontsize=14, fontweight='bold')
    for i, (t, p) in enumerate(zip(totals, peaks)):
        ax.text(i, t+max(totals)*0.01, f'{t:,}\n(peak {p:02d}:00)', ha='center', fontsize=7)
    plt.tight_layout()
    plt.savefig(os.path.join(keseluruhan_dir, 'total_per_bulan.png'), bbox_inches='tight'); plt.close()

df_res = pd.DataFrame(all_results)
df_res.to_csv(SUMMARY_FILE, index=False)

elapsed = time.time() - start_time
with open(os.path.join(BASE_DIR, 'LAPORAN.md'), 'w') as f:
    f.write("# Laporan Analisis 2: Temporal Activity Pattern\n")
    f.write("## Data: GPS Mobilitas DIY (Oktober 2021 - Juni 2022)\n\n")
    f.write("### Tujuan\n")
    f.write("Menganalisis pola aktivitas temporal pengguna GPS: distribusi per jam, per hari, weekday vs weekend.\n\n")
    f.write("### Metodologi\n")
    f.write("- Konversi timestamp Unix ke WIB (UTC+7) via DuckDB\n")
    f.write("- Heatmap jam x hari, line chart per jam, bar chart per hari, time series harian\n")
    f.write("- Analisis per bulan dan perbandingan keseluruhan\n\n")
    f.write("### Hasil Per Bulan\n\n")
    f.write("| Bulan | Total Data | Users Unik | Peak Hour | Avg Weekday | Avg Weekend | Rasio WD/WE |\n")
    f.write("|-------|-----------|------------|-----------|-------------|-------------|-------------|\n")
    for r in all_results:
        f.write(f"| {r['Bulan']} | {r['Total_Rows']:,} | {r['Unique_Users']:,} | {r['Peak_Hour']:02d}:00 | {r['Avg_Weekday']:,.0f} | {r['Avg_Weekend']:,.0f} | {r['Rasio_WD_WE']:.2f}x |\n")
    f.write("\n### Hasil Keseluruhan\n\n")
    if all_results:
        total_all = sum(r['Total_Rows'] for r in all_results)
        f.write(f"- **Total data points**: {total_all:,}\n")
        from collections import Counter
        peak_ctr = Counter(r['Peak_Hour'] for r in all_results)
        common_peak = peak_ctr.most_common(1)[0][0]
        f.write(f"- **Peak hour paling umum**: {common_peak:02d}:00 WIB\n")
        avg_ratio = np.mean([r['Rasio_WD_WE'] for r in all_results])
        f.write(f"- **Rata-rata rasio weekday/weekend**: {avg_ratio:.2f}x\n")
    f.write("\n### Visualisasi\n")
    f.write("- Plot per bulan: `output_plots/{bulan}/`\n")
    f.write("- Perbandingan keseluruhan: `output_plots/Keseluruhan/`\n\n")
    f.write(f"*Waktu eksekusi: {elapsed:.1f} detik*\n")

con.close()
print(f"\n{'='*60}")
print(f"ANALISIS 2 SELESAI! ({elapsed:.1f} detik)")
print(f"{'='*60}")
