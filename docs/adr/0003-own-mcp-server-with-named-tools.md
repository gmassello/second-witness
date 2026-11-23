---
status: accepted
date: 2026-11-23
decision-makers: [German]
consulted: []
informed: []
---

# 0003. Our own MCP server with named tools over `relate-db`

## Context and Problem Statement

R7 asks that a coding agent call named tools (take down, lonely cameras, country report) and get the page's answer. Relate's built-in MCP (`relate serve --mcp`) lists `read_cypher`, `write_cypher` and `get_schema` only, so the agent would have to write the Cypher itself. `relate-db` 1.2.0 opens the committed store read-only from Python and returned the CLI's rows in S7 (0.3–0.4 ms). Which MCP surface does the agent get?

## Decision Drivers

* R7 and AE6: named tools; the answer equals the page's, checked with a recorded agent run
* QA-05: same rows as the page and CLI
* Agent-computer interface: a tool per question, with parameters the user would name (`station`, `country`), not a query language (`knowledge/wiki/agent-architectures.md`)

## Considered Options

* A — `relate serve --mcp` with the README's queries
* B — a stdio MCP server in Python on `relate-db`, one tool per `queries/*.cypher` file
* C — both: our named tools plus Relate's `read_cypher` for free-form questions

## Decision Outcome

Chosen option "B", because named tools give the agent the same questions the page asks, and each tool runs the same file (ADR-0001).

### Consequences

* Good: interoperability (R7) as written; each tool's result carries `{query, parameters, rows}`, so an answer can be traced.
* Bad: one more process to document and test; it needs Python and `relate-db==1.2.0`.
* To watch: if judges expect Relate's own MCP, the README shows `relate serve --mcp --read-only store/gmn.rl` as the second way (option C costs one paragraph).

### Confirmation

A recorded agent run asks about HU000B and its tool result equals the page's take-down rows (AE6); the parity test calls each tool.

## Pros and Cons of the Options

### A — Relate's MCP

* Good, because nothing to build.
* Bad, because no named tools; the agent writes Cypher.

### B — own named tools

* Good, because R7 and the same query files.
* Bad, because an extra process.

### C — both

* Good, because free-form questions too.
* Bad, because two surfaces to explain in a 2-minute video.

## More Information

`docs/api/mcp/spec.md` in https://github.com/relatedb/relate; spike S7 in `docs/ARCHITECTURE.md`. Read-only: no tool writes, so the lethal trifecta does not apply (no private data, no outbound action).
