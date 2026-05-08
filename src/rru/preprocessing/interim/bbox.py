from pathlib import Path
import polars as pl
from src.rru.utils import drop_singleton_maids
from configs import bounding_boxes

INPUT_PARQUET = Path("./data/raw/DataGPS_parquet/all_gps_data_no_dup.parquet") 
OUTPUT_BBOX = Path("./data/interim/output_bbox.parquet")

# Spatial scope (Bounding box Ring Road Utara)
LON_MIN, LON_MAX = bounding_boxes["rru"]["lon_min"], bounding_boxes["rru"]["lon_max"]
LAT_MIN, LAT_MAX = bounding_boxes["rru"]["lat_min"], bounding_boxes["rru"]["lat_max"]

def main():
    if OUTPUT_BBOX.exists():
        df_bb = pl.read_parquet(OUTPUT_BBOX)
        print(f"Load existing: {df_bb.height:,} ping, "
              f"{df_bb['maid'].n_unique():,} MAID")
        return

    print(f"Read and filter from {INPUT_PARQUET}...")
    
    OUTPUT_BBOX.parent.mkdir(parents=True, exist_ok=True)

    bbox_filter = (
        pl.col("latitude").is_between(LAT_MIN, LAT_MAX)
        & pl.col("longitude").is_between(LON_MIN, LON_MAX)
    )

    scan = pl.scan_parquet(INPUT_PARQUET).filter(bbox_filter)

    df_bb = scan.select("maid", "latitude", "longitude", "timestamp").collect()
    df_bb = drop_singleton_maids(df_bb, label="stage 1a")
    df_bb.write_parquet(OUTPUT_BBOX, compression="zstd")
    print(f"Saved: {OUTPUT_BBOX}")

if __name__ == "__main__":
    main()