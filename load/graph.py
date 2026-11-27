import datetime
import math
from collections import Counter, defaultdict
from itertools import combinations

UPLOAD_LAG_H = 17
LATE_H, DARK_H, SILENT_H = 36, 72, 168


def adjacency(pairs):
    adj = defaultdict(set)
    for p in pairs:
        adj[p["a"]].add(p["b"])
        adj[p["b"]].add(p["a"])
    return adj


def components(adj):
    seen, comps = set(), []
    for start in sorted(adj):
        if start in seen:
            continue
        comp, stack = [], [start]
        seen.add(start)
        while stack:
            u = stack.pop()
            comp.append(u)
            for v in adj[u]:
                if v not in seen:
                    seen.add(v)
                    stack.append(v)
        comps.append(sorted(comp))
    return comps


def cut_offs(adj, comps):
    out = {}
    for comp in comps:
        n = len(comp)
        root = comp[0]
        disc, low, size = {root: 0}, {root: 0}, {root: 1}
        pieces = defaultdict(list)
        timer = 1
        stack = [(root, None, iter(sorted(adj[root])))]
        while stack:
            u, parent, it = stack[-1]
            advanced = False
            for v in it:
                if v not in disc:
                    disc[v] = low[v] = timer
                    size[v] = 1
                    timer += 1
                    stack.append((v, u, iter(sorted(adj[v]))))
                    advanced = True
                    break
                if v != parent:
                    low[u] = min(low[u], disc[v])
            if advanced:
                continue
            stack.pop()
            if parent is not None:
                low[parent] = min(low[parent], low[u])
                size[parent] += size[u]
                if low[u] >= disc[parent]:
                    pieces[parent].append(size[u])
        for u in comp:
            split = pieces.get(u, [])
            if u == root:
                split = split if len(split) > 1 else []
            if not split:
                out[u] = 0
                continue
            rest = n - 1 - sum(split)
            out[u] = n - 1 - max(split + [rest])
    return out


def haversine_km(a, b):
    la1, lo1, la2, lo2 = map(math.radians, (a[0], a[1], b[0], b[1]))
    h = math.sin((la2 - la1) / 2) ** 2 + math.cos(la1) * math.cos(la2) * math.sin((lo2 - lo1) / 2) ** 2
    return 12742.0 * math.asin(math.sqrt(min(1.0, h)))


def site_of(lat, lon):
    return None if lat is None or lon is None else f"{lat:.2f},{lon:.2f}"


def nearest_islands(comps, pos):
    placed = [[(s, pos[s]) for s in c if s in pos] for c in comps]
    best = {}
    for i, j in combinations(range(len(comps)), 2):
        if not placed[i] or not placed[j]:
            continue
        d, a, b = min((haversine_km(pa, pb), sa, sb) for sa, pa in placed[i] for sb, pb in placed[j])
        for k in (i, j):
            if k not in best or d < best[k][0]:
                best[k] = (d, a, b)
    edges = {(a, b): d for d, a, b in best.values()}
    return [{"a": a, "b": b, "km": round(d)} for (a, b), d in sorted(edges.items())]


def upload_state(last_upload, now):
    if not last_upload:
        return None
    age = (now - datetime.datetime.fromisoformat(last_upload)).total_seconds() / 3600 - UPLOAD_LAG_H
    return "silent" if age > SILENT_H else "dark" if age > DARK_H else "late" if age > LATE_H else "running"


def annotate(data, prev_pairs, positions=None, now=None):
    positions = positions or {}
    stations = {s["code"]: s for s in data["stations"]}
    adj = adjacency(data["pairs"])
    comps = components(adj)
    island = {s: c[0] for c in comps for s in c}
    cut = cut_offs(adj, comps)
    prev_adj = adjacency(prev_pairs) if prev_pairs is not None else None
    gone = set(prev_adj) - set(adj) if prev_adj is not None else set()
    new = set(adj) - set(prev_adj) if prev_adj is not None else set()
    lost = Counter()
    for p in prev_pairs or []:
        if p["a"] in gone and p["b"] in adj:
            lost[p["b"]] += p["meteors"]
        elif p["b"] in gone and p["a"] in adj:
            lost[p["a"]] += p["meteors"]
    for code in gone - set(stations):
        lat, lon = positions.get(code, (None, None))
        stations[code] = {"code": code, "country": code[:2], "lat": lat, "lon": lon, "nights": 0, "detections": 0,
                          "orbits": 0, "two_station_orbits": 0, "partners": 0, "az": None, "alt": None, "last_upload": None,
                          "aim_newer": False}
    for s in stations.values():
        s.setdefault("lat", None)
        s.setdefault("lon", None)
        s["site"] = site_of(s["lat"], s["lon"])
    new_sites = {stations[c]["site"] for c in new if c in stations and stations[c]["site"]}
    for code, s in stations.items():
        s["island"] = island.get(code)
        s["cut_off"] = cut.get(code, 0)
        s["status"] = ("paired" if code in adj else "running_no_partner" if s["detections"] > 0
                       else "uploaded_zero" if s["nights"] > 0 else "no_upload")
        s["change"] = ("possibly_moved" if code in gone and s["site"] in new_sites else "stopped" if code in gone
                       else "new" if code in new else None)
        s["lost"] = lost[code]
        s["upload"] = upload_state(s["last_upload"], now) if now else None
    data["stations"] = [stations[c] for c in sorted(stations)]
    pos = {c: (s["lat"], s["lon"]) for c, s in stations.items() if s["lat"] is not None and s["lon"] is not None}
    data["nearest"] = nearest_islands(comps, pos)
    return data


def self_check():
    pairs = [{"a": a, "b": b, "meteors": 1} for a, b in
             [("A", "B"), ("B", "C"), ("C", "A"), ("C", "D"), ("D", "E"), ("E", "F"), ("X", "Y")]]
    adj = adjacency(pairs)
    comps = components(adj)
    assert comps == [["A", "B", "C", "D", "E", "F"], ["X", "Y"]], comps
    cut = cut_offs(adj, comps)
    assert cut == {"A": 0, "B": 0, "C": 2, "D": 2, "E": 1, "F": 0, "X": 0, "Y": 0}, cut
    star = adjacency([{"a": "H", "b": x} for x in "PQR"])
    assert cut_offs(star, components(star))["H"] == 2
    now = datetime.datetime(2026, 11, 25, 12)
    ago = lambda h: (now - datetime.timedelta(hours=h)).isoformat()
    assert [upload_state(ago(h), now) for h in (40, 72, 96, 192)] == ["running", "late", "dark", "silent"]
    assert site_of(40.0, -3.456) == "40.00,-3.46"
    print("ok")


if __name__ == "__main__":
    self_check()
