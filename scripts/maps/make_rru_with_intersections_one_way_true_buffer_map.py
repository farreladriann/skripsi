"""Create Folium map for the one-way-true RRU with intersections network.

Outputs:
- data/external/rru_with_intersections_one_way_true.geojson
- deliverables/maps/rru_with_intersections_one_way_true_buffer_20m.html
"""

from __future__ import annotations

from pathlib import Path
import importlib.util
import json
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import folium
import geopandas as gpd
from folium.plugins import Fullscreen, MeasureControl, MiniMap

from configs import intersections

OUTPUT_DIR = PROJECT_ROOT / "deliverables" / "maps"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

BUFFER_M = 20.0
METRIC_CRS = "EPSG:32749"
WGS84 = "EPSG:4326"
NETWORK_MODULE_PATH = PROJECT_ROOT / "src/rru/network/rru_with_intersections-one-way-true.py"


def _load_one_way_module():
    spec = importlib.util.spec_from_file_location(
        "src.rru.network.rru_with_intersections_one_way_true",
        NETWORK_MODULE_PATH,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load module from {NETWORK_MODULE_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _clean_for_geojson(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    out = gdf.copy()
    for col in out.columns:
        if col == out.geometry.name:
            continue
        out[col] = out[col].apply(
            lambda v: json.dumps(v, ensure_ascii=False)
            if isinstance(v, (list, dict, tuple))
            else v
        )
    return out


def _style(feature):
    oneway = feature["properties"].get("oneway")
    role = feature["properties"].get("network_role", "")
    is_oneway = str(oneway).lower() in {"true", "1", "yes"}
    is_parallel = "parallel" in str(role)
    return {
        "color": "#ffb000" if is_oneway else "#0057ff",
        "weight": 4 if is_oneway else 3,
        "opacity": 0.95 if not is_parallel else 0.85,
        "dashArray": None if is_oneway else "5, 5",
    }


def main() -> None:
    module = _load_one_way_module()
    roads = module.load_rru_with_intersections()
    if roads.crs is None:
        roads = roads.set_crs(WGS84)
    roads = roads.to_crs(WGS84)

    roads_m = roads.to_crs(METRIC_CRS)
    buffer_geom_m = roads_m.geometry.buffer(BUFFER_M).union_all()
    buffer_gdf = gpd.GeoDataFrame(
        {"name": [f"Buffer {BUFFER_M:g} m dari rru_with_intersections_one_way_true"], "buffer_m": [BUFFER_M]},
        geometry=[buffer_geom_m],
        crs=METRIC_CRS,
    ).to_crs(WGS84)

    bounds = roads.total_bounds
    center_lat = (bounds[1] + bounds[3]) / 2
    center_lon = (bounds[0] + bounds[2]) / 2

    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=14,
        tiles="CartoDB dark_matter",
        control_scale=True,
        prefer_canvas=True,
    )
    folium.TileLayer("OpenStreetMap", name="OpenStreetMap", control=True).add_to(m)
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
            "fillOpacity": 0.18,
            "opacity": 0.65,
        },
        tooltip=folium.GeoJsonTooltip(fields=["name", "buffer_m"], aliases=["Layer", "Buffer (m)"]),
    ).add_to(m)

    roads_clean = _clean_for_geojson(roads)
    tooltip_fields = [
        c for c in ["name", "highway", "length", "oneway", "lanes", "network_role"]
        if c in roads_clean.columns
    ]
    folium.GeoJson(
        roads_clean.to_json(),
        name="RRU with intersections — one-way true dual carriageway",
        style_function=_style,
        tooltip=folium.GeoJsonTooltip(fields=tooltip_fields) if tooltip_fields else None,
    ).add_to(m)

    legend_html = """
    <div style="position: fixed; bottom: 32px; left: 32px; z-index: 9999;
                background: rgba(20,20,20,0.82); color: white; padding: 10px 12px;
                border: 1px solid #999; border-radius: 6px; font-size: 13px;">
      <b>RRU one-way true</b><br>
      <span style="color:#ffb000;">━━</span> OSM oneway=True carriageway<br>
      <span style="color:#0057ff;">┅┅</span> OSM oneway=False branch<br>
      <span style="color:#ff7800;">▰</span> Buffer 20 m
    </div>
    """
    m.get_root().html.add_child(folium.Element(legend_html))

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

    out_html = OUTPUT_DIR / "rru_with_intersections_one_way_true_buffer_20m.html"
    m.save(out_html)
    print(out_html)


if __name__ == "__main__":
    main()
