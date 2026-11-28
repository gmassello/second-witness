# Pending — Relate by Neo4j Hackathon close

Deadline: **2026-12-11 18:00 -08:00** (2026-12-11 23:00 -03:00). Competition:
<https://relate.devpost.com/> · Submission: not yet (not registered) · PR: none.

Stages (from `/details/dates`; `/rules` agrees on the days, see `docs/HACKATHON.md` § Timeline): submissions until
2026-12-11 18:00 -08:00, judging 2026-12-11 18:15 -08:00 → 2026-12-16 23:45 -08:00, winners 2026-12-17 18:00 -08:00.

Code status in one line: no product code yet; `docs/BRIEF.md` describes Second Witness, and `research/` holds the measurements behind it (`research/metrics-202610.json`).

---

## Surfaces

| Surface | Where | Status | Verified |
|---|---|---|---|
| Repo and CI | `gmassello/second-witness` @ `<sha>` | public, topics `relate` + `relate-neo4j-hackathon` | |
| Site | https://gmassello.github.io/second-witness/ (daily Pages deploy, `gmn.rl` and `gmn-latest.rl` beside it) | ok | 2026-11-28 |
| Submission | <public URL, not /edit> | | |
| Gallery card | <gallery URL> | | |
| Upstream PR | #<n> | | |
| Second checkout | `~/<path>` branch `<branch>` | | |
| Video | `<id>` | | |
| Deck | `docs/deck.pdf` sha256 `<hash>` | | |
| Landing | <Pages URL> | | |

## Billable resources

Written by the skill that creates the resource. Shut down in `hackathon-retro`, once judging ends.

| Resource | Provider | How to delete | Live until |
|---|---|---|---|

## Duplicated facts

| Fact | Real value | Command that produces it | Copies |
|---|---|---|---|
| Test count | | | |
| Parts in the catalog | | | |
| Version | | | |

## Known gaps

What does not work, and why. This is what keeps the form from promising too much, and in a
competition where everyone overpromises, saying it is a differentiator.

- **Detections per night** — the fourth field of GMN's per-night upload index is read as the night's detection count; GMN does not document it. Confirm on the GMN mailing list before publishing "running, no partner" numbers.

## Don't break this when you come back

The repo's traps, for whoever touches it three days from now (you, without context).

- `<script>` deletes `<gitignored directory>`: running it loses <what>.

## Out of my control

Not tasks: risks. Each one with its fallback.

- **Devpost registration** — not registered yet; "Join hackathon" on https://relate.devpost.com/ before submitting. Fallback: none, it is required.
- **Prize shipping to Argentina** — the rules only say "a country where Neo4j can lawfully ship"; import duties are on the winner. Ask the organizers through the Devpost page or the Neo4j Discord. Fallback: name a recipient address in a country they ship to.
- **The `relate` topic stays on the repo through the winner announcement** — fallback: Neo4j may grant a grace period to add it back (`/rules` §4).
- **Relate is experimental and may break** (`/rules` §3) — fallback: pin the exact Relate version that the demo was recorded with.
