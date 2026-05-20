# Jalankan dari root repo: .venv/bin/python scripts/figures/plot_interping.py
import polars as pl
import matplotlib.pyplot as plt
import numpy as np
from src.rru.utils import calculate_inter_ping_metrics

# 1) load dataset (sesuaikan path jika perlu)
p = "data/matched/backbone/gps_rru_labeled.parquet"
df = pl.read_parquet(p)

# 2) tambahkan dt_seconds, dist_meters, speed_kmh
df = calculate_inter_ping_metrics(df, maid_col="maid", time_col="timestamp",
                                  lat_col="latitude", lon_col="longitude")

# 3) buang nilai null/zero pada jarak (inter-ping valid)
df_valid = df.filter(pl.col("dist_meters").is_not_null() & (pl.col("dist_meters") > 0))

# 4) statistik ringkas (overall)
overall_mean = float(df_valid["dist_meters"].mean())
overall_median = float(df_valid["dist_meters"].median())
pcts = df_valid.select([
    pl.col("dist_meters").quantile(0.25).alias("q25"),
    pl.col("dist_meters").quantile(0.75).alias("q75"),
    pl.col("dist_meters").quantile(0.95).alias("p95"),
]).to_dict(as_series=False)

print(f"Overall mean inter-ping (m): {overall_mean:.2f}")
print(f"Overall median (m): {overall_median:.2f}")
print(f"Quantiles: {pcts}")

# 5) Jika ada kolom trip_id, hitung rata-rata per-trip dan distribusinya
if "trip_id" in df_valid.columns:
    per_trip = (
        df_valid.group_by(["maid", "trip_id"])
        .agg([
            pl.col("dist_meters").mean().alias("mean_interping_m"),
            pl.col("dist_meters").count().alias("n_interping")
        ])
    )
    per_trip_mean = per_trip["mean_interping_m"].to_numpy()
    print(f"Number of trips: {len(per_trip_mean)}")
else:
    per_trip_mean = None
    print("Kolom 'trip_id' tidak ditemukan — melewatkan agregasi per-trip.")

# 6) Plot distribusi: (a) semua inter-ping, (b) rata-rata per-trip (jika ada)
all_d = df_valid["dist_meters"].to_numpy()

plt.figure(figsize=(8, 4))
plt.hist(all_d, bins=np.linspace(0, 200, 100), color="#2c7fb8", alpha=0.85)
plt.xlabel("Inter-ping distance (m)")
plt.ylabel("Count")
plt.title("Distribusi jarak antar-ping (semua inter-ping)")
plt.grid(alpha=0.2)
plt.tight_layout()
plt.savefig("results/figures/interping_hist_all.png", dpi=150)
plt.close()

if per_trip_mean is not None:
    plt.figure(figsize=(8, 4))
    plt.hist(per_trip_mean, bins=80, color="#feb24c", alpha=0.9)
    plt.xlabel("Rata-rata jarak antar-ping per trip (m)")
    plt.ylabel("Count")
    plt.title("Distribusi rata-rata inter-ping per trip")
    plt.grid(alpha=0.2)
    plt.tight_layout()
    plt.savefig("results/figures/interping_hist_per_trip.png", dpi=150)
    plt.close()