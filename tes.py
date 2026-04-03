import duckdb
import pandas as pd

con = duckdb.connect()

# Cek dtype parquet April
print("Schema Parquet April:")
print(con.execute("DESCRIBE SELECT * FROM read_parquet('DataGPS_parquet/2022_04_April.parquet')").df())

# Bandingkan dengan ignore_errors (handle duplicate header)
csv_stats = con.execute("""
    SELECT COUNT(DISTINCT latitude) as dist_lat, COUNT(DISTINCT longitude) as dist_lon
    FROM read_csv_auto('DataGPS/2022April/April2022.csv', ignore_errors=true)
""").df()

pq_stats = con.execute("""
    SELECT COUNT(DISTINCT latitude) as dist_lat, COUNT(DISTINCT longitude) as dist_lon
    FROM read_parquet('DataGPS_parquet/2022_04_April.parquet')
""").df()

print("\nCSV April:", csv_stats)
print("Parquet April:", pq_stats)