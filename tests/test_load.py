import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BUILD = ROOT / "load" / "build.py"
FIXTURE = ROOT / "store" / "gmn-202610.rl"
RAW_OCT = ROOT / "research" / "raw" / "202610" / "traj_summary_monthly_202610.txt"


def cypher(store, query):
    with tempfile.TemporaryDirectory() as tmp:
        copy = Path(tmp) / Path(store).name
        shutil.copy(store, copy)
        out = subprocess.run(["relate", "--database", str(copy), "--jsonl", query], capture_output=True, text=True, check=True)
    return [json.loads(line) for line in out.stdout.splitlines() if line.startswith("{")]


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def traj_line(tid, stations, columns=86):
    fields = [" x"] * columns
    fields[0] = tid
    fields[-1] = " " + ",".join(stations)
    return ";".join(fields) + "\n\r"


def write_month(src, month, trajs, index=None, columns=86):
    d = src / month
    (d / "index").mkdir(parents=True, exist_ok=True)
    lines = ["# header\n", "# units\n"] + [traj_line(t, s, columns) for t, s in trajs]
    (d / f"traj_summary_monthly_{month}.txt").write_text("".join(lines))
    for cc, day, rows in index or []:
        (d / "index" / cc).mkdir(parents=True, exist_ok=True)
        (d / "index" / cc / f"{cc}_{day}.json").write_text(json.dumps(rows))


def write_common(src, coords):
    src.mkdir(parents=True, exist_ok=True)
    (src / "GMN_station_coordinates_public.json").write_text(json.dumps(coords))
    (src / "gmncountries2.json").write_text(json.dumps([{"name": "Spain", "code": "ES"}, {"name": "Portugal", "code": "PT"}]))


def build(*args, env=None):
    return subprocess.run([sys.executable, str(BUILD), *args, "--offline"], capture_output=True, text=True, env=env)


COORDS = {
    "ES0001": {"2026-01-01T00:00:00": {"lat": 40.0, "lon": -3.0, "ht": 600, "pointing": {"azim_center": 90.0, "alt_center": 40.0}}},
    "ES0002": {"2026-01-01T00:00:00": {"lat": 41.0, "lon": -3.5, "ht": 600, "pointing": {"azim_center": 180.0, "alt_center": 35.0}}},
    "PT0001": {"2026-01-01T00:00:00": {"lat": 39.0, "lon": -8.0, "ht": 100, "pointing": {"azim_center": 45.0, "alt_center": 30.0}}},
}


class TestLoad(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.src = self.tmp / "raw"
        self.store = self.tmp / "gmn.rl"
        write_common(self.src, COORDS)
        write_month(self.src, "202609", [
            ("20260901000000_a", ["ES0001", "ES0002"]),
        ], [("ES", "20260901", [["ES0001", "20260901_180000_000000", "20260901", 5]])])
        write_month(self.src, "202610", [
            ("20261001000000_a", ["ES0001", "ES0002"]),
            ("20261001000001_b", ["ES0001", "ES0002", "PT0001"]),
            ("20261002000000_c", ["ES0001", "ES0001", "ES0002"]),
            ("20261003000000_d", ["ES0002", "ES001", "XX9999"]),
        ], [
            ("ES", "20261001", [["ES0001", "20261001_180000_000000", "20261001", 7], ["ES0001", "20261001_190000_000000", "20261001", 9]]),
            ("ES", "20261002", [["ES0001", "20261002_180000_000000", "20261002", 3], ["ES0003", "20261002_180000_000000", "20261002", 12]]),
        ])

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def load(self, *months, store=None):
        r = build(*months, "--source", str(self.src), "--store", str(store or self.store))
        self.assertEqual(r.returncode, 0, r.stderr)
        return r

    def shared(self, a, b, month="202610", store=None):
        rows = cypher(store or self.store, f"MATCH (x:Station {{code:'{a}'}})-[s:SHARED {{month:'{month}'}}]-(y:Station {{code:'{b}'}}) RETURN s.meteors AS n, s.two_station AS two, s.sample_ids AS ids")
        return rows[0] if rows else None

    def stats(self, code, month="202610", store=None):
        rows = cypher(store or self.store, f"MATCH (s:Station {{code:'{code}'}})-[t:STATS]->(:Month {{id:'{month}'}}) RETURN t.nights AS nights, t.detections AS detections, t.orbits AS orbits, t.two_station_orbits AS two, t.partners AS partners, t.az AS az, t.alt AS alt, t.last_upload AS last_upload")
        return rows[0] if rows else None

    def test_weight_equals_trajectory_count(self):
        self.load("202610")
        self.assertEqual(self.shared("ES0001", "ES0002")["n"], 3)
        self.assertEqual(self.shared("ES0001", "ES0002")["two"], 2)
        self.assertEqual(self.shared("ES0002", "PT0001")["n"], 1)
        self.assertLessEqual(len(self.shared("ES0001", "ES0002")["ids"]), 3)

    @unittest.skipUnless(FIXTURE.exists() and RAW_OCT.exists(), "needs the committed fixture and research/raw/202610")
    def test_ae1_fixture_matches_raw_october(self):
        count = 0
        with open(RAW_OCT, encoding="utf-8") as f:
            for line in f:
                if line.startswith("#") or not line.strip():
                    continue
                st = {s.strip() for s in line.split(";")[85].split(",")}
                count += {"ES001G", "ES0013"} <= st
        self.assertEqual(self.shared("ES001G", "ES0013", store=FIXTURE)["n"], count)
        self.assertEqual(count, 144)

    @unittest.skipUnless(FIXTURE.exists(), "needs the committed fixture")
    def test_ae5_fixture_answers_offline(self):
        hu = self.stats("HU000B", store=FIXTURE)
        self.assertEqual(hu["two"], 899)
        partners = cypher(FIXTURE, "MATCH (:Station {code:'HU000B'})-[s:SHARED {month:'202610'}]-(p:Station) RETURN p.code AS code")
        self.assertGreater(len(partners), 0)
        es = self.stats("ES000C", store=FIXTURE)
        self.assertEqual((es["nights"], es["detections"], es["partners"]), (31, 1797, 0))

    def test_reload_replaces_only_that_month(self):
        self.load("202609", "202610")
        before = self.shared("ES0001", "ES0002", "202609")
        self.load("202610")
        self.assertEqual(self.shared("ES0001", "ES0002", "202609"), before)
        self.assertEqual(self.shared("ES0001", "ES0002")["n"], 3)
        months = cypher(self.store, "MATCH (m:Month) RETURN m.id AS id ORDER BY id")
        self.assertEqual([m["id"] for m in months], ["202609", "202610"])

    def test_partial_marks_month_and_leaves_source(self):
        self.load("202609")
        before = digest(self.store)
        latest = self.tmp / "gmn-latest.rl"
        write_month(self.src, "202611", [("20261101000000_a", ["ES0001", "PT0001"])])
        r = build("--partial", "--as-of", "2026-11-25", "--source", str(self.src), "--store", str(self.store), "--out", str(latest))
        self.assertEqual(r.returncode, 0, r.stderr)
        m = cypher(latest, "MATCH (m:Month {id:'202611'}) RETURN m.partial AS p, m.as_of AS a")[0]
        self.assertEqual((m["p"], m["a"]), (True, "2026-11-25"))
        self.assertEqual(self.shared("ES0001", "PT0001", "202611", store=latest)["n"], 1)
        self.assertIsNotNone(self.shared("ES0001", "ES0002", "202609", store=latest))
        self.assertEqual(digest(self.store), before)

    def test_station_without_coordinates_kept_with_null_position(self):
        self.load("202610")
        row = cypher(self.store, "MATCH (s:Station {code:'XX9999'}) RETURN s.lat AS lat, s.lon AS lon, s.country AS country")[0]
        self.assertEqual((row["lat"], row["lon"], row["country"]), (None, None, "XX"))

    def test_repeated_station_counted_once_and_codes_exact(self):
        self.load("202610")
        self.assertEqual(self.stats("ES0001")["orbits"], 3)
        self.assertEqual(self.stats("ES001")["orbits"], 1)
        self.assertIsNone(self.shared("ES0001", "ES001"))

    def test_stats_from_index_and_pointing(self):
        self.load("202610")
        s = self.stats("ES0001")
        self.assertEqual((s["nights"], s["detections"], s["partners"]), (2, 12, 2))
        self.assertEqual((s["az"], s["alt"]), (90.0, 40.0))
        self.assertEqual(s["last_upload"], "2026-10-02T18:00:00")
        lone = self.stats("ES0003")
        self.assertEqual((lone["orbits"], lone["partners"], lone["detections"]), (0, 0, 12))

    def test_wrong_column_count_exits_and_leaves_store(self):
        self.load("202609")
        before = digest(self.store)
        write_month(self.src, "202610", [("20261001000000_a", ["ES0001", "ES0002"])], columns=85)
        r = build("202610", "--source", str(self.src), "--store", str(self.store))
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("85", r.stderr)
        self.assertEqual(digest(self.store), before)

    def test_release_lists_month_in_manifest(self):
        self.load("202609", "202610")
        fake = self.tmp / "gh"
        log = self.tmp / "gh.log"
        fake.write_text(f"#!/bin/sh\necho \"$@\" >> {log}\n")
        fake.chmod(0o755)
        manifest = self.tmp / "months.json"
        env = dict(os.environ, GH_BIN=str(fake))
        r = build("--release", "202610", "--store", str(self.store), "--manifest", str(manifest), env=env)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("release create store-202610", log.read_text())
        entry = json.loads(manifest.read_text())["releases"][0]
        self.assertEqual(entry["tag"], "store-202610")
        self.assertEqual(entry["months"], ["202609", "202610"])
        self.assertEqual(entry["bytes"], self.store.stat().st_size)
        self.assertTrue(entry["url"].endswith("/releases/download/store-202610/gmn.rl"))

    def test_repo_tracks_no_store_but_the_fixture(self):
        tracked = subprocess.run(["git", "-C", str(ROOT), "ls-files", "*.rl"], capture_output=True, text=True).stdout.split()
        self.assertTrue(set(tracked) <= {"store/gmn-202610.rl"}, tracked)


if __name__ == "__main__":
    unittest.main()
