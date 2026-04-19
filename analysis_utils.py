"""
Utility functions untuk analisis lalu lintas Ring Road Utara.
=============================================================
Modul ini berisi fungsi pembantu untuk map matching, analisis 
kepadatan, kecepatan, dan perempatan.
"""

import os
import json
import numpy as np
import pandas as pd
import geopandas as gpd
import folium
import osmnx as ox
from branca.colormap import LinearColormap
from shapely.geometry import Point
from pathlib import Path

# ---------------------------------------------------------------------------
# Konstanta
# ---------------------------------------------------------------------------
RING_ROAD_CENTER = [-7.7559, 110.3877]
RING_ROAD_EDGES_GEOJSON = "cache/ring_road_utara_edges.geojson"
RING_ROAD_FILTERED_GEOJSON = "cache/ring_road_utara_filtered.geojson"
GPS_PARQUET = "DataGPS_parquet/gps_ring_road_utara.parquet"
MATCHED_PARQUET = "DataGPS_parquet/matched_ring_road.parquet"

INTERSECTIONS = {
    "Jombor": {"lat": -7.7492, "lon": 110.3621},
    "Monjali": {"lat": -7.7512, "lon": 110.3712},
    "Kentungan": {"lat": -7.7559, "lon": 110.3877},
    "Condongcatur": {"lat": -7.7584, "lon": 110.3957},
    "UPN/Veteran": {"lat": -7.7617, "lon": 110.4120},
    "Maguwoharjo": {"lat": -7.7660, "lon": 110.4330}
}


# Batas Ring Road Utara (dari notebook eksisting)
LAT_NORTH = -7.737
LAT_SOUTH = -7.777
LON_WEST = 110.335
LON_EAST = 110.438


# ---------------------------------------------------------------------------
# Haversine Distance
# ---------------------------------------------------------------------------
def haversine(lat1, lon1, lat2, lon2):
    """Hitung jarak Haversine (dalam meter) antar koordinat."""
    R = 6_371_000  # radius bumi (meter)
    phi1, phi2 = np.radians(lat1), np.radians(lat2)
    dphi = np.radians(lat2 - lat1)
    dlam = np.radians(lon2 - lon1)
    a = np.sin(dphi / 2) ** 2 + np.cos(phi1) * np.cos(phi2) * np.sin(dlam / 2) ** 2
    return 2 * R * np.arctan2(np.sqrt(a), np.sqrt(1 - a))


# ---------------------------------------------------------------------------
# Graph Loading
# ---------------------------------------------------------------------------
def load_road_graph():
    """
    Load / download OSMnx drive graph untuk area Ring Road Utara.
    Menggunakan cache OSMnx untuk load yang lebih cepat.
    """
    ox.settings.log_console = False
    ox.settings.use_cache = True
    ox.settings.cache_folder = "cache"

    # Gunakan Sleman agar Ring Road Utara ter‑cover penuh
    place = "Daerah Istimewa Yogyakarta, Indonesia"
    custom_filter = '["highway"~"motorway|trunk|primary"]'
    # Gunakan parameter yang persis sama dengan folium-test.ipynb
    G = ox.graph_from_place(place, custom_filter=custom_filter, retain_all=True)
    return G


def load_edges_geodataframe(G=None):
    """
    Load edges sebagai GeoDataFrame.
    Jika G diberikan, pakai `graph_to_gdfs`.
    Jika tidak, load dari GeoJSON cache.
    """
    if G is not None:
        _, edges_gdf = ox.graph_to_gdfs(G)
        return edges_gdf

    path = RING_ROAD_FILTERED_GEOJSON
    if os.path.exists(path):
        return gpd.read_file(path)
    return None


# ---------------------------------------------------------------------------
# GPS Data Loading
# ---------------------------------------------------------------------------
def load_gps_data(
    parquet_path=GPS_PARQUET,
    ts_start=None,
    ts_end=None,
    hour_start=None,
    hour_end=None,
    sample_n=None,
):
    """
    Load data GPS dari Parquet via DuckDB.

    Parameters
    ----------
    ts_start, ts_end : int, optional
        Unix timestamp range filter.
    hour_start, hour_end : int, optional
        Jam dalam sehari (0-23) untuk filter.
    sample_n : int, optional
        Jumlah baris maximum yang diambil.

    Returns
    -------
    pd.DataFrame
        Kolom: maid, latitude, longitude, timestamp, datetime
    """
    import duckdb

    con = duckdb.connect()
    os.makedirs(".duckdb_tmp", exist_ok=True)
    con.execute("SET temp_directory='.duckdb_tmp'")
    con.execute("SET memory_limit='3GB'")
    con.execute("SET threads=4")

    where_clauses = []
    if ts_start is not None:
        where_clauses.append(f"timestamp >= {ts_start}")
    if ts_end is not None:
        where_clauses.append(f"timestamp <= {ts_end}")
    if hour_start is not None and hour_end is not None:
        where_clauses.append(
            f"extract(hour from to_timestamp(timestamp)) >= {hour_start}"
        )
        where_clauses.append(
            f"extract(hour from to_timestamp(timestamp)) <= {hour_end}"
        )

    where = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""
    limit = f"LIMIT {sample_n}" if sample_n else ""

    query = f"""
        SELECT maid, latitude, longitude, timestamp
        FROM read_parquet('{parquet_path}')
        {where}
        {limit}
    """
    df = con.execute(query).df()
    con.close()

    if not df.empty:
        df["datetime"] = pd.to_datetime(df["timestamp"], unit="s", utc=True)
        df["datetime"] = df["datetime"].dt.tz_convert("Asia/Jakarta")
        df["hour"] = df["datetime"].dt.hour
        df["date"] = df["datetime"].dt.date

    return df


# ---------------------------------------------------------------------------
# Edge Snapping (Nearest-Edge)
# ---------------------------------------------------------------------------
def snap_to_nearest_edges(G, latitudes, longitudes):
    """
    Snap titik GPS ke edge jalan terdekat menggunakan R-tree OSMnx.

    Returns
    -------
    np.ndarray
        Array of (u, v, key) tuples.
    """
    lats = np.asarray(latitudes, dtype=float)
    lons = np.asarray(longitudes, dtype=float)
    nearest = ox.nearest_edges(G, X=lons, Y=lats)
    return nearest


def add_edge_info(df, G):
    """
    Tambahkan informasi edge (u, v) ke DataFrame GPS.
    """
    nearest = snap_to_nearest_edges(
        G, df["latitude"].values, df["longitude"].values
    )
    df = df.copy()
    df["edge_u"] = [e[0] for e in nearest]
    df["edge_v"] = [e[1] for e in nearest]
    df["edge_key"] = [f"{e[0]}-{e[1]}" for e in nearest]
    return df


# ---------------------------------------------------------------------------
# Traffic Density  
# ---------------------------------------------------------------------------
def compute_edge_density(df, group_by="hour"):
    """
    Hitung kepadatan (jumlah GPS point) per edge per kelompok waktu.

    Parameters
    ----------
    df : pd.DataFrame
        Harus memiliki kolom edge_u, edge_v, edge_key, dan group_by column.
    group_by : str
        Kolom grouping: 'hour', 'date', dll.

    Returns
    -------
    pd.DataFrame
        Kolom: edge_u, edge_v, edge_key, {group_by}, count
    """
    density = (
        df.groupby(["edge_u", "edge_v", "edge_key", group_by])
        .size()
        .reset_index(name="count")
    )
    return density


def compute_total_edge_density(df):
    """Hitung total kepadatan per edge (tanpa grouping waktu)."""
    density = (
        df.groupby(["edge_u", "edge_v", "edge_key"])
        .size()
        .reset_index(name="count")
    )
    return density.sort_values("count", ascending=False)


# ---------------------------------------------------------------------------
# Speed Analysis
# ---------------------------------------------------------------------------
def compute_trajectory_speeds(df):
    """
    Hitung kecepatan antar titik berurutan untuk setiap MAID.

    Returns
    -------
    pd.DataFrame
        Dengan kolom tambahan: speed_kmh, distance_m, time_diff_s
    """
    df = df.sort_values(["maid", "timestamp"]).copy()
    df["prev_lat"] = df.groupby("maid")["latitude"].shift(1)
    df["prev_lon"] = df.groupby("maid")["longitude"].shift(1)
    df["prev_ts"] = df.groupby("maid")["timestamp"].shift(1)

    mask = df["prev_lat"].notna()
    df.loc[mask, "distance_m"] = haversine(
        df.loc[mask, "prev_lat"].values,
        df.loc[mask, "prev_lon"].values,
        df.loc[mask, "latitude"].values,
        df.loc[mask, "longitude"].values,
    )
    df.loc[mask, "time_diff_s"] = (
        df.loc[mask, "timestamp"] - df.loc[mask, "prev_ts"]
    )

    # Hitung kecepatan (km/h), hindari pembagian nol
    valid = mask & (df["time_diff_s"] > 0) & (df["time_diff_s"] < 3600)
    df.loc[valid, "speed_kmh"] = (
        df.loc[valid, "distance_m"] / df.loc[valid, "time_diff_s"] * 3.6
    )

    # Filter kecepatan realistis (< 200 km/h)
    df.loc[df["speed_kmh"] > 200, "speed_kmh"] = np.nan

    df.drop(columns=["prev_lat", "prev_lon", "prev_ts"], inplace=True)
    return df


def compute_edge_avg_speed(df):
    """Hitung kecepatan rata-rata per edge."""
    speed = (
        df.dropna(subset=["speed_kmh"])
        .groupby(["edge_u", "edge_v", "edge_key"])
        .agg(
            avg_speed=("speed_kmh", "mean"),
            median_speed=("speed_kmh", "median"),
            count=("speed_kmh", "count"),
        )
        .reset_index()
    )
    return speed.sort_values("avg_speed")


# ---------------------------------------------------------------------------
# Intersection Analysis
# ---------------------------------------------------------------------------
def detect_intersections(G, min_degree=3):
    """
    Deteksi perempatan — node dengan degree ≥ min_degree.

    Returns
    -------
    dict
        {node_id: {'lat': float, 'lon': float, 'degree': int}}
    """
    intersections = {}
    for node, degree in G.degree():
        if degree >= min_degree:
            data = G.nodes[node]
            intersections[node] = {
                "lat": data["y"],
                "lon": data["x"],
                "degree": degree,
            }
    return intersections


def compute_intersection_density(df, G, intersections):
    """
    Hitung kepadatan di setiap perempatan.
    Perempatan = node yang merupakan u atau v dari edge yang di-match.
    """
    int_set = set(intersections.keys())

    # Hitung berapa kali setiap intersection muncul sebagai u atau v
    u_counts = df[df["edge_u"].isin(int_set)]["edge_u"].value_counts()
    v_counts = df[df["edge_v"].isin(int_set)]["edge_v"].value_counts()
    combined = u_counts.add(v_counts, fill_value=0).astype(int)

    results = []
    for node_id, count in combined.items():
        info = intersections.get(node_id, {})
        results.append(
            {
                "node_id": node_id,
                "lat": info.get("lat", 0),
                "lon": info.get("lon", 0),
                "degree": info.get("degree", 0),
                "traffic_count": count,
            }
        )
    return pd.DataFrame(results).sort_values("traffic_count", ascending=False)


def compute_turning_movements(df, intersections):
    """
    Analisis pergerakan di perempatan: dari edge mana ke edge mana.
    Untuk setiap MAID, ketika berpindah dari satu edge ke edge lain 
    melalui perempatan, catat pergerakan tersebut.

    Returns
    -------
    pd.DataFrame
        Kolom: intersection_node, from_edge, to_edge, count
    """
    int_set = set(intersections.keys())
    movements = []

    for maid, group in df.sort_values("timestamp").groupby("maid"):
        edges = list(zip(group["edge_u"], group["edge_v"]))
        for i in range(1, len(edges)):
            prev_u, prev_v = edges[i - 1]
            curr_u, curr_v = edges[i]

            # Cek shared node di perempatan
            shared = {prev_u, prev_v} & {curr_u, curr_v} & int_set
            if shared:
                node = next(iter(shared))
                from_edge = f"{prev_u}-{prev_v}"
                to_edge = f"{curr_u}-{curr_v}"
                if from_edge != to_edge:
                    movements.append(
                        {
                            "intersection_node": node,
                            "from_edge": from_edge,
                            "to_edge": to_edge,
                        }
                    )

    if not movements:
        return pd.DataFrame(
            columns=["intersection_node", "from_edge", "to_edge", "count"]
        )

    mv_df = pd.DataFrame(movements)
    result = (
        mv_df.groupby(["intersection_node", "from_edge", "to_edge"])
        .size()
        .reset_index(name="count")
        .sort_values("count", ascending=False)
    )
    return result


# ---------------------------------------------------------------------------
# Folium Map Creators
# ---------------------------------------------------------------------------
def _get_edge_geometry(G, u, v):
    """Get LineString geometry for edge (u, v) from graph."""
    try:
        data = G.edges[u, v, 0]
        if "geometry" in data:
            return data["geometry"]
        # Fallback: straight line between nodes
        from shapely.geometry import LineString

        p1 = (G.nodes[u]["x"], G.nodes[u]["y"])
        p2 = (G.nodes[v]["x"], G.nodes[v]["y"])
        return LineString([p1, p2])
    except Exception:
        return None


def create_base_map(center=None, zoom=14, tiles="CartoDB dark_matter"):
    """Buat base Folium map."""
    if center is None:
        center = RING_ROAD_CENTER
    m = folium.Map(
        location=center,
        zoom_start=zoom,
        tiles=tiles,
    )
    return m


def add_road_network_layer(m, edges_gdf=None, geojson_path=None, color="#3b82f6"):
    """Tambahkan layer jaringan jalan ke peta."""
    if edges_gdf is not None:
        data = edges_gdf[["geometry"]].to_json()
    elif geojson_path and os.path.exists(geojson_path):
        with open(geojson_path) as f:
            data = f.read()
    else:
        return m

    folium.GeoJson(
        data,
        name="Ring Road Utara",
        style_function=lambda x: {
            "color": color,
            "weight": 3,
            "opacity": 0.5,
        },
    ).add_to(m)
    return m


def create_density_map(G, density_df, center=None, zoom=14):
    """
    Buat peta kepadatan — warna edge berdasarkan jumlah titik GPS.
    """
    m = create_base_map(center, zoom)

    if density_df.empty:
        return m

    max_count = density_df["count"].max()
    min_count = density_df["count"].min()

    colormap = LinearColormap(
        colors=["#10b981", "#f59e0b", "#ef4444"],
        vmin=min_count,
        vmax=max_count,
        caption="Kepadatan Lalu Lintas (jumlah titik GPS)",
    )

    for _, row in density_df.iterrows():
        geom = _get_edge_geometry(G, int(row["edge_u"]), int(row["edge_v"]))
        if geom is None:
            continue

        coords = [(y, x) for x, y in geom.coords]
        color = colormap(row["count"])
        weight = max(3, min(10, row["count"] / max_count * 10))

        folium.PolyLine(
            locations=coords,
            color=color,
            weight=weight,
            opacity=0.85,
            popup=folium.Popup(
                f"<b>Kepadatan:</b> {row['count']:,} titik<br>"
                f"<b>Edge:</b> {row['edge_key']}",
                max_width=250,
            ),
        ).add_to(m)

    colormap.add_to(m)
    return m


def create_speed_map(G, speed_df, center=None, zoom=14):
    """
    Buat peta kecepatan — warna edge berdasarkan kecepatan rata-rata.
    Merah = lambat (macet), Hijau = cepat (lancar).
    """
    m = create_base_map(center, zoom)

    if speed_df.empty:
        return m

    max_speed = speed_df["avg_speed"].quantile(0.95)
    min_speed = speed_df["avg_speed"].quantile(0.05)

    # Warna terbalik: merah = lambat, hijau = cepat
    colormap = LinearColormap(
        colors=["#ef4444", "#f59e0b", "#10b981"],
        vmin=min_speed,
        vmax=max_speed,
        caption="Kecepatan Rata-rata (km/h)",
    )

    for _, row in speed_df.iterrows():
        geom = _get_edge_geometry(G, int(row["edge_u"]), int(row["edge_v"]))
        if geom is None:
            continue

        coords = [(y, x) for x, y in geom.coords]
        color = colormap(min(row["avg_speed"], max_speed))

        folium.PolyLine(
            locations=coords,
            color=color,
            weight=5,
            opacity=0.85,
            popup=folium.Popup(
                f"<b>Speed:</b> {row['avg_speed']:.1f} km/h<br>"
                f"<b>Median:</b> {row['median_speed']:.1f} km/h<br>"
                f"<b>Sample:</b> {row['count']:,}",
                max_width=250,
            ),
        ).add_to(m)

    colormap.add_to(m)
    return m


def create_intersection_map(intersections_df, center=None, zoom=14):
    """
    Buat peta perempatan — ukuran circle berdasarkan kepadatan.
    """
    m = create_base_map(center, zoom)

    # Tambahkan road network layer
    add_road_network_layer(
        m, geojson_path=RING_ROAD_FILTERED_GEOJSON, color="#3b82f6"
    )

    if intersections_df.empty:
        return m

    max_traffic = intersections_df["traffic_count"].max()

    for _, row in intersections_df.iterrows():
        radius = max(5, min(25, row["traffic_count"] / max_traffic * 25))
        opacity = max(0.4, min(0.9, row["traffic_count"] / max_traffic))

        folium.CircleMarker(
            location=[row["lat"], row["lon"]],
            radius=radius,
            color="#8b5cf6",
            fill=True,
            fillColor="#8b5cf6",
            fillOpacity=opacity,
            popup=folium.Popup(
                f"<b>Perempatan</b><br>"
                f"Node: {row['node_id']}<br>"
                f"Degree: {row['degree']}<br>"
                f"Traffic: {row['traffic_count']:,}",
                max_width=250,
            ),
        ).add_to(m)

    return m
