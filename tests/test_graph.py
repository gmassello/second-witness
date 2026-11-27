import json
import os
import shutil
import sys
import tempfile
import unittest
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "load"))
from test_load import FIXTURE, build, cypher, write_common, write_month
import gmn

HAS_GRAPH = FIXTURE.exists() and bool(cypher(FIXTURE, "MATCH ()-[t:STATS]->() WHERE t.island IS NOT NULL RETURN t.island AS i LIMIT 1"))


def square(lat, lon, half=0.4):
    return [(lon - half, lat - half), (lon + half, lat - half), (lon + half, lat + half), (lon - half, lat + half)]


def kml(points):
    coords = " ".join(f"{lon},{lat},100000" for lon, lat in points)
    return f"<kml><Placemark><Polygon><outerBoundaryIs><LinearRing><coordinates>{coords}</coordinates></LinearRing></outerBoundaryIs></Polygon></Placemark></kml>"


def entry(lat, lon, az=90.0, date="2026-01-01T00:00:00"):
    return {date: {"lat": lat, "lon": lon, "ht": 600, "pointing": {"azim_center": az, "alt_center": 40.0}}}


def night(cam, day, n=10):
    return [cam, f"{day}_180000_000000", day, n]


class TestGraph(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.src = self.tmp / "raw"
        self.store = self.tmp / "gmn.rl"

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def setup_month(self, coords, month, trajs, index, polygons=None):
        write_common(self.src, coords)
        write_month(self.src, month, trajs, index)
        for code, pts in (polygons or {}).items():
            (self.src / "kml").mkdir(parents=True, exist_ok=True)
            (self.src / "kml" / f"{code}-100km.kml").write_text(kml(pts))

    def load(self, *args):
        r = build(*args, "--source", str(self.src), "--store", str(self.store))
        self.assertEqual(r.returncode, 0, r.stderr)

    def stats(self, code, month="202610"):
        rows = cypher(self.store, f"MATCH (s:Station {{code:'{code}'}})-[t:STATS {{month:'{month}'}}]->() RETURN t.status AS status, t.change AS change, t.island AS island, t.cut_off AS cut_off, t.partners AS partners, t.upload AS upload, t.nights AS nights, t.last_upload AS last, t.lost AS lost, s.site AS site, s.fov100 AS fov")
        return rows[0] if rows else None

    def could(self, code, month="202610"):
        return cypher(self.store, f"MATCH (:Station {{code:'{code}'}})-[c:COULD_PAIR {{month:'{month}'}}]->(b:Station) RETURN b.code AS b, c.km2 AS km2, c.turn_deg AS turn, c.estimate AS estimate, c.aim_changed AS aim_changed, c.fov_date AS fov_date")

    def lonely_and_neighbour(self, neighbour_lon=-2.5, lonely_coords=None, lonely_poly=None, extra_coords=None):
        coords = {"ES0001": lonely_coords or entry(40.0, -3.0), "ES0002": entry(40.0, neighbour_lon, az=90.0),
                  "ES0003": entry(43.0, 2.0), "ES0004": entry(43.5, 2.5), **(extra_coords or {})}
        self.setup_month(coords, "202610", [("20261001000000_a", ["ES0002", "ES0003"]), ("20261001000001_b", ["ES0003", "ES0004"])],
                         [("ES", "20261001", [night("ES0001", "20261001"), night("ES0002", "20261001")])],
                         {"ES0001": lonely_poly or square(41.0, -3.0), "ES0002": square(40.0, neighbour_lon + 0.7)})
        self.load("202610")

    @unittest.skipUnless(HAS_GRAPH, "needs the fixture built by U2")
    def test_ae8_us004l_cuts_off_86_that_still_share_meteors(self):
        us = cypher(FIXTURE, "MATCH (:Station {code:'US004L'})-[t:STATS {month:'202610'}]->() RETURN t.cut_off AS c, t.island AS i")[0]
        self.assertEqual(us["c"], 86)
        edges = cypher(FIXTURE, f"MATCH (a:Station)-[t:STATS {{month:'202610', island:'{us['i']}'}}]->(), (a)-[:SHARED {{month:'202610'}}]->(b:Station) RETURN a.code AS a, b.code AS b")
        adj = defaultdict(set)
        for e in edges:
            if "US004L" not in (e["a"], e["b"]):
                adj[e["a"]].add(e["b"])
                adj[e["b"]].add(e["a"])
        seen, sizes = set(), []
        for s in adj:
            if s not in seen:
                stack, n = [s], 0
                seen.add(s)
                while stack:
                    u = stack.pop()
                    n += 1
                    for v in adj[u] - seen:
                        seen.add(v)
                        stack.append(v)
                sizes.append(n)
        sizes.sort(reverse=True)
        self.assertEqual(sum(sizes[1:]), 86)
        self.assertTrue(all(n >= 2 for n in sizes), sizes)

    @unittest.skipUnless(HAS_GRAPH, "needs the fixture built by U2")
    def test_ae10_46_stopped_and_nz002c_lost_408(self):
        rows = cypher(FIXTURE, "MATCH (s:Station)-[t:STATS {month:'202610'}]->() WHERE t.change IN ['stopped', 'possibly_moved'] RETURN s.code AS code")
        self.assertEqual(len(rows), 46)
        nz = cypher(FIXTURE, "MATCH (:Station {code:'NZ002C'})-[t:STATS {month:'202610'}]->() RETURN t.lost AS lost")[0]
        self.assertEqual(nz["lost"], 408)

    @unittest.skipUnless(HAS_GRAPH, "needs the fixture built by U2")
    def test_ae11_spain_and_portugal_island_470_km_away(self):
        island = cypher(FIXTURE, "MATCH (:Station {code:'ES0019'})-[t:STATS {month:'202610'}]->() RETURN t.island AS i")[0]["i"]
        members = cypher(FIXTURE, f"MATCH (s:Station)-[:STATS {{month:'202610', island:'{island}'}}]->() RETURN s.country AS c")
        self.assertEqual(len(members), 17)
        self.assertEqual({m["c"] for m in members}, {"ES", "PT"})
        de = cypher(FIXTURE, "MATCH (:Station {code:'DE0001'})-[t:STATS {month:'202610'}]->() RETURN t.island AS i")[0]["i"]
        self.assertNotEqual(de, island)
        near = cypher(FIXTURE, f"MATCH (a:Station)-[n:NEAREST_ISLAND {{month:'202610'}}]-(b:Station), (a)-[:STATS {{month:'202610', island:'{island}'}}]->() RETURN n.km AS km")
        self.assertTrue(near and 450 <= min(n["km"] for n in near) <= 490, near)

    @unittest.skipUnless(HAS_GRAPH, "needs the fixture built by U2")
    def test_ae14_es000c_could_pair_marked_estimate(self):
        rows = cypher(FIXTURE, "MATCH (a:Station {code:'ES000C'})-[c:COULD_PAIR {month:'202610'}]->(b:Station), (a)-[t:STATS {month:'202610'}]->(), (b)-[u:STATS {month:'202610'}]->() RETURN c.estimate AS e, c.fov_date AS d, a.fov100_date AS da, b.fov100_date AS db, t.az AS az, t.alt AS alt, u.az AS baz")
        self.assertGreaterEqual(len(rows), 1)
        for r in rows:
            self.assertTrue(r["e"])
            self.assertEqual(r["d"], min(r["da"], r["db"]))
            self.assertIsNotNone(r["az"])
            self.assertIsNotNone(r["baz"])

    def test_same_site_cameras_are_partners_and_share_a_site(self):
        coords = {"ES0001": entry(40.0, -3.0), "ES0002": entry(40.0, -3.0), "PT0001": entry(39.0, -8.0)}
        self.setup_month(coords, "202610", [("20261001000000_a", ["ES0001", "ES0002"])], [])
        self.load("202610")
        a, b = self.stats("ES0001"), self.stats("ES0002")
        self.assertEqual((a["partners"], a["status"], b["status"]), (1, "paired", "paired"))
        self.assertEqual(a["site"], b["site"])
        self.assertEqual(a["site"], "40.00,-3.00")

    def test_stopped_code_with_a_new_code_at_its_site_is_possibly_moved(self):
        coords = {"ES0001": entry(40.0, -3.0), "ES0002": entry(41.0, -3.0), "ES0003": entry(42.0, -3.0), "ES0009": entry(41.0, -3.0)}
        write_common(self.src, coords)
        write_month(self.src, "202609", [("20260901000000_a", ["ES0001", "ES0002"]), ("20260901000001_b", ["ES0001", "ES0003"])])
        write_month(self.src, "202610", [("20261001000000_a", ["ES0001", "ES0009"])])
        self.load("202609", "202610")
        self.assertEqual(self.stats("ES0002")["change"], "possibly_moved")
        self.assertEqual(self.stats("ES0003")["change"], "stopped")
        self.assertEqual(self.stats("ES0009")["change"], "new")
        self.assertEqual(self.stats("ES0001")["lost"], 2)

    def test_previous_month_read_from_the_store(self):
        coords = {"ES0001": entry(40.0, -3.0), "ES0002": entry(41.0, -3.0), "ES0003": entry(42.0, -3.0)}
        write_common(self.src, coords)
        write_month(self.src, "202609", [("20260901000000_a", ["ES0001", "ES0002"])])
        write_month(self.src, "202610", [("20261001000000_a", ["ES0001", "ES0003"])])
        self.load("202609")
        shutil.rmtree(self.src / "202609")
        self.load("202610")
        self.assertEqual(self.stats("ES0002")["change"], "stopped")

    def test_previous_month_from_the_store_is_not_capped_at_100_rows(self):
        many = [f"ES{i:04d}" for i in range(2, 152)]
        write_common(self.src, {})
        write_month(self.src, "202609", [(f"2026090100{i:04d}_a", ["ES0001", c]) for i, c in enumerate(many)])
        write_month(self.src, "202610", [("20261001000000_a", ["ES0001", "ES0002"])])
        self.load("202609")
        shutil.rmtree(self.src / "202609")
        self.load("202610")
        rows = cypher(self.store, "MATCH (s:Station)-[t:STATS {month:'202610', change:'stopped'}]->() RETURN s.code AS c")
        self.assertEqual(len(rows), 149)

    def test_station_with_no_pointing_has_no_could_pair(self):
        self.lonely_and_neighbour(lonely_coords={"2026-01-01T00:00:00": {"lat": 40.0, "lon": -3.0, "ht": 600, "pointing": None}})
        self.assertEqual(self.stats("ES0001")["status"], "running_no_partner")
        self.assertEqual(self.could("ES0001"), [])

    def test_lonely_camera_could_pair_by_turning(self):
        self.lonely_and_neighbour()
        rows = self.could("ES0001")
        self.assertEqual([r["b"] for r in rows], ["ES0002"])
        self.assertTrue(rows[0]["estimate"])
        self.assertGreater(rows[0]["km2"], 0)
        self.assertAlmostEqual(rows[0]["turn"], 90, delta=15)
        self.assertFalse(rows[0]["aim_changed"])

    def test_station_without_kml_has_no_could_pair_and_null_fov(self):
        self.lonely_and_neighbour()
        (self.src / "kml" / "ES0002-100km.kml").unlink()
        self.load("202610")
        self.assertEqual(self.could("ES0001"), [])
        self.assertIsNone(self.stats("ES0004")["fov"])

    def test_no_could_pair_under_5_or_over_600_km(self):
        for lon in (-2.965, 5.5):
            with self.subTest(lon=lon):
                shutil.rmtree(self.src, ignore_errors=True)
                self.store.unlink(missing_ok=True)
                self.lonely_and_neighbour(neighbour_lon=lon)
                self.assertEqual(self.could("ES0001"), [])

    def test_self_crossing_ring_still_scored(self):
        bow = [(-3.4, 40.6), (-2.6, 41.4), (-2.6, 40.6), (-3.4, 41.4)]
        self.lonely_and_neighbour(lonely_poly=bow)
        self.assertEqual([r["b"] for r in self.could("ES0001")], ["ES0002"])

    def test_pointing_newer_than_the_month_marks_aim_changed(self):
        newer = {**entry(40.0, -3.0), **entry(40.0, -3.0, az=0.0, date="2026-11-10T00:00:00")}
        self.lonely_and_neighbour(lonely_coords=newer)
        self.assertTrue(self.could("ES0001")[0]["aim_changed"])

    def test_upload_state_in_the_current_month(self):
        write_common(self.src, {})
        index = [("ES", "20261120", [night("ES0001", "20261123", 5), night("ES0002", "20261122", 5),
                                     night("ES0003", "20261120", 5), night("ES0004", "20261116", 5)])]
        write_month(self.src, "202611", [], index)
        latest = self.tmp / "latest.rl"
        r = build("--partial", "--as-of", "2026-11-25T10:00:00", "--source", str(self.src), "--store", str(self.store), "--out", str(latest))
        self.assertEqual(r.returncode, 0, r.stderr)
        self.store = latest
        got = {c: self.stats(c, "202611")["upload"] for c in ("ES0001", "ES0002", "ES0003", "ES0004")}
        self.assertEqual(got, {"ES0001": "running", "ES0002": "late", "ES0003": "dark", "ES0004": "silent"})
        self.assertEqual(cypher(latest, "MATCH (m:Month {id:'202611'}) RETURN m.as_of AS a")[0]["a"], "2026-11-25")

    def test_bulk_reupload_counts_each_night_on_its_date(self):
        write_common(self.src, {})
        rows = [night("ES0001", f"202610{d:02d}", 3) for d in range(1, 11)]
        write_month(self.src, "202610", [], [("ES", "20261020", rows)])
        self.load("202610")
        s = self.stats("ES0001")
        self.assertEqual(s["nights"], 10)
        self.assertEqual(s["last"], "2026-10-10T18:00:00")

    def test_closed_month_has_no_upload_state(self):
        self.lonely_and_neighbour()
        self.assertIsNone(self.stats("ES0001")["upload"])


class TestFovFetch(unittest.TestCase):
    def setUp(self):
        self.cache = Path(tempfile.mkdtemp())
        (self.cache / "kml").mkdir()
        self.codes = [f"ES000{i}" for i in range(6)]
        for c in self.codes:
            f = gmn.kml_path(self.cache, c)
            f.write_text(kml(square(40, -3)))
            os.utime(f, (1_760_000_000, 1_760_000_000))
        self.before = gmn.read_fov(self.codes, self.cache)
        self.get = gmn.get

    def tearDown(self):
        gmn.get = self.get
        shutil.rmtree(self.cache)

    def test_timeout_keeps_previous_polygons_and_dates(self):
        def down(*a, **k):
            raise SystemExit("failed after 3 attempts")
        gmn.get = down
        self.assertEqual(gmn.fetch_fov(self.codes, self.cache, fresh=True), 0)
        self.assertEqual(gmn.read_fov(self.codes, self.cache), self.before)

    def test_round_with_fewer_than_half_keeps_previous_polygons(self):
        gmn.get = lambda url, dest, force=False: url.endswith("ES0000-100km.kml")
        self.assertEqual(gmn.fetch_fov(self.codes, self.cache, fresh=True), 1)
        self.assertEqual(gmn.read_fov(self.codes, self.cache), self.before)


if __name__ == "__main__":
    unittest.main()
