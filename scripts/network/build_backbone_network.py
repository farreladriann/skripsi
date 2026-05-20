"""
Build the Ring Road Utara backbone-only road network.

Usage:
  .venv/bin/python scripts/network/build_backbone_network.py
"""

from __future__ import annotations

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from src.rru.network.rru_with_intersections import load_rru_backbone


def main() -> None:
    load_rru_backbone(
        cache_dir=PROJECT_ROOT / "data/external",
        output_filename="generated_network/rru_backbone.geojson",
    )


if __name__ == "__main__":
    main()
