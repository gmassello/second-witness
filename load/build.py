import argparse
import datetime
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import geometry
import gmn
import graph

ROOT = Path(__file__).resolve().parent.parent
REPO = "gmassello/second-witness"
BATCH = 1000

MONTH = ("MERGE (m:Month {id: $meta.month}) SET m.partial = $meta.partial, m.as_of = $meta.as_of, "
         "m.sigma2_median = $meta.sigma2_median, m.sigma3_median = $meta.sigma3_median")
DROP_COUNTRY_STATS = "MATCH (:Country)-[t:STATS]->(:Month {id: $meta.month}) DELETE t"
KNOWN = ("UNWIND $known[{i}..{j}] AS r MERGE (s:Station {{code: r.code}}) "
         "WITH s, r WHERE s.country IS NULL SET s.country = r.country")
COUNTRY_STATS = ("UNWIND $country_stats AS r MERGE (c:Country {code: r.country}) WITH c, r MATCH (m:Month {id: $meta.month}) "
                 "CREATE (c)-[:STATS {month: $meta.month, orbits: r.orbits, two_station_orbits: r.two_station_orbits, "
                 "three_station_orbits: r.three_station_orbits, two_station_share: r.two_station_share, running_no_partner: r.running_no_partner, islands: r.islands}]->(m)")
LINK = [s.strip() for s in (ROOT / "site" / "cypher" / "link.cypher").read_text().split(";") if s.strip()]
DROP_SHARED = "MATCH (:Station)-[s:SHARED {month: $meta.month}]->(:Station) DELETE s"
DROP_STATS = "MATCH (:Station)-[t:STATS]->(:Month {id: $meta.month}) DELETE t"
DROP_COULD = "MATCH (:Station)-[c:COULD_PAIR {month: $meta.month}]->(:Station) DELETE c"
DROP_NEAREST = "MATCH (:Station)-[n:NEAREST_ISLAND {month: $meta.month}]->(:Station) DELETE n"
COUNTRIES = "UNWIND $countries AS c MERGE (x:Country {code: c.code}) SET x.name = c.name"
STATIONS = ("UNWIND $stations[{i}..{j}] AS r MERGE (s:Station {{code: r.code}}) SET s.country = r.country "
            "WITH s, r WHERE s.pos_month IS NULL OR s.pos_month <= $meta.month "
            "SET s.lat = r.lat, s.lon = r.lon, s.site = r.site, s.pos_month = $meta.month")
FOV = ("UNWIND $fov[{i}..{j}] AS r MATCH (s:Station {{code: r.code}}) "
       "SET s.fov100 = r.poly, s.fov100_date = r.date")
STATS = ("UNWIND $stations[{i}..{j}] AS r MATCH (s:Station {{code: r.code}}), (m:Month {{id: $meta.month}}) "
         "CREATE (s)-[:STATS {{month: $meta.month, nights: r.nights, detections: r.detections, orbits: r.orbits, "
         "two_station_orbits: r.two_station_orbits, three_station_orbits: r.three_station_orbits, partners: r.partners, az: r.az, alt: r.alt, last_upload: r.last_upload, "
         "island: r.island, cut_off: r.cut_off, status: r.status, change: r.change, lost: r.lost, upload: r.upload}}]->(m)")
SHARED = ("UNWIND $pairs[{i}..{j}] AS r MATCH (a:Station {{code: r.a}}), (b:Station {{code: r.b}}) "
          "CREATE (a)-[:SHARED {{month: $meta.month, meteors: r.meteors, two_station: r.two_station, sample_ids: r.sample_ids}}]->(b)")
COULD = ("UNWIND $could[{i}..{j}] AS r MATCH (a:Station {{code: r.a}}), (b:Station {{code: r.b}}) "
         "CREATE (a)-[:COULD_PAIR {{month: $meta.month, turn_deg: r.turn_deg, to_az: r.to_az, km: r.km, km2: r.km2, "
         "estimate: true, fov_date: r.fov_date, aim_changed: r.aim_changed}}]->(b)")
NEAREST = ("UNWIND $nearest AS r MATCH (a:Station {code: r.a}), (b:Station {code: r.b}) "
           "CREATE (a)-[:NEAREST_ISLAND {month: $meta.month, km: r.km}]->(b)")
PREV = "MATCH (a:Station)-[s:SHARED {{month: '{month}'}}]->(b:Station) RETURN a.code AS a, b.code AS b, s.meteors AS meteors"


def batched(template, n):
    return [template.format(i=i, j=i + BATCH) for i in range(0, n, BATCH)]


def run(store, statements, params):
    with tempfile.TemporaryDirectory() as d:
        args = ["relate", "query", "--database", str(store), "--jsonl"]
        for name, value in params.items():
            f = Path(d) / f"{name}.json"
            f.write_text(json.dumps(value))
            args += ["--fetch-params", f"{name}={f}"]
        r = subprocess.run(args, input=";\n".join(statements) + ";\n", capture_output=True, text=True)
    if r.returncode != 0 or "error" in r.stdout.lower() or "error" in r.stderr.lower():
        raise SystemExit(f"relate failed on {store}:\n{r.stderr or r.stdout}")
    return r.stdout


def write_month(store, month, data, partial=False, as_of=None):
    meta = {"month": month, "partial": partial, "as_of": as_of, **data["meta"]}
    statements = [MONTH, DROP_SHARED, DROP_STATS, DROP_COULD, DROP_NEAREST, DROP_COUNTRY_STATS, COUNTRIES]
    statements += batched(KNOWN, len(data["known"]))
    statements += batched(STATIONS, len(data["stations"]))
    statements += batched(FOV, len(data["fov"]))
    statements += batched(STATS, len(data["stations"]))
    statements += batched(SHARED, len(data["pairs"]))
    statements += batched(COULD, len(data["could"]))
    statements += [NEAREST, COUNTRY_STATS]
    keys = ("countries", "known", "stations", "pairs", "fov", "could", "nearest", "country_stats")
    run(store, statements, {"meta": meta, **{k: data[k] for k in keys}})


def months_in(store):
    out = subprocess.run(["relate", "--database", str(store), "--max-rows", "0", "--jsonl", "MATCH (m:Month) RETURN m.id AS id ORDER BY id"],
                         capture_output=True, text=True, check=True).stdout
    return [json.loads(line)["id"] for line in out.splitlines() if line.startswith("{")]


def previous(month):
    y, m = int(month[:4]), int(month[4:])
    return f"{y - 1:04d}12" if m == 1 else f"{y:04d}{m - 1:02d}"


def prev_pairs(month, data, store, cache):
    prev = previous(month)
    if prev in data:
        return data[prev]["pairs"]
    if store.exists() and prev in months_in(store):
        out = subprocess.run(["relate", "--database", str(store), "--max-rows", "0", "--jsonl", PREV.format(month=prev)],
                             capture_output=True, text=True, check=True).stdout
        return [json.loads(line) for line in out.splitlines() if line.startswith("{")]
    traj = cache / prev / f"traj_summary_monthly_{prev}.txt"
    return gmn.pairs(gmn.read_trajectories(traj)) if traj.exists() else None


def enrich(month, data, store, cache, offline, now, fresh_fov):
    d = data[month]
    graph.annotate(d, prev_pairs(month, data, store, cache), d.pop("positions"), now)
    need = geometry.fov_needed(d["stations"])
    if not offline:
        gmn.fetch_fov(need, cache, fresh=fresh_fov)
    polys, dates = gmn.read_fov(need, cache)
    d["fov"] = [{"code": c, "poly": [v for pt in polys[c] for v in pt], "date": dates[c]} for c in sorted(polys)]
    d["could"] = geometry.could_pair(d["stations"], polys, dates)


def load(store, months, cache, offline, fresh_store=False, partial_as_of=None, base=None):
    data = {}
    for month in months:
        if not offline:
            gmn.fetch(month, cache, fresh=partial_as_of is not None)
        if not (cache / month / f"traj_summary_monthly_{month}.txt").exists():
            raise SystemExit(f"stopped before writing: {month}: no trajectory file at GMN")
        try:
            data[month] = gmn.month_data(month, cache)
        except gmn.LayoutError as e:
            raise SystemExit(f"stopped before writing: {e}")
    store.parent.mkdir(parents=True, exist_ok=True)
    tmp = store.with_name(store.name + ".tmp.rl")
    tmp.unlink(missing_ok=True)
    source = base or store
    if source.exists() and not fresh_store:
        shutil.copyfile(source, tmp)
    now = datetime.datetime.fromisoformat(partial_as_of).replace(tzinfo=None) if partial_as_of else None
    as_of = partial_as_of[:10] if partial_as_of else None
    for month in months:
        enrich(month, data, tmp, cache, offline, now, fresh_fov=partial_as_of is not None)
        write_month(tmp, month, data[month], partial=partial_as_of is not None, as_of=as_of)
        print(f"{month}: {len(data[month]['stations'])} stations, {len(data[month]['pairs'])} pairs")
    run(tmp, LINK, {"latest": months_in(tmp)[-1]})
    tmp.replace(store)


def release(store, tag_month, manifest):
    months = months_in(store)
    gh = os.environ.get("GH_BIN", "gh")
    tag = f"store-{tag_month}"
    with tempfile.TemporaryDirectory() as d:
        asset = Path(d) / "gmn.rl"
        shutil.copyfile(store, asset)
        notes = f"Second Witness store: GMN trajectories {months[0]}–{months[-1]} as a Relate single-file store. Data: Global Meteor Network, CC BY 4.0."
        if subprocess.run([gh, "release", "view", tag, "--repo", REPO], capture_output=True).returncode == 0:
            subprocess.run([gh, "release", "upload", tag, str(asset), "--repo", REPO, "--clobber"], check=True)
        else:
            subprocess.run([gh, "release", "create", tag, str(asset), "--repo", REPO, "--title", tag, "--notes", notes, "--latest"], check=True)
    doc = json.loads(manifest.read_text()) if manifest.exists() else {"releases": []}
    entry = {"tag": tag, "months": months, "bytes": store.stat().st_size,
             "url": f"https://github.com/{REPO}/releases/download/{tag}/gmn.rl"}
    doc["releases"] = [r for r in doc["releases"] if r["tag"] != tag] + [entry]
    doc["latest"] = tag
    manifest.parent.mkdir(parents=True, exist_ok=True)
    manifest.write_text(json.dumps(doc, indent=2) + "\n")
    print(f"released {tag}: {len(months)} months, {entry['bytes']} bytes")


def main():
    ap = argparse.ArgumentParser(description="Load GMN months into the Second Witness store")
    ap.add_argument("months", nargs="*", help="YYYYMM to add or replace")
    ap.add_argument("--store", type=Path, default=ROOT / "store" / "gmn.rl")
    ap.add_argument("--source", type=Path, default=ROOT / "research" / "raw", help="download cache")
    ap.add_argument("--offline", action="store_true", help="read only the cache")
    ap.add_argument("--fresh", action="store_true", help="start from an empty store")
    ap.add_argument("--rebuild", metavar="YYYYMM", help="rebuild the 12 months ending at YYYYMM")
    ap.add_argument("--partial", action="store_true", help="load the current month into a copy of the store")
    ap.add_argument("--as-of", help="date or UTC date-time of the partial month (default now)")
    ap.add_argument("--out", type=Path, default=ROOT / "store" / "gmn-latest.rl")
    ap.add_argument("--release", metavar="YYYYMM", help="upload the store as release store-YYYYMM")
    ap.add_argument("--manifest", type=Path, default=ROOT / "data" / "months.json")
    a = ap.parse_args()
    if a.release:
        release(a.store, a.release, a.manifest)
    elif a.partial:
        as_of = a.as_of or datetime.datetime.now(datetime.UTC).replace(tzinfo=None).isoformat(timespec="seconds")
        load(a.out, [as_of[:4] + as_of[5:7]], a.source, a.offline, partial_as_of=as_of, base=a.store)
    elif a.rebuild:
        load(a.store, gmn.window(a.rebuild), a.source, a.offline, fresh_store=True)
    elif a.months:
        load(a.store, a.months, a.source, a.offline, fresh_store=a.fresh)
    else:
        ap.error("give months, --rebuild, --partial or --release")


if __name__ == "__main__":
    main()
