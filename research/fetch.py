import calendar
import json
import sys
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

BASE = "https://globalmeteornetwork.org"
RAW = Path(__file__).resolve().parent / "raw"
HEADERS = {"User-Agent": "second-witness/0.1 (GMN network analysis)"}
WORKERS = 4


def get(url, dest, pause=0.2):
    if dest.exists() and dest.stat().st_size > 0:
        return True
    gone = dest.with_suffix(dest.suffix + ".404")
    if gone.exists():
        return False
    dest.parent.mkdir(parents=True, exist_ok=True)
    req = urllib.request.Request(url, headers=HEADERS)
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                tmp = dest.with_suffix(dest.suffix + ".part")
                tmp.write_bytes(r.read())
                tmp.replace(dest)
            time.sleep(pause)
            return True
        except urllib.error.HTTPError as e:
            if e.code == 404:
                gone.touch()
                return False
            time.sleep(2 * (attempt + 1))
        except urllib.error.URLError:
            time.sleep(2 * (attempt + 1))
    raise SystemExit(f"failed after 3 attempts: {url}")


def fetch(month):
    year, mon = int(month[:4]), int(month[4:])
    out = RAW / month
    traj = out / f"traj_summary_monthly_{month}.txt"
    get(f"{BASE}/data/traj_summary_data/monthly/{traj.name}", traj)
    get(f"{BASE}/data/kml_fov/GMN_station_coordinates_public.json", RAW / "GMN_station_coordinates_public.json")
    countries_file = RAW / "country_dataset.json"
    get(f"{BASE}/status/Rmsindexes/country_dataset.json", countries_file)
    countries = json.loads(countries_file.read_text())
    jobs = [(c, f"{month}{day:02d}") for c in countries for day in range(1, calendar.monthrange(year, mon)[1] + 1)]
    with ThreadPoolExecutor(max_workers=WORKERS) as pool:
        found = pool.map(lambda j: get(f"{BASE}/status/Rmsindexes/{j[0]}/{year}/{j[0]}_{j[1]}.json", out / "index" / j[0] / f"{j[0]}_{j[1]}.json"), jobs)
        missing = sorted(f"{c}_{stamp}" for (c, stamp), ok in zip(jobs, found) if not ok)
    (out / "index_missing.txt").write_text("\n".join(missing) + ("\n" if missing else ""))
    print(f"{month}: trajectories {traj.stat().st_size} bytes, {len(countries)} countries, {len(missing)} index days missing")


if __name__ == "__main__":
    if len(sys.argv) != 2 or len(sys.argv[1]) != 6 or not sys.argv[1].isdigit():
        raise SystemExit("usage: fetch.py YYYYMM")
    fetch(sys.argv[1])
