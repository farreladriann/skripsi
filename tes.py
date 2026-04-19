"""
Analisis Pergerakan Ring Road Utara – 4 Titik Ramp Exit Tol
Tol Solo–Yogyakarta–NYIA Kulon Progo (segmen elevated dalam kota)

Ramp yang dianalisis:
  1. Maguwoharjo  – dekat Stadion Maguwoharjo / Ring Road Timur
  2. UPN/Seturan  – sekitar UPN Veteran / Jl. Seturan Raya
  3. Monjali      – Monumen Jogja Kembali / Jl. Magelang
  4. Trihanggo    – Mlati / Kronggahan

Analisis yang dilakukan:
  A. Jaringan jalan sekitar Ring Road Utara
  B. Ego-graph 500m dari tiap ramp (jangkauan langsung)
  C. Betweenness centrality (node paling kritis/ramai dilalui)
  D. Degree centrality (persimpangan paling terhubung)
  E. Isochrone 5 menit berjalan / berkendara dari tiap ramp
  F. Export GeoJSON untuk QGIS

Install:
    pip install osmnx geopandas matplotlib networkx shapely
"""

import osmnx as ox
import geopandas as gpd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.colors as mcolors
import networkx as nx
import numpy as np
from shapely.geometry import Point
import warnings
warnings.filterwarnings("ignore")

# ─────────────────────────────────────────────
# 0. KONFIGURASI
# ─────────────────────────────────────────────
ox.settings.log_console = False
ox.settings.use_cache = True

# Koordinat 4 titik ramp (lat, lon)
RAMP_EXITS = {
    "Maguwoharjo":  (-7.7654, 110.4148),   # dekat Stadion / RR Timur
    "UPN/Seturan":  (-7.7622, 110.3958),   # sekitar UPN Veteran
    "Monjali":      (-7.7497, 110.3673),   # Monumen Jogja Kembali
    "Trihanggo":    (-7.7385, 110.3441),   # Mlati / Kronggahan
}

RAMP_COLORS = {
    "Maguwoharjo": "#E24B4A",   # merah
    "UPN/Seturan": "#EF9F27",   # amber
    "Monjali":     "#1D9E75",   # teal
    "Trihanggo":   "#378ADD",   # biru
}

# Radius buffer analisis (meter)
BUFFER_RADIUS  = 2000   # ambil graph seluruh area RRU
EGO_RADIUS     = 500    # ego-graph per ramp
ISO_TRIP_TIME  = 5      # menit untuk isochrone
TRAVEL_SPEED   = 30     # km/jam asumsi kendaraan dalam kota

# ─────────────────────────────────────────────
# 1. AMBIL GRAPH JARINGAN JALAN
# ─────────────────────────────────────────────
print("⏳ Mengambil graph jaringan jalan dari OpenStreetMap...")

# Titik tengah – sekitar antara Monjali dan UPN (Ring Road Utara)
CENTER_LAT, CENTER_LON = -7.752, 110.384

G = ox.graph_from_point(
    (CENTER_LAT, CENTER_LON),
    dist=BUFFER_RADIUS,
    network_type="drive",
    simplify=True
)
print(f"   ✓ Graph: {len(G.nodes):,} node, {len(G.edges):,} edge")

# Konversi ke GeoDataFrame
nodes_gdf, edges_gdf = ox.graph_to_gdfs(G)

# ─────────────────────────────────────────────
# 2. FILTER RING ROAD UTARA
# ─────────────────────────────────────────────
def is_ring_road_utara(name):
    if isinstance(name, str):
        return any(k in name for k in ["Ring Road Utara", "Ringroad Utara", "Jalan Lingkar Utara"])
    if isinstance(name, list):
        return any(is_ring_road_utara(n) for n in name)
    return False

rru_edges = edges_gdf[edges_gdf["name"].apply(is_ring_road_utara)].copy()
print(f"   ✓ Ring Road Utara: {len(rru_edges)} segmen, total {rru_edges['length'].sum()/1000:.2f} km")

# ─────────────────────────────────────────────
# 3. CARI NODE TERDEKAT UNTUK TIAP RAMP
# ─────────────────────────────────────────────
print("\n📍 Mencari node terdekat untuk tiap ramp...")
ramp_nodes = {}
for name, (lat, lon) in RAMP_EXITS.items():
    node_id = ox.nearest_nodes(G, X=lon, Y=lat)
    node_data = G.nodes[node_id]
    dist_m = ox.distance.great_circle(lat, lon, node_data["y"], node_data["x"])
    ramp_nodes[name] = node_id
    print(f"   {name}: node {node_id} (jarak {dist_m:.0f}m dari koordinat ramp)")

# ─────────────────────────────────────────────
# 4. BETWEENNESS CENTRALITY
# ─────────────────────────────────────────────
print("\n🔢 Menghitung betweenness centrality (ini bisa makan waktu ~30 detik)...")
# Gunakan subgraph yang diperkecil agar cepat
G_sub = ox.truncate.truncate_graph_dist(G, CENTER_LAT, CENTER_LON, max_dist=BUFFER_RADIUS)
bc = nx.betweenness_centrality(G_sub, normalized=True, weight="length")
nx.set_node_attributes(G_sub, bc, "betweenness")
nodes_sub, _ = ox.graph_to_gdfs(G_sub)
nodes_sub["betweenness"] = nodes_sub.index.map(bc).fillna(0)
print(f"   ✓ Selesai. Node paling kritis: {max(bc, key=bc.get)} (skor {max(bc.values()):.4f})")

# ─────────────────────────────────────────────
# 5. EGO-GRAPH (radius 500m dari tiap ramp)
# ─────────────────────────────────────────────
print("\n🔵 Membuat ego-graph 500m per ramp...")
ego_graphs = {}
for name, node_id in ramp_nodes.items():
    ego = nx.ego_graph(G_sub, node_id, radius=EGO_RADIUS, distance="length")
    ego_graphs[name] = ego
    ego_nodes, ego_edges = ox.graph_to_gdfs(ego)
    print(f"   {name}: {len(ego.nodes)} node, {len(ego.edges)} edge dalam radius {EGO_RADIUS}m")

# ─────────────────────────────────────────────
# 6. ISOCHRONE 5 MENIT
# ─────────────────────────────────────────────
print(f"\n🕐 Membuat isochrone {ISO_TRIP_TIME} menit (asumsi {TRAVEL_SPEED} km/jam)...")
meters_per_min = TRAVEL_SPEED * 1000 / 60
trip_distance  = ISO_TRIP_TIME * meters_per_min  # dalam meter

isochrone_polys = {}
for name, node_id in ramp_nodes.items():
    # Subgraph dalam jarak trip_distance dari ramp
    subgraph = nx.ego_graph(G_sub, node_id, radius=trip_distance, distance="length")
    node_pts  = [Point(G_sub.nodes[n]["x"], G_sub.nodes[n]["y"]) for n in subgraph.nodes]
    if len(node_pts) > 2:
        from shapely.ops import unary_union
        iso_poly = unary_union([p.buffer(0.001) for p in node_pts]).convex_hull
        isochrone_polys[name] = iso_poly
    print(f"   {name}: {len(subgraph.nodes)} node terjangkau")

# ─────────────────────────────────────────────
# 7. VISUALISASI UTAMA
# ─────────────────────────────────────────────
print("\n🗺️  Membuat peta visualisasi...")
fig, axes = plt.subplots(1, 2, figsize=(20, 10))
fig.patch.set_facecolor("#0f1117")
for ax in axes:
    ax.set_facecolor("#0f1117")

_, edges_sub = ox.graph_to_gdfs(G_sub)

# ── Panel Kiri: Betweenness Centrality Heatmap ──────────────────────────────
ax = axes[0]
ax.set_title("Betweenness Centrality – Ring Road Utara\n(Node paling kritis dalam pergerakan lalu lintas)",
             color="white", fontsize=12, pad=10)

# Semua jalan (latar)
edges_sub.plot(ax=ax, color="#2a2a3a", linewidth=0.4, alpha=0.7)

# Ring Road Utara highlight
if len(rru_edges) > 0:
    rru_edges.plot(ax=ax, color="#ffffff", linewidth=2.5, alpha=0.9, label="Ring Road Utara")

# Node betweenness sebagai scatter (warna = intensitas)
bc_values = nodes_sub["betweenness"].values
norm = mcolors.LogNorm(vmin=max(bc_values.min(), 1e-6), vmax=bc_values.max())
cmap = plt.cm.YlOrRd

ax.scatter(
    nodes_sub.geometry.x,
    nodes_sub.geometry.y,
    c=bc_values,
    cmap=cmap,
    norm=norm,
    s=5,
    alpha=0.8,
    zorder=3
)

# Colorbar
sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
sm.set_array([])
cbar = fig.colorbar(sm, ax=ax, fraction=0.025, pad=0.02)
cbar.set_label("Betweenness centrality", color="white", fontsize=9)
cbar.ax.yaxis.set_tick_params(color="white")
plt.setp(cbar.ax.yaxis.get_ticklabels(), color="white")

# Plot ramp points
for name, (lat, lon) in RAMP_EXITS.items():
    color = RAMP_COLORS[name]
    ax.scatter(lon, lat, s=150, c=color, marker="*", zorder=6, edgecolors="white", linewidths=0.8)
    ax.annotate(
        name,
        xy=(lon, lat), xytext=(6, 6),
        textcoords="offset points",
        color="white", fontsize=8,
        bbox=dict(boxstyle="round,pad=0.2", facecolor=color, alpha=0.85, edgecolor="none")
    )

ax.set_xlabel("Longitude", color="white", fontsize=9)
ax.set_ylabel("Latitude", color="white", fontsize=9)
ax.tick_params(colors="white", labelsize=8)
for spine in ax.spines.values():
    spine.set_edgecolor("#444")

# ── Panel Kanan: Ego-graph + Isochrone per Ramp ─────────────────────────────
ax = axes[1]
ax.set_title(f"Ego-graph (radius {EGO_RADIUS}m) + Isochrone {ISO_TRIP_TIME} menit\nper titik ramp exit tol",
             color="white", fontsize=12, pad=10)

# Semua jalan latar
edges_sub.plot(ax=ax, color="#2a2a3a", linewidth=0.4, alpha=0.6)

# Ring Road Utara
if len(rru_edges) > 0:
    rru_edges.plot(ax=ax, color="#ffffff", linewidth=2.5, alpha=0.9)

# Isochrone polygons
for name, poly in isochrone_polys.items():
    color = RAMP_COLORS[name]
    iso_gdf = gpd.GeoDataFrame(geometry=[poly], crs="EPSG:4326")
    iso_gdf.plot(ax=ax, color=color, alpha=0.15, zorder=2)
    iso_gdf.boundary.plot(ax=ax, color=color, linewidth=1.2, alpha=0.6, zorder=3)

# Ego-graph edges
for name, ego in ego_graphs.items():
    color = RAMP_COLORS[name]
    if len(ego.edges) > 0:
        ego_nodes_gdf, ego_edges_gdf = ox.graph_to_gdfs(ego)
        ego_edges_gdf.plot(ax=ax, color=color, linewidth=1.2, alpha=0.75, zorder=4)

# Ramp points
for name, (lat, lon) in RAMP_EXITS.items():
    color = RAMP_COLORS[name]
    ax.scatter(lon, lat, s=160, c=color, marker="*", zorder=7, edgecolors="white", linewidths=0.8)
    ax.annotate(
        name,
        xy=(lon, lat), xytext=(6, 6),
        textcoords="offset points",
        color="white", fontsize=8,
        bbox=dict(boxstyle="round,pad=0.2", facecolor=color, alpha=0.85, edgecolor="none")
    )

# Legend
legend_patches = [
    mpatches.Patch(color="#ffffff", label="Ring Road Utara"),
] + [
    mpatches.Patch(color=RAMP_COLORS[n], label=f"{n} (ego+iso)")
    for n in RAMP_EXITS
]
ax.legend(handles=legend_patches, loc="lower left", fontsize=8,
          facecolor="#1a1a2e", edgecolor="#444", labelcolor="white")

ax.set_xlabel("Longitude", color="white", fontsize=9)
ax.set_ylabel("Latitude", color="white", fontsize=9)
ax.tick_params(colors="white", labelsize=8)
for spine in ax.spines.values():
    spine.set_edgecolor("#444")

plt.tight_layout()
plt.savefig("peta_analisis_rru_exit.png", dpi=180, bbox_inches="tight",
            facecolor=fig.get_facecolor())
print("   ✓ Disimpan: peta_analisis_rru_exit.png")
plt.show()

# ─────────────────────────────────────────────
# 8. RINGKASAN STATISTIK TIAP RAMP
# ─────────────────────────────────────────────
print("\n" + "="*60)
print("RINGKASAN ANALISIS TIAP RAMP")
print("="*60)

for name, node_id in ramp_nodes.items():
    ego = ego_graphs[name]
    ego_bc = {n: bc.get(n, 0) for n in ego.nodes}
    top_node = max(ego_bc, key=ego_bc.get)
    top_bc   = ego_bc[top_node]
    avg_degree = np.mean([d for _, d in ego.degree()])

    print(f"\n📍 {name}")
    print(f"   Node OSM     : {node_id}")
    print(f"   Betweenness  : {bc.get(node_id, 0):.5f} (ramp node itu sendiri)")
    print(f"   Node kritis  : {top_node} (BC={top_bc:.5f}) dalam radius {EGO_RADIUS}m")
    print(f"   Avg degree   : {avg_degree:.2f} (rata-rata persimpangan terhubung)")
    print(f"   Jalan dalam ego-graph: {len(ego.edges)}")

# ─────────────────────────────────────────────
# 9. EXPORT GEOJSON
# ─────────────────────────────────────────────
print("\n💾 Export GeoJSON...")

# Ring Road Utara
if len(rru_edges) > 0:
    rru_edges[["name","highway","length","geometry"]].to_file(
        "ring_road_utara.geojson", driver="GeoJSON")
    print("   ✓ ring_road_utara.geojson")

# Ramp points
import json
ramp_features = []
for name, (lat, lon) in RAMP_EXITS.items():
    ramp_features.append({
        "type": "Feature",
        "properties": {"name": name, "jenis": "ramp_exit_tol",
                       "betweenness": bc.get(ramp_nodes[name], 0)},
        "geometry": {"type": "Point", "coordinates": [lon, lat]}
    })
with open("ramp_exits.geojson", "w") as f:
    json.dump({"type": "FeatureCollection", "features": ramp_features}, f, indent=2)
print("   ✓ ramp_exits.geojson")

# Isochrone polygons
if isochrone_polys:
    iso_features = []
    for name, poly in isochrone_polys.items():
        iso_features.append({
            "type": "Feature",
            "properties": {"name": name, "trip_time_menit": ISO_TRIP_TIME,
                           "travel_speed_kmh": TRAVEL_SPEED},
            "geometry": poly.__geo_interface__
        })
    with open("isochrone_ramp.geojson", "w") as f:
        json.dump({"type": "FeatureCollection", "features": iso_features}, f, indent=2)
    print("   ✓ isochrone_ramp.geojson")

print("\n✅ Selesai! File output:")
print("   peta_analisis_rru_exit.png  → visualisasi peta")
print("   ring_road_utara.geojson     → segmen RRU (buka di QGIS)")
print("   ramp_exits.geojson          → titik 4 ramp exit")
print("   isochrone_ramp.geojson      → area 5 menit dari tiap ramp")