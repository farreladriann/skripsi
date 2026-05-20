"""
QA checks for the selected Ring Road Utara corridor network.

This script turns the network-selection argument into measurable checks:
- geometry size and total length
- graph connectivity
- matched-point distance distribution
- edge usage from matched MPD/GPS pings

Usage:
  .venv/bin/python scripts/network/qa_network_selection.py
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import geopandas as gpd
import networkx as nx
import polars as pl

from src.rru.paths import RRU_WITH_INTERSECTION_CLEAN_GEOJSON


DEFAULT_NETWORK_PATH = RRU_WITH_INTERSECTION_CLEAN_GEOJSON
DEFAULT_MATCHED_PATH = PROJECT_ROOT / "data/matched/gps_rru_matched.parquet"
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "results/network_qa"


def _edge_key_expr() -> pl.Expr:
    """Build an edge key expression that matches map-matching output."""
    return (
        pl.col("u").cast(pl.Utf8)
        + pl.lit("_")
        + pl.col("v").cast(pl.Utf8)
    )


def _resolve_project_path(path: str | Path) -> Path:
    path = Path(path)
    return path if path.is_absolute() else PROJECT_ROOT / path


def _load_network(network_path: Path) -> gpd.GeoDataFrame:
    if not network_path.exists():
        raise FileNotFoundError(f"Network file not found: {network_path}")

    edges = gpd.read_file(network_path)
    required = {"u", "v", "length", "geometry"}
    missing = required - set(edges.columns)
    if missing:
        raise ValueError(f"Network is missing required columns: {sorted(missing)}")

    return edges


def _network_stats(edges: gpd.GeoDataFrame) -> dict[str, float | int]:
    graph = nx.Graph()
    for row in edges[["u", "v"]].itertuples(index=False):
        graph.add_edge(str(row.u), str(row.v))

    components = list(nx.connected_components(graph))
    largest_component_nodes = max((len(c) for c in components), default=0)

    return {
        "edge_count": int(len(edges)),
        "node_count": int(graph.number_of_nodes()),
        "component_count": int(len(components)),
        "largest_component_nodes": int(largest_component_nodes),
        "total_length_km": float(edges["length"].fillna(0).sum() / 1000),
    }


def _matched_stats(
    edges: gpd.GeoDataFrame,
    matched_path: Path | None,
) -> tuple[dict[str, float | int], pl.DataFrame | None]:
    if matched_path is None or not matched_path.exists():
        return {
            "matched_file_found": 0,
            "matched_pings": 0,
            "unique_maids": 0,
            "unique_edges_used": 0,
            "edge_usage_pct": 0.0,
            "matched_dist_p50_m": 0.0,
            "matched_dist_p90_m": 0.0,
            "matched_dist_p95_m": 0.0,
            "matched_dist_p99_m": 0.0,
        }, None

    matched = pl.read_parquet(matched_path)
    if "matched_edge" not in matched.columns or "matched_dist" not in matched.columns:
        raise ValueError("Matched data must contain matched_edge and matched_dist columns")

    usage = (
        matched.group_by("matched_edge")
        .len()
        .rename({"len": "ping_count"})
        .sort("ping_count", descending=True)
    )

    network_edges = pl.DataFrame(
        {
            "u": edges["u"].astype(str).to_list(),
            "v": edges["v"].astype(str).to_list(),
            "name": edges.get("name", "").astype(str).to_list(),
            "length": edges["length"].fillna(0).to_list(),
        }
    ).with_columns(edge_key=_edge_key_expr())

    edge_usage = (
        network_edges.join(usage, left_on="edge_key", right_on="matched_edge", how="left")
        .with_columns(pl.col("ping_count").fill_null(0))
        .sort("ping_count", descending=True)
    )

    used_edges = edge_usage.filter(pl.col("ping_count") > 0).height
    total_edges = edge_usage.height

    stats = {
        "matched_file_found": 1,
        "matched_pings": int(matched.height),
        "unique_maids": int(matched["maid"].n_unique()) if "maid" in matched.columns else 0,
        "unique_edges_used": int(used_edges),
        "edge_usage_pct": float(used_edges / total_edges * 100) if total_edges else 0.0,
        "matched_dist_p50_m": float(matched["matched_dist"].quantile(0.50)),
        "matched_dist_p90_m": float(matched["matched_dist"].quantile(0.90)),
        "matched_dist_p95_m": float(matched["matched_dist"].quantile(0.95)),
        "matched_dist_p99_m": float(matched["matched_dist"].quantile(0.99)),
    }
    return stats, edge_usage


def _format_report(
    network_stats: dict[str, float | int],
    matched_stats: dict[str, float | int],
    network_path: Path,
) -> str:
    return f"""# Network Selection QA

## Network

- Network file: `{network_path.relative_to(PROJECT_ROOT)}`
- Edge count: {network_stats["edge_count"]:,}
- Node count: {network_stats["node_count"]:,}
- Connected components: {network_stats["component_count"]:,}
- Largest component nodes: {network_stats["largest_component_nodes"]:,}
- Total OSM length: {network_stats["total_length_km"]:.2f} km

## Matched MPD/GPS Coverage

- Matched file found: {bool(matched_stats["matched_file_found"])}
- Matched pings: {matched_stats["matched_pings"]:,}
- Unique MAIDs: {matched_stats["unique_maids"]:,}
- Unique network edges used: {matched_stats["unique_edges_used"]:,}
- Edge usage: {matched_stats["edge_usage_pct"]:.1f}%
- Match distance P50: {matched_stats["matched_dist_p50_m"]:.1f} m
- Match distance P90: {matched_stats["matched_dist_p90_m"]:.1f} m
- Match distance P95: {matched_stats["matched_dist_p95_m"]:.1f} m
- Match distance P99: {matched_stats["matched_dist_p99_m"]:.1f} m

## Interpretation Checklist

- `Connected components` should be 1 for the main fishbone network.
- High P90/P95 match distance suggests the selected network is too narrow, the candidate radius is too loose, or the input still contains off-corridor points.
- Low edge usage can mean unused branch segments, excessive branch length, or demand concentrated only on the RRU backbone.
- Repeat this report for branch lengths 300 m, 400 m, and 500 m before finalizing the network.
"""


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--network",
        default=str(DEFAULT_NETWORK_PATH.relative_to(PROJECT_ROOT)),
        help="GeoJSON network path, absolute or relative to project root.",
    )
    parser.add_argument(
        "--matched",
        default=str(DEFAULT_MATCHED_PATH.relative_to(PROJECT_ROOT)),
        help="Matched parquet path, absolute or relative to project root. Use 'none' to skip.",
    )
    parser.add_argument(
        "--output-dir",
        default=str(DEFAULT_OUTPUT_DIR.relative_to(PROJECT_ROOT)),
        help="Output directory, absolute or relative to project root.",
    )
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    network_path = _resolve_project_path(args.network)
    matched_path = None if args.matched.lower() == "none" else _resolve_project_path(args.matched)
    output_dir = _resolve_project_path(args.output_dir)
    report_path = output_dir / "network_selection_qa.md"
    edge_usage_path = output_dir / "edge_usage.csv"

    output_dir.mkdir(parents=True, exist_ok=True)

    edges = _load_network(network_path)
    network_stats = _network_stats(edges)
    matched_stats, edge_usage = _matched_stats(edges, matched_path)

    report_path.write_text(
        _format_report(network_stats, matched_stats, network_path),
        encoding="utf-8",
    )
    if edge_usage is not None:
        edge_usage.write_csv(edge_usage_path)

    print(f"Saved QA report: {report_path}")
    if edge_usage is not None:
        print(f"Saved edge usage: {edge_usage_path}")


if __name__ == "__main__":
    main()
