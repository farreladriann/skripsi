import networkx as nx
import osmnx as ox
import geopandas as gpd
from pathlib import Path

SLEMAN_PLACE = "Sleman, Daerah Istimewa Yogyakarta, Indonesia"
GRAPH_FILENAME = "graph_osmnx_sleman.graphml"
CACHE_DIR = Path("data/external")

def load_or_build_graph(cache_dir: Path = CACHE_DIR) -> nx.MultiDiGraph:
    """Load OSM graph from cache, or build new if not exists."""
    cache_path = cache_dir / "osm_cache" / GRAPH_FILENAME
    if cache_path.exists():
        return ox.load_graphml(cache_path)
    cache_path.parent.mkdir(parents=True, exist_ok=True)    
    graph = ox.graph_from_place(SLEMAN_PLACE, network_type="drive", simplify=False)
    ox.save_graphml(graph, cache_path)
    return graph

def name_matches_any(name, targets) -> bool:
    if isinstance(name, list):
        return any(name_matches_any(n, targets) for n in name)
    if not isinstance(name, str):
        return False
    lower = name.lower()
    return any(t in lower for t in targets)