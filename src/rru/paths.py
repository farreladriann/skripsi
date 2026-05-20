"""Centralized project paths for the RRU thesis pipeline.

The QGIS-curated clean network files under ``data/processed/network`` are the
authoritative analytical network inputs. OSM-generated files under
``data/external`` are kept only as cache/reference artifacts.
"""

from __future__ import annotations

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"
EXTERNAL_DATA_DIR = DATA_DIR / "external"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
PROCESSED_NETWORK_DIR = PROCESSED_DATA_DIR / "network"

# Authoritative QGIS-curated network inputs.
RRU_BACKBONE_CLEAN_GEOJSON = PROCESSED_NETWORK_DIR / "rru_backbone_clean.geojson"
RRU_WITH_INTERSECTION_CLEAN_GEOJSON = PROCESSED_NETWORK_DIR / "rru_with_intersection_clean.geojson"

def require_path(path: Path, description: str) -> Path:
    """Return ``path`` if it exists, otherwise raise a helpful error."""
    if not path.exists():
        raise FileNotFoundError(f"{description} not found: {path}")
    return path
