"""Create a Folium HTML map of all Sleman motorway/trunk/primary roads.

The road graph is loaded with `load_or_build_graph()` from
`src.rru.network.helper`, so it uses the same cached OSMnx graph as the rest of
this project:

    data/external/osm_cache/graph_osmnx_sleman.graphml

Output:
- deliverables/maps/sleman_motorway_trunk_primary_roads.html
"""

from __future__ import annotations

from pathlib import Path
import json
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import folium
import osmnx as ox
from folium.plugins import Fullscreen, MeasureControl, MiniMap

from src.rru.network.helper import CACHE_DIR, load_or_build_graph

OUTPUT_DIR = PROJECT_ROOT / "deliverables" / "maps"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

TARGET_HIGHWAYS = {"motorway", "motorway_link", "trunk", "trunk_link", "primary", "primary_link"}
WGS84 = "EPSG:4326"


STYLE_BY_HIGHWAY = {
    "motorway": {"color": "#d00000", "weight": 5, "opacity": 0.95},
    "motorway_link": {"color": "#ff4d4d", "weight": 3, "opacity": 0.85},
    "trunk": {"color": "#ffb000", "weight": 4, "opacity": 0.95},
    "trunk_link": {"color": "#ffd166", "weight": 3, "opacity": 0.85},
    "primary": {"color": "#0057ff", "weight": 3, "opacity": 0.90},
    "primary_link": {"color": "#5aa0ff", "weight": 2, "opacity": 0.80},
}
DEFAULT_STYLE = {"color": "#888888", "weight": 2, "opacity": 0.75}


def highway_matches(value) -> bool:
    """Return True if an OSM highway value contains a target class."""
    if isinstance(value, list):
        return any(v in TARGET_HIGHWAYS for v in value)
    return value in TARGET_HIGHWAYS


def main_highway(value) -> str:
    """Pick one highway class for styling when OSM stores a list."""
    if isinstance(value, list):
        for cls in ["motorway", "motorway_link", "trunk", "trunk_link", "primary", "primary_link"]:
            if cls in value:
                return cls
        return str(value[0]) if value else "unknown"
    return str(value)


def clean_for_geojson(gdf):
    """Convert list/dict/tuple values so Folium can serialize the GeoJSON."""
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


def style_function(feature):
    highway = feature["properties"].get("highway_main")
    return STYLE_BY_HIGHWAY.get(highway, DEFAULT_STYLE)


def main() -> None:
    graph = load_or_build_graph(CACHE_DIR)
    _nodes, edges = ox.graph_to_gdfs(graph)

    selected = edges[edges["highway"].apply(highway_matches)].copy()
    if selected.empty:
        raise RuntimeError(f"No edges found for highway classes: {sorted(TARGET_HIGHWAYS)}")

    if selected.crs is None:
        selected = selected.set_crs(WGS84)
    selected = selected.to_crs(WGS84)
    selected["highway_main"] = selected["highway"].apply(main_highway)

    bounds = selected.total_bounds  # minx, miny, maxx, maxy
    center_lat = (bounds[1] + bounds[3]) / 2
    center_lon = (bounds[0] + bounds[2]) / 2

    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=12,
        tiles="CartoDB positron",
        control_scale=True,
        prefer_canvas=True,
    )
    folium.TileLayer("OpenStreetMap", name="OpenStreetMap", control=True).add_to(m)
    folium.TileLayer("CartoDB positron", name="CartoDB Positron", control=True).add_to(m)
    folium.TileLayer("CartoDB dark_matter", name="CartoDB Dark", control=True).add_to(m)
    folium.TileLayer("Esri.WorldImagery", name="Esri Satellite", control=True).add_to(m)

    tooltip_fields = [
        c
        for c in ["name", "highway", "highway_main", "oneway", "lanes", "length", "maxspeed", "ref"]
        if c in selected.columns
    ]

    folium.GeoJson(
        clean_for_geojson(selected).to_json(),
        name="Sleman motorway/trunk/primary roads",
        style_function=style_function,
        tooltip=folium.GeoJsonTooltip(fields=tooltip_fields) if tooltip_fields else None,
        popup=folium.GeoJsonPopup(fields=tooltip_fields, max_width=450) if tooltip_fields else None,
    ).add_to(m)

    legend_html = """
    <div style="position: fixed; bottom: 32px; left: 32px; z-index: 9999;
                background: rgba(255,255,255,0.92); color: #111; padding: 10px 12px;
                border: 1px solid #777; border-radius: 6px; font-size: 13px;">
      <b>Sleman major roads</b><br>
      <span style="color:#d00000;">━━</span> motorway<br>
      <span style="color:#ffb000;">━━</span> trunk<br>
      <span style="color:#0057ff;">━━</span> primary<br>
      <span style="color:#888;">━━</span> *_link variants styled lighter
    </div>
    """
    m.get_root().html.add_child(folium.Element(legend_html))

    folium.LayerControl(collapsed=False).add_to(m)
    Fullscreen(position="topleft").add_to(m)
    MiniMap(toggle_display=True, minimized=True).add_to(m)
    MeasureControl(position="topleft", primary_length_unit="meters").add_to(m)
    m.fit_bounds([[bounds[1], bounds[0]], [bounds[3], bounds[2]]])

    out_html = OUTPUT_DIR / "sleman_motorway_trunk_primary_roads.html"
    m.save(out_html)

    print(f"Selected edges: {len(selected)}")
    print(selected["highway_main"].value_counts().to_string())
    print(f"Saved map: {out_html}")


if __name__ == "__main__":
    main()
