from pathlib import Path
import duckdb

STAGING = Path("staging")
DIM = (STAGING / "dim_station.parquet").as_posix()
