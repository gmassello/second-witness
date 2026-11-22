# Relate by Neo4j Hackathon

> Read from the event pages on 2026-11-21 (home, `/rules`, `/details/dates`).

## Event

- **Name:** Relate by Neo4j Hackathon — challenge "Context, connected"
- **URL:** https://relate.devpost.com/
- **Organizer / sponsor:** Neo4j, Inc. (San Mateo, CA), hosted on Devpost. Launched alongside NODES 2026.
- **Product:** Relate, an open-source (Apache-2.0) embedded graph database for AI agents. It runs as a library in Rust or Python, from the CLI, or in the browser through WebAssembly, and connects to the Neo4j ecosystem through Cypher, Bolt, HTTP and MCP. It also has in-process vector search, transactions for several agents writing to the same graph, a store kept in one file or one directory, and subgraph pull from Neo4j/Aura.
- **Resources:** https://relatedb.ai · install: https://relatedb.ai/docs/get-started/install · https://github.com/relatedb/relate · ideas: https://github.com/jexp/relate-ideas
- **Participants:** 675 (as of 2026-11-21)
- **Judges:** Michael Hunger, Andreas Kollegger, William Lyon, Oskar Hane, Yaru Lin, Kate Smith, Jennifer Reif, Stephen Chin (all Neo4j)

## Timeline

| Stage | Event time (PST) | Local (ART) |
|---|---|---|
| Submission deadline | 2026-12-11 18:00 -08:00 | 2026-12-11 23:00 -03:00 |
| Contest period opens | 2026-11-11 18:00 -08:00 | 2026-11-11 23:00 -03:00 |
| Judging | 2026-12-11 18:15 -08:00 → 2026-12-16 23:45 -08:00 | 2026-12-11 23:15 -03:00 → 2026-12-17 04:45 -03:00 |
| Public voting window | 2026-11-11 18:00 -08:00 → 2026-12-16 18:00 -08:00 | 2026-11-11 23:00 -03:00 → 2026-12-16 23:00 -03:00 |
| Winners announced | 2026-12-17 18:00 -08:00 | 2026-12-17 23:00 -03:00 |

- `/rules` gives judging as "Saturday, December 12 to Wednesday, December 16" without hours; `/details/dates` starts it on Dec 11 at 18:15 PST. `/rules` wins on the dates, and the hours come from `/details/dates`.
- `/details/dates` lists a **Public Voting** period, but `/rules` §5 says winners are chosen by a panel of Neo4j judges and does not mention public voting. As far as the rules go, the vote does not decide any prize.

## Prizes and tracks

No tracks. Three non-cash prizes, one per winning entry (not per team member). Total value US$6,197.

| Place | Prize | Approx. value |
|---|---|---|
| 1st | Mac Studio M5 Max, 64 GB / 1 TB | US$3,799 |
| 2nd | Mac mini M6, 32 GB / 512 GB | US$1,499 |
| 3rd | Mac mini M6, 16 GB / 256 GB | US$899 |

The prizes cannot be exchanged for cash. Neo4j ships them at its own cost "in a country where Neo4j can lawfully ship and where the Contest is permitted". The recipient pays "all applicable taxes, import duties, customs fees" and has to provide tax documentation.

## Judging criteria

`/rules` §5 lists five criteria "weighted equally". The home page lists a different set with points, and **`/rules` wins**.

| Criterion | Weight (`/rules`) | Rule text | Home page |
|---|---|---|---|
| Creativity | 20% (equal) | "how original the idea and approach are." | Creativity: 10 points |
| Usefulness | 20% (equal) | "how well the project solves a real problem." | Usefulness: 20 points |
| Completeness | 20% (equal) | "whether it works end to end and can be run from the setup instructions." | Functionality and completeness: 25 points |
| Clarity | 20% (equal) | "the quality of the written explanation, demo, and visual presentation." | Documentation and reproducibility: 15 points |
| Effective use of connected context | 20% (equal) | "how well it uses the Product's graph, retrieval, and agent features." | Relate and connected context: 30 points |

Ready for `docs/judging.tsv`:

```
Creativity	20%	novel|original|first|inventive|unlike
Usefulness	20%	problem|users?|teams?|developers?|saves?|pain
Completeness	20%	end[- ]to[- ]end|working|setup|install|run|demo
Clarity	20%	readme|docs?|documentation|diagram|screenshots?|video
Effective use of connected context	20%	relate|graph|cypher|relationships?|traversal|vector|mcp|bolt|wasm|webassembly
```

## Required tech

- Relate has to be used meaningfully: "for example through the CLI, embedded use, WebAssembly, MCP, Bolt or HTTP, hybrid retrieval, or a connection to Neo4j or Aura" (§3).
- How the use is proved:
  - The repo carries the GitHub topic `relate` (required); `relate-neo4j-hackathon` is recommended.
  - A **persistent Relate store** (a directory or a single file) is committed to the repo or shown in the demo.
  - The README says which mode was used (in memory, directory or single file) and why.
- Entries that are "only prompts or AI-generated text, with no running Relate integration, won't be considered" (home page).

## Submission requirements

| Field | Requirement | Limit |
|---|---|---|
| Title + description | what it does and why it is useful; the use case and "what connects to what" | not published |
| GitHub repo | public, topic `relate`, kept public with the tag through the winner announcement | — |
| Setup instructions | let a judge install and run it "without asking you anything" | — |
| README | the template on the home page: Use case · How it uses Relate (mode, why, what the graph models) · Setup and run · Where the data lives | — |
| Demo | a video of up to 2 minutes (the home page says 1–2 min) **or** a link to a working demo, plus screenshots if useful; it must be viewable without a login | 2 min; format not published |
| Persistent store | a directory or file that judges can inspect | — |
| Statement | the Relate capabilities, third-party tools and AI tools used; any significant AI use described | not published |
| Reused code | disclose your own earlier code and the OSS libraries | — |
| License | MIT or Apache-2.0 encouraged, not required | — |

## Disqualifiers

- **New project only:** started on or after 2026-11-11 18:00 PST. "Pre-existing projects will not be accepted." Your own earlier code can be reused if disclosed, and only the work done during the Contest Period is judged. The home page says "new or extend something you already have", and `/rules` wins.
- The repo is not public, or it lacks the `relate` topic. Neo4j may give a grace period to add the tag before treating the entry as incomplete.
- No Relate integration running.
- Late, incomplete or unintelligible entries.
- Not eligible to take part: under 18 (or under the local age of majority), or living in a country under U.S. embargo or sanctions, or on a U.S. restricted-party list. Neo4j staff, government agency staff and contest organizers are excluded too.
- More than one identity per person, or membership in more than one team. Teams have 1 to 4 people.
- Confidential employer information, or work done as part of a job without the employer's permission (§8).
- A video with third-party material used without permission.

## Blockers

- Register on the Devpost page (Join hackathon).
- Create a public GitHub repo with the `relate` topic.
- If you win: an affidavit of eligibility and a publicity release within 7 days of the email, then the shipment and the import to Argentina (see below).

### Go / no-go notes

- **Argentina:** not excluded by name. Delivery depends on "where Neo4j can lawfully ship"; nothing on the pages says whether they ship to Argentina → **not published**. It is worth asking the organizers through the Devpost page or the Neo4j Discord before investing.
- **Import cost:** the winner pays the duties and taxes. A Mac Studio worth US$3,799 that comes in as a prize pays the full customs regime, and the courier limits for personal shipments may not apply → a real cost, to be quoted before deciding.
- **Competition:** 675 registered. On 2026-11-21: 57 entries in the gallery and 87 more public repos using Relate not yet submitted, none about meteors or astronomy (competitor survey kept outside the repo until judging ends). The prize is not cash, so the cash score per participant from the radar does not apply.
- **Public voting:** there is a window on `/details/dates`, but the rules give no prize for it.
- **Differences from the summary pasted on 2026-11-21:**
  - Public voting exists in the schedule, but it decides nothing.
  - The judging criteria are five with equal weight, not points.
  - The demo can be a link to a working demo instead of a video.
  - A persistent store and a README that follows the template are required.
