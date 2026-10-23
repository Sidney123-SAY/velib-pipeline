# ingest.py
import json, time
from datetime import datetime, timezone
from pathlib import Path
import requests

BASE = "https://velib-metropole-opendata.smovengo.cloud/opendata/Velib_Metropole"
ENDPOINTS = {
    "station_information": f"{BASE}/station_information.json",
    "station_status": f"{BASE}/station_status.json",
}
RAW = Path("raw")


def fetch(url, tries=3):
    """Appelle l'API, réessaie en espaçant les tentatives."""
    for n in range(tries):
        try:
            r = requests.get(url, timeout=20)
            r.raise_for_status()
            return r.json()
        except requests.RequestException:
            if n == tries - 1:
                raise
            time.sleep(2 ** n)


def main():
    captured_at = datetime.now(timezone.utc)
    day = captured_at.strftime("%Y-%m-%d")
    stamp = captured_at.strftime("%H-%M-%S")

    for name, url in ENDPOINTS.items():
        payload = fetch(url)
        folder = RAW / name / day
        folder.mkdir(parents=True, exist_ok=True)
        path = folder / f"{stamp}.json"
        path.write_text(
            json.dumps({
                "captured_at": captured_at.isoformat(),
                "source_url": url,
                "payload": payload,
            }),
            encoding="utf-8",
        )
        n_stations = len(payload["data"]["stations"])
        print(f"{captured_at.isoformat()}  {name}  {n_stations} stations  -> {path}")


if __name__ == "__main__":
    main()