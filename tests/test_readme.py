import re
import subprocess
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_load import FIXTURE
from test_queries import q

ROOT = Path(__file__).resolve().parent.parent
README = ROOT / "README.md"
MONTH = "202610"

CLAIMS = {
    "HU000B: two-station orbits lost if it stops": lambda: q("take_down", station="HU000B", month=MONTH)[0]["orbits_lost"],
    "US004L: stations cut off if it stops": lambda: q("take_down", station="US004L", month=MONTH)[0]["cut_off"],
    "Islands in October 2026": lambda: len(q("network", month=MONTH)[0]["islands"]),
    "Cameras running with no partner": lambda: len(q("lonely_cameras", country=None, month=MONTH)),
    "ES000C: nights uploaded": lambda: q("take_down", station="ES000C", month=MONTH)[0]["nights"],
    "ES000C: detections": lambda: q("take_down", station="ES000C", month=MONTH)[0]["detections"],
    "ES000C: orbits": lambda: q("take_down", station="ES000C", month=MONTH)[0]["orbits"],
    "Stations that stopped since September": lambda: len([r for r in q("changes", month=MONTH) if r["change"] in ("stopped", "possibly_moved")]),
    "NZ002C: shared meteors lost to stations that stopped": lambda: next(r for r in q("changes", month=MONTH) if r["station"] == "NZ002C")["lost"],
}


def table(text):
    rows = {}
    for line in text.splitlines():
        m = re.match(r"^\|\s*([^|]+?)\s*\|\s*([\d,]+)\s*\|", line)
        if m:
            rows[m.group(1)] = int(m.group(2).replace(",", ""))
    return rows


def mismatches(text):
    found = table(text)
    out = [f"{label}: missing" for label in CLAIMS if label not in found]
    out += [f"{label}: README says {found[label]}, the store gives {fn()}" for label, fn in CLAIMS.items() if label in found and found[label] != fn()]
    return out


def check_blocks(text):
    return [b for b in re.findall(r"```bash\n(.*?)```", text, re.S) if b.startswith("# check:")]


@unittest.skipUnless(FIXTURE.exists(), "needs the committed fixture")
class TestReadme(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = README.read_text() if README.exists() else ""

    def test_follows_the_event_template(self):
        for h in ("## Use case", "## How it uses Relate", "## Setup and run", "## Where the data lives", "## Works with the meteor map"):
            self.assertIn(h, self.text)

    def test_mermaid_names_the_components(self):
        block = re.search(r"```mermaid\n(.*?)```", self.text, re.S)
        self.assertTrue(block, "no mermaid block")
        for name in ("GMN", "loader", "gmn.rl", "queries", "page", "MCP", "CLI"):
            self.assertIn(name, block.group(1))

    def test_says_mode_limits_and_sources(self):
        for phrase in ("single-file", "clouds", "broken lens", "re-entry", "Datasette", "several times a day",
                       "CC BY 4.0", "Vida et al. (2020)", "Vida et al. (2021)", "https://tammojan.github.io/meteormap/", "docs/agent-run.md"):
            self.assertIn(phrase, self.text)

    def test_ae5_first_take_down_runs_offline_from_the_fixture(self):
        blocks = check_blocks(self.text)
        self.assertTrue(blocks, "no '# check:' block")
        for block in blocks:
            expect = re.match(r"# check: prints (\S+)", block).group(1)
            r = subprocess.run(["bash", "-c", block], cwd=ROOT, capture_output=True, text=True)
            Path("/tmp/sw.rl").unlink(missing_ok=True)
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertIn(expect, r.stdout, block)

    def test_ae16_every_number_in_the_table_comes_from_the_store(self):
        self.assertEqual(mismatches(self.text), [])

    def test_a_changed_number_is_named(self):
        bad = self.text.replace("| HU000B: two-station orbits lost if it stops | 899 |", "| HU000B: two-station orbits lost if it stops | 900 |")
        self.assertIn("HU000B: two-station orbits lost if it stops: README says 900, the store gives 899", mismatches(bad))


if __name__ == "__main__":
    unittest.main()
