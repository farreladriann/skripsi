"""
Analisis 1: Power-Law & Levy Flight (Jump Length Distribution)
==============================================================
Mendiagnosis distribusi jarak lompatan menggunakan analisis power-law.
Output per bulan dan keseluruhan (DuckDB engine).
"""

import duckdb
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy import stats
import pandas as pd
import os
import time

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_ROOT = os.path.join(BASE_DIR, '..', 'DataGPS_parquet')
OUTPUT_BASE = os.path.join(BASE_DIR, 'output_plots')
SUMMARY_FILE = os.path.join(BASE_DIR, 'hasil_analisis_summary.csv')

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


def analyze_power_law(jump_lengths, title, output_path):
    tail = jump_lengths[jump_lengths >= 1]
    result = {'Alpha': np.nan, 'R2': np.nan, 'Diagnosis': 'Data Kurang',
              'Valid_Moves': len(jump_lengths), 'Tail_Count': len(tail)}
    if len(tail) < 100:
        return result
    counts, edges = np.histogram(tail, bins=50, density=True)
    centers = (edges[:-1] + edges[1:]) / 2
    mask = counts > 0
    x, y = centers[mask], counts[mask]
    if len(x) < 3:
        return result
    slope, intercept, r_val, _, _ = stats.linregress(np.log10(x), np.log10(y))
    alpha = -slope
    result['Alpha'] = alpha
    result['R2'] = r_val**2
    if 1.0 <= alpha <= 2.0:
        result['Diagnosis'] = "FAT TAILED (BAHAYA)"
    elif alpha > 2.0:
        result['Diagnosis'] = "Thin Tailed (Aman)"
    else:
        result['Diagnosis'] = "SUPER FAT (Ekstrem)"
    fig, ax = plt.subplots(figsize=(10, 7))
    ax.scatter(x, y, alpha=0.6, s=30, label='Data', zorder=5)
    y_fit = 10**(intercept + slope * np.log10(x))
    ax.plot(x, y_fit, 'r--', lw=2, label=f'a = {alpha:.2f} (R2 = {r_val**2:.3f})')
    ax.set_xscale('log'); ax.set_yscale('log')
    ax.set_title(f'{title}\na = {alpha:.2f} - {result["Diagnosis"]}', fontsize=13, fontweight='bold')
    ax.set_xlabel('Jarak Lompatan (km)'); ax.set_ylabel('Density')
    ax.legend(fontsize=11); ax.grid(True, which='both', alpha=0.2)
    plt.tight_layout()
    plt.savefig(output_path, bbox_inches='tight'); plt.close()
    return result


def compute_jumps(con, filepath):
    total = con.execute(
        f"SELECT COUNT(*) FROM read_parquet('{filepath}')"
    ).fetchone()[0]
    n_chunks = max(1, total // 10_000_000)
    all_jumps = []
    for ci in range(n_chunks):
        chunk_where = f"WHERE HASH(maid) % {n_chunks} = {ci}" if n_chunks > 1 else ""
        chunk = con.execute(f"""
            WITH shifted AS (
                SELECT latitude, longitude, timestamp,
                       LAG(latitude)  OVER w AS prev_lat,
                       LAG(longitude) OVER w AS prev_lon,
                       LAG(timestamp) OVER w AS prev_ts
                FROM read_parquet('{filepath}')
                {chunk_where}
                WINDOW w AS (PARTITION BY maid ORDER BY timestamp)
            ),
            dists AS (
                SELECT
                    6371.0 * 2.0 * ASIN(SQRT(
                        POWER(SIN(RADIANS(latitude - prev_lat) / 2.0), 2) +
                        COS(RADIANS(prev_lat)) * COS(RADIANS(latitude)) *
                        POWER(SIN(RADIANS(longitude - prev_lon) / 2.0), 2)
                    )) AS jump_km,
                    (timestamp - prev_ts) / 3600.0 AS dt_h
                FROM shifted
                WHERE prev_lat IS NOT NULL AND (timestamp - prev_ts) > 0
            )
            SELECT jump_km FROM dists
            WHERE jump_km > 0.1 AND dt_h > 0 AND (jump_km / dt_h) < 1000
        """).fetchnumpy()['jump_km']
        all_jumps.append(chunk)
    jumps = np.concatenate(all_jumps) if all_jumps else np.array([], dtype=np.float64)
    return jumps, total


print("=" * 60)
print("ANALISIS 1: POWER-LAW & LEVY FLIGHT")
print("=" * 60)

start_time = time.time()
con = get_con()
all_results = []
all_jumps = []

for month_name, pfile in DATA_FILES:
    fpath = os.path.join(DATA_ROOT, pfile)
    if not os.path.exists(fpath):
        print(f"[{month_name}] SKIP - file tidak ditemukan"); continue
    print(f"\n[{month_name}] Memproses...", end=' ', flush=True)
    month_dir = os.path.join(OUTPUT_BASE, month_name)
    os.makedirs(month_dir, exist_ok=True)
    jumps, total_rows = compute_jumps(con, fpath)
    if len(jumps) == 0:
        print("SKIP - tidak ada data valid"); continue
    plot_path = os.path.join(month_dir, f'power_law_{month_name}.png')
    result = analyze_power_law(jumps, f'Power-Law - {month_name}', plot_path)
    result['Bulan'] = month_name
    result['Total_Rows'] = total_rows
    all_results.append(result)
    all_jumps.append(jumps)
    print(f"OK a={result['Alpha']:.2f} | {result['Diagnosis']}")

keseluruhan_dir = os.path.join(OUTPUT_BASE, 'Keseluruhan')
os.makedirs(keseluruhan_dir, exist_ok=True)
overall_result = {}
if all_jumps:
    combined = np.concatenate(all_jumps)
    print(f"\n[KESELURUHAN] {len(combined):,} jump lengths gabungan...")
    overall_result = analyze_power_law(
        combined, 'Power-Law - Keseluruhan (Okt 2021 - Jun 2022)',
        os.path.join(keseluruhan_dir, 'power_law_keseluruhan.png'))
    if len(all_results) > 1:
        fig, ax = plt.subplots(figsize=(12, 6))
        months = [r['Bulan'] for r in all_results]
        alphas = [r['Alpha'] for r in all_results]
        colors = ['#4CAF50' if a > 2 else '#F44336' if a < 1 else '#FF9800' for a in alphas]
        bars = ax.bar(range(len(months)), alphas, color=colors, edgecolor='white')
        ax.set_xticks(range(len(months)))
        ax.set_xticklabels(months, rotation=45, ha='right')
        ax.axhline(y=2.0, color='red', linestyle='--', alpha=0.7, label='Batas Fat/Thin (a=2.0)')
        ax.axhline(y=1.0, color='darkred', linestyle='--', alpha=0.7, label='Batas Super Fat (a=1.0)')
        ax.set_ylabel('Alpha (a)')
        ax.set_title('Perbandingan Alpha per Bulan', fontsize=14, fontweight='bold')
        ax.legend(); plt.tight_layout()
        for bar, a in zip(bars, alphas):
            ax.text(bar.get_x()+bar.get_width()/2, bar.get_height()+0.02, f'{a:.2f}',
                    ha='center', va='bottom', fontsize=9, fontweight='bold')
        plt.savefig(os.path.join(keseluruhan_dir, 'perbandingan_alpha.png'), bbox_inches='tight')
        plt.close()

df_res = pd.DataFrame(all_results)
df_res.to_csv(SUMMARY_FILE, index=False)

elapsed = time.time() - start_time
with open(os.path.join(BASE_DIR, 'LAPORAN.md'), 'w') as f:
    f.write("# Laporan Analisis 1: Power-Law & Levy Flight\n")
    f.write("## Data: GPS Mobilitas DIY (Oktober 2021 - Juni 2022)\n\n")
    f.write("### Tujuan\n")
    f.write("Mendiagnosis apakah distribusi jarak lompatan pengguna mengikuti pola Fat Tailed (Levy Flight) atau Thin Tailed.\n\n")
    f.write("### Metodologi\n")
    f.write("- Menghitung jarak Haversine antar titik GPS berurutan per pengguna (DuckDB window functions)\n")
    f.write("- Filter noise (<0.1 km) dan teleportasi (>1000 km/jam)\n")
    f.write("- Regresi linear pada histogram log-log untuk estimasi eksponen alpha\n")
    f.write("- alpha < 1.0: SUPER FAT | 1.0 <= alpha <= 2.0: FAT TAILED | alpha > 2.0: Thin Tailed\n\n")
    f.write("### Hasil Per Bulan\n\n")
    f.write("| Bulan | Total Baris | Pergerakan Valid | Alpha | R2 | Diagnosis |\n")
    f.write("|-------|-------------|------------------|-------|----|-----------|\n")
    for r in all_results:
        f.write(f"| {r['Bulan']} | {r['Total_Rows']:,} | {r['Valid_Moves']:,} | {r['Alpha']:.2f} | {r['R2']:.3f} | {r['Diagnosis']} |\n")
    f.write("\n### Hasil Keseluruhan\n\n")
    if all_jumps:
        f.write(f"- **Total jump lengths gabungan**: {len(combined):,}\n")
        f.write(f"- **Alpha keseluruhan**: {overall_result.get('Alpha', 0):.2f}\n")
        f.write(f"- **R2**: {overall_result.get('R2', 0):.3f}\n")
        f.write(f"- **Diagnosis**: {overall_result.get('Diagnosis', '-')}\n")
    f.write("\n### Visualisasi\n")
    f.write("- Plot per bulan: `output_plots/{bulan}/`\n")
    f.write("- Plot keseluruhan: `output_plots/Keseluruhan/`\n\n")
    f.write(f"*Waktu eksekusi: {elapsed:.1f} detik*\n")

con.close()
print(f"\n{'='*60}")
print(f"ANALISIS 1 SELESAI! ({elapsed:.1f} detik)")
print(f"{'='*60}")
