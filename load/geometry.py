import math
import re

from graph import haversine_km

MIN_KM, MAX_KM = 5.0, 600.0
GRID = 40
KEEP = 5
KM_LAT = 110.574
KM_LON = 111.320
COORDS = re.compile(r"<Polygon>.*?<coordinates>(.*?)</coordinates>", re.S)


def parse_kml(text):
    m = COORDS.search(text)
    if not m:
        return None
    pts = []
    for token in m.group(1).split():
        lon, lat = (float(x) for x in token.split(",")[:2])
        if pts:
            while lon - pts[-1][0] > 180:
                lon -= 360
            while lon - pts[-1][0] < -180:
                lon += 360
        pts.append((lon, lat))
    return pts if len(pts) >= 3 else None


def to_local(poly, lat0, lon0):
    k = KM_LON * math.cos(math.radians(lat0))
    out = []
    for lon, lat in poly:
        d = (lon - lon0 + 180) % 360 - 180
        out.append((d * k, (lat - lat0) * KM_LAT))
    return out


def rotate(poly, deg):
    c, s = math.cos(math.radians(deg)), math.sin(math.radians(deg))
    return [(x * c + y * s, -x * s + y * c) for x, y in poly]


def centroid(poly):
    return sum(x for x, _ in poly) / len(poly), sum(y for _, y in poly) / len(poly)


def bearing(x, y):
    return math.degrees(math.atan2(x, y)) % 360


def inside(pt, poly):
    x, y = pt
    hit = False
    j = len(poly) - 1
    for i in range(len(poly)):
        xi, yi = poly[i]
        xj, yj = poly[j]
        if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / (yj - yi) + xi:
            hit = not hit
        j = i
    return hit


def bbox(poly):
    xs, ys = [x for x, _ in poly], [y for _, y in poly]
    return min(xs), min(ys), max(xs), max(ys)


def overlap_km2(p, q):
    a, b = bbox(p), bbox(q)
    x0, y0, x1, y1 = max(a[0], b[0]), max(a[1], b[1]), min(a[2], b[2]), min(a[3], b[3])
    if x0 >= x1 or y0 >= y1:
        return 0.0
    dx, dy = (x1 - x0) / GRID, (y1 - y0) / GRID
    hits = sum(1 for i in range(GRID) for j in range(GRID)
               if inside((x0 + (i + .5) * dx, y0 + (j + .5) * dy), p) and inside((x0 + (i + .5) * dx, y0 + (j + .5) * dy), q))
    return hits * dx * dy


def turn(lonely, other, polys):
    lat0, lon0 = lonely["lat"], lonely["lon"]
    own = to_local(polys[lonely["code"]], lat0, lon0)
    theirs = to_local(polys[other["code"]], lat0, lon0)
    delta = (bearing(*centroid(theirs)) - bearing(*centroid(own)) + 180) % 360 - 180
    return round(delta), overlap_km2(rotate(own, delta), theirs)


def candidates(lonely, stations):
    p = (lonely["lat"], lonely["lon"])
    for s in stations:
        if s["code"] == lonely["code"] or s["lat"] is None or s["lon"] is None:
            continue
        km = haversine_km(p, (s["lat"], s["lon"]))
        if MIN_KM <= km <= MAX_KM:
            yield s, km


def lonely_cameras(stations):
    return [s for s in stations if s["status"] == "running_no_partner" and s["lat"] is not None and s["az"] is not None]


def installed(stations):
    return [s for s in stations if s["nights"] > 0 or s["orbits"] > 0]


def fov_needed(stations):
    codes = set()
    for s in lonely_cameras(stations):
        codes.add(s["code"])
        codes.update(o["code"] for o, _ in candidates(s, installed(stations)))
    return sorted(codes)


def could_pair(stations, polys, dates):
    out = []
    others = [s for s in installed(stations) if s["code"] in polys]
    for s in lonely_cameras(stations):
        if s["code"] not in polys:
            continue
        rows = []
        for o, km in candidates(s, others):
            deg, km2 = turn(s, o, polys)
            if km2 > 0:
                rows.append({"a": s["code"], "b": o["code"], "turn_deg": deg, "to_az": round(((s["az"] or 0) + deg) % 360, 1),
                             "km": round(km), "km2": round(km2), "fov_date": min(dates[s["code"]], dates[o["code"]]),
                             "aim_changed": bool(s.get("aim_newer") or o.get("aim_newer"))})
        out += sorted(rows, key=lambda r: (-r["km2"], r["b"]))[:KEEP]
    return out


def square(lon, lat, half_deg):
    return [(lon - half_deg, lat - half_deg), (lon + half_deg, lat - half_deg), (lon + half_deg, lat + half_deg), (lon - half_deg, lat + half_deg)]


def self_check():
    kml = "<Placemark><Polygon><outerBoundaryIs><LinearRing><coordinates>179.9,10,100000 -179.9,10,100000 -179.9,11,100000</coordinates></LinearRing></outerBoundaryIs></Polygon></Placemark>"
    assert parse_kml(kml)[1][0] == 180.1
    assert parse_kml("<Polygon></Polygon>") is None
    sq = to_local(square(0, 0, 0.5), 0, 0)
    assert abs(overlap_km2(sq, sq) - 111.32 * 110.574) < 200
    bow = to_local([(0, 0), (1, 1), (1, 0), (0, 1)], 0, 0)
    assert overlap_km2(bow, bow) > 0
    lonely = {"code": "A", "lat": 0.0, "lon": 0.0}
    other = {"code": "B", "lat": 0.0, "lon": 2.0}
    deg, km2 = turn(lonely, other, {"A": square(0, 1, 0.4), "B": square(1.2, 0, 0.5)})
    assert deg == 90 and km2 > 0, (deg, km2)
    print("ok")


if __name__ == "__main__":
    self_check()
