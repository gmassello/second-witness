import calendar
import json
import time
import urllib.error
import urllib.request
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
from itertools import combinations
from pathlib import Path

BASE = "https://globalmeteornetwork.org"
HEADERS = {"User-Agent": "second-witness/0.1 (GMN network analysis)"}
COLUMNS = 86
COL_STATIONS = 85
SAMPLE_IDS = 3
WORKERS = 4


class LayoutError(Exception):
    pass


def get(url, dest, force=False):
    if dest.exists() and dest.stat().st_size > 0 and not force:
        return True
    gone = dest.with_suffix(dest.suffix + ".404")
    if gone.exists() and not force:
        return False
    dest.parent.mkdir(parents=True, exist_ok=True)
    req = urllib.request.Request(url, headers=HEADERS)
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                tmp = dest.with_suffix(dest.suffix + ".part")
                tmp.write_bytes(r.read())
                tmp.replace(dest)
            return True
        except urllib.error.HTTPError as e:
            if e.code == 404:
                gone.touch()
                return False
            time.sleep(2 * (attempt + 1))
        except (urllib.error.URLError, TimeoutError, ConnectionError):
            time.sleep(2 * (attempt + 1))
    raise SystemExit(f"failed after 3 attempts: {url}")


def fetch(month, cache, fresh=False):
    year, mon = int(month[:4]), int(month[4:])
    traj = cache / month / f"traj_summary_monthly_{month}.txt"
    get(f"{BASE}/data/traj_summary_data/monthly/{traj.name}", traj, force=fresh)
    get(f"{BASE}/data/kml_fov/GMN_station_coordinates_public.json", cache / "GMN_station_coordinates_public.json", force=fresh)
    get(f"{BASE}/status/gmncountries2.json", cache / "gmncountries2.json")
    get(f"{BASE}/status/Rmsindexes/country_dataset.json", cache / "country_dataset.json")
    countries = json.loads((cache / "country_dataset.json").read_text())
    days = [f"{month}{d:02d}" for d in range(1, calendar.monthrange(year, mon)[1] + 1)]
    jobs = [(c, d) for c in countries for d in days]
    with ThreadPoolExecutor(max_workers=WORKERS) as pool:
        list(pool.map(lambda j: get(f"{BASE}/status/Rmsindexes/{j[0]}/{year}/{j[0]}_{j[1]}.json", cache / month / "index" / j[0] / f"{j[0]}_{j[1]}.json", force=fresh), jobs))


def read_trajectories(path):
    out = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            if line.startswith("#") or not line.strip():
                continue
            c = line.split(";")
            if len(c) != COLUMNS:
                raise LayoutError(f"{path}: {len(c)} columns, expected {COLUMNS}")
            stations = tuple(sorted({s.strip() for s in c[COL_STATIONS].split(",") if s.strip()}))
            out.append((c[0].strip(), stations))
    return out


def pairs(trajs):
    acc = {}
    for tid, stations in trajs:
        for a, b in combinations(stations, 2):
            p = acc.setdefault((a, b), {"a": a, "b": b, "meteors": 0, "two_station": 0, "sample_ids": []})
            p["meteors"] += 1
            p["two_station"] += len(stations) == 2
            if len(p["sample_ids"]) < SAMPLE_IDS:
                p["sample_ids"].append(tid)
    return list(acc.values())


def read_index(month_dir):
    per_night, last = {}, {}
    for f in sorted((month_dir / "index").glob("*/*.json")):
        try:
            rows = json.loads(f.read_text())
        except json.JSONDecodeError:
            continue
        for cam, stamp, night, n in rows:
            per_night[cam, night] = max(per_night.get((cam, night), 0), int(n or 0))
            last[cam] = max(last.get(cam, ""), stamp)
    return per_night, last


def stamp_iso(stamp):
    d, t = stamp.split("_")[:2]
    return f"{d[:4]}-{d[4:6]}-{d[6:]}T{t[:2]}:{t[2:4]}:{t[4:6]}"


def at_or_before(history, cutoff):
    dates = sorted(d for d in history if d <= cutoff)
    return history[dates[-1]] if dates else None


def month_end(month):
    year, mon = int(month[:4]), int(month[4:])
    return f"{month[:4]}-{month[4:]}-{calendar.monthrange(year, mon)[1]:02d}T23:59:59"


def station_rows(trajs, per_night, last, coords, month):
    orbits, two, partners = Counter(), Counter(), defaultdict(set)
    for _, stations in trajs:
        for s in stations:
            orbits[s] += 1
            two[s] += len(stations) == 2
            partners[s].update(x for x in stations if x != s)
    nights, detections = Counter(), Counter()
    for (cam, _), n in per_night.items():
        nights[cam] += 1
        detections[cam] += n
    cutoff = month_end(month)
    rows = []
    for code in sorted(set(orbits) | set(nights)):
        e = at_or_before(coords.get(code, {}), cutoff) or {}
        p = e.get("pointing") or {}
        rows.append({
            "code": code,
            "country": code[:2],
            "lat": e.get("lat"),
            "lon": e.get("lon"),
            "nights": nights[code],
            "detections": detections[code],
            "orbits": orbits[code],
            "two_station_orbits": two[code],
            "partners": len(partners[code]),
            "az": p.get("azim_center"),
            "alt": p.get("alt_center"),
            "last_upload": stamp_iso(last[code]) if code in last else None,
        })
    return rows


def country_rows(stations, names_file):
    names = {}
    if names_file.exists():
        names = {c["code"]: c["name"] for c in json.loads(names_file.read_text())}
    return [{"code": c, "name": names.get(c, c)} for c in sorted({s["country"] for s in stations})]


def month_data(month, cache):
    month_dir = cache / month
    trajs = read_trajectories(month_dir / f"traj_summary_monthly_{month}.txt")
    coords_file = cache / "GMN_station_coordinates_public.json"
    coords = json.loads(coords_file.read_text()) if coords_file.exists() else {}
    per_night, last = read_index(month_dir)
    stations = station_rows(trajs, per_night, last, coords, month)
    return {
        "stations": stations,
        "countries": country_rows(stations, cache / "gmncountries2.json"),
        "pairs": pairs(trajs),
    }


def window(last_month, n=12):
    y, m = int(last_month[:4]), int(last_month[4:])
    out = []
    for _ in range(n):
        out.append(f"{y:04d}{m:02d}")
        y, m = (y, m - 1) if m > 1 else (y - 1, 12)
    return sorted(out)


def self_check():
    t = [("a", ("A", "B")), ("b", ("A", "B", "C")), ("c", ("A", "B"))]
    p = {(x["a"], x["b"]): x for x in pairs(t)}
    assert p["A", "B"]["meteors"] == 3 and p["A", "B"]["two_station"] == 2
    assert p["B", "C"]["sample_ids"] == ["b"]
    assert window("202610")[0] == "202511" and window("202610")[-1] == "202610"
    assert stamp_iso("20261002_180000_000000") == "2026-10-02T18:00:00"
    assert month_end("202602") == "2026-02-28T23:59:59"
    print("ok")


if __name__ == "__main__":
    self_check()
