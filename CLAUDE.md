@~/Documents/dotfiles/projects/hackathon/CLAUDE.md

Source of truth: `docs/BRIEF.md` (Second Witness). `research/` holds the measurements behind the brief and is not part of the product.

## Commands

```bash
# install: Relate CLI 1.2.0 (the event's required technology)
curl -fsSL https://relatedb.ai/install.sh | sh
python3 -m venv .venv && .venv/bin/pip install relate-db==1.2.0   # MCP server only (U9)
# dev (planned, U5): static page, no build step
python3 -m http.server 8000 --bind 127.0.0.1 --directory site
# full suite (planned, U1-U10): Python loader/queries/MCP tests + Node page tests
python3 -m unittest discover -s tests && node --test tests/
# single test (planned)
python3 -m unittest tests.test_queries.TestTakeDown
# lint: none — no build step and no linter dependency; the parity tests are the gate
# type-check: none — plain JavaScript and Python, no type checker added
# deploy (planned, U11): GitHub Pages from .github/workflows/pages.yml on push to main and daily,
# loading the current month with `python3 load/build.py --partial` (published, never committed)
```

Planned, not built: these lines follow `docs/PLAN.md` and become real as each unit lands.
