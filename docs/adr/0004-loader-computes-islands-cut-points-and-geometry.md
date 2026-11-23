---
status: accepted
date: 2026-11-23
decision-makers: [German]
consulted: []
informed: []
---

# 0004. The loader computes islands, cut points, same-site groups, moved codes and "could pair", and stores them in the graph

## Context and Problem Statement

R8, R10 and R12 need each station's island and the stations a cut point leaves behind (US004L: 86). R14 needs which installed camera could pair by turning, which is field-of-view geometry at 100 km. The BRIEF's assumptions add same-site groups and codes that move. Relate 1.2.0 has no graph algorithms (C6). In S4 plain reachability from US004L took 50 ms, but a `shortestPath` that excludes the cut station ran for over 10 minutes and was stopped. R16 asks that every number come from Cypher on the store. What runs live and what is precomputed?

## Decision Drivers

* QA-03: take-down ≤ 1 s in the browser
* R16: numbers read with Cypher from the store
* C6 and S4: no algorithms; the exclusion query does not finish

## Considered Options

* A — everything live in Cypher
* B — the loader computes `island`, `cut_off`, `site`, `possibly_moved`, `COULD_PAIR` and `NEAREST_ISLAND` once per month with the Python standard library and writes them as properties and relationships; every query, including the take-down and the chain, stays live Cypher over them
* C — compute them in the page's JavaScript

## Decision Outcome

Chosen option "B", because the take-down, the chain, the talk-to list and the history stay live Cypher (S2, S3, S6: 2–40 ms), and the only values Cypher cannot reach in time are computed once and read from the graph.

### Consequences

* Good: time behaviour — every page answer under 10 ms in S6; R16 holds as "read from the store with Cypher", and the README names the precomputed properties.
* Bad: the graph's showcase loses the cut-point traversal; a judge reading the queries sees `cut_off` as a property, not a traversal.
* To watch: if a later Relate adds connected components or a predicate-aware shortest path that finishes in under 5 s, move `island` and `cut_off` back to live queries.

### Confirmation

The parity test checks US004L's `cut_off` = 86 and the island of ES0019 = 17 stations in ES and PT against an independent computation over the month's trajectory file.

## Pros and Cons of the Options

### A — all live

* Good, because purest use of the graph.
* Bad, because the cut-point query did not finish in 10 min (S4).

### B — precompute what Cypher cannot

* Good, because fast and honest about what is precomputed.
* Bad, because a loader with graph code to test.

### C — in the page

* Good, because no loader logic.
* Bad, because the MCP and CLI would not have the values, breaking ADR-0001.

## More Information

S4 in `docs/ARCHITECTURE.md`. The loader's algorithms are written for the product; `research/measure.py` stays the brief's evidence and is not imported.
