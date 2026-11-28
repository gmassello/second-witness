import hashlib
import json
import subprocess
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_load import FIXTURE
from test_queries import QUERIES, run_file

ROOT = Path(__file__).resolve().parent.parent
PYTHON = ROOT / ".venv" / "bin" / "python"
SERVER = ROOT / "mcp" / "server.py"

TOOLS = {
    "lonely_cameras": ("lonely_cameras", {"country": "ES"}, {"country": "ES", "month": "202610"}),
    "take_down": ("take_down", {"station": "HU000B"}, {"station": "HU000B", "month": "202610"}),
    "country_report": ("country", {"country": "ES"}, {"country": "ES", "month": "202610"}),
    "who_could_turn": ("could_turn", {"station": "ES000C"}, {"station": "ES000C", "month": "202610"}),
    "talk_to": ("talk_to", {"station": "ES000C"}, {"station": "ES000C", "month": "202610"}),
    "witness_chain": ("chain", {"from": "DE0001", "to": "HU000B"}, {"station": "DE0001", "other": "HU000B"}),
    "station_history": ("station_history", {"station": "HU000B"}, {"station": "HU000B"}),
}


def canon(rows):
    return sorted(json.dumps(r, sort_keys=True) for r in rows)


@unittest.skipUnless(PYTHON.exists() and FIXTURE.exists(), "needs .venv with relate-db and the fixture")
class TestMcp(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.before = hashlib.sha256(FIXTURE.read_bytes()).hexdigest()
        cls.proc = subprocess.Popen([str(PYTHON), str(SERVER)], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
        cls.next_id = 0

    @classmethod
    def tearDownClass(cls):
        cls.proc.stdin.close()
        cls.proc.wait(timeout=10)

    def send(self, payload):
        self.proc.stdin.write(payload + "\n")
        self.proc.stdin.flush()
        return json.loads(self.proc.stdout.readline())

    def rpc(self, method, params=None):
        TestMcp.next_id += 1
        return self.send(json.dumps({"jsonrpc": "2.0", "id": self.next_id, "method": method, "params": params or {}}))

    def call(self, name, args):
        return self.rpc("tools/call", {"name": name, "arguments": args})["result"]

    def test_initialize_negotiates_known_versions(self):
        for v in ("2025-06-18", "2025-03-26", "2024-11-05"):
            r = self.rpc("initialize", {"protocolVersion": v, "capabilities": {}, "clientInfo": {"name": "t", "version": "0"}})["result"]
            self.assertEqual(r["protocolVersion"], v)
            self.assertIn("tools", r["capabilities"])
        r = self.rpc("initialize", {"protocolVersion": "1999-01-01"})["result"]
        self.assertEqual(r["protocolVersion"], "2025-06-18")

    def test_tools_are_named_read_only_with_output_schema(self):
        tools = self.rpc("tools/list")["result"]["tools"]
        self.assertEqual(sorted(t["name"] for t in tools), sorted(TOOLS))
        for t in tools:
            self.assertTrue(t["annotations"]["readOnlyHint"])
            self.assertTrue(t["title"])
            self.assertEqual(set(t["outputSchema"]["properties"]) >= {"query", "parameters", "rows"}, True)

    def test_every_tool_gives_the_cli_rows(self):
        for name, (query, args, params) in TOOLS.items():
            with self.subTest(tool=name):
                r = self.call(name, args)
                self.assertFalse(r["isError"])
                s = r["structuredContent"]
                self.assertEqual(s["query"], query)
                cli_params = {k: v for k, v in params.items()}
                self.assertEqual(canon(s["rows"]), canon(run_file(QUERIES / f"{query}.cypher", **cli_params)))
                self.assertEqual(json.loads(r["content"][0]["text"])["rows"], s["rows"])

    def test_ae6_hu000b_take_down(self):
        s = self.call("take_down", {"station": "HU000B"})["structuredContent"]
        self.assertEqual(s["rows"][0]["orbits_lost"], 899)
        self.assertEqual(len([r for r in s["rows"] if r["partner"]]), 50)

    def test_missing_month_resolves_to_the_latest(self):
        s = self.call("lonely_cameras", {})["structuredContent"]
        self.assertEqual(s["parameters"]["month"], "202610")
        self.assertIsNone(s["parameters"]["country"])
        self.assertEqual(self.call("witness_chain", {"from": "DE0001", "to": "HU000B"})["structuredContent"]["parameters"]["month"], "202610")

    def test_unknown_station_is_named_with_format_and_suggestions(self):
        r = self.call("take_down", {"station": "HU00B"})
        self.assertFalse(r["isError"])
        s = r["structuredContent"]
        self.assertEqual(s["rows"], [])
        self.assertIn("HU00B", s["message"])
        self.assertIn("6-character GMN code like HU000B", s["message"])
        self.assertTrue(1 <= len(s["suggestions"]) <= 3)
        self.assertTrue(all(c.startswith("HU") for c in s["suggestions"]))

    def test_history_is_ordered_by_month(self):
        rows = self.call("station_history", {"station": "HU000B"})["structuredContent"]["rows"]
        self.assertEqual([r["month"] for r in rows], sorted(r["month"] for r in rows))

    def test_protocol_errors(self):
        self.assertEqual(self.send("{not json")["error"]["code"], -32700)
        self.assertEqual(self.rpc("tools/call", {"name": "drop_everything", "arguments": {}})["error"]["code"], -32602)
        self.assertEqual(self.rpc("tools/call", {"name": "take_down", "arguments": {}})["error"]["code"], -32602)
        self.assertEqual(self.rpc("no/such")["error"]["code"], -32601)

    def test_store_is_not_modified(self):
        self.call("take_down", {"station": "HU000B"})
        self.assertEqual(hashlib.sha256(FIXTURE.read_bytes()).hexdigest(), self.before)


if __name__ == "__main__":
    unittest.main()
