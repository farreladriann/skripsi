import pandas as pd

from src.rru.preprocessing.transport_mode_filter import (
    MOTOR_VEHICLE_MAX_SPEED_KMH,
    MOTOR_VEHICLE_P95_SPEED_KMH,
    classify_vehicle_maids,
    filter_motor_vehicle_maids,
)


def _df_for_maid(maid: str, speeds: list[float]) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "maid": [maid] * len(speeds),
            "latitude": [-7.75] * len(speeds),
            "longitude": [110.37] * len(speeds),
            "timestamp": pd.date_range("2022-01-01", periods=len(speeds), freq="min"),
            "speed_kmh": speeds,
        }
    )


def test_classify_vehicle_maids_marks_motorized_when_high_speed_evidence_exists():
    df = pd.concat(
        [
            _df_for_maid("walk", [0.0, 2.0, 4.0, 5.0]),
            _df_for_maid("bike_like", [0.0, 8.0, 12.0, 14.0]),
            _df_for_maid("motor_p95", [0.0, 16.0, 18.0, 20.0]),
            _df_for_maid("motor_max", [0.0, 4.0, 6.0, MOTOR_VEHICLE_MAX_SPEED_KMH + 1.0]),
        ],
        ignore_index=True,
    )

    classified = classify_vehicle_maids(df)
    modes = dict(zip(classified["maid"], classified["transport_mode"]))

    assert modes["walk"] == "non_vehicle"
    assert modes["bike_like"] == "non_vehicle"
    assert modes["motor_p95"] == "motor_vehicle"
    assert modes["motor_max"] == "motor_vehicle"
    assert classified.loc[classified["maid"] == "motor_p95", "speed_p95_kmh"].iloc[0] >= MOTOR_VEHICLE_P95_SPEED_KMH


def test_filter_motor_vehicle_maids_keeps_only_motorized_vehicle_rows_and_drops_helper_columns():
    df = pd.concat(
        [
            _df_for_maid("walk", [0.0, 2.0, 4.0, 5.0]),
            _df_for_maid("motor", [0.0, 12.0, 20.0, 35.0]),
        ],
        ignore_index=True,
    )
    df["candidate_edge_keys"] = [["e1"]] * len(df)
    df["candidate_dists"] = [[1.0]] * len(df)

    filtered, summary = filter_motor_vehicle_maids(df)

    assert set(filtered["maid"].unique()) == {"motor"}
    assert summary["n_motor_vehicle_maids"] == 1
    assert summary["n_non_vehicle_maids"] == 1
    assert "speed_kmh" not in filtered.columns
    assert "time_diff_hours" not in filtered.columns
    assert "distance_km" not in filtered.columns
