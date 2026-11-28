import http.server
import json
import os
import sys
import tempfile
import threading
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "load"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build
import gmn
from test_load import build as run_build, write_common, write_month

WORKFLOWS = ROOT / ".github" / "workflows"


class Gmn(http.server.BaseHTTPRequestHandler):
    etag = '"v1"'
    modified = "Sat, 31 Oct 2026 23:00:00 GMT"
    full = 0
    conditional = []

    def do_GET(self):
        Gmn.conditional.append(self.headers.get("If-None-Match"))
        if self.headers.get("If-None-Match") == Gmn.etag:
            self.send_response(304)
            self.end_headers()
            return
        Gmn.full += 1
        body = b"# header\n"
        self.send_response(200)
        self.send_header("ETag", Gmn.etag)
        self.send_header("Last-Modified", Gmn.modified)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_HEAD(self):
        self.send_response(200)
        self.send_header("Last-Modified", Gmn.modified)
        self.end_headers()

    def log_message(self, *a):
        pass


class TestConditionalDownload(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = http.server.HTTPServer(("127.0.0.1", 0), Gmn)
        threading.Thread(target=cls.server.serve_forever, daemon=True).start()
        cls.url = f"http://127.0.0.1:{cls.server.server_port}/traj.txt"

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()

    def test_unchanged_etag_downloads_nothing(self):
        with tempfile.TemporaryDirectory() as d:
            dest = Path(d) / "traj.txt"
            Gmn.full, Gmn.conditional = 0, []
            self.assertTrue(gmn.get(self.url, dest, force=True))
            mtime = dest.stat().st_mtime_ns
            self.assertTrue(gmn.get(self.url, dest, force=True))
            self.assertEqual(Gmn.full, 1)
            self.assertEqual(Gmn.conditional, [None, '"v1"'])
            self.assertEqual(dest.stat().st_mtime_ns, mtime)
            self.assertEqual(gmn.saved_headers(dest)["last_modified"], Gmn.modified)

    def test_last_modified_comes_from_a_head_request(self):
        self.assertEqual(gmn.last_modified(self.url), Gmn.modified)


class TestMonthly(unittest.TestCase):
    manifest = {"latest": "store-202610", "releases": [{"tag": "store-202610", "months": ["202609", "202610"],
                                                       "last_modified": {"202609": "A", "202610": "B"}}]}
    same = {"202609": "A", "202610": "B"}

    def test_before_day_15_the_previous_month_is_not_released(self):
        self.assertIsNone(build.plan_monthly("2026-12-14", self.manifest, self.same))

    def test_from_day_15_the_previous_month_is_released(self):
        self.assertEqual(build.plan_monthly("2026-12-15", self.manifest, self.same), ("202611", []))

    def test_a_released_month_is_not_released_again(self):
        self.assertIsNone(build.plan_monthly("2026-11-20", self.manifest, self.same))

    def test_a_changed_closed_month_rebuilds_and_replaces_the_latest_release(self):
        self.assertEqual(build.plan_monthly("2026-11-20", self.manifest, {"202609": "C", "202610": "B"}), ("202610", ["202609"]))

    def test_release_records_last_modified_per_month(self):
        with tempfile.TemporaryDirectory() as d:
            d = Path(d)
            src, store = d / "raw", d / "gmn.rl"
            write_common(src, {})
            write_month(src, "202610", [("20261001000000_a", ["ES0001", "ES0002"])])
            (src / "202610" / "traj_summary_monthly_202610.txt.headers").write_text(json.dumps({"etag": '"x"', "last_modified": "B"}))
            self.assertEqual(run_build("202610", "--source", str(src), "--store", str(store)).returncode, 0)
            fake = d / "gh"
            fake.write_text("#!/bin/sh\n[ \"$2\" = view ] && exit 1\nexit 0\n")
            fake.chmod(0o755)
            manifest = d / "months.json"
            r = run_build("--release", "202610", "--store", str(store), "--manifest", str(manifest), "--source", str(src),
                          env=dict(os.environ, GH_BIN=str(fake)))
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertEqual(json.loads(manifest.read_text())["releases"][0]["last_modified"], {"202610": "B"})


class TestWorkflows(unittest.TestCase):
    def test_pages_publishes_on_push_and_daily_with_a_content_check(self):
        y = (WORKFLOWS / "pages.yml").read_text()
        for s in ("push:", "schedule:", "load/build.py --partial", "load/export.py", "site/gmn.rl", "site/gmn-latest.rl",
                  "<title>Second Witness</title>", "data/stats.json", "actions/deploy-pages", "v1.2.0", "cp -R queries site/queries"):
            self.assertIn(s, y)

    def test_monthly_releases_with_write_permission(self):
        y = (WORKFLOWS / "monthly.yml").read_text()
        for s in ("schedule:", "workflow_dispatch:", "contents: write", "load/build.py --monthly", "data/months.json"):
            self.assertIn(s, y)


if __name__ == "__main__":
    unittest.main()
