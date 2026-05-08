"""
Build the Ring Road Utara (RRU) "fishbone" road network.

Shape:
  - Backbone: single west→east line along RRU
  - Branches: one north + one south line per intersection,
              each capped at MAX_BRANCH_LENGTH_M from the intersection point
  - All edges set to oneway=False (bidirectional for map matching)

The output is a single connected GeoDataFrame saved as GeoJSON.
"""

from pathlib import Path

import geopandas as gpd
import networkx as nx
import osmnx as ox

from .helper import load_or_build_graph, name_matches_any, CACHE_DIR
from configs import bounding_boxes, intersections

# ── Bounding box ────────────────────────────────────────────────────
_BBOX = bounding_boxes["rru"]
LAT_MIN, LAT_MAX = _BBOX["lat_min"], _BBOX["lat_max"]
LON_MIN, LON_MAX = _BBOX["lon_min"], _BBOX["lon_max"]

# ── Road selection ──────────────────────────────────────────────────
RRU_NAMES = (
    "siliwangi", "padjajaran", "pajajaran", "ring road utara",
    "kabupaten", "kronggahan",
    "magelang", "jombor", "monjali", "palagan", "nyi tjondro",
    "kaliurang", "affandi", "gejayan", "anggajaya 1", "seturan",
    "babarsari", "pawiro",
)
HIGHWAY_CLASSES = ("trunk", "primary")
OUTPUT_FILENAME = "rru_with_intersections.geojson"

# Backbone road names (west→east), including roundabout for Jombor
_BACKBONE_NAMES = (
    "siliwangi", "ring road utara", "padjajaran", "bunderan",
)

# When multiple parallel edges exist, prefer these (first match wins)
_BACKBONE_PRIORITY = ("siliwangi", "ring road utara", "bunderan")

# Each intersection and the road(s) that cross the RRU backbone there
_INTERSECTION_ROADS = {
    "kronggahan": ("kabupaten",),
    "jombor": ("magelang",),
    "monjali": ("palagan", "nyi tjondro"),
    "kentungan": ("kaliurang",),
    "condongcatur": ("affandi", "anggajaya"),
    "upn": ("seturan", "pawiro"),
}

# Maximum distance (meters) for intersection branches north/south
MAX_BRANCH_LENGTH_M = 400


# ═══════════════════════════════════════════════════════════════════
#  Graph query helpers
# ═══════════════════════════════════════════════════════════════════


def _highway_matches(highway, classes: tuple[str, ...]) -> bool:
    """Check whether a highway value (str or list) contains any target class."""
    if isinstance(highway, list):
        return any(h in classes for h in highway)
    return highway in classes


def _get_filtered_edges(
    G: nx.MultiDiGraph,
    name_filter: tuple[str, ...],
) -> gpd.GeoDataFrame:
    """Return trunk/primary edges matching `name_filter`, clipped to bbox."""
    _, edges = ox.graph_to_gdfs(G)
    is_target_highway = edges["highway"].apply(
        lambda h: _highway_matches(h, HIGHWAY_CLASSES)
    )
    is_target_name = edges["name"].apply(
        lambda n: name_matches_any(n, name_filter)
    )
    selected = edges[is_target_highway & is_target_name].copy()
    return selected.cx[LON_MIN:LON_MAX, LAT_MIN:LAT_MAX].copy()


def _shortest_path_pairs(
    G_undirected: nx.Graph, source: int, target: int,
) -> set[frozenset]:
    """Return edge pairs (as frozensets) along the shortest path."""
    path = nx.shortest_path(G_undirected, source, target, weight="length")
    return {frozenset(pair) for pair in zip(path[:-1], path[1:])}


def _shortest_path_nodes(
    G_undirected: nx.Graph, source: int, target: int,
) -> list[int]:
    """Return ordered node list of the shortest path."""
    return nx.shortest_path(G_undirected, source, target, weight="length")


def _closest_node_to_point(
    node_set: set[int],
    lon: float,
    lat: float,
    nodes_gdf: gpd.GeoDataFrame,
) -> int:
    """Find the node in `node_set` nearest to (lon, lat) by Euclidean distance."""
    distances = {
        n: (nodes_gdf.loc[n, "x"] - lon) ** 2
           + (nodes_gdf.loc[n, "y"] - lat) ** 2
        for n in node_set
        if n in nodes_gdf.index
    }
    return min(distances, key=distances.get)


def _find_bridge(
    node_a: int,
    node_b: int,
    G: nx.MultiDiGraph,
) -> tuple[set[frozenset], float]:
    """
    Find shortest path between two nodes using the full graph (undirected).

    Returns (edge_pairs, path_length). On failure returns (empty set, inf).
    """
    full_undirected = G.to_undirected()
    try:
        pairs = _shortest_path_pairs(full_undirected, node_a, node_b)
        length = nx.shortest_path_length(
            full_undirected, node_a, node_b, weight="length",
        )
        return pairs, length
    except nx.NetworkXNoPath:
        return set(), float("inf")


def _edge_length(G_undirected: nx.Graph, u: int, v: int) -> float:
    """Get the shortest edge length between two adjacent nodes."""
    edge_data = G_undirected[u][v]
    # Plain Graph → dict with 'length' key directly
    if isinstance(edge_data, dict) and "length" in edge_data:
        return edge_data["length"]
    # MultiGraph → pick shortest among parallel edges
    return min(d.get("length", 0) for d in edge_data.values())


# ═══════════════════════════════════════════════════════════════════
#  Backbone builder
# ═══════════════════════════════════════════════════════════════════


def _build_backbone(
    G: nx.MultiDiGraph, nodes_gdf: gpd.GeoDataFrame,
) -> tuple[set[frozenset], set[int]]:
    """
    Build the RRU backbone by waypoint-routing through Bunderan Jombor.

    Route: west → jombor(roundabout) → east.
    The Jombor waypoint forces the path through the roundabout instead of
    the Padjajaran bypass.

    Returns (edge_pairs, backbone_node_set).
    """
    backbone_edges = _get_filtered_edges(G, _BACKBONE_NAMES)

    # Largest weakly-connected component → undirected for routing
    sub = G.edge_subgraph(backbone_edges.index.tolist())
    largest_cc = max(nx.weakly_connected_components(sub), key=len)
    sub_undirected = sub.subgraph(largest_cc).to_undirected()

    xs = nx.get_node_attributes(sub_undirected, "x")
    west_node = min(xs, key=xs.get)
    east_node = max(xs, key=xs.get)

    # Collect Bunderan Jombor nodes that exist in the backbone subgraph
    _, all_edges = ox.graph_to_gdfs(G)
    is_roundabout = all_edges["name"].apply(
        lambda n: name_matches_any(n, ("bunderan jombor",))
    )
    roundabout_nodes = (
        set(all_edges[is_roundabout].index.get_level_values(0))
        | set(all_edges[is_roundabout].index.get_level_values(1))
    ) & set(sub_undirected.nodes())

    # Build waypoint through Jombor roundabout
    jombor_coord = intersections["jombor"]
    if roundabout_nodes:
        jombor_node = _closest_node_to_point(
            roundabout_nodes,
            jombor_coord["longitude"],
            jombor_coord["latitude"],
            nodes_gdf,
        )
    else:
        jombor_node = _closest_node_to_point(
            set(sub_undirected.nodes()),
            jombor_coord["longitude"],
            jombor_coord["latitude"],
            nodes_gdf,
        )

    waypoints = [west_node, jombor_node, east_node]

    # Start with all roundabout edges (full circle)
    pairs: set[frozenset] = set()
    for u, v, _k in all_edges[is_roundabout].index:
        pairs.add(frozenset([u, v]))

    # Route segment-by-segment through waypoints
    for src, dst in zip(waypoints[:-1], waypoints[1:]):
        if src != dst:
            pairs |= _shortest_path_pairs(sub_undirected, src, dst)

    nodes = set()
    for pair in pairs:
        nodes.update(pair)

    print(f"  Backbone: {len(pairs)} edge pairs")
    return pairs, nodes


# ═══════════════════════════════════════════════════════════════════
#  Intersection line builder
# ═══════════════════════════════════════════════════════════════════


def _split_components_by_direction(
    components: list[set[int]],
    intersection_lat: float,
    nodes_gdf: gpd.GeoDataFrame,
) -> list[set[int]]:
    """
    Group road components into north/south of the intersection, then
    return the largest component per direction.

    Avoids picking both sides of a dual carriageway.
    """
    north_comps: list[set] = []
    south_comps: list[set] = []

    for comp_nodes in components:
        if len(comp_nodes) < 2:
            continue
        avg_lat = sum(
            nodes_gdf.loc[n, "y"] for n in comp_nodes
            if n in nodes_gdf.index
        ) / len(comp_nodes)

        if avg_lat > intersection_lat:
            north_comps.append(comp_nodes)
        else:
            south_comps.append(comp_nodes)

    selected = []
    if north_comps:
        selected.append(max(north_comps, key=len))
    if south_comps:
        selected.append(max(south_comps, key=len))
    return selected


def _truncate_path_by_distance(
    path: list[int],
    G_undirected: nx.Graph,
    max_distance_m: float,
) -> list[int]:
    """
    Walk along `path` and cut it off once cumulative distance exceeds
    `max_distance_m`. Always includes at least the first node.
    """
    if len(path) <= 1:
        return path

    truncated = [path[0]]
    cumulative = 0.0

    for u, v in zip(path[:-1], path[1:]):
        cumulative += _edge_length(G_undirected, u, v)
        if cumulative > max_distance_m:
            break
        truncated.append(v)

    return truncated


def _trace_lines_from_anchor(
    comp_nodes: set[int],
    sub: nx.MultiDiGraph,
    anchor_lon: float,
    anchor_lat: float,
    nodes_gdf: gpd.GeoDataFrame,
    max_distance_m: float = MAX_BRANCH_LENGTH_M,
) -> set[frozenset]:
    """
    Within one connected component, trace from the anchor (nearest node
    to the intersection point) toward the northernmost and southernmost
    nodes, truncated at `max_distance_m`.
    """
    comp_undirected = sub.subgraph(comp_nodes).to_undirected()
    anchor = _closest_node_to_point(
        set(comp_nodes), anchor_lon, anchor_lat, nodes_gdf,
    )

    ys = nx.get_node_attributes(comp_undirected, "y")
    northmost = max(ys, key=ys.get)
    southmost = min(ys, key=ys.get)

    pairs: set[frozenset] = set()
    for endpoint in (northmost, southmost):
        if anchor == endpoint:
            continue
        try:
            full_path = _shortest_path_nodes(comp_undirected, anchor, endpoint)
            truncated = _truncate_path_by_distance(
                full_path, comp_undirected, max_distance_m,
            )
            pairs |= {
                frozenset(pair)
                for pair in zip(truncated[:-1], truncated[1:])
            }
        except nx.NetworkXNoPath:
            pass

    return pairs


def _connect_to_backbone(
    line_nodes: set[int],
    backbone_nodes: set[int],
    intersection_lon: float,
    intersection_lat: float,
    nodes_gdf: gpd.GeoDataFrame,
    G: nx.MultiDiGraph,
) -> set[frozenset]:
    """
    If the intersection line doesn't share nodes with the backbone,
    find a bridge through the full graph.

    Returns the bridge edge pairs, or an empty set if already connected
    or if no path exists.
    """
    if line_nodes & backbone_nodes:
        return set()

    closest_line = _closest_node_to_point(
        line_nodes, intersection_lon, intersection_lat, nodes_gdf,
    )
    closest_backbone = _closest_node_to_point(
        backbone_nodes, intersection_lon, intersection_lat, nodes_gdf,
    )

    bridge_pairs, _ = _find_bridge(closest_line, closest_backbone, G)
    return bridge_pairs


def _build_intersection_lines(
    int_name: str,
    road_names: tuple[str, ...],
    G: nx.MultiDiGraph,
    backbone_nodes: set[int],
    nodes_gdf: gpd.GeoDataFrame,
) -> set[frozenset]:
    """
    Build north and south line segments for one intersection road.

    Strategy:
    1. Get all matching road edges in the bbox
    2. Split components into north/south (largest per direction)
    3. Trace anchor→endpoint, capped at MAX_BRANCH_LENGTH_M
    4. Bridge to backbone if not directly connected
    """
    int_edges = _get_filtered_edges(G, road_names)
    if len(int_edges) == 0:
        print(f"  ⚠ {int_name}: no edges found for {road_names}")
        return set()

    int_coord = intersections.get(int_name)
    if int_coord is None:
        print(f"  ⚠ {int_name}: no intersection coordinate in config")
        return set()

    int_lon = int_coord["longitude"]
    int_lat = int_coord["latitude"]

    # Split into directional components
    sub = G.edge_subgraph(int_edges.index.tolist())
    components = list(nx.weakly_connected_components(sub))
    selected_comps = _split_components_by_direction(
        components, int_lat, nodes_gdf,
    )

    # Trace lines in each selected component
    all_pairs: set[frozenset] = set()
    for comp_nodes in selected_comps:
        all_pairs |= _trace_lines_from_anchor(
            comp_nodes, sub, int_lon, int_lat, nodes_gdf,
        )

    if not all_pairs:
        print(f"  ⚠ {int_name}: no line pairs built")
        return all_pairs

    # Connect to backbone if needed
    line_nodes = set()
    for pair in all_pairs:
        line_nodes.update(pair)

    bridge = _connect_to_backbone(
        line_nodes, backbone_nodes, int_lon, int_lat, nodes_gdf, G,
    )
    all_pairs |= bridge

    status = "bridged" if bridge else "connected"
    print(f"  ✓ {int_name}: {len(all_pairs)} edges, "
          f"{len(selected_comps)} directions, {status}")
    return all_pairs


# ═══════════════════════════════════════════════════════════════════
#  Edge collection (pairs → GeoDataFrame)
# ═══════════════════════════════════════════════════════════════════


def _edge_priority(edge_name) -> int:
    """Score an edge name against backbone priority (lower = better)."""
    if isinstance(edge_name, str):
        for i, priority_name in enumerate(_BACKBONE_PRIORITY):
            if name_matches_any(edge_name, (priority_name,)):
                return i
    elif isinstance(edge_name, list):
        for i, priority_name in enumerate(_BACKBONE_PRIORITY):
            if any(name_matches_any(n, (priority_name,)) for n in edge_name):
                return i
    return 999


def _collect_edges_from_pairs(
    pairs: set[frozenset], G: nx.MultiDiGraph,
) -> gpd.GeoDataFrame:
    """
    Convert frozenset({u,v}) pairs into a deduplicated GeoDataFrame.

    When multiple edges exist for one pair, select by:
    1. Backbone priority (prefer main road name)
    2. Shortest length (tie-breaker)
    """
    _, all_edges = ox.graph_to_gdfs(G)
    best: dict[frozenset, tuple] = {}

    for (u, v, k), row in all_edges.iterrows():
        pair = frozenset([u, v])
        if pair not in pairs:
            continue

        length = row.get("length", 0)
        priority = _edge_priority(row.get("name", ""))

        if pair not in best:
            best[pair] = ((u, v, k), length, priority)
        else:
            prev_priority = best[pair][2]
            prev_length = best[pair][1]
            is_better = (
                priority < prev_priority
                or (priority == prev_priority and length < prev_length)
            )
            if is_better:
                best[pair] = ((u, v, k), length, priority)

    if not best:
        return all_edges.iloc[:0].copy()

    keep_ids = [idx for idx, _, _ in best.values()]
    return all_edges.loc[keep_ids].copy()


# ═══════════════════════════════════════════════════════════════════
#  Connectivity repair
# ═══════════════════════════════════════════════════════════════════


def _ensure_single_component(
    pairs: set[frozenset],
    G: nx.MultiDiGraph,
    nodes_gdf: gpd.GeoDataFrame,
) -> set[frozenset]:
    """
    If the edge pairs form multiple connected components, bridge the
    smaller ones to the largest via shortest paths in the full graph.

    Returns the (possibly augmented) pair set.
    """
    graph = nx.Graph()
    for pair in pairs:
        u, v = pair
        graph.add_edge(u, v)

    components = sorted(nx.connected_components(graph), key=len, reverse=True)
    if len(components) <= 1:
        return pairs

    print(f"  {len(components)} disconnected components, "
          f"sizes: {[len(c) for c in components]}")

    largest = components[0]
    for comp in components[1:]:
        comp_node = _closest_node_to_point(
            comp,
            (LON_MIN + LON_MAX) / 2,
            (LAT_MIN + LAT_MAX) / 2,
            nodes_gdf,
        )
        backbone_node = _closest_node_to_point(
            largest,
            nodes_gdf.loc[comp_node, "x"],
            nodes_gdf.loc[comp_node, "y"],
            nodes_gdf,
        )

        bridge, bridge_length = _find_bridge(comp_node, backbone_node, G)
        if bridge:
            pairs |= bridge
            largest = largest | comp
            print(f"    Bridged stray component ({bridge_length:.0f}m)")

    return pairs


# ═══════════════════════════════════════════════════════════════════
#  Public entry point
# ═══════════════════════════════════════════════════════════════════


def load_rru_with_intersections(
    cache_dir: Path = CACHE_DIR,
) -> gpd.GeoDataFrame:
    """
    Build the RRU fishbone network and save as GeoJSON.

    Steps:
    1. Build backbone (single west→east line)
    2. Build intersection branches (north + south, max {MAX_BRANCH_LENGTH_M}m each)
    3. Ensure full connectivity (bridge any stray components)
    4. Collect and deduplicate edges
    5. Save to cache
    """
    G = load_or_build_graph(cache_dir)
    nodes_gdf, _ = ox.graph_to_gdfs(G)

    # 1. Backbone
    print("Building backbone...")
    backbone_pairs, backbone_nodes = _build_backbone(G, nodes_gdf)

    # 2. Intersection branches
    print(f"Building intersection lines (max {MAX_BRANCH_LENGTH_M}m)...")
    all_pairs = set(backbone_pairs)
    for int_name, road_names in _INTERSECTION_ROADS.items():
        all_pairs |= _build_intersection_lines(
            int_name, road_names, G, backbone_nodes, nodes_gdf,
        )

    # 3. Connectivity repair
    all_pairs = _ensure_single_component(all_pairs, G, nodes_gdf)

    # 4. Collect edges
    edges = _collect_edges_from_pairs(all_pairs, G)
    edges = edges.copy()
    edges["oneway"] = False

    # 5. Verify and save
    graph = nx.Graph()
    for u, v, _ in edges.index:
        graph.add_edge(u, v)
    n_components = nx.number_connected_components(graph)

    cache_path = cache_dir / OUTPUT_FILENAME
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    edges.to_file(cache_path, driver="GeoJSON")
    print(f"✓ Saved {len(edges)} edges ({n_components} component) → {cache_path}")

    return edges


if __name__ == "__main__":
    load_rru_with_intersections()