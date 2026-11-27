import calendar
import datetime
import json
import re
import statistics
import time
import urllib.error
import urllib.request
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
from itertools import combinations
from pathlib import Path

import geometry

BASE = "https://globalmeteornetwork.org"
HEADERS = {"User-Agent": "second-witness/0.1 (GMN network analysis)"}
COLUMNS = 86
COL_STATIONS = 85
COL_VGEO_SIGMA = 16
SAMPLE_IDS = 3
WORKERS = 4
SUFFIX = re.compile(r"_\d+$")


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
            stations = tuple(sorted({SUFFIX.sub("", s.strip()) for s in c[COL_STATIONS].split(",") if s.strip()}))
            out.append((c[0].strip(), stations, parse_float(c[COL_VGEO_SIGMA])))
    return out


def parse_float(s):
    try:
        v = float(s)
    except ValueError:
        return None
    return v if v == v and abs(v) != float("inf") else None


def median_sigma(trajs, n):
    vals = sorted(v for _, st, v in trajs if len(st) == n and v is not None)
    return statistics.median(vals) if vals else None


def country_rows_stats(trajs):
    orbits, two = Counter(), Counter()
    for _, st, _ in trajs:
        for c in {s[:2] for s in st}:
            orbits[c] += 1
            two[c] += len(st) == 2
    return {c: {"country": c, "orbits": orbits[c], "two_station_orbits": two[c],
                "two_station_share": round(two[c] / orbits[c], 6)} for c in orbits}


def pairs(trajs):
    acc = {}
    for tid, stations, _ in trajs:
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
    orbits, two, three, partners = Counter(), Counter(), Counter(), defaultdict(set)
    for _, stations, _ in trajs:
        for s in stations:
            orbits[s] += 1
            two[s] += len(stations) == 2
            three[s] += len(stations) == 3
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
            "three_station_orbits": three[code],
            "partners": len(partners[code]),
            "az": p.get("azim_center"),
            "alt": p.get("alt_center"),
            "last_upload": stamp_iso(last[code]) if code in last else None,
            "aim_newer": max(coords.get(code, {}) or [""]) > cutoff,
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
    cutoff = month_end(month)
    positions = {c: (e["lat"], e["lon"]) for c, h in coords.items() if (e := at_or_before(h, cutoff))}
    return {
        "stations": stations,
        "countries": country_rows(stations, cache / "gmncountries2.json"),
        "pairs": pairs(trajs),
        "positions": positions,
        "known": [{"code": c, "country": c[:2]} for c in sorted(coords)],
        "country_stats": country_rows_stats(trajs),
        "meta": {"sigma2_median": median_sigma(trajs, 2), "sigma3_median": median_sigma(trajs, 3)},
    }


def kml_path(cache, code):
    return cache / "kml" / f"{code}-100km.kml"


def fetch_fov(codes, cache, fresh=False):
    def one(code):
        try:
            return get(f"{BASE}/data/kml_fov/{code}-100km.kml", kml_path(cache, code), force=fresh)
        except SystemExit:
            return False
    with ThreadPoolExecutor(max_workers=WORKERS) as pool:
        return sum(pool.map(one, codes))


def read_fov(codes, cache):
    polys, dates = {}, {}
    for code in codes:
        f = kml_path(cache, code)
        if not f.exists() or f.stat().st_size == 0:
            continue
        poly = geometry.parse_kml(f.read_text(errors="replace"))
        if poly:
            polys[code] = poly
            dates[code] = datetime.datetime.fromtimestamp(f.stat().st_mtime, datetime.UTC).date().isoformat()
    return polys, dates


def window(last_month, n=12):
    y, m = int(last_month[:4]), int(last_month[4:])
    out = []
    for _ in range(n):
        out.append(f"{y:04d}{m:02d}")
        y, m = (y, m - 1) if m > 1 else (y - 1, 12)
    return sorted(out)


def self_check():
    t = [("a", ("A", "B"), 1.0), ("b", ("A", "B", "C"), 2.0), ("c", ("A", "B"), None)]
    assert median_sigma(t, 2) == 1.0 and median_sigma(t, 3) == 2.0
    assert country_rows_stats([("a", ("ES0001", "PT0001"), None), ("b", ("ES0001", "ES0002", "PT0002"), None)])["ES"]["orbits"] == 2
    assert parse_float(" nan") is None and parse_float("x") is None
    p = {(x["a"], x["b"]): x for x in pairs(t)}
    assert p["A", "B"]["meteors"] == 3 and p["A", "B"]["two_station"] == 2
    assert p["B", "C"]["sample_ids"] == ["b"]
    assert window("202610")[0] == "202511" and window("202610")[-1] == "202610"
    assert stamp_iso("20261002_180000_000000") == "2026-10-02T18:00:00"
    assert month_end("202602") == "2026-02-28T23:59:59"
    print("ok")


if __name__ == "__main__":
    self_check()
