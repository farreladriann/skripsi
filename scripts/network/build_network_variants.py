"""
Build branch-length variants for Ring Road Utara network sensitivity analysis.

Usage:
  .venv/bin/python scripts/network/build_network_variants.py
"""

from __future__ import annotations

from pathlib import Path
import sys

import networkx as nx
import osmnx as ox

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from src.rru.network.helper import load_or_build_graph
from src.rru.network.rru_with_intersections import (
    build_rru_with_intersections_from_graph,
)


BRANCH_LENGTHS_M = (300, 400, 500)
EXTERNAL_DIR = PROJECT_ROOT / "data/external"
OUTPUT_DIR = EXTERNAL_DIR / "network_variants"


def _save_network(edges, output_path: Path) -> None:
    edges = edges.copy()

    graph = nx.Graph()
    for u, v, _ in edges.index:
        graph.add_edge(u, v)
    n_components = nx.number_connected_components(graph)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    edges.to_file(output_path, driver="GeoJSON")
    print(f"Saved {len(edges)} edges ({n_components} component) -> {output_path}")


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print("Loading OSM graph once...", flush=True)
    graph = load_or_build_graph(EXTERNAL_DIR)
    nodes_gdf, _ = ox.graph_to_gdfs(graph)

    for branch_length_m in BRANCH_LENGTHS_M:
        output_filename = f"rru_fishbone_{branch_length_m}m.geojson"
        print(f"\nBuilding {output_filename}...", flush=True)
        edges = build_rru_with_intersections_from_graph(
            graph,
            nodes_gdf=nodes_gdf,
            max_branch_length_m=branch_length_m,
        )
        _save_network(edges, OUTPUT_DIR / output_filename)


if __name__ == "__main__":
    main()
