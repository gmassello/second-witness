import json
import re
import shutil
import statistics
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_load import FIXTURE, RAW_OCT, cypher

ROOT = Path(__file__).resolve().parent.parent
QUERIES = ROOT / "queries"
NAMES = ["lonely_cameras", "take_down", "country", "changes", "could_turn", "talk_to", "chain",
         "station_history", "country_history", "search"]
MONTH = "202610"
SUFFIX = re.compile(r"_\d+$")


def run_file(path, store=FIXTURE, **params):
    with tempfile.TemporaryDirectory() as tmp:
        copy = Path(tmp) / "q.rl"
        shutil.copy(store, copy)
        args = ["relate", "--database", str(copy), "--max-rows", "0", "--jsonl"]
        for k, v in params.items():
            args += ["--param", f"{k}={json.dumps(v)}"]
        r = subprocess.run(args + [Path(path).read_text()], capture_output=True, text=True)
    if r.returncode != 0 or '"error"' in r.stdout:
        raise AssertionError(f"{Path(path).name}: {(r.stdout + r.stderr).strip().splitlines()[0]}")
    return [json.loads(line) for line in r.stdout.splitlines() if line.startswith("{")]


def q(name, **params):
    return run_file(QUERIES / f"{name}.cypher", **params)


def raw_rows():
    with open(RAW_OCT, encoding="utf-8") as f:
        for line in f:
            if line.startswith("#") or not line.strip():
                continue
            c = line.split(";")
            st = {SUFFIX.sub("", s.strip()) for s in c[85].split(",") if s.strip()}
            yield c, st


@unittest.skipUnless(FIXTURE.exists(), "needs the committed fixture")
class TestQueries(unittest.TestCase):
    def test_every_query_is_one_file(self):
        self.assertEqual(sorted(p.stem for p in QUERIES.glob("*.cypher")), sorted(NAMES))

    def single_partner(self):
        rows = cypher(FIXTURE, "MATCH (p:Station)-[t:STATS {month:'202610', partners: 1}]->(), (p)-[:SHARED {month:'202610'}]-(x:Station) RETURN p.code AS lone, x.code AS hub ORDER BY lone LIMIT 1")
        return rows[0]["lone"], rows[0]["hub"]

    def test_ae2_take_down_lists_who_loses_its_only_partner(self):
        lone, hub = self.single_partner()
        rows = q("take_down", station=hub, month=MONTH)
        self.assertIn((lone, "loses_only_partner"), {(r["partner"], r["effect"]) for r in rows})
        for r in rows:
            if r["effect"] == "loses_only_partner":
                self.assertEqual([p["partner"] for p in q("take_down", station=r["partner"], month=MONTH)], [hub])

    def test_ae3_hu000b_take_down_loses_899_with_proof(self):
        rows = q("take_down", station="HU000B", month=MONTH)
        self.assertEqual(rows[0]["orbits_lost"], 899)
        affected = [r for r in rows if r["two_station"] > 0]
        self.assertEqual(sum(r["two_station"] for r in affected), 899)
        for r in affected:
            self.assertGreaterEqual(len(r["sample_ids"]), 1)
            self.assertEqual(r["link"], f"https://tammojan.github.io/meteormap/?data=2026-10&stations=HU000B;{r['partner']}")
            self.assertIn("CC BY 4.0", r["credit"])

    @unittest.skipUnless(RAW_OCT.exists(), "needs research/raw/202610")
    def test_ae3_orbits_lost_equals_raw_two_station_count(self):
        n = sum(1 for _, st in raw_rows() if len(st) == 2 and "HU000B" in st)
        self.assertEqual(q("take_down", station="HU000B", month=MONTH)[0]["orbits_lost"], n)

    def test_ae4_search_br_lists_brazilian_stations(self):
        rows = q("search", text="BR")
        stations = [r["code"] for r in rows if r["kind"] == "station"]
        self.assertGreater(len(stations), 5)
        self.assertTrue(all(c.startswith("BR") for c in stations), stations[:5])
        self.assertIn("BR", [r["code"] for r in rows if r["kind"] == "country"])

    def test_search_by_country_name(self):
        rows = q("search", text="spa")
        self.assertIn({"kind": "country", "code": "ES"}, [{"kind": r["kind"], "code": r["code"]} for r in rows])

    def test_ae7_status_from_the_index_without_a_cause(self):
        self.assertEqual(q("take_down", station="ES000C", month=MONTH)[0]["status"], "running_no_partner")
        zero = q("lonely_cameras", country=None, month=MONTH)
        self.assertNotIn("uploaded_zero", {r["status"] for r in zero})
        absent = cypher(FIXTURE, "MATCH (s:Station) OPTIONAL MATCH (s)-[t:STATS {month:'202610'}]->() WITH s, t WHERE t IS NULL RETURN s.code AS code ORDER BY code LIMIT 1")
        self.assertTrue(absent, "known stations without data are loaded")
        known = q("take_down", station=absent[0]["code"], month=MONTH)
        self.assertEqual([r["status"] for r in known], ["no_upload"])
        for r in q("take_down", station="ES000C", month=MONTH):
            self.assertNotIn("cause", r)

    @unittest.skipUnless(RAW_OCT.exists(), "needs research/raw/202610")
    def test_ae9_spain_two_station_share_equals_the_file(self):
        total = two = 0
        for _, st in raw_rows():
            if any(s.startswith("ES") for s in st):
                total += 1
                two += len(st) == 2
        es = q("country", country="ES", month=MONTH)[0]
        self.assertEqual((es["orbits"], es["two_station_orbits"]), (total, two))
        self.assertAlmostEqual(es["two_station_share"], two / total, places=4)

    def test_country_neighbours_and_islands(self):
        es = q("country", country="ES", month=MONTH)[0]
        self.assertIn("PT", es["neighbours"])
        self.assertGreaterEqual(len(es["islands"]), 1)

    @unittest.skipUnless(RAW_OCT.exists(), "needs research/raw/202610")
    def test_ae12_third_witness_uncertainty_is_the_three_station_median(self):
        sig = []
        for c, st in raw_rows():
            try:
                v = float(c[16])
            except ValueError:
                continue
            if len(st) == 3 and v == v:
                sig.append(v)
        rows = q("take_down", station="HU000B", month=MONTH)
        self.assertGreater(rows[0]["third_witness_orbits"], 0)
        self.assertAlmostEqual(rows[0]["sigma3_median"], statistics.median(sig), places=6)

    def test_ae13_lonely_cameras_lists_es000c(self):
        rows = q("lonely_cameras", country=None, month=MONTH)
        es = next(r for r in rows if r["station"] == "ES000C")
        self.assertEqual((es["nights"], es["detections"]), (31, 1797))
        self.assertEqual(len(rows), 115)
        self.assertEqual(q("lonely_cameras", country="ES", month=MONTH)[0]["country"], "ES")

    def test_ae16_the_readme_numbers(self):
        self.assertEqual(q("take_down", station="HU000B", month=MONTH)[0]["orbits_lost"], 899)
        self.assertEqual(q("take_down", station="US004L", month=MONTH)[0]["cut_off"], 86)
        stopped = [r for r in q("changes", month=MONTH) if r["change"] in ("stopped", "possibly_moved")]
        self.assertEqual(len(stopped), 46)
        self.assertEqual(next(r for r in q("changes", month=MONTH) if r["station"] == "NZ002C")["lost"], 408)

    def test_ae20_chain_across_islands_names_both(self):
        r = q("chain", station="ES0019", other="DE0001")[0]
        self.assertEqual(r["reason"], "different_islands")
        self.assertTrue(r["island"] and r["other_island"] and r["island"] != r["other_island"])
        self.assertIsNone(r["path"])

    def test_chain_within_an_island(self):
        r = q("chain", station="DE0001", other="HU000B")[0]
        self.assertIsNone(r["reason"])
        self.assertEqual((r["path"][0], r["path"][-1]), ("DE0001", "HU000B"))
        self.assertEqual(len(r["meteors"]), len(r["path"]) - 1)
        self.assertEqual(r["month"], MONTH)

    def test_could_turn_es000c(self):
        rows = q("could_turn", station="ES000C", month=MONTH)
        self.assertGreaterEqual(len(rows), 1)
        self.assertTrue(all(r["estimate"] and r["az"] is not None and r["other_az"] is not None for r in rows))

    def test_talk_to_carries_reasons(self):
        self.assertIn("could_pair", {r["reason"] for r in q("talk_to", station="ES000C", month=MONTH)})
        lone, hub = self.single_partner()
        reasons = q("talk_to", station=lone, month=MONTH)
        self.assertIn((hub, "only_partner"), {(r["other"], r["reason"]) for r in reasons})

    def test_station_and_country_history(self):
        h = q("station_history", station="HU000B")
        self.assertEqual([r["month"] for r in h], sorted(r["month"] for r in h))
        self.assertEqual(h[-1]["orbits"], q("take_down", station="HU000B", month=MONTH)[0]["orbits"])
        c = q("country_history", country="ES")
        self.assertEqual(c[-1]["two_station_share"], q("country", country="ES", month=MONTH)[0]["two_station_share"])

    def test_unknown_station_gives_empty_rows(self):
        for name in ("take_down", "could_turn", "talk_to", "station_history"):
            self.assertEqual(q(name, station="ZZ9999", month=MONTH), [], name)

    def test_syntax_error_names_the_file_and_relate_message(self):
        with tempfile.TemporaryDirectory() as tmp:
            bad = Path(tmp) / "broken.cypher"
            bad.write_text("MATCH (s:Station RETURN s")
            with self.assertRaises(AssertionError) as e:
                run_file(bad)
        self.assertIn("broken.cypher", str(e.exception))
        self.assertIn("syntax", str(e.exception).lower())


if __name__ == "__main__":
    unittest.main()
