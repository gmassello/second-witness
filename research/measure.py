import argparse
import calendar
import json
import math
import statistics
import sys
from collections import Counter, defaultdict, deque
from itertools import combinations
from pathlib import Path

RAW = Path(__file__).resolve().parent / "raw"
COL_VGEO_SIGMA, COL_LAT, COL_LON, COL_QC, COL_STATIONS = 16, 63, 65, 80, 85
MIN_COUNTRY_ORBITS = 500
TOP_SUSTAINERS = 50
LOW_QC_DEG = 10.0


def parse_float(s):
    try:
        v = float(s)
    except ValueError:
        return None
    return v if math.isfinite(v) else None


def load_trajectories(path):
    out = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            if line.startswith("#") or not line.strip():
                continue
            c = line.split(";")
            if len(c) <= COL_STATIONS:
                raise SystemExit(f"unexpected layout in {path}: {len(c)} columns")
            stations = tuple(sorted({s.strip() for s in c[COL_STATIONS].split(",") if s.strip()}))
            if len(stations) < 2:
                continue
            out.append({
                "stations": stations,
                "vgeo_sigma": parse_float(c[COL_VGEO_SIGMA]),
                "qc": parse_float(c[COL_QC]),
            })
    return out


def build_graph(trajs):
    adj = defaultdict(set)
    weight = Counter()
    for t in trajs:
        for a, b in combinations(t["stations"], 2):
            adj[a].add(b)
            adj[b].add(a)
            weight[a, b] += 1
    return adj, weight


def components(adj, nodes=None):
    nodes = set(adj) if nodes is None else nodes
    seen, comps = set(), []
    for start in sorted(nodes):
        if start in seen:
            continue
        comp, queue = set(), deque([start])
        seen.add(start)
        while queue:
            u = queue.popleft()
            comp.add(u)
            for v in adj[u]:
                if v in nodes and v not in seen:
                    seen.add(v)
                    queue.append(v)
        comps.append(comp)
    return sorted(comps, key=lambda c: (-len(c), min(c)))


def articulation_points(adj):
    disc, low, points, timer = {}, {}, set(), 0
    for root in sorted(adj):
        if root in disc:
            continue
        disc[root] = low[root] = timer
        timer += 1
        root_children = 0
        stack = [(root, None, iter(sorted(adj[root])))]
        while stack:
            u, parent, it = stack[-1]
            advanced = False
            for v in it:
                if v not in disc:
                    disc[v] = low[v] = timer
                    timer += 1
                    if u == root:
                        root_children += 1
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
                if parent != root and low[u] >= disc[parent]:
                    points.add(parent)
        if root_children > 1:
            points.add(root)
    return points


def cut_off(adj, comp_of, comps, x):
    rest = comps[comp_of[x]] - {x}
    sizes = sorted((len(c) for c in components(adj, rest)), reverse=True)
    return sum(sizes[1:])


def haversine_km(a, b):
    la1, lo1, la2, lo2 = map(math.radians, (a[0], a[1], b[0], b[1]))
    h = math.sin((la2 - la1) / 2) ** 2 + math.cos(la1) * math.cos(la2) * math.sin((lo2 - lo1) / 2) ** 2
    return 6371.0 * 2 * math.asin(math.sqrt(h))


def positions_at(coords, cutoff_iso):
    pos = {}
    for station, history in coords.items():
        dates = sorted(d for d in history if d <= cutoff_iso)
        if dates:
            e = history[dates[-1]]
            pos[station] = (e["lat"], e["lon"])
    return pos


def load_index(month_dir):
    per_night = {}
    for f in sorted((month_dir / "index").glob("*/*.json")):
        try:
            rows = json.loads(f.read_text())
        except json.JSONDecodeError:
            continue
        for row in rows:
            key = (row[0], row[2])
            per_night[key] = max(per_night.get(key, 0), int(row[3] or 0))
    nights, detections = Counter(), Counter()
    for (station, _), n in per_night.items():
        nights[station] += 1
        detections[station] += n
    return nights, detections


def network_metrics(trajs):
    adj, weight = build_graph(trajs)
    comps = components(adj)
    comp_of = {s: i for i, c in enumerate(comps) for s in c}
    points = articulation_points(adj)
    cuts = sorted(((cut_off(adj, comp_of, comps, x), x) for x in points), key=lambda t: (-t[0], t[1]))
    multiplicity = Counter(min(len(t["stations"]), 6) for t in trajs)
    two = [t for t in trajs if len(t["stations"]) == 2]
    second_witness = Counter(s for t in two for s in t["stations"])
    top = [s for s, _ in sorted(second_witness.items(), key=lambda kv: (-kv[1], kv[0]))[:TOP_SUSTAINERS]]
    top_set = set(top)
    by_country = defaultdict(lambda: [0, 0])
    for t in trajs:
        for c in {s[:2] for s in t["stations"]}:
            by_country[c][0] += 1
            by_country[c][1] += len(t["stations"]) == 2
    country_share = {c: round(v[1] / v[0], 4) for c, v in sorted(by_country.items()) if v[0] >= MIN_COUNTRY_ORBITS}
    sigma = {}
    for k, label in ((2, "2"), (3, "3"), (4, "4"), (5, "5+")):
        vals = [t["vgeo_sigma"] for t in trajs if t["vgeo_sigma"] is not None and (len(t["stations"]) == k if k < 5 else len(t["stations"]) >= 5)]
        sigma[label] = {"median_km_s": round(statistics.median(vals), 3), "n": len(vals)} if vals else None
    low_qc = sum(1 for t in two if t["qc"] is not None and t["qc"] < LOW_QC_DEG)
    best_sw = max(second_witness.items(), key=lambda kv: (kv[1], kv[0])) if second_witness else (None, 0)
    return {
        "adj": adj,
        "weight": weight,
        "comps": comps,
        "comp_of": comp_of,
        "summary": {
            "trajectories": len(trajs),
            "stations": len(adj),
            "countries": len({s[:2] for s in adj}),
            "pairs": len(weight),
            "multiplicity": {("6+" if k == 6 else str(k)): v for k, v in sorted(multiplicity.items())},
            "two_station_orbits": len(two),
            "two_station_share": round(len(two) / len(trajs), 4) if trajs else 0,
            "top_second_witness": {"station": best_sw[0], "orbits": best_sw[1]},
            "single_partner_stations": sorted(s for s in adj if len(adj[s]) == 1),
            "islands": [{"stations": len(c), "countries": sorted({s[:2] for s in c})} for c in comps],
            "cut_points": len(points),
            "cut_points_top": [{"station": x, "cut_off_stations": n} for n, x in cuts[:10]],
            "cut_points_3plus": sum(1 for n, _ in cuts if n >= 3),
            "country_two_station_share": country_share,
            "top_sustainers": {"stations": TOP_SUSTAINERS, "two_station_orbits": sum(1 for t in two if top_set & set(t["stations"]))},
            "international_orbits": sum(1 for t in trajs if len({s[:2] for s in t["stations"]}) > 1),
            "vgeo_sigma_by_stations": sigma,
            "two_station_low_qc": {"threshold_deg": LOW_QC_DEG, "orbits": low_qc},
        },
    }


def closest_islands(comps, pos, limit=10):
    placed = [[(s, pos[s]) for s in sorted(c) if s in pos] for c in comps]
    out = []
    for i, j in combinations(range(len(comps)), 2):
        if not placed[i] or not placed[j]:
            continue
        d, a, b = min((haversine_km(pa, pb), sa, sb) for sa, pa in placed[i] for sb, pb in placed[j])
        out.append({"km": round(d), "a": a, "b": b, "island_a": sorted({s[:2] for s in comps[i]}), "island_b": sorted({s[:2] for s in comps[j]})})
    return sorted(out, key=lambda r: (r["km"], r["a"], r["b"]))[:limit]


def changes(prev_trajs, cur_adj):
    p_adj, p_weight = build_graph(prev_trajs)
    gone = sorted(set(p_adj) - set(cur_adj))
    gone_set = set(gone)
    p_two = Counter(s for t in prev_trajs if len(t["stations"]) == 2 for s in t["stations"])
    hurt = Counter()
    for (a, b), w in p_weight.items():
        if a in gone_set and b in cur_adj:
            hurt[b] += w
        elif b in gone_set and a in cur_adj:
            hurt[a] += w
    return {
        "previous_stations": len(p_adj),
        "disappeared": len(gone),
        "appeared": len(set(cur_adj) - set(p_adj)),
        "disappeared_two_station_orbits_previous": sum(p_two[g] for g in gone),
        "neighbours_hurt": len(hurt),
        "neighbours_hurt_top": [{"station": s, "shared_meteors_lost": n} for s, n in sorted(hurt.items(), key=lambda kv: (-kv[1], kv[0]))[:10]],
        "disappeared_by_country": dict(Counter(g[:2] for g in gone).most_common()),
        "disappeared_stations": gone,
    }


def liveness(adj, nights, detections, known):
    uploaded = set(nights)
    running_no_partner = sorted((s for s in uploaded if detections[s] > 0 and s not in adj), key=lambda s: (-detections[s], s))
    zero = sorted(s for s in uploaded if detections[s] == 0)
    return {
        "uploaded": len(uploaded),
        "uploaded_with_orbits": len(uploaded & set(adj)),
        "running_no_partner": len(running_no_partner),
        "running_no_partner_top": [{"station": s, "nights": nights[s], "detections": detections[s]} for s in running_no_partner[:20]],
        "uploaded_zero_detections": len(zero),
        "known_not_uploaded": len(set(known) - uploaded),
        "orbits_without_index": len(set(adj) - uploaded),
    }


def measure(month, prev=None):
    cur_dir = RAW / month
    trajs = load_trajectories(cur_dir / f"traj_summary_monthly_{month}.txt")
    net = network_metrics(trajs)
    year, mon = int(month[:4]), int(month[4:])
    cutoff = f"{year:04d}-{mon:02d}-{calendar.monthrange(year, mon)[1]:02d}T23:59:59"
    coords_path = RAW / "GMN_station_coordinates_public.json"
    coords = json.loads(coords_path.read_text()) if coords_path.exists() else {}
    pos = positions_at(coords, cutoff)
    result = {"month": month, "sources": {
        "trajectories": f"https://globalmeteornetwork.org/data/traj_summary_data/monthly/traj_summary_monthly_{month}.txt",
        "coordinates": "https://globalmeteornetwork.org/data/kml_fov/GMN_station_coordinates_public.json",
        "daily_index": "https://globalmeteornetwork.org/status/Rmsindexes/",
        "license": "CC BY 4.0, Global Meteor Network",
    }, **net["summary"]}
    result["closest_islands"] = closest_islands(net["comps"], pos)
    if (cur_dir / "index").exists():
        nights, detections = load_index(cur_dir)
        result["liveness"] = liveness(net["adj"], nights, detections, pos)
    if prev:
        prev_trajs = load_trajectories(RAW / prev / f"traj_summary_monthly_{prev}.txt")
        result["changes"] = {"previous_month": prev, **changes(prev_trajs, net["adj"])}
    return result


def self_check():
    def t(*s, sigma=0.3, qc=20.0):
        return {"stations": tuple(sorted(s)), "vgeo_sigma": sigma, "qc": qc}
    trajs = [t("AA0001", "AA0002"), t("AA0002", "AA0003"), t("AA0003", "AA0004"), t("AA0002", "AA0004", sigma=0.1),
             t("BB0001", "BB0002", qc=5.0)]
    net = network_metrics(trajs)
    s = net["summary"]
    assert [i["stations"] for i in s["islands"]] == [4, 2], s["islands"]
    assert s["cut_points"] == 1 and s["cut_points_top"][0] == {"station": "AA0002", "cut_off_stations": 1}, s["cut_points_top"]
    assert s["single_partner_stations"] == ["AA0001", "BB0001", "BB0002"], s["single_partner_stations"]
    assert s["two_station_orbits"] == 5 and s["two_station_low_qc"]["orbits"] == 1
    assert s["top_second_witness"] == {"station": "AA0002", "orbits": 3}, s["top_second_witness"]
    ch = changes(trajs + [t("CC0001", "AA0001")], net["adj"])
    assert ch["disappeared"] == 1 and ch["neighbours_hurt_top"][0] == {"station": "AA0001", "shared_meteors_lost": 1}, ch
    live = liveness(net["adj"], Counter({"AA0001": 3, "DD0001": 2, "EE0001": 1}), Counter({"AA0001": 9, "DD0001": 40}), {"AA0001": 0, "DD0001": 0, "EE0001": 0, "FF0001": 0})
    assert live["running_no_partner"] == 1 and live["running_no_partner_top"][0]["station"] == "DD0001", live
    assert live["uploaded_zero_detections"] == 1 and live["known_not_uploaded"] == 1, live
    near = closest_islands(net["comps"], {"AA0001": (0.0, 0.0), "BB0001": (0.0, 1.0)})
    assert near and near[0]["a"] == "AA0001" and 110 < near[0]["km"] < 112, near
    print("self-check ok")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("month", nargs="?")
    p.add_argument("--prev")
    p.add_argument("--json")
    p.add_argument("--self-check", action="store_true")
    a = p.parse_args()
    if a.self_check:
        self_check()
        return
    if not a.month:
        p.error("month YYYYMM is required")
    result = measure(a.month, a.prev)
    text = json.dumps(result, indent=1, ensure_ascii=False)
    if a.json:
        Path(a.json).write_text(text + "\n")
    print(text if not a.json else f"wrote {a.json}")


if __name__ == "__main__":
    sys.exit(main())
