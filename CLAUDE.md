@~/Documents/dotfiles/projects/hackathon/CLAUDE.md

Source of truth: `docs/BRIEF.md` (Second Witness). `research/` holds the measurements behind the brief and is not part of the product.

## Commands

```bash
# install: Relate CLI 1.2.0 (the event's required technology); the loader is Python 3 stdlib + this CLI
curl -fsSL https://relatedb.ai/install.sh | sh
python3 -m venv .venv && .venv/bin/pip install relate-db==1.2.0   # MCP server only (U9)
# load (U1): one month into store/gmn.rl (downloads are cached in research/raw/)
python3 load/build.py 202610
python3 load/build.py --rebuild 202610                                  # the 12 months ending in 202610
python3 load/build.py 202610 --fresh --store store/gmn-202610.rl        # the committed October fixture
python3 load/build.py --partial                                         # current month into store/gmn-latest.rl
python3 load/build.py --release 202610                                  # gh release store-202610 + data/months.json
# open the store (on a copy: opening a .rl rewrites it, and the fixture is tracked)
cp store/gmn-202610.rl /tmp/q.rl && relate --database /tmp/q.rl "MATCH (s:Station {code:'HU000B'})-[t:STATS]->() RETURN t.two_station_orbits"
# dev (planned, U5): static page, no build step
python3 -m http.server 8000 --bind 127.0.0.1 --directory site
# full suite: Python loader/queries/MCP tests + Node page tests (node --test finds *.test.mjs itself; a directory argument fails)
python3 -m unittest discover -s tests && node --test
# single test
python3 -m unittest tests.test_load.TestLoad.test_ae1_fixture_matches_raw_october
# lint: none — no build step and no linter dependency; the parity tests are the gate
# type-check: none — plain JavaScript and Python, no type checker added
# deploy (planned, U11): GitHub Pages from .github/workflows/pages.yml on push to main and daily,
# loading the current month with `python3 load/build.py --partial` (published, never committed);
# monthly: `python3 load/build.py --rebuild <YYYYMM>` then `--release <YYYYMM>` on day 15 of the next month, and again whenever a closed month's `Last-Modified` changes (ADR-0007)
```

U1 is built; the other lines follow `docs/PLAN.md` and become real as each unit lands.
