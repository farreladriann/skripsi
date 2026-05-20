"""
Transport mode filtering for active MPD preprocessing.

This module adds a journal-backed, rule-based transport mode classifier before
map matching. The goal is conservative filtering: keep MAIDs with evidence of
motorized vehicle movement on Ring Road Utara and remove stationary,
pedestrian, and bicycle-like traces from the downstream OD/density/turning
analyses.

Literature basis:
- GPS transport-mode studies commonly use speed-derived features such as
  maximum speed, average speed, and high-percentile speed to separate walking,
  cycling, and motorized modes (Reddy et al., 2010; Zheng et al., 2008).
- For sparse MPD without labelled mode ground truth, a transparent threshold
  rule is more defensible than a supervised classifier that cannot be trained
  or validated locally.

Operational rule used here:
- motor_vehicle if max_speed >= 25 km/h OR p95_speed >= 15 km/h
- non_vehicle otherwise

The thresholds are intentionally conservative for an urban arterial corridor:
walking is far below these values, bicycle-like traces are mostly below the
p95 criterion, and a single high-speed segment can preserve motorized users
that are otherwise observed in congestion.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from src.rru.preprocessing.outlier_cleaning.low_speed.low_speed_check import (
    calculate_consecutive_speed,
)

INPUT_PATH = Path("./data/processed/gps_rru_collapsed.parquet")
OUTPUT_PATH = Path("./data/processed/gps_rru_vehicle_only.parquet")
SUMMARY_PATH = Path("./results/preprocessing/transport_mode_summary.json")

# Journal-backed speed-feature thresholds for conservative motorized filtering.
MOTOR_VEHICLE_MAX_SPEED_KMH = 25.0
MOTOR_VEHICLE_P95_SPEED_KMH = 15.0

HELPER_COLUMNS = ["time_diff_hours", "distance_km", "speed_kmh"]


def _ensure_datetime_timestamp(df: pd.DataFrame) -> pd.DataFrame:
    """Return a copy with timestamp as pandas datetime for speed calculation."""
    out = df.copy()
    if not pd.api.types.is_datetime64_any_dtype(out["timestamp"]):
        out["timestamp"] = pd.to_datetime(out["timestamp"], unit="s")
    return out


def _ensure_speed_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """Return dataframe with consecutive speed metrics available."""
    if "speed_kmh" in df.columns:
        return df.copy()
    return calculate_consecutive_speed(_ensure_datetime_timestamp(df))


def classify_vehicle_maids(
    df_with_speed: pd.DataFrame,
    *,
    max_speed_threshold_kmh: float = MOTOR_VEHICLE_MAX_SPEED_KMH,
    p95_speed_threshold_kmh: float = MOTOR_VEHICLE_P95_SPEED_KMH,
) -> pd.DataFrame:
    """
    Classify each MAID as motor_vehicle or non_vehicle from speed features.

    Parameters
    ----------
    df_with_speed:
        DataFrame containing at least `maid` and `speed_kmh`. NaN/inf speeds
        from first pings or zero time gaps are ignored in feature aggregation.
    max_speed_threshold_kmh:
        A MAID is kept as motor_vehicle if its maximum valid segment speed is
        at least this threshold.
    p95_speed_threshold_kmh:
        A MAID is kept as motor_vehicle if its 95th percentile valid segment
        speed is at least this threshold.

    Returns
    -------
    DataFrame with one row per MAID and columns:
    `maid`, `n_speed_segments`, `mean_speed_kmh`, `median_speed_kmh`,
    `speed_p95_kmh`, `max_speed_kmh`, `transport_mode`, `classification_rule`.
    """
    speeds = df_with_speed[["maid", "speed_kmh"]].copy()
    speeds["speed_kmh"] = pd.to_numeric(speeds["speed_kmh"], errors="coerce")
    speeds = speeds.replace([float("inf"), float("-inf")], pd.NA).dropna(
        subset=["speed_kmh"]
    )
    speeds = speeds[speeds["speed_kmh"] >= 0]

    features = (
        speeds.groupby("maid")["speed_kmh"]
        .agg(
            n_speed_segments="count",
            mean_speed_kmh="mean",
            median_speed_kmh="median",
            speed_p95_kmh=lambda s: s.quantile(0.95),
            max_speed_kmh="max",
        )
        .reset_index()
    )

    # MAIDs without valid speed segments are non-vehicle by construction.
    all_maids = pd.DataFrame({"maid": pd.unique(df_with_speed["maid"])})
    features = all_maids.merge(features, on="maid", how="left")
    for col in [
        "n_speed_segments",
        "mean_speed_kmh",
        "median_speed_kmh",
        "speed_p95_kmh",
        "max_speed_kmh",
    ]:
        features[col] = features[col].fillna(0)

    is_motor_vehicle = (
        features["max_speed_kmh"] >= max_speed_threshold_kmh
    ) | (features["speed_p95_kmh"] >= p95_speed_threshold_kmh)

    features["transport_mode"] = is_motor_vehicle.map(
        {True: "motor_vehicle", False: "non_vehicle"}
    )
    features["classification_rule"] = (
        f"motor_vehicle if max_speed >= {max_speed_threshold_kmh:g} km/h "
        f"or p95_speed >= {p95_speed_threshold_kmh:g} km/h"
    )

    return features.sort_values("maid").reset_index(drop=True)


def filter_motor_vehicle_maids(
    df: pd.DataFrame,
    *,
    max_speed_threshold_kmh: float = MOTOR_VEHICLE_MAX_SPEED_KMH,
    p95_speed_threshold_kmh: float = MOTOR_VEHICLE_P95_SPEED_KMH,
    drop_helper_columns: bool = True,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Filter a ping-level dataframe to motor-vehicle MAIDs only."""
    df_metrics = _ensure_speed_metrics(df)
    mode_table = classify_vehicle_maids(
        df_metrics,
        max_speed_threshold_kmh=max_speed_threshold_kmh,
        p95_speed_threshold_kmh=p95_speed_threshold_kmh,
    )
    motor_maids = mode_table.loc[
        mode_table["transport_mode"] == "motor_vehicle", "maid"
    ]

    filtered = df_metrics[df_metrics["maid"].isin(motor_maids)].copy()
    if drop_helper_columns:
        cols_to_drop = [col for col in HELPER_COLUMNS if col in filtered.columns]
        filtered = filtered.drop(columns=cols_to_drop)

    summary: dict[str, Any] = {
        "method": "journal_based_speed_feature_rule",
        "classification_rule": mode_table["classification_rule"].iloc[0]
        if not mode_table.empty
        else "no_maids",
        "max_speed_threshold_kmh": max_speed_threshold_kmh,
        "p95_speed_threshold_kmh": p95_speed_threshold_kmh,
        "n_input_rows": int(len(df)),
        "n_output_rows": int(len(filtered)),
        "n_input_maids": int(df["maid"].nunique()),
        "n_motor_vehicle_maids": int(len(motor_maids)),
        "n_non_vehicle_maids": int(
            (mode_table["transport_mode"] == "non_vehicle").sum()
        ),
        "rows_removed": int(len(df) - len(filtered)),
        "maids_removed": int(df["maid"].nunique() - len(motor_maids)),
        "literature_basis": [
            "Reddy et al. (2010): GPS transport mode classification uses speed/acceleration features.",
            "Zheng et al. (2008): GPS trajectory transportation mode inference uses velocity-derived features.",
            "Rakhman (2024): local MPD vehicle/non-vehicle filtering context.",
        ],
    }
    return filtered, summary


def write_summary(summary: dict[str, Any], path: Path = SUMMARY_PATH) -> None:
    """Write preprocessing summary as JSON."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(summary, indent=2), encoding="utf-8")


def main() -> None:
    if not INPUT_PATH.exists():
        print(f"ERROR: File {INPUT_PATH} tidak ditemukan.")
        print("Jalankan collapse_bilocation.py terlebih dahulu.")
        return

    print(f"Membaca data: {INPUT_PATH.resolve()}")
    df = pd.read_parquet(INPUT_PATH)
    print(f"Input: {len(df):,} baris, {df['maid'].nunique():,} MAID")

    filtered, summary = filter_motor_vehicle_maids(df)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    filtered.to_parquet(OUTPUT_PATH, compression="zstd")
    write_summary(summary)

    print("\n--- Ringkasan Klasifikasi Moda Transportasi ---")
    print(f"Aturan: {summary['classification_rule']}")
    print(f"MAID kendaraan bermotor: {summary['n_motor_vehicle_maids']:,}")
    print(f"MAID non-kendaraan   : {summary['n_non_vehicle_maids']:,}")
    print(f"Baris output         : {summary['n_output_rows']:,}")
    print(f"Tersimpan            : {OUTPUT_PATH.resolve()}")
    print(f"Summary              : {SUMMARY_PATH.resolve()}")


if __name__ == "__main__":
    main()
