@~/Documents/dotfiles/projects/hackathon/CLAUDE.md

Source of truth: `docs/BRIEF.md` (Second Witness). `research/` holds the measurements behind the brief and is not part of the product.

## Commands

```bash
# install: Relate CLI 1.2.0 (the event's required technology); the loader is Python 3 stdlib + this CLI
curl -fsSL https://relatedb.ai/install.sh | sh
python3 -m venv .venv && .venv/bin/pip install relate-db==1.2.0   # MCP server only (U9)
# MCP server (U9): stdio, read-only, default the October fixture; --store store/gmn.rl for 12 months
.venv/bin/python mcp/server.py
# load (U1): one month into store/gmn.rl (downloads are cached in research/raw/)
python3 load/build.py 202610
python3 load/build.py --rebuild 202610                                  # the 12 months ending in 202610
python3 load/build.py 202610 --fresh --store store/gmn-202610.rl        # the committed October fixture
python3 load/build.py --partial                                         # current month into store/gmn-latest.rl
python3 load/build.py --release 202610                                  # gh release store-202610 + data/months.json
# open the store (on a copy: opening a .rl rewrites it, and the fixture is tracked; --max-rows 0, or an agent shell caps reads at 100 rows)
cp store/gmn-202610.rl /tmp/q.rl && relate --database /tmp/q.rl --max-rows 0 "MATCH (s:Station {code:'HU000B'})-[t:STATS]->() RETURN t.two_station_orbits"
# page data (U4): site/data/stats.json + pairs-<YYYYMM>.json from the store (git-ignored)
python3 load/export.py --store store/gmn.rl
python3 load/export.py --check-size                                     # tracked repo under 50 MB
# run one shared query (U3): parameters as JSON, so the month goes quoted
relate --database /tmp/q.rl --max-rows 0 --param station=HU000B --param month='"202610"' "$(cat queries/take_down.cypher)"
# dev (U5): static page, no build step; export the page data first
python3 load/export.py --store store/gmn-202610.rl && python3 -m http.server 8000 --bind 127.0.0.1 --directory site
# full suite: Python loader/queries/MCP tests + Node page tests (node --test finds *.test.mjs itself; a directory argument fails)
python3 -m unittest discover -s tests && node --test
# single test
python3 -m unittest tests.test_graph.TestGraph.test_ae8_us004l_cuts_off_86_that_still_share_meteors
python3 -m unittest tests.test_readme   # every number in README.md against the store; runs its '# check:' blocks
# lint: none — no build step and no linter dependency; the parity tests are the gate
# type-check: none — plain JavaScript and Python, no type checker added
# deploy (U11): push to main, or `gh workflow run pages.yml`; .github/workflows/pages.yml publishes site/ on Pages on every push and daily,
# with the latest release's gmn.rl, the current month from `python3 load/build.py --partial` (gmn-latest.rl, never committed) and a content check
# monthly (U11): .github/workflows/monthly.yml runs `python3 load/build.py --monthly` daily: releases the previous month from day 15,
# or rebuilds and replaces the latest release when a closed month's Last-Modified changed (ADR-0007); `gh workflow run monthly.yml -f today=2026-12-15`
```

U1 to U11 are built; the other lines follow `docs/PLAN.md` and become real as each unit lands.
