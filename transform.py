import json
import pathlib as pl
import pandas as pd

RAW = pl.Path("raw")
STAGING = pl.Path("staging")
STALE_AFTER = pd.Timedelta("2h")

def read_status_file(path):
    doc = json.loads(path.read_text(encoding="utf-8"))
    captured_at = pd.Timestamp(doc["captured_at"])
    rows = []
    for s in doc["payload"]["data"]["stations"]:
        kinds = {k: v for d in s.get("num_bikes_available_types", []) for k, v in d.items()}
        rows.append({
            "captured_at": captured_at,
            "station_id": s["station_id"],
            "bikes_total": s["num_bikes_available"] ,
            "bikes_mechanical": kinds.get("mechanical", 0),
            "bikes_ebike": kinds.get("ebike", 0),
            "docks_available": s["num_docks_available"],
            "is_renting": bool(s["is_renting"]),
            "is_returning": bool(s["is_returning"]),
            "last_reported": pd.Timestamp(s["last_reported"], unit="s"),
        })
    return pd.DataFrame(rows)
def transform_day(day_dir):
    files = sorted(day_dir.glob("*.json"))
    df = pd.concat([read_status_file(p) for p in files], ignore_index=True)

    read = len(df)
    df = df.drop_duplicates(subset=["station_id", "captured_at"])
    fresh = (df["captured_at"] - df["last_reported"]) <= STALE_AFTER
    df = df.loc[fresh & df["is_renting"]]

    out = STAGING / "station_status"
    out.mkdir(parents=True, exist_ok=True)
    df.to_parquet(out / f"{day_dir.name}.parquet", index=False)
    print(f"{day_dir.name}: {len(files)} captures, {read} lignes lues, "
          f"{read - len(df)} écartées, {len(df)} conservées")


def transform_dimension():
    latest = sorted(RAW.glob("station_information/*/*.json"))[-1]
    doc = json.loads(latest.read_text(encoding="utf-8"))
    df = pd.DataFrame(doc["payload"]["data"]["stations"])
    df = df[["station_id", "stationCode", "name", "lat", "lon", "capacity"]]
    df = df.drop_duplicates(subset=["station_id"])
    STAGING.mkdir(parents=True, exist_ok=True)
    df.to_parquet(STAGING / "dim_station.parquet", index=False)
    print(f"dimension : {len(df)} stations")


if __name__ == "__main__":
    transform_dimension()
    for day_dir in sorted((RAW / "station_status").iterdir()):
        transform_day(day_dir)