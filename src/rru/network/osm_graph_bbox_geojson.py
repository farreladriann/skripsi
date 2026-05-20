"""Export the cached Sleman OSM drive graph clipped to the configured RRU bbox.

This script intentionally starts from the same graph source as `helper.load_or_build_graph`:

    ox.graph_from_place(SLEMAN_PLACE, network_type="drive", simplify=False)

Then it filters to motorway/trunk/primary roads, clips the resulting
OSMnx edge GeoDataFrame to `configs.bounding_boxes["rru"]`, and writes a plain
GeoJSON for map review / downstream processing.

Run from project root:

    .venv/bin/python src/rru/network/osm_graph_bbox_geojson.py
"""

from __future__ import annotations

from pathlib import Path
import json
import sys

# Allow direct execution from the project root or from this file's directory.
_PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

import geopandas as gpd
import networkx as nx
import osmnx as ox
from shapely.geometry import box

try:
    from .helper import CACHE_DIR, load_or_build_graph
except ImportError:  # direct script execution
    from helper import CACHE_DIR, load_or_build_graph

from configs import bounding_boxes

BBOX_NAME = "rru"
OUTPUT_FILENAME = "osm_sleman_drive_rru_bbox.geojson"
WGS84 = "EPSG:4326"
HIGHWAY_CLASSES = ("motorway", "trunk", "primary")


def _highway_matches(highway, classes: tuple[str, ...] = HIGHWAY_CLASSES) -> bool:
    """Check whether an OSM highway value (str/list/serialized list) matches."""
    if isinstance(highway, list):
        return any(_highway_matches(value, classes) for value in highway)
    if highway is None:
        return False
    text = str(highway).strip().lower()
    return text in classes


def _bbox_polygon(bbox_name: str = BBOX_NAME):
    """Return shapely bbox polygon from configs.bounding_boxes."""
    bbox = bounding_boxes[bbox_name]
    return box(
        bbox["lon_min"],
        bbox["lat_min"],
        bbox["lon_max"],
        bbox["lat_max"],
    )


def _clean_for_geojson(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """Serialize list/dict/tuple attributes so GeoJSON writing is robust."""
    out = gdf.copy()
    for col in out.columns:
        if col == out.geometry.name:
            continue
        out[col] = out[col].apply(
            lambda value: json.dumps(value, ensure_ascii=False)
            if isinstance(value, (list, dict, tuple))
            else value
        )
    return out


def graph_edges_to_bbox_geojson(
    G: nx.MultiDiGraph,
    bbox_name: str = BBOX_NAME,
    highway_classes: tuple[str, ...] = HIGHWAY_CLASSES,
) -> gpd.GeoDataFrame:
    """Convert graph edges to GeoDataFrame, filter road class, then clip bbox."""
    _, edges = ox.graph_to_gdfs(G)

    if edges.crs is None:
        edges = edges.set_crs(WGS84)
    else:
        edges = edges.to_crs(WGS84)

    edges = edges[edges["highway"].apply(lambda value: _highway_matches(value, highway_classes))].copy()

    bbox_geom = _bbox_polygon(bbox_name)
    bbox_gdf = gpd.GeoDataFrame({"bbox_name": [bbox_name]}, geometry=[bbox_geom], crs=WGS84)

    # First use .cx as a fast spatial prefilter, then true geometry clip so lines
    # crossing the bbox boundary are cut at the configured boundary.
    minx, miny, maxx, maxy = bbox_geom.bounds
    candidate_edges = edges.cx[minx:maxx, miny:maxy].copy()
    clipped = gpd.clip(candidate_edges, bbox_gdf).copy()

    # Keep OSMnx index IDs as normal columns for later graph reconstruction/review.
    clipped = clipped.reset_index()
    clipped["bbox_name"] = bbox_name
    clipped["source_graph"] = "Sleman drive graph, simplify=False"
    clipped["highway_filter"] = ",".join(highway_classes)

    return _clean_for_geojson(clipped)


def load_graph_and_export_bbox_geojson(
    cache_dir: Path = CACHE_DIR,
    bbox_name: str = BBOX_NAME,
    output_filename: str = OUTPUT_FILENAME,
    highway_classes: tuple[str, ...] = HIGHWAY_CLASSES,
) -> gpd.GeoDataFrame:
    """Load/build graph, clip edges to bbox, save GeoJSON, and return GeoDataFrame."""
    graph = load_or_build_graph(cache_dir)
    roads = graph_edges_to_bbox_geojson(
        graph,
        bbox_name=bbox_name,
        highway_classes=highway_classes,
    )

    output_path = cache_dir / output_filename
    output_path.parent.mkdir(parents=True, exist_ok=True)
    roads.to_file(output_path, driver="GeoJSON")

    bounds = roads.total_bounds
    total_length_km = roads.to_crs(epsg=32749).length.sum() / 1000
    print(f"✓ Saved {len(roads)} clipped OSM drive edges → {output_path}")
    print(f"  bbox: {bbox_name}")
    print(f"  highway: {', '.join(highway_classes)}")
    print(f"  bounds: lon {bounds[0]:.6f}..{bounds[2]:.6f}, lat {bounds[1]:.6f}..{bounds[3]:.6f}")
    print(f"  total length: {total_length_km:.2f} km")
    return roads


if __name__ == "__main__":
    load_graph_and_export_bbox_geojson()
