---
status: accepted
date: 2026-11-23
decision-makers: [German]
consulted: []
informed: []
---

# 0001. One set of Cypher files, read by three adapters

## Context and Problem Statement

Second Witness answers the same questions in three places: the public page, an agent over MCP and the judge's CLI command. R16 says every number comes from a Cypher query on the store, and AE6 asks that the agent's answer equal the page's. If each adapter wrote its own query, the three would drift the first time a rule changed (a same-site pair, a moved code). Where does each question live?

## Decision Drivers

* QA-05: page, MCP and CLI give 100% equal rows for HU000B, ES000C and US004L
* R16: every published number from Cypher on the store
* Deadline 2026-12-11: one place to change a rule

## Considered Options

* A — each adapter keeps its own query strings
* B — `queries/<name>.cypher`, one statement per file, read verbatim by every adapter
* C — a query service the adapters call

## Decision Outcome

Chosen option "B", because the files are the core and the page, the MCP server and the CLI are adapters around it, so a rule changes in one file.

### Consequences

* Good: functional correctness (QA-05) is a parity test over the same files; a judge can paste any file into `relate`.
* Bad: queries cannot be composed in code; a question that needs two statements is two files.
* To watch: if a query needs per-adapter changes, the adapter is doing logic it should not.

### Confirmation

A parity test runs every file through WASM, `relate-db` and the CLI on the committed October 2026 fixture and compares rows; a lint step fails if a `.js` or `.py` file under `site/` or `mcp/` contains `MATCH `.

## Pros and Cons of the Options

### A — own strings per adapter

* Good, because each adapter is self-contained.
* Bad, because three copies of each rule drift.

### B — shared files

* Good, because one place decides and judges can read them.
* Bad, because no query composition.

### C — query service

* Good, because one runtime.
* Bad, because it needs a server, against R5.

## More Information

Spikes S2, S6 and S7 in `docs/ARCHITECTURE.md` ran the same statements on the CLI, WASM and `relate-db` and got the same rows.
