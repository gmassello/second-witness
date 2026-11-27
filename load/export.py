import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LIMIT = 50_000_000
PAIRS = 2

NODES = {
    "months": "MATCH (m:Month) RETURN properties(m) AS p ORDER BY m.id",
    "countries": "MATCH (c:Country) RETURN properties(c) AS p ORDER BY c.code",
    "stations": "MATCH (s:Station) RETURN properties(s) AS p ORDER BY s.code",
}
STATS = {
    "station_stats": "MATCH (s:Station)-[t:STATS]->(m:Month) RETURN s.code AS code, m.id AS month, properties(t) AS p ORDER BY month, code",
    "country_stats": "MATCH (c:Country)-[t:STATS]->(m:Month) RETURN c.code AS code, m.id AS month, properties(t) AS p ORDER BY month, code",
}
EDGES = {"shared": "SHARED", "could": "COULD_PAIR", "nearest": "NEAREST_ISLAND"}
EDGE = "MATCH (a:Station)-[e:{rel} {{month: $month}}]->(b:Station) RETURN a.code AS a, b.code AS b, properties(e) AS p ORDER BY a, b"
DROPPED = ("fov100",)


def read(store, query, **params):
    args = ["relate", "--database", str(store), "--max-rows", "0", "--jsonl"]
    for k, v in params.items():
        args += ["--param", f"{k}={json.dumps(v)}"]
    r = subprocess.run(args + [query], capture_output=True, text=True)
    if r.returncode != 0 or '"error"' in r.stdout:
        raise SystemExit(f"relate failed on {store}: {(r.stdout + r.stderr).strip()[:300]}")
    return [json.loads(line) for line in r.stdout.splitlines() if line.startswith("{") and "rowCap" not in line]


def export(store, out):
    with tempfile.TemporaryDirectory() as d:
        copy = Path(d) / "q.rl"
        shutil.copyfile(store, copy)
        doc = {k: [r["p"] for r in read(copy, q)] for k, q in NODES.items()}
        for s in doc["stations"]:
            for k in DROPPED:
                s.pop(k, None)
        doc.update({k: read(copy, q) for k, q in STATS.items()})
        months = [m["id"] for m in doc["months"]]
        doc["pairs"] = months[-PAIRS:]
        out.mkdir(parents=True, exist_ok=True)
        for old in out.glob("pairs-*.json"):
            old.unlink()
        for month in doc["pairs"]:
            pairs = {"month": month, **{k: read(copy, EDGE.format(rel=rel), month=month) for k, rel in EDGES.items()}}
            (out / f"pairs-{month}.json").write_text(json.dumps(pairs, separators=(",", ":")))
        (out / "stats.json").write_text(json.dumps(doc, separators=(",", ":")))
    for f in sorted(out.glob("*.json")):
        print(f"{f.name}: {f.stat().st_size} bytes")


def check_size(paths, limit=LIMIT):
    total = sum(Path(p).stat().st_size for p in paths if Path(p).is_file())
    print(f"{len(paths)} files, {total / 1e6:.1f} MB (limit {limit / 1e6:.0f} MB)")
    return total <= limit


def main():
    ap = argparse.ArgumentParser(description="Export the page data from the store")
    ap.add_argument("--store", type=Path, default=ROOT / "store" / "gmn.rl")
    ap.add_argument("--out", type=Path, default=ROOT / "site" / "data")
    ap.add_argument("--check-size", nargs="*", metavar="FILE", help="sum these files, or the tracked repo, against 50 MB")
    a = ap.parse_args()
    if a.check_size is not None:
        paths = a.check_size or subprocess.run(["git", "ls-files"], capture_output=True, text=True, check=True, cwd=ROOT).stdout.split()
        if not check_size([p if Path(p).is_absolute() else ROOT / p for p in paths]):
            sys.exit(1)
        return
    export(a.store, a.out)


if __name__ == "__main__":
    main()
