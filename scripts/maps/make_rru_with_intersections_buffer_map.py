"""Create a Folium HTML map for QGIS-clean RRU with intersections and a 20 m buffer.

Input:
- data/processed/network/rru_with_intersection_clean.geojson

Output:
- deliverables/maps/rru_with_intersections_buffer_20m.html
"""

from __future__ import annotations

from pathlib import Path
import json
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import folium
import geopandas as gpd
from folium.plugins import Fullscreen, MeasureControl, MiniMap

from configs import intersections
from src.rru.paths import RRU_WITH_INTERSECTION_CLEAN_GEOJSON, require_path

OUTPUT_DIR = PROJECT_ROOT / "deliverables" / "maps"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

BUFFER_M = 20.0
METRIC_CRS = "EPSG:32749"  # UTM zone 49S, suitable for Yogyakarta
WGS84 = "EPSG:4326"


def _clean_for_geojson(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """Convert non-JSON-friendly columns to strings for Folium GeoJson."""
    out = gdf.copy()
    for col in out.columns:
        if col == out.geometry.name:
            continue
        out[col] = out[col].apply(
            lambda v: json.dumps(v, ensure_ascii=False) if isinstance(v, (list, dict, tuple)) else v
        )
    return out


def main() -> None:
    # Use the QGIS-curated fishbone network as the authoritative map input.
    roads = gpd.read_file(require_path(RRU_WITH_INTERSECTION_CLEAN_GEOJSON, "QGIS-clean fishbone network"))
    if roads.crs is None:
        roads = roads.set_crs(WGS84)
    roads = roads.to_crs(WGS84)

    # 20 m metric buffer around the rru_with_intersections linework.
    roads_m = roads.to_crs(METRIC_CRS)
    buffer_geom_m = roads_m.geometry.buffer(BUFFER_M).union_all()
    buffer_gdf = gpd.GeoDataFrame(
        {"name": [f"Buffer {BUFFER_M:g} m dari rru_with_intersections"], "buffer_m": [BUFFER_M]},
        geometry=[buffer_geom_m],
        crs=METRIC_CRS,
    ).to_crs(WGS84)

    roads_clean = _clean_for_geojson(roads)

    bounds = roads.total_bounds  # minx, miny, maxx, maxy
    center_lat = (bounds[1] + bounds[3]) / 2
    center_lon = (bounds[0] + bounds[2]) / 2

    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=14,
        tiles="OpenStreetMap",
        control_scale=True,
        prefer_canvas=True,
    )

    folium.TileLayer("CartoDB positron", name="CartoDB Positron", control=True).add_to(m)
    folium.TileLayer("CartoDB dark_matter", name="CartoDB Dark", control=True).add_to(m)
    folium.TileLayer("Esri.WorldImagery", name="Esri Satellite", control=True).add_to(m)

    folium.GeoJson(
        buffer_gdf.to_json(),
        name="Buffer 20 m",
        style_function=lambda _feature: {
            "fillColor": "#ff7800",
            "color": "#ff7800",
            "weight": 1,
            "fillOpacity": 0.22,
            "opacity": 0.75,
        },
        tooltip=folium.GeoJsonTooltip(fields=["name", "buffer_m"], aliases=["Layer", "Buffer (m)"]),
    ).add_to(m)

    # Main network linework.
    tooltip_fields = [c for c in ["name", "highway", "length", "oneway"] if c in roads_clean.columns]
    folium.GeoJson(
        roads_clean.to_json(),
        name="RRU with intersections",
        style_function=lambda _feature: {
            "color": "#0057ff",
            "weight": 4,
            "opacity": 0.95,
        },
        tooltip=folium.GeoJsonTooltip(fields=tooltip_fields) if tooltip_fields else None,
    ).add_to(m)

    # Intersection markers from configs.py.
    for name, coord in intersections.items():
        folium.CircleMarker(
            location=[coord["latitude"], coord["longitude"]],
            radius=6,
            color="#d00000",
            fill=True,
            fill_color="#ff3333",
            fill_opacity=0.95,
            tooltip=name.title(),
            popup=f"<b>{name.title()}</b><br>lat={coord['latitude']}<br>lon={coord['longitude']}",
        ).add_to(m)

    folium.LayerControl(collapsed=False).add_to(m)
    Fullscreen(position="topleft").add_to(m)
    MiniMap(toggle_display=True, minimized=True).add_to(m)
    MeasureControl(position="topleft", primary_length_unit="meters").add_to(m)

    m.fit_bounds([[bounds[1], bounds[0]], [bounds[3], bounds[2]]])

    out_html = OUTPUT_DIR / "rru_with_intersections_buffer_20m.html"
    m.save(out_html)
    print(out_html)


if __name__ == "__main__":
    main()
