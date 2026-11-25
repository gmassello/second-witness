---
status: accepted
date: 2026-11-25
decision-makers: [German]
consulted: []
informed: []
---

# 0006. The current month reloads daily as a partial slice published on GitHub Pages; only closed months are committed

## Context and Problem Statement

The product has to be up to date to the day. GMN rewrites the current month's trajectory file several times a day: on 2026-11-25 `traj_summary_monthly_202611.txt` was 72 MB and modified at 09:54 UTC. ADR-0002 commits a 12-month `store/gmn.rl` (33.2 MB, S5). Committing it every day would add a store to git history each day. How does the page get today's data?

## Decision Drivers

* Freshness: the latest month is at most one day old
* R6 and R16: the store is built by one documented command and every number comes from Cypher on it
* QA-04: the repo history stays flat
* R5: the page opens without depending on GMN at view time

## Considered Options

* A — closed months only, loaded once a month
* B — a scheduled GitHub Actions job runs `load/build.py --partial` daily on the current month and publishes the page data and `gmn-latest.rl` as the Pages artifact; the committed store takes only closed months
* C — the page downloads GMN's daily files itself and adds them in WebAssembly

## Decision Outcome

Chosen option "B", because it keeps every number on a store built by the loader (R16), keeps the repo history to one store change per month, and the page never calls GMN while a judge looks at it.

### Consequences

* Good: the latest month shows "partial, to <date>" and moves every day; closed months never change.
* Bad: two store URLs: the committed one for an offline clone (closed months) and the Pages one for the latest; the README names both.
* Bad: a partial month undercounts pairs, since cameras keep uploading late data; the page labels it.
* To watch: the daily job downloads about 72 MB from GMN; if a run fails, the page keeps the previous day and uptime turns red after 2 days.

### Confirmation

U1 (`--partial` leaves the committed store unchanged, AE23), U11 (the scheduled run publishes today's date) and U12 (uptime red when `as_of` is older than 2 days).

## Pros and Cons of the Options

### A — closed months only

* Good, because simplest.
* Bad, because the page is up to 5 weeks old.

### B — daily partial, published not committed

* Good, because fresh and reproducible.
* Bad, because a scheduled job and two store URLs.

### C — live in the page

* Good, because fresh to the hour.
* Bad, because numbers no longer come from the store (R16) and the page depends on GMN at view time.

## More Information

Amends ADR-0002 only for the current month. Since ADR-0007, closed months are GitHub Release assets: the daily job downloads the latest `gmn.rl` asset, adds the partial month and publishes `gmn-latest.rl` on Pages.
