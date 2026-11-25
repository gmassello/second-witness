---
status: accepted, amended by ADR-0007
date: 2026-11-23
decision-makers: [German]
consulted: []
informed: []
---

# 0002. Monthly slices in a committed `.rl`; the page data is exported from the store

## Context and Problem Statement

The rules ask for a persistent Relate store that judges can inspect. The CLI opens a `.rl` from a URL (S5: 0.20 s), but the browser build only opens `:memory:` or `opfs://` and has no call that takes `.rl` bytes (S6). One month is 9.5 MB as a store; 12 months are 33.2 MB (S5). Loading a month into WASM takes 1.1 s (S6), so loading all 12 months of pairs at page open would take about 13 s, over QA-01's 10 s. How is the data stored, and how does the page get it?

## Decision Drivers

* QA-01: first answer on the page ≤ 10 s
* QA-02 and QA-04: CLI answer ≤ 5 s; store ≤ 50 MB
* R6, R20: one committed store, 12 months
* R16: the page's numbers must equal the store's

## Considered Options

* A — the page reads JSON built straight from GMN's files, separate from the store
* B — the loader writes `store/gmn.rl`, then exports the page data by running queries on that store; the page loads 12 months of station and country stats plus the latest two months of pairs, and other months' pairs on demand
* C — the page fetches `store/gmn.rl` into OPFS

## Decision Outcome

Chosen option "B", because the store is the single source and the page data is a query result of it, which keeps R16 honest and QA-01 within budget.

### Consequences

* Good: functional correctness — the page cannot show a number the store does not hold; installability — about 2.5 MB of WASM and under 2 MB of data at open.
* Bad: two artifacts to commit per month (`store/gmn.rl` and `site/data/*.json`); a chain or take-down on an older month waits for its pairs file (about 1 s).
* To watch: store over 50 MB → keep one trajectory ID per pair (13.2 MB without IDs in S5).

### Confirmation

The parity test compares the page data's rows with the same queries on `store/gmn.rl`; CI fails if `store/gmn.rl` exceeds 50 MB.

## Pros and Cons of the Options

### A — JSON from GMN

* Good, because no export step.
* Bad, because the page and the store can disagree.

### B — export from the store

* Good, because one source.
* Bad, because an export step per month.

### C — `.rl` into OPFS

* Good, because the page would open the real store.
* Bad, because no documented API accepts `.rl` bytes, OPFS needs a dedicated worker, and it would download 33 MB at open.

## More Information

Amended by ADR-0007 (2026-11-25): closed months are no longer committed but published as GitHub Release assets; the repo keeps a fixed October 2026 fixture. S5 and S6 in `docs/ARCHITECTURE.md`; `docs/api/wasm/spec.md` and `docs/api/cli/spec.md` in https://github.com/relatedb/relate.
