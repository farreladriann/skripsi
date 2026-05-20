"""
Master Pipeline — Run the complete analysis pipeline end-to-end.

Pipeline stages:
  Stage 1a: Bounding box filter
  Stage 1b: R-tree edge candidates
  Stage 1c: Bilocation collapse
  Stage 1d: Journal-based transport mode filtering (motor vehicles only)
  Stage 2: Map Matching (nearest-edge assignment)
  Stage 3: Trajectory Segmentation (time-gap splitting)
  Stage 4: Intersection Labeling (zone assignment + trip OD)
  Stage 5a: OD Matrix Extraction
  Stage 5b: Traffic Density Estimation
  Stage 6: Backbone analytical filter for OD
  Stage 7: OD Matrix Extraction

Usage:
  uv run python scripts/run_pipeline.py
"""

import time
import sys
from pathlib import Path

# Ensure project root is importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def _run_stage(name: str, func):
    """Run a pipeline stage with timing."""
    print(f"\n{'='*70}")
    print(f"  STAGE: {name}")
    print(f"{'='*70}")
    t0 = time.time()
    try:
        func()
        elapsed = time.time() - t0
        print(f"\n  ✓ {name} completed in {elapsed:.1f}s")
    except Exception as e:
        elapsed = time.time() - t0
        print(f"\n  ❌ {name} FAILED after {elapsed:.1f}s: {e}")
        raise


def main():
    t_total = time.time()

    # Stage 0: Verify QGIS-curated network inputs.
    # Fishbone is the primary preprocessing network for all RRU intersection vehicles.
    # Backbone-only is used later as an analytical filter for OD.
    from src.rru.paths import (
        RRU_BACKBONE_CLEAN_GEOJSON,
        RRU_WITH_INTERSECTION_CLEAN_GEOJSON,
        require_path,
    )
    _run_stage(
        "Verify QGIS-clean RRU Fishbone Network",
        lambda: print(require_path(RRU_WITH_INTERSECTION_CLEAN_GEOJSON, "QGIS-clean fishbone network")),
    )
    _run_stage(
        "Verify QGIS-clean RRU Backbone-only Network",
        lambda: print(require_path(RRU_BACKBONE_CLEAN_GEOJSON, "QGIS-clean backbone network")),
    )

    # Stage 1a: Bounding box filter
    from src.rru.preprocessing.interim.bbox import main as bbox_filter
    _run_stage("Bounding Box Filter", bbox_filter)

    # Stage 1b: R-tree candidate road filtering
    from src.rru.preprocessing.interim.rtree import main as rtree_candidates
    _run_stage("R-tree Edge Candidates", rtree_candidates)

    # Stage 1c: Bilocation collapse
    from src.rru.preprocessing.outlier_cleaning.bilocation.collapse_bilocation import main as collapse_bilocation
    _run_stage("Bilocation Collapse", collapse_bilocation)

    # Stage 1d: Journal-based transport mode filtering
    from src.rru.preprocessing.transport_mode_filter import main as transport_mode_filter
    _run_stage("Transport Mode Filter (Motor Vehicles Only)", transport_mode_filter)

    # Stage 2: Map Matching
    from src.rru.preprocessing.mapmatching.map_matching import main as map_match
    _run_stage("Map Matching", map_match)

    # Stage 3: Trajectory Segmentation
    from src.rru.preprocessing.traj_segmentation.segmentation import main as segment
    _run_stage("Trajectory Segmentation", segment)

    # Stage 4: Intersection Labeling
    from src.rru.analysis.intersection_labeling import main as label
    _run_stage("Intersection Labeling", label)

    # Stage 5a: Traffic Density on fishbone-labeled data
    from src.rru.analysis.density import main as density
    _run_stage("Traffic Density Estimation (Fishbone)", density)

    # Stage 5b: Turning movement on fishbone-labeled data
    from src.rru.analysis.turning_movement import main as turning_movement
    _run_stage("Turning Movement Analysis (Fishbone)", turning_movement)

    # Stage 6: Derive a backbone-only matched/labeled dataset from vehicle-only fishbone preprocessing
    from src.rru.analysis.backbone_filter import main as backbone_filter
    _run_stage("Backbone Analytical Filter", backbone_filter)

    # Stage 7a: OD Matrix on backbone-labeled data
    from src.rru.analysis.od_matrix import main as od_matrix
    _run_stage("OD Matrix Extraction (Backbone)", od_matrix)

    elapsed_total = time.time() - t_total
    print(f"\n{'='*70}")
    print(f"  PIPELINE COMPLETE — Total time: {elapsed_total:.1f}s")
    print(f"{'='*70}")


if __name__ == "__main__":
    main()
