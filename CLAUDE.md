# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a thesis (skripsi) project analyzing spatiotemporal GPS mobility data for Yogyakarta, Indonesia (Daerah Istimewa Yogyakarta), specifically focusing on Ring Road Utara (RRU) traffic patterns around the planned Yogyakarta-Solo toll road construction. Data covers October 2021 - June 2022.

**Research goals:** Origin-Destination matrix extraction, turning movement analysis, traffic density estimation, and catchment area mapping for 6 major intersections along RRU.

## Environment Setup
- Python + uv. Command: `uv add <pkg>`, `uv run <script>`.

Python 3.13+ is required. Dependencies managed via `pyproject.toml`.

## Project Structure

```
src/rru/                    # Main analysis package
├── network/                # Road network analysis (OSMnx)
│   ├── helper.py           # Graph loading utilities, cache management
│   └── rru_with_intersections.py  # Build "fishbone" road structure
├── utils.py                # Haversine distance, MAID filtering
├── analysis/               # (placeholder for analysis modules)
├── mapmatching/            # (placeholder for map matching)
├── preprocessing/          # (placeholder for data preprocessing)
└── segmentation/           # Trajectory segmentation (semi-supervised, unsupervised)

configs.py                  # Bounding boxes and intersection coordinates
data/
├── raw/                    # Raw GPS data
├── processed/              # Processed data
├── matched/                # Map-matched trajectories
└── external/               # OSM cache, external data
    └── osm_cache/          # Cached OSMnx graphs
```

## Key Configurations

**6 Intersections along RRU (west to east):**
Kronggahan → Jombor → Monjali → Kentungan → Condongcatur → UPN

Defined in `configs.py` with latitude/longitude coordinates.

**Bounding box (RRU):**
- lat: -7.767411 to -7.742002
- lon: 110.342299 to 110.433240

## Data Format

GPS records contain:
- `maid`: Mobile Advertising Identifier (anonymized device ID)
- `latitude`, `longitude`: GPS coordinates
- `timestamp`: Unix timestamp

Data stored in parquet format across `data/` subdirectories.

## Road Network Analysis

`src/rru/network/rru_with_intersections.py` builds a "fishbone" network structure:
- **Backbone**: Single road line along RRU (west → east)
- **Branches**: One north line + one south line per intersection
- Ensures connectivity through waypoint routing, including Jombor roundabout

