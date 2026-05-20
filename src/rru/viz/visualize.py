"""
Visualization Module — Generate publication-quality plots for thesis.

Produces:
1. OD Matrix heatmaps (aggregate, weekday/weekend, peak/off-peak)
2. Traffic density hourly profiles (all intersections)
3. Density weekday vs weekend comparison
4. Turning movement bar charts per intersection
5. Monthly density trends
6. Daily density time series
7. Pipeline and network maps
"""

import polars as pl
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import numpy as np
from pathlib import Path
import geopandas as gpd

# ── Style configuration ─────────────────────────────────────────────
plt.rcParams.update({
    "font.family": "serif",
    "font.size": 10,
    "axes.titlesize": 12,
    "axes.labelsize": 11,
    "xtick.labelsize": 9,
    "ytick.labelsize": 9,
    "legend.fontsize": 9,
    "figure.dpi": 150,
    "savefig.dpi": 300,
    "savefig.bbox": "tight",
    "savefig.pad_inches": 0.1,
})

RESULTS_DIR = Path("./results")
FIGURES_DIR = Path("./results/figures")

INTERSECTION_ORDER = [
    "kronggahan", "jombor", "monjali",
    "kentungan", "condongcatur", "upn",
]

INTERSECTION_LABELS = {
    "kronggahan": "Kronggahan",
    "jombor": "Jombor",
    "monjali": "Monjali",
    "kentungan": "Kentungan",
    "condongcatur": "Condongcatur",
    "upn": "UPN",
}

# Color palette for intersections
COLORS = {
    "kronggahan": "#e74c3c",
    "jombor": "#e67e22",
    "monjali": "#2ecc71",
    "kentungan": "#3498db",
    "condongcatur": "#9b59b6",
    "upn": "#1abc9c",
}


def plot_od_heatmap(csv_path: Path, title: str, output_path: Path):
    """Plot a 6×6 OD matrix as an annotated heatmap."""
    df = pl.read_csv(csv_path)
    labels = [INTERSECTION_LABELS.get(c, c) for c in df.columns]
    matrix = df.to_numpy()

    fig, ax = plt.subplots(figsize=(7, 5.5))
    im = ax.imshow(matrix, cmap="YlOrRd", aspect="auto")

    ax.set_xticks(range(len(labels)))
    ax.set_yticks(range(len(labels)))
    ax.set_xticklabels(labels, rotation=45, ha="right")
    ax.set_yticklabels(labels)
    ax.set_xlabel("Tujuan")
    ax.set_ylabel("Asal")
    ax.set_title(title)

    # Annotate cells
    for i in range(len(labels)):
        for j in range(len(labels)):
            val = matrix[i, j]
            color = "white" if val > matrix.max() * 0.6 else "black"
            ax.text(j, i, f"{int(val):,}", ha="center", va="center",
                    fontsize=8, color=color, fontweight="bold" if i == j else "normal")

    cbar = fig.colorbar(im, ax=ax, shrink=0.8, label="Jumlah trip")
    fig.tight_layout()
    fig.savefig(output_path)
    plt.close(fig)
    print(f"  ✓ {output_path.name}")


def plot_pipeline_flowchart():
    """Create a compact methodology pipeline flowchart for Chapter 3."""
    fig_dir = FIGURES_DIR / "pipeline"
    fig_dir.mkdir(parents=True, exist_ok=True)

    steps = [
        ("Data wilayah kajian", "15.386.869 ping\n370.778 MAID"),
        ("Jaringan RRU bersih", "fishbone + backbone\n593 edge"),
        ("Kandidat jalan R-tree", "839.304 ping\nradius 20 m"),
        ("Bilocation collapse", "552.413 ping\n42.613 MAID"),
        ("Klasifikasi moda", "236.700 ping\n8.458 MAID kendaraan"),
        ("Map matching geometris", "nearest-edge\nrerata jarak 6,0 m"),
        ("Segmentasi trajektori", "gap 10 menit\n38.973 trip"),
        ("Pelabelan persimpangan", "radius 200 m\n28.767 trip ber-OD"),
        ("Analisis", "OD | Kepadatan\nTurning movement"),
    ]

    fig, ax = plt.subplots(figsize=(7.2, 10))
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    box_w = 0.74
    box_h = 0.075
    x = 0.13
    y_top = 0.84
    gap = 0.043

    for idx, (title, detail) in enumerate(steps):
        y = y_top - idx * (box_h + gap)
        color = "#eef6f3" if idx < 4 else "#eef2fb"
        edge = "#1B998B" if idx < 4 else "#365FA0"
        box = FancyBboxPatch(
            (x, y), box_w, box_h,
            boxstyle="round,pad=0.012,rounding_size=0.012",
            linewidth=1.4,
            edgecolor=edge,
            facecolor=color,
        )
        ax.add_patch(box)
        ax.text(x + 0.03, y + box_h * 0.62, title, fontsize=11, fontweight="bold", va="center")
        ax.text(x + 0.03, y + box_h * 0.28, detail, fontsize=9, va="center", color="#333333")

        if idx < len(steps) - 1:
            start = (0.5, y - 0.004)
            end = (0.5, y - gap + 0.006)
            arrow = FancyArrowPatch(
                start, end,
                arrowstyle="-|>",
                mutation_scale=13,
                linewidth=1.2,
                color="#444444",
            )
            ax.add_patch(arrow)

    ax.text(0.5, 0.985, "Alur Pipeline Penelitian", ha="center", va="top",
            fontsize=14, fontweight="bold")
    fig.savefig(fig_dir / "research_pipeline.png", dpi=300, bbox_inches="tight", pad_inches=0.08)
    plt.close(fig)
    print("  ✓ research_pipeline.png")


def plot_backbone_network_map():
    """Visualize the backbone-only road network and backbone-filtered pings."""
    fig_dir = FIGURES_DIR / "network"
    fig_dir.mkdir(parents=True, exist_ok=True)

    from src.rru.paths import RRU_BACKBONE_CLEAN_GEOJSON, RRU_WITH_INTERSECTION_CLEAN_GEOJSON

    network_path = RRU_BACKBONE_CLEAN_GEOJSON
    fishbone_path = RRU_WITH_INTERSECTION_CLEAN_GEOJSON
    labeled_path = Path("./data/matched/backbone/gps_rru_labeled.parquet")
    if not network_path.exists() or not labeled_path.exists():
        return

    edges = gpd.read_file(network_path).to_crs(epsg=4326)
    fishbone = gpd.read_file(fishbone_path).to_crs(epsg=4326) if fishbone_path.exists() else None
    df = pl.read_parquet(labeled_path).select(["latitude", "longitude", "nearest_intersection"])
    # Deterministic down-sample for legibility while preserving the full spatial pattern.
    sample = df.with_row_index("row_idx").filter((pl.col("row_idx") % 12) == 0)

    fig, ax = plt.subplots(figsize=(10, 4.8))
    if fishbone is not None:
        fishbone.plot(ax=ax, color="#bdbdbd", linewidth=0.8, alpha=0.65, label="Jaringan fishbone preprocessing")
    edges.plot(ax=ax, color="#c0392b", linewidth=2.2, label="Backbone RRU untuk OD")

    ax.scatter(
        sample["longitude"].to_numpy(),
        sample["latitude"].to_numpy(),
        s=2,
        alpha=0.18,
        color="#1f77b4",
        label="Ping kendaraan yang melintasi backbone (sampel)",
    )

    intersection_points = {
        "kronggahan": (-7.744769426425405, 110.34897889640796),
        "jombor": (-7.749221082422497, 110.36229833670288),
        "monjali": (-7.751208485968954, 110.37121050305969),
        "kentungan": (-7.754883591097026, 110.38329930140856),
        "condongcatur": (-7.758447985710783, 110.39574179820893),
        "upn": (-7.761726028519824, 110.41203208408224),
    }
    for int_name, (lat, lon) in intersection_points.items():
        ax.scatter([lon], [lat], s=60, color=COLORS[int_name], edgecolor="white", linewidth=0.6, zorder=5)
        ax.text(lon, lat + 0.001, INTERSECTION_LABELS[int_name], fontsize=8, ha="center", weight="bold")

    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    ax.set_title("Filter Backbone Ring Road Utara dari Preprocessing Fishbone")
    ax.grid(True, alpha=0.25)
    ax.legend(loc="lower left", framealpha=0.9)
    fig.tight_layout()
    fig.savefig(fig_dir / "rru_backbone_vehicle_map.png")
    plt.close(fig)
    print("  ✓ rru_backbone_vehicle_map.png")


def plot_all_od_matrices():
    """Generate OD heatmaps for all matrix variants."""
    od_dir = RESULTS_DIR / "od_matrix"
    fig_dir = FIGURES_DIR / "od_matrix"
    fig_dir.mkdir(parents=True, exist_ok=True)

    configs = [
        ("od_matrix_all.csv", "Matriks OD Agregat (Okt 2021 - Jun 2022)", "od_heatmap_all.png"),
        ("od_matrix_weekday.csv", "Matriks OD Hari Kerja", "od_heatmap_weekday.png"),
        ("od_matrix_weekend.csv", "Matriks OD Akhir Pekan", "od_heatmap_weekend.png"),
        ("od_matrix_peak.csv", "Matriks OD Jam Sibuk (07-09 & 16-18 WIB)", "od_heatmap_peak.png"),
        ("od_matrix_offpeak.csv", "Matriks OD Jam Non-Sibuk", "od_heatmap_offpeak.png"),
    ]

    print("Generating OD Matrix heatmaps...")
    for fname, title, outname in configs:
        csv_path = od_dir / fname
        if csv_path.exists():
            plot_od_heatmap(csv_path, title, fig_dir / outname)


def plot_density_hourly_profile():
    """Plot hourly density profile for all intersections (line chart)."""
    df = pl.read_csv(RESULTS_DIR / "density" / "density_hourly.csv")
    fig_dir = FIGURES_DIR / "density"
    fig_dir.mkdir(parents=True, exist_ok=True)

    fig, ax = plt.subplots(figsize=(10, 5))

    for int_name in INTERSECTION_ORDER:
        subset = df.filter(pl.col("nearest_intersection") == int_name).sort("hour_wib")
        hours = subset["hour_wib"].to_list()
        maids = subset["avg_maids"].to_list()
        ax.plot(hours, maids, marker="o", markersize=3, linewidth=1.8,
                color=COLORS[int_name], label=INTERSECTION_LABELS[int_name])

    ax.set_xlabel("Jam (WIB)")
    ax.set_ylabel("Rata-rata MAID Unik")
    ax.set_title("Profil Kepadatan per Jam di Setiap Persimpangan")
    ax.set_xticks(range(0, 24, 2))
    ax.set_xlim(-0.5, 23.5)
    ax.legend(loc="upper left", framealpha=0.9)
    ax.grid(True, alpha=0.3)
    ax.axvspan(7, 9, alpha=0.08, color="red", label="_AM Peak")
    ax.axvspan(16, 18, alpha=0.08, color="orange", label="_PM Peak")

    fig.tight_layout()
    fig.savefig(fig_dir / "density_hourly_profile.png")
    plt.close(fig)
    print("  ✓ density_hourly_profile.png")


def plot_density_weekday_weekend():
    """Plot weekday vs weekend density comparison per intersection."""
    df = pl.read_csv(RESULTS_DIR / "density" / "density_weekday_weekend.csv")
    fig_dir = FIGURES_DIR / "density"
    fig_dir.mkdir(parents=True, exist_ok=True)

    fig, axes = plt.subplots(2, 3, figsize=(14, 8), sharey=True)
    axes = axes.flatten()

    for idx, int_name in enumerate(INTERSECTION_ORDER):
        ax = axes[idx]
        subset = df.filter(pl.col("nearest_intersection") == int_name)

        for is_weekday, label, color, ls in [
            (True, "Hari kerja", COLORS[int_name], "-"),
            (False, "Akhir pekan", COLORS[int_name], "--"),
        ]:
            data = subset.filter(pl.col("is_weekday") == is_weekday).sort("hour_wib")
            hours = data["hour_wib"].to_list()
            maids = data["avg_maids"].to_list()
            ax.plot(hours, maids, marker="o", markersize=2, linewidth=1.5,
                    linestyle=ls, color=color, label=label,
                    alpha=1.0 if is_weekday else 0.7)

        ax.set_title(INTERSECTION_LABELS[int_name], fontsize=11, fontweight="bold")
        ax.set_xlabel("Jam (WIB)")
        ax.set_xticks(range(0, 24, 4))
        ax.grid(True, alpha=0.3)
        ax.legend(fontsize=8)

    axes[0].set_ylabel("Rata-rata MAID Unik")
    axes[3].set_ylabel("Rata-rata MAID Unik")
    fig.suptitle("Perbandingan Kepadatan Hari Kerja dan Akhir Pekan", fontsize=13, fontweight="bold", y=1.01)
    fig.tight_layout()
    fig.savefig(fig_dir / "density_weekday_weekend.png")
    plt.close(fig)
    print("  ✓ density_weekday_weekend.png")


def plot_density_monthly():
    """Plot monthly density trends per intersection."""
    df = pl.read_csv(RESULTS_DIR / "density" / "density_monthly.csv")
    fig_dir = FIGURES_DIR / "density"
    fig_dir.mkdir(parents=True, exist_ok=True)

    fig, ax = plt.subplots(figsize=(10, 5))

    for int_name in INTERSECTION_ORDER:
        subset = df.filter(pl.col("nearest_intersection") == int_name).sort("month")
        months = subset["month"].to_list()
        maids = subset["n_maids"].to_list()
        ax.plot(months, maids, marker="s", markersize=5, linewidth=2,
                color=COLORS[int_name], label=INTERSECTION_LABELS[int_name])

    ax.set_xlabel("Bulan (YYYY-MM)")
    ax.set_ylabel("MAID Unik Bulanan")
    ax.set_title("Tren Kepadatan Bulanan di Setiap Persimpangan")
    ax.legend(loc="best", framealpha=0.9)
    ax.grid(True, alpha=0.3)
    plt.xticks(rotation=45, ha="right")

    fig.tight_layout()
    fig.savefig(fig_dir / "density_monthly_trend.png")
    plt.close(fig)
    print("  ✓ density_monthly_trend.png")


def plot_turning_movements():
    """Plot turning movement distribution per intersection."""
    df = pl.read_csv(RESULTS_DIR / "turning_movement" / "turning_movements.csv")
    fig_dir = FIGURES_DIR / "turning_movement"
    fig_dir.mkdir(parents=True, exist_ok=True)

    # Overall bar chart per intersection
    intersections_in_data = df["intersection"].unique().sort().to_list()

    fig, axes = plt.subplots(2, 3, figsize=(14, 8))
    axes = axes.flatten()

    for idx, int_name in enumerate(INTERSECTION_ORDER):
        ax = axes[idx]
        if int_name not in intersections_in_data:
            ax.set_visible(False)
            continue

        subset = df.filter(pl.col("intersection") == int_name).sort("count", descending=True)
        movements = subset["movement"].to_list()
        counts = subset["count"].to_list()

        short_labels = [
            m.replace("arriving_from_west", "datang barat")
            .replace("arriving_from_east", "datang timur")
            .replace("departing_west", "menuju barat")
            .replace("departing_east", "menuju timur")
            .replace("u_turn", "O=D")
            for m in movements
        ]

        bars = ax.barh(range(len(short_labels)), counts, color=COLORS.get(int_name, "#666"))
        ax.set_yticks(range(len(short_labels)))
        ax.set_yticklabels(short_labels, fontsize=8)
        ax.set_title(INTERSECTION_LABELS[int_name], fontsize=11, fontweight="bold")
        ax.invert_yaxis()

        # Add value labels
        for bar, val in zip(bars, counts):
            ax.text(bar.get_width() + max(counts) * 0.02, bar.get_y() + bar.get_height() / 2,
                    f"{val:,}", va="center", fontsize=7)

    fig.suptitle("Distribusi Pola Pergerakan per Persimpangan", fontsize=13, fontweight="bold", y=1.01)
    fig.tight_layout()
    fig.savefig(fig_dir / "turning_movements_all.png")
    plt.close(fig)
    print("  ✓ turning_movements_all.png")


def plot_od_weekday_weekend_comparison():
    """Side-by-side OD comparison: weekday vs weekend."""
    fig_dir = FIGURES_DIR / "od_matrix"
    fig_dir.mkdir(parents=True, exist_ok=True)

    od_dir = RESULTS_DIR / "od_matrix"
    df_wd = pl.read_csv(od_dir / "od_matrix_weekday.csv")
    df_we = pl.read_csv(od_dir / "od_matrix_weekend.csv")
    labels = [INTERSECTION_LABELS.get(c, c) for c in df_wd.columns]
    mat_wd = df_wd.to_numpy()
    mat_we = df_we.to_numpy()

    vmax = max(mat_wd.max(), mat_we.max())

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5.5))

    for ax, mat, title in [(ax1, mat_wd, "Hari Kerja"), (ax2, mat_we, "Akhir Pekan")]:
        im = ax.imshow(mat, cmap="YlOrRd", aspect="auto", vmin=0, vmax=vmax)
        ax.set_xticks(range(len(labels)))
        ax.set_yticks(range(len(labels)))
        ax.set_xticklabels(labels, rotation=45, ha="right")
        ax.set_yticklabels(labels)
        ax.set_xlabel("Tujuan")
        ax.set_ylabel("Asal")
        ax.set_title(title)

        for i in range(len(labels)):
            for j in range(len(labels)):
                val = mat[i, j]
                color = "white" if val > vmax * 0.6 else "black"
                ax.text(j, i, f"{int(val):,}", ha="center", va="center",
                        fontsize=7, color=color)

    fig.colorbar(im, ax=[ax1, ax2], shrink=0.8, label="Jumlah trip")
    fig.suptitle("Perbandingan Matriks OD: Hari Kerja vs Akhir Pekan", fontsize=13, fontweight="bold")
    fig.tight_layout()
    fig.savefig(fig_dir / "od_weekday_weekend_comparison.png")
    plt.close(fig)
    print("  ✓ od_weekday_weekend_comparison.png")


def plot_density_daily_timeseries():
    """Plot daily density time series for top 3 intersections."""
    df = pl.read_csv(RESULTS_DIR / "density" / "density_daily.csv")
    fig_dir = FIGURES_DIR / "density"
    fig_dir.mkdir(parents=True, exist_ok=True)

    fig, ax = plt.subplots(figsize=(14, 5))

    for int_name in ["condongcatur", "monjali", "kentungan"]:
        subset = df.filter(pl.col("nearest_intersection") == int_name).sort("date_wib")
        dates = subset["date_wib"].to_list()
        maids = subset["n_maids"].to_list()
        ax.plot(dates, maids, linewidth=0.8, alpha=0.7,
                color=COLORS[int_name], label=INTERSECTION_LABELS[int_name])

    ax.set_xlabel("Tanggal")
    ax.set_ylabel("MAID Unik Harian")
    ax.set_title("Kepadatan Harian pada Tiga Persimpangan Terpadat")
    ax.legend(loc="upper right", framealpha=0.9)
    ax.grid(True, alpha=0.3)

    # Show every 30th date label
    xtick_locs = range(0, len(dates), 30)
    ax.set_xticks([dates[i] for i in xtick_locs if i < len(dates)])
    plt.xticks(rotation=45, ha="right")

    fig.tight_layout()
    fig.savefig(fig_dir / "density_daily_timeseries.png")
    plt.close(fig)
    print("  ✓ density_daily_timeseries.png")


def plot_catchment_grid():
    """Plot estimated home-location catchment grids for each intersection."""
    fig_dir = FIGURES_DIR / "catchment"
    fig_dir.mkdir(parents=True, exist_ok=True)

    fig, axes = plt.subplots(2, 3, figsize=(13, 8), sharex=True, sharey=True)
    axes = axes.flatten()

    all_grids = []
    for int_name in INTERSECTION_ORDER:
        path = RESULTS_DIR / "catchment" / f"catchment_grid_{int_name}.csv"
        if path.exists():
            all_grids.append(pl.read_csv(path).with_columns(intersection=pl.lit(int_name)))
    if not all_grids:
        return

    combined = pl.concat(all_grids)
    vmax = combined["n_maids"].max()

    for idx, int_name in enumerate(INTERSECTION_ORDER):
        ax = axes[idx]
        path = RESULTS_DIR / "catchment" / f"catchment_grid_{int_name}.csv"
        if not path.exists():
            ax.set_visible(False)
            continue

        df = pl.read_csv(path).sort("n_maids", descending=True)
        sizes = 18 + (df["n_maids"].to_numpy() / vmax) * 260
        scatter = ax.scatter(
            df["home_lon"].to_numpy(),
            df["home_lat"].to_numpy(),
            s=sizes,
            c=df["n_maids"].to_numpy(),
            cmap="viridis",
            alpha=0.75,
            edgecolors="white",
            linewidths=0.4,
            vmin=0,
            vmax=vmax,
        )

        # Mark top catchment cell.
        top = df.row(0, named=True)
        ax.scatter([top["home_lon"]], [top["home_lat"]], marker="*", s=160,
                   color="#d62728", edgecolors="white", linewidths=0.5)
        ax.set_title(INTERSECTION_LABELS[int_name], fontsize=11, fontweight="bold")
        ax.grid(True, alpha=0.25)

    for ax in axes[3:]:
        ax.set_xlabel("Longitude")
    axes[0].set_ylabel("Latitude")
    axes[3].set_ylabel("Latitude")

    cbar = fig.colorbar(scatter, ax=axes.tolist(), shrink=0.82, label="Jumlah MAID")
    fig.suptitle("Sebaran Catchment Area Berdasarkan Estimasi Lokasi Rumah", fontsize=13, fontweight="bold", y=0.97)
    fig.savefig(fig_dir / "catchment_grid_comparison.png")
    plt.close(fig)
    print("  ✓ catchment_grid_comparison.png")


def main():
    """Generate all visualizations."""
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    print("=" * 60)
    print("  GENERATING THESIS FIGURES")
    print("=" * 60)

    plot_pipeline_flowchart()
    plot_backbone_network_map()
    plot_all_od_matrices()
    plot_od_weekday_weekend_comparison()
    plot_density_hourly_profile()
    plot_density_weekday_weekend()
    plot_density_monthly()
    plot_density_daily_timeseries()
    plot_turning_movements()

    print(f"\n✓ All figures saved to {FIGURES_DIR}/")


if __name__ == "__main__":
    main()
