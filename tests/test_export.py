import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "load"))
from test_load import FIXTURE, build, write_common, write_month
from test_queries import QUERIES, run_file
import gmn

ROOT = Path(__file__).resolve().parent.parent
EXPORT = ROOT / "load" / "export.py"
CYPHER = ROOT / "site" / "cypher"
COORDS = ROOT / "research" / "raw" / "GMN_station_coordinates_public.json"


def export(store, out, *args):
    return subprocess.run([sys.executable, str(EXPORT), "--store", str(store), "--out", str(out), *args], capture_output=True, text=True)


def rebuild(data_dir, query, **params):
    stats = data_dir / "stats.json"
    doc = json.loads(stats.read_text())
    statements = (CYPHER / "stats.cypher").read_text()
    args = ["relate", "query", "--database", ":memory:", "--max-rows", "0", "--jsonl", "--fetch-params", f"stats={stats}"]
    for i, month in enumerate(doc["pairs"]):
        args += ["--fetch-params", f"pairs{i}={data_dir / f'pairs-{month}.json'}"]
        statements += (CYPHER / "pairs.cypher").read_text().replace("$pairs", f"$pairs{i}")
    args += ["--param", f"latest={json.dumps(doc['pairs'][-1])}"]
    statements += (CYPHER / "link.cypher").read_text()
    for k, v in params.items():
        args += ["--param", f"{k}={json.dumps(v)}"]
    r = subprocess.run(args, input=statements + query, capture_output=True, text=True)
    if r.returncode != 0 or '"error"' in r.stdout:
        raise AssertionError((r.stdout + r.stderr)[:500])
    return [json.loads(line) for line in r.stdout.splitlines() if line.startswith("{") and "rowCap" not in line]


CASES = [
    ("take_down", {"station": "HU000B", "month": "202610"}),
    ("lonely_cameras", {"country": None, "month": "202610"}),
    ("country", {"country": "ES", "month": "202610"}),
    ("changes", {"month": "202610"}),
    ("could_turn", {"station": "ES000C", "month": "202610"}),
    ("chain", {"station": "DE0001", "other": "HU000B"}),
    ("chain", {"station": "ES0019", "other": "DE0001"}),
    ("station_history", {"station": "HU000B"}),
    ("country_history", {"country": "ES"}),
    ("talk_to", {"station": "ES000C", "month": "202610"}),
    ("search", {"text": "BR"}),
]


def canon(rows):
    return sorted(json.dumps(r, sort_keys=True) for r in rows)


@unittest.skipUnless(FIXTURE.exists(), "needs the committed fixture")
class TestExport(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = Path(tempfile.mkdtemp())
        cls.out = cls.tmp / "data"
        r = export(FIXTURE, cls.out)
        assert r.returncode == 0, r.stderr

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp)

    def test_page_data_answers_like_the_store(self):
        for name, params in CASES:
            with self.subTest(name=name, **{k: str(v) for k, v in params.items()}):
                q = (QUERIES / f"{name}.cypher").read_text()
                self.assertEqual(canon(rebuild(self.out, q, **params)), canon(run_file(QUERIES / f"{name}.cypher", **params)))

    def test_one_month_store_has_no_previous_pairs_file(self):
        doc = json.loads((self.out / "stats.json").read_text())
        self.assertEqual(doc["pairs"], ["202610"])
        self.assertEqual(sorted(p.name for p in self.out.glob("pairs-*.json")), ["pairs-202610.json"])

    def test_one_month_store_has_no_country_partner_files(self):
        doc = json.loads((self.out / "stats.json").read_text())
        self.assertEqual(doc["partners"], [])
        self.assertEqual(list(self.out.glob("partners-*.json")), [])

    def test_no_fov_polygons_in_page_data(self):
        doc = json.loads((self.out / "stats.json").read_text())
        self.assertFalse(any("fov100" in s for s in doc["stations"]))

    @unittest.skipUnless(COORDS.exists(), "needs research/raw coordinates")
    def test_positions_equal_gmn_public_values(self):
        coords = json.loads(COORDS.read_text())
        cutoff = gmn.month_end("202610")
        doc = json.loads((self.out / "stats.json").read_text())
        placed = [s for s in doc["stations"] if s.get("lat") is not None]
        self.assertGreater(len(placed), 1000)
        for s in placed:
            e = gmn.at_or_before(coords[s["code"]], cutoff)
            self.assertEqual((s["lat"], s["lon"]), (e["lat"], e["lon"]), s["code"])


class TestExportShape(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def test_two_months_export_the_latest_two_pairs_files(self):
        src, store = self.tmp / "raw", self.tmp / "gmn.rl"
        write_common(src, {})
        for m in ("202608", "202609", "202610"):
            write_month(src, m, [(f"{m}01000000_a", ["ES0001", "ES0002"])])
        r = build("202608", "202609", "202610", "--source", str(src), "--store", str(store))
        self.assertEqual(r.returncode, 0, r.stderr)
        r = export(store, self.tmp / "data")
        self.assertEqual(r.returncode, 0, r.stderr)
        doc = json.loads((self.tmp / "data" / "stats.json").read_text())
        self.assertEqual(doc["pairs"], ["202609", "202610"])
        self.assertEqual([m["id"] for m in doc["months"]], ["202608", "202609", "202610"])
        self.assertEqual(doc["partners"], ["ES"])
        es = json.loads((self.tmp / "data" / "partners-ES.json").read_text())
        self.assertEqual([e["p"]["month"] for e in es["shared"]], ["202608"])
        self.assertTrue(all("ES" in (e["a"][:2], e["b"][:2]) for e in es["shared"]))

    def test_size_check_fails_over_50_mb_with_the_size(self):
        big = self.tmp / "big.rl"
        with open(big, "wb") as f:
            f.truncate(51 * 1024 * 1024)
        r = subprocess.run([sys.executable, str(EXPORT), "--check-size", str(big)], capture_output=True, text=True)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("53.5 MB", r.stdout + r.stderr)

    def test_tracked_repo_is_under_50_mb(self):
        r = subprocess.run([sys.executable, str(EXPORT), "--check-size"], capture_output=True, text=True, cwd=ROOT)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)


if __name__ == "__main__":
    unittest.main()
