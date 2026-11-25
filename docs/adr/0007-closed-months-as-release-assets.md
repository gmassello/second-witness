---
status: accepted
date: 2026-11-25
decision-makers: [German]
consulted: []
informed: []
---

# 0007. Closed months published as GitHub Release assets; a fixed October fixture committed

## Context and Problem Statement

ADR-0002 commits `store/gmn.rl` once a month. A `.rl` is a zip, so git cannot store a delta: every monthly commit adds the whole file to history, 13.2–33.2 MB per month once 12 months are loaded (S5), about 1 GB in two to three years if the tool is left running for GMN. GitHub also disables scheduled workflows in a public repository after 60 days without activity, which would stop the daily job of ADR-0006. The rules ask for a persistent Relate store "committed to the repo or shown in the demo" (`docs/HACKATHON.md`). Where do closed months live so the repo does not grow with use?

## Decision Drivers

* QA-04: the repo stays small however many months are loaded
* R5, AE5: a fresh clone answers a take-down with no network
* C1: a persistent store judges can inspect
* ADR-0006: the daily job keeps running without a person

## Considered Options

* A — commit `store/gmn.rl` every month (ADR-0002 as written)
* B — each closed month is built into `gmn.rl` and uploaded as the asset of a GitHub Release `store-<YYYYMM>`; the repo commits once a fixed fixture, `store/gmn-202610.rl` (October 2026, one trajectory ID per pair), plus a small `data/months.json` per month
* C — Git LFS

## Decision Outcome

Chosen option "B", because the repo's history stays at a few MB, the fixture keeps the offline clone, the parity tests and C1, and the monthly commit of `data/months.json` is the activity that keeps the scheduled workflows enabled.

### Consequences

* Good: the CLI and the MCP open the latest 12 months from one stable URL, `https://github.com/gmassello/second-witness/releases/latest/download/gmn.rl`; each asset may be up to 2 GB.
* Good: the page is unchanged; it reads `site/data/*.json` from Pages and never the `.rl` (S6).
* Bad: the 12-month store needs network; offline, only the October fixture answers.
* Bad: the release URL redirects to `objects.githubusercontent.com`; `relate --load` must follow it (spike S8).
* To watch: if the monthly job stops, the cron is disabled after 60 days; uptime turns red when `as_of` is over 2 days old and `gh workflow enable` restores it.

### Confirmation

Spike S8 (`relate --load` on a test release URL answers a take-down), U1 (`build.py <YYYYMM>` creates the release and lists it in `data/months.json`; the tracked size grows by under 10 KB) and U11 (the daily job starts from the latest asset).

## Pros and Cons of the Options

### A — monthly commit

* Good, because the store sits next to the code.
* Bad, because history grows by the full store every month and cannot shrink without rewriting it.

### B — release assets and a fixed fixture

* Good, because the repo stays flat and the URL is stable.
* Bad, because a release step per month and two store locations.

### C — Git LFS

* Good, because the file stays in the tree.
* Bad, because the free quota is 1 GB of bandwidth a month and every clone or `--load` spends it.

## More Information

Amends ADR-0002 (where closed months are stored) and ADR-0006 (what the daily job starts from). GitHub limits: 100 MB per tracked file, 2 GB per release asset; scheduled workflows in public repositories are disabled after 60 days of no repository activity.
