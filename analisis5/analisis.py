"""
Analisis 5: Demographic-Mobility Correlation
==============================================
Korelasi demografi dan mobilitas per bulan dan keseluruhan (DuckDB engine).
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
PEOPLE_FILE = os.path.join(DATA_ROOT, 'people_graph.parquet')
OUTPUT_BASE = os.path.join(BASE_DIR, 'output_plots')
SUMMARY_FILE = os.path.join(BASE_DIR, 'hasil_demografi_summary.csv')

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


def process_demografi(con, month_name, parquet_file, out_dir):
    fpath = os.path.join(DATA_ROOT, parquet_file)
    if not os.path.exists(fpath):
        return None

    stats_row = con.execute(f"""
        SELECT COUNT(*) AS total, COUNT(DISTINCT maid) AS n_users
        FROM read_parquet('{fpath}')
    """).fetchone()
    total, n_users = stats_row

    merged = con.execute(f"""
        WITH user_stats AS (
            SELECT maid, COUNT(*) AS n_points,
                   AVG(latitude) AS mean_lat, AVG(longitude) AS mean_lon,
                   STDDEV_SAMP(latitude) AS std_lat, STDDEV_SAMP(longitude) AS std_lon
            FROM read_parquet('{fpath}')
            GROUP BY maid HAVING n_points >= 5
        )
        SELECT u.maid, u.n_points, u.mean_lat, u.mean_lon, u.std_lat, u.std_lon,
               p.gender, p.income, p.kabupaten
        FROM user_stats u
        JOIN read_parquet('{PEOPLE_FILE}') p ON u.maid = p.maid
    """).fetchdf()

    if len(merged) == 0:
        return None

    merged['std_lat'] = merged['std_lat'].fillna(0)
    merged['std_lon'] = merged['std_lon'].fillna(0)
    merged['mobility_radius_km'] = np.sqrt(merged['std_lat']**2 + merged['std_lon']**2) * 111

    os.makedirs(out_dir, exist_ok=True)

    # 1. Boxplot per gender
    gender_data = merged[merged['gender'].isin(['male', 'female'])]
    if len(gender_data) > 10:
        fig, axes = plt.subplots(1, 2, figsize=(14, 5))
        sns.boxplot(data=gender_data, x='gender', y='mobility_radius_km', ax=axes[0],
                    palette={'male': '#2196F3', 'female': '#E91E63'}, showfliers=False)
        axes[0].set_title('Radius Mobilitas per Gender'); axes[0].set_ylabel('Radius (km)')
        sns.boxplot(data=gender_data, x='gender', y='n_points', ax=axes[1],
                    palette={'male': '#2196F3', 'female': '#E91E63'}, showfliers=False)
        axes[1].set_title('Data Points per Gender'); axes[1].set_ylabel('Jumlah')
        fig.suptitle(f'Mobilitas vs Gender - {month_name}', fontsize=13, fontweight='bold')
        plt.tight_layout()
        plt.savefig(os.path.join(out_dir, 'mobilitas_gender.png'), bbox_inches='tight'); plt.close()

    # 2. Boxplot per income
    income_data = merged[merged['income'].notna()]
    if len(income_data) > 10:
        fig, ax = plt.subplots(figsize=(10, 6))
        sns.boxplot(data=income_data, x='income', y='mobility_radius_km', palette='viridis', showfliers=False)
        ax.set_title(f'Radius Mobilitas per Income - {month_name}', fontsize=13, fontweight='bold')
        ax.set_ylabel('Radius (km)'); ax.set_xlabel('Income Level')
        plt.tight_layout()
        plt.savefig(os.path.join(out_dir, 'mobilitas_income.png'), bbox_inches='tight'); plt.close()

    # 3. Bar chart kabupaten
    kab = merged['kabupaten'].value_counts().head(10)
    if len(kab) > 0:
        fig, ax = plt.subplots(figsize=(10, 5))
        colors = plt.cm.viridis(np.linspace(0.2, 0.8, len(kab)))
        ax.barh(range(len(kab)), kab.values, color=colors)
        ax.set_yticks(range(len(kab))); ax.set_yticklabels(kab.index)
        ax.set_xlabel('Jumlah Pengguna'); ax.invert_yaxis()
        ax.set_title(f'Top Kabupaten - {month_name}', fontsize=13, fontweight='bold')
        plt.tight_layout()
        plt.savefig(os.path.join(out_dir, 'users_kabupaten.png'), bbox_inches='tight'); plt.close()

    stats = {'Bulan': month_name, 'Total_Rows': total, 'Users_GPS': n_users,
             'Matched_Users': len(merged), 'Median_Radius_km': merged['mobility_radius_km'].median(),
             'Mean_Radius_km': merged['mobility_radius_km'].mean()}
    for g in ['male', 'female']:
        gd = gender_data[gender_data['gender'] == g] if len(gender_data) > 0 else pd.DataFrame()
        if len(gd) > 0:
            stats[f'{g}_n'] = len(gd)
            stats[f'{g}_median_radius'] = gd['mobility_radius_km'].median()
    return stats, merged


print("=" * 60)
print("ANALISIS 5: DEMOGRAPHIC-MOBILITY CORRELATION")
print("=" * 60)

start_time = time.time()
con = get_con()
all_results = []
all_merged = []

for month_name, pfile in DATA_FILES:
    print(f"\n[{month_name}] Memproses...", end=' ', flush=True)
    out_dir = os.path.join(OUTPUT_BASE, month_name)
    out = process_demografi(con, month_name, pfile, out_dir)
    if out is None:
        print("SKIP"); continue
    result, merged = out
    all_results.append(result)
    all_merged.append(merged)
    print(f"OK {result['Matched_Users']:,} matched | median Rg={result['Median_Radius_km']:.2f} km")

keseluruhan_dir = os.path.join(OUTPUT_BASE, 'Keseluruhan')
os.makedirs(keseluruhan_dir, exist_ok=True)

if all_merged:
    combined = pd.concat(all_merged, ignore_index=True)
    gender_all = combined[combined['gender'].isin(['male', 'female'])]
    if len(gender_all) > 10:
        fig, ax = plt.subplots(figsize=(10, 6))
        sns.boxplot(data=gender_all, x='gender', y='mobility_radius_km',
                    palette={'male': '#2196F3', 'female': '#E91E63'}, showfliers=False)
        ax.set_title('Radius Mobilitas per Gender - Keseluruhan', fontsize=14, fontweight='bold')
        ax.set_ylabel('Radius (km)')
        plt.tight_layout()
        plt.savefig(os.path.join(keseluruhan_dir, 'gender_keseluruhan.png'), bbox_inches='tight'); plt.close()

    fig, ax = plt.subplots(figsize=(12, 6))
    months = [r['Bulan'] for r in all_results]
    med_radius = [r['Median_Radius_km'] for r in all_results]
    ax.plot(range(len(months)), med_radius, 'o-', color='#4CAF50', lw=2, ms=8)
    ax.set_xticks(range(len(months))); ax.set_xticklabels(months, rotation=45, ha='right')
    ax.set_ylabel('Median Radius (km)')
    ax.set_title('Tren Median Radius Mobilitas per Bulan', fontsize=14, fontweight='bold')
    plt.tight_layout()
    plt.savefig(os.path.join(keseluruhan_dir, 'tren_radius.png'), bbox_inches='tight'); plt.close()

    kab_all = combined['kabupaten'].value_counts().head(10)
    if len(kab_all) > 0:
        fig, ax = plt.subplots(figsize=(10, 6))
        colors = plt.cm.viridis(np.linspace(0.2, 0.8, len(kab_all)))
        ax.barh(range(len(kab_all)), kab_all.values, color=colors)
        ax.set_yticks(range(len(kab_all))); ax.set_yticklabels(kab_all.index)
        ax.set_xlabel('Jumlah Pengguna'); ax.invert_yaxis()
        ax.set_title('Top 10 Kabupaten - Keseluruhan', fontsize=14, fontweight='bold')
        plt.tight_layout()
        plt.savefig(os.path.join(keseluruhan_dir, 'kabupaten_keseluruhan.png'), bbox_inches='tight'); plt.close()

df_res = pd.DataFrame(all_results)
df_res.to_csv(SUMMARY_FILE, index=False)

elapsed = time.time() - start_time
with open(os.path.join(BASE_DIR, 'LAPORAN.md'), 'w') as f:
    f.write("# Laporan Analisis 5: Demographic-Mobility Correlation\n")
    f.write("## Data: GPS + PeopleGraph DIY (Oktober 2021 - Juni 2022)\n\n")
    f.write("### Tujuan\n")
    f.write("Mengkorelasikan data demografi (gender, income, lokasi) dengan pola mobilitas.\n\n")
    f.write("### Metodologi\n")
    f.write("- Hitung mobility radius per user via DuckDB (std koordinat x 111 km)\n")
    f.write("- Join GPS metrics dengan PeopleGraph (gender, income, kabupaten)\n")
    f.write("- Boxplot per kategori demografi per bulan dan keseluruhan\n\n")
    f.write("### Hasil Per Bulan\n\n")
    f.write("| Bulan | Users GPS | Matched | Median Radius (km) | Mean Radius (km) |\n")
    f.write("|-------|-----------|---------|--------------------|------------------|\n")
    for r in all_results:
        f.write(f"| {r['Bulan']} | {r['Users_GPS']:,} | {r['Matched_Users']:,} | {r['Median_Radius_km']:.2f} | {r['Mean_Radius_km']:.2f} |\n")
    f.write("\n### Gender Analysis\n\n")
    f.write("| Bulan | Male (n) | Male Median | Female (n) | Female Median |\n")
    f.write("|-------|----------|-------------|------------|---------------|\n")
    for r in all_results:
        mn = r.get('male_n', 0); mm = r.get('male_median_radius', 0)
        fn = r.get('female_n', 0); fm = r.get('female_median_radius', 0)
        f.write(f"| {r['Bulan']} | {mn:,} | {mm:.2f} km | {fn:,} | {fm:.2f} km |\n")
    f.write("\n### Hasil Keseluruhan\n\n")
    if all_results:
        total_matched = sum(r['Matched_Users'] for r in all_results)
        avg_radius = np.mean([r['Median_Radius_km'] for r in all_results])
        f.write(f"- **Total matched users**: {total_matched:,}\n")
        f.write(f"- **Rata-rata median radius**: {avg_radius:.2f} km\n")
    f.write("\n### Visualisasi\n")
    f.write("- Plot per bulan: `output_plots/{bulan}/`\n")
    f.write("- Plot keseluruhan: `output_plots/Keseluruhan/`\n\n")
    f.write(f"*Waktu eksekusi: {elapsed:.1f} detik*\n")

con.close()
print(f"\n{'='*60}")
print(f"ANALISIS 5 SELESAI! ({elapsed:.1f} detik)")
print(f"{'='*60}")
