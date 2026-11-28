import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_load import RAW_OCT, build, digest, write_common, write_month
from test_queries import QUERIES, SUFFIX, STORE12, raw_rows, run_file


class TestHistory(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.src = self.tmp / "raw"
        self.store = self.tmp / "gmn.rl"

    def tearDown(self):
        shutil.rmtree(self.tmp)

    @unittest.skipUnless(STORE12.exists(), "needs the 12-month store/gmn.rl")
    def test_ae21_es000c_october_row(self):
        rows = run_file(QUERIES / "station_history.cypher", store=STORE12, station="ES000C")
        october = next(r for r in rows if r["month"] == "202610")
        self.assertEqual((october["nights"], october["detections"], october["orbits"]), (31, 1797, 0))
        self.assertEqual([r["month"] for r in rows], sorted(r["month"] for r in rows))

    @unittest.skipUnless(STORE12.exists() and RAW_OCT.exists(), "needs store/gmn.rl and research/raw/202610")
    def test_ae22_spain_twelve_months_and_october_share(self):
        rows = run_file(QUERIES / "country_history.cypher", store=STORE12, country="ES")
        self.assertEqual(len(rows), 12)
        total = two = 0
        for _, st in raw_rows():
            if any(s.startswith("ES") for s in st):
                total += 1
                two += len(st) == 2
        self.assertAlmostEqual(rows[-1]["two_station_share"], two / total, places=4)
        self.assertEqual(rows[-1]["month"], "202610")

    def test_station_that_started_in_june_has_no_earlier_rows(self):
        write_common(self.src, {})
        write_month(self.src, "202605", [("20260501000000_a", ["ES0001", "ES0002"])])
        write_month(self.src, "202606", [("20260601000000_a", ["ES0001", "ES0003"])])
        write_month(self.src, "202607", [("20260701000000_a", ["ES0003", "ES0002"])])
        r = build("202605", "202606", "202607", "--source", str(self.src), "--store", str(self.store))
        self.assertEqual(r.returncode, 0, r.stderr)
        rows = run_file(QUERIES / "station_history.cypher", store=self.store, station="ES0003")
        self.assertEqual([x["month"] for x in rows], ["202606", "202607"])
        self.assertEqual(rows[0]["partners"], [{"partner": "ES0001", "meteors": 1}])

    def test_missing_month_stops_the_rebuild_naming_it(self):
        write_common(self.src, {})
        write_month(self.src, "202609", [("20260901000000_a", ["ES0001", "ES0002"])])
        r = build("202609", "--source", str(self.src), "--store", str(self.store))
        self.assertEqual(r.returncode, 0, r.stderr)
        before = digest(self.store)
        write_month(self.src, "202610", [("20261001000000_a", ["ES0001", "ES0002"])])
        (self.src / "202608").mkdir()
        r = build("202608", "202610", "--source", str(self.src), "--store", str(self.store))
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("202608: no trajectory file at GMN", r.stderr)
        self.assertNotIn("Traceback", r.stderr)
        self.assertEqual(digest(self.store), before)


if __name__ == "__main__":
    unittest.main()
