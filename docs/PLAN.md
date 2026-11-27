# Second Witness — Plan

Source: `docs/BRIEF.md`, `docs/ARCHITECTURE.md` · Deadline: 2026-12-11 18:00 -08:00 (2026-12-11 23:00 -03:00) · Hours left at writing: 435.1

## Summary
At the end of the plan a judge opens a public page with no account and sees the GMN cameras that run with no partner, takes any one down, opens a country, follows a witness chain, reads a station's last 12 months and copies an introduction for the mailing list. An agent asks the same questions over MCP and the CLI opens the store from its GitHub Release URL; all three read the same Cypher files. The unit that unblocks the demo is U1 (the store), then U3 (the queries) and U5 (the page).

## Key technical decisions
- One set of Cypher files read by the page, the MCP server and the CLI — chosen over per-adapter query strings because the three must give equal rows (QA-05). settled: user-approved (ADR-0001)
- Monthly slices in one `gmn.rl`; the page data is exported by querying that store — chosen over JSON built straight from GMN because the page must show only what the store holds. settled: user-approved (ADR-0002)
- Closed months published as GitHub Release assets with a fixed October 2026 fixture committed — chosen over committing the store monthly because git history would grow by the whole file each month. settled: user-approved (ADR-0007)
- Own MCP server with named tools on `relate-db==1.2.0` — chosen over Relate's built-in `read_cypher` because R7 asks for named tools. settled: user-approved (ADR-0003)
- Islands, cut points, same-site groups, moved codes, "could pair" and nearest islands computed by the loader and stored in the graph — chosen over all-live Cypher because the cut-point query ran over 10 min in spike S4. settled: user-approved (ADR-0004)
- Graph built from measured pairs (orbits), runs in the browser on Relate WASM, no LLM inside the product, introductions by station code posted by the operator, twelve monthly slices. inherited from BRIEF
- Relate WASM 1.2.0 files copied into `site/vendor/relate-wasm/` — chosen over a CDN because the demo must not depend on a third party during judging. plan-time
- Data window November 2025 → October 2026; November 2026 is added on 2026-12-15, once GMN has settled the month (ADR-0007). plan-time
- Tests with Python `unittest` and `node --test`; no test framework added. plan-time
- Page as plain HTML, CSS and ES modules with no build step. plan-time
- Languages: Cypher (queries), Python 3 stdlib (loader, tests), Python 3 + `relate-db` (MCP), JavaScript + HTML/CSS (page), YAML (workflows). plan-time

## Units
### U1. Monthly loader into the released store
- **Goal:** one command downloads a month of GMN trajectories, station coordinates and the per-night upload index and writes that month's slice into `gmn.rl` (stations, countries, months, `SHARED` pairs with meteors, two-station count and up to three trajectory IDs, `STATS` per station); a rebuild command produces the 12-month store; a closed month is uploaded as the asset of a GitHub Release `store-<YYYYMM>` and listed in `data/months.json`; the October 2026 fixture is committed once
- **Covers:** R1, R6 · F3
- **Files:** `load/build.py`, `load/gmn.py`, `store/gmn-202610.rl`, `data/months.json`, `.gitignore` (`store/gmn.rl`), `tests/test_load.py`
- **Notes:** write with batched `UNWIND $rows` and an index on `Station.code`, 1,000 rows per statement and one transaction per batch (Relate ADR-0155: one statement per node is quadratic; issue #322: a single commit over 64 MB of WAL fails); never match on `id()`; delete the old `.rl` first, then `flush()` and `close()` so the zip is complete. `CREATE INDEX` only registers a name in Relate (ADR-0040); property lookups use automatic indexes. Parse `traj_summary` with the `;` delimiter, strip each field (the writer uses `"; "` and ends lines in `"\n\r"`), skip `#` lines; the station list is the last column and already excludes stations the solver set aside (`ignore_station`); columns are read by position (stations at 85 of 86) and a changed count fails loudly, and reading the two-row header by name is U14; a code with a `_<n>` suffix is the same camera listed twice and is folded into its base code (13 rows in October, D27)
- **Depends on:** —
- **Status:** done
- **Tests:**
  - happy: October 2026 files → the `SHARED` weight between two stations equals the count of trajectories in `traj_summary_monthly_202610.txt` whose participating stations include both. Covers AE1.
  - happy: a fresh clone with no network and no keys → the CLI answers a take-down from the committed `store/gmn-202610.rl`. Covers AE5.
  - happy: spike S8 first → `relate --load` on a test release URL answers a take-down; if not, the README downloads with `curl -L` and opens the local file (ran 2026-11-25: refused by Relate; the fixture's blob URL and Pages serve `--load`)
  - happy: `build.py --rebuild 202610` then `--release 202610` → a release `store-202610` whose `gmn.rl` holds 12 months, `data/months.json` lists it, and no `.rl` but the fixture is tracked (ran 2026-11-25: 12 months, 31.1 MB; rebuilt 2026-11-26 after the `_2` fix: 30.9 MB, 25,442 October pairs; November follows on 2026-12-15, once GMN has settled the month)
  - edge: a month already in the store is loaded again → its slice is replaced, the other months are unchanged
  - happy: `--partial` on 2026-11-25 → the latest month is `202611` with `partial: true` and `as_of: 2026-11-25`, its counts equal that day's `traj_summary_monthly_202611.txt`, the 12 closed months, the latest release and the committed fixture are unchanged. Covers AE23.
  - edge: a station in the trajectories but missing from the coordinates file → stored with null position, not dropped
  - edge: a row that lists the same station twice → counted once; `ES001` never matches `ES001G` (exact codes, station list read from column 85)
  - error: a trajectory file with a column count other than 86 → non-zero exit naming the count, store untouched
  - edge: a row listing `ES0002` and `ES0002_2` → one station, the pair counted once and no `_` code in the store
  - happy: `--release` of a tag that already exists → the asset is replaced (`gh release upload --clobber`) and the manifest keeps one entry

### U2. Graph properties computed by the loader
- **Notes:** islands and cut points in one iterative Tarjan pass (no recursion), O(N+E), with DFS subtree sizes: dedupe parallel edges, update the parent's `low` and size when the child is popped, a root needs two DFS children, use `disc[w]` for back edges; store both `cut_off` (stations outside the largest remaining piece) and the smallest piece, and keep whichever gives US004L = 86. A node-removal BFS is O(N²·(N+E)) and is not used. "Could pair": the first `<Polygon>` of each KML is the 100 km footprint, lon,lat order, ring not closed, longitudes may pass ±180, may be non-convex; score overlap by sampling points with ray-casting point-in-polygon, not by clipping, and report it in km² (an area in square degrees favours high latitudes, D26). The upload index stamp is the night's recording start, about 17 h before the upload (D26): late, dark and silent count 36 h, 3 days and 7 days from the stamp plus that offset, measured once against weblog `Last updated`. WesternMeteorPyLib's `stationsCommonVolume` (MIT) is the 3D reference, too slow to run per station
- **Goal:** after writing a month, the loader stores per station `island`, `cut_off`, `site` and `status` (including `possibly_moved`), plus `COULD_PAIR` (marked estimate) and `NEAREST_ISLAND` relationships, all readable with Cypher
- **Covers:** R8, R10, R11, R12, R14
- **Files:** `load/graph.py`, `load/geometry.py`, `tests/test_graph.py`
- **Depends on:** U1
- **Status:** done (2026-11-27: fixture 14.1 MB, `store-202610` 36.2 MB; the CLI caps reads at 100 rows under an agent harness, so every read passes `--max-rows 0`)
- **Tests:**
  - happy: October 2026 → US004L has `cut_off` = 86 and the 86 stations still share meteors among themselves. Covers AE8.
  - happy: September and October 2026 → 46 stations have status `stopped` and NZ002C lost 408 shared meteors. Covers AE10.
  - happy: October 2026 → Spain and Portugal form an island apart from Europe, with its nearest camera pair about 470 km away. Covers AE11.
  - edge: two cameras at the same site that share meteors → counted as each other's partners; `site` only groups them for display
  - edge: a code that stopped while a new code started within the same-site distance → `possibly_moved`, not `stopped`
  - error: a station with no pointing data → no `COULD_PAIR` for it, no crash
  - happy: ES000C with the 100 km polygons from `kml_fov` → at least one `COULD_PAIR` whose `fov_date` is the fetch date. Covers AE14.
  - edge: a station with no `<CODE>-100km.kml` → no `COULD_PAIR`, `fov100` null
  - edge: two cameras 3 km apart, or 700 km apart, with overlapping polygons → no `COULD_PAIR` (solver range 5–600 km)
  - edge: the current month with a station whose last index stamp is 40 h old → still running (a healthy camera before its next upload); 3 days old → `late`; 4 days old → `dark`; 8 days old → `silent`
  - edge: a camera that re-uploads ten old nights in one day → each night counted on its own date, so it is not shown as running every night
  - edge: a 100 km polygon whose ring crosses itself → overlap still scored, no crash
  - edge: a closed month shown with a pointing entry newer than that month → `COULD_PAIR` marked `aim_changed`
  - error: the `kml_fov` listing returns fewer than half the previous polygons → the previous polygons stay
  - error: `kml_fov` times out → the previous polygons and `fov_date` stay, the loader still writes the month

### U3. Query module and the brief's numbers
- **Goal:** every question is one `queries/<name>.cypher` file (lonely cameras, take down, country, changes, could turn, talk to, chain, station history, country history, search); a test runs each through the CLI on the committed October 2026 fixture and anchors the brief's numbers
- **Covers:** R2, R3, R4, R13, R16, R19
- **Files:** `queries/*.cypher`, `tests/test_queries.py`
- **Depends on:** U1, U2
- **Status:** done (2026-11-27: also touched `load/` for `three_station_orbits`, `Month.sigma2_median`/`sigma3_median`, Country `STATS`, every known station and `LINK`, the newest month's pairs the chain walks because `shortestPath` takes no month filter; queries return codes, the adapters map them to text)
- **Tests:**
  - happy: take down a station that is another station's only partner → that station is listed as losing its only partner. Covers AE2.
  - happy: take down HU000B → 899 orbits lost and at least one trajectory ID per affected partner. Covers AE3.
  - happy: search "BR" → the Brazilian stations. Covers AE4.
  - happy: look up stations → "no data uploaded", "running, no partner" or "uploaded, zero detections" by the index, without claiming why. Covers AE7.
  - happy: Spain → its two-station share equals the count over the October file. Covers AE9.
  - happy: take down a third witness → the shown uncertainty equals the median of the month's three-station trajectories. Covers AE12.
  - happy: lonely cameras → ES000C with 31 nights and 1,797 detections. Covers AE13.
  - happy: the README's queries → HU000B 899, ES000C running with no partner, 46 stopped, US004L 86. Covers AE16.
  - happy: chain between a Spanish and a German station → "no chain: different islands" naming both. Covers AE20.
  - edge: a station code that does not exist → empty rows, not an error
  - error: a query file with a syntax error → the test names the file and Relate's message

### U4. Page data exported from the store
- **Goal:** the loader exports `site/data/stats.json` (12 months of station and country stats) and `site/data/pairs-<YYYYMM>.json` for the latest two months by running queries on `store/gmn.rl`; CI fails if the tracked repo passes 50 MB
- **Covers:** R6, R16
- **Files:** `load/export.py`, `site/data/`, `tests/test_export.py`
- **Depends on:** U3
- **Status:** done (2026-11-27: `site/data/` is git-ignored build output, ADR-0002 amended; `site/cypher/*.cypher` rebuilds the graph in `:memory:`; the chain picks the strongest of the shortest paths and lists are ordered, so the page and the CLI give equal rows)
- **Tests:**
  - happy: export after loading October → every row in `pairs-202610.json` matches the same query on the store
  - edge: only one month in the store → no previous-month file, the page shows "no earlier month"
  - error: store over 50 MB → the size check fails with the size
  - edge: every exported position equals GMN's public 2-decimal value (no offset of our own; ADR-0005)

### U5. Page: lonely cameras, take-down and links
- **Goal:** the static page loads Relate WASM and the latest data, opens on the whole network's fragility (islands, the stations whose loss costs the most or cuts an island) with running cameras with no partner beside it, lets the user search and take any station down with its proof, gives every station and country its own link, and carries the language, theme and plain/technical toggles; the same queries on WASM return the CLI's rows
- **Covers:** R2, R3, R4, R5, R8, R13, R18 · F1, F3
- **Files:** `site/index.html`, `site/app.js`, `site/text.js`, `site/style.css`, `site/vendor/relate-wasm/`, `tests/page.test.mjs`
- **Notes:** no build step: `await init()`, `new RelateDb()`, fetch the JSON, load it with chunked `UNWIND $rows` (about 700 rows per statement), and `JSON.parse(db.execute(q, JSON.stringify(params)))` checking `.error`, since engine errors do not throw; recreate the instance after `isWasmTrap`. Vendor exactly `relate.js`, `relate_bg.wasm` (7.2 MB), `trap.js` and `snippets/relate-wasm-dd0c6225f894802b/js/opfs.js` from `@relate/relate-wasm@1.2.0` with its Apache-2.0 `LICENSE`, and patch `trap.js` with 1.3.0's regex ("too much recursion", "recursive use of an object") so Firefox traps are caught. No worker: paint a loading state, then load pairs in batches of about 5,000 positional rows, yielding between batches; add a worker only if a phone takes over 2 s. Add `?v=N` to data and query fetches (Pages caches for minutes). Chain queries use relationship types in the pattern, never `NONE()`/`WHERE` on edges
- **Depends on:** U4
- **Status:** todo
- **Tests:**
  - happy: open ES000C's link in a new page → ES000C shown running with no partner, 31 nights, 1,797 detections. Covers AE19.
  - happy: every pair shown for October 2026 carries `https://tammojan.github.io/meteormap/?data=2026-10&stations=<A>;<B>` with its two codes, `data` exactly 7 characters (another length sends the meteor map to a daily file and it loads forever), the map centred on the pair with `lat`, `lng` and `zoom` together, and the data's cut-off date beside the link
  - happy: the first screen shows 18 islands with US004L among the stations whose loss cuts an island, and beside them ES000C with the note that it still counts for flux and no claimed reason for having no partner. Covers AE13.
  - happy: each query file run on WASM with the page data → equal rows to the CLI on the store
  - edge: a link to an unknown station → a "not found" message with the search box
  - edge: the parity test of copy keys → every key in English and Spanish, every `_tech` with its `_plain`
  - error: WASM traps → the page shows a reload message and the CLI command
  - happy: every proof shown carries the GMN CC BY 4.0 credit with the site link
  - happy: the February 2026 store, US003Y taken down → US005V is left with no partner and its 8 shared meteors are shown. Covers AE27.

### U6. Country, changes, could turn and chain views
- **Goal:** the country view is also the monthly report (islands, cut points, single-partner and lonely cameras, two-station share, nearest island, printable and linkable); the change view lists stopped stations and what neighbours lost; "who could turn" lists nearby cameras with their aim marked as an estimate; the chain view shows the shortest chain between two stations
- **Covers:** R8, R10, R11, R12, R14, R15, R19 · F2, F5, F6, F7, F9
- **Files:** `site/views/country.js`, `site/views/changes.js`, `site/views/turn.js`, `site/views/chain.js`, `tests/views.test.mjs`
- **Depends on:** U5
- **Status:** todo
- **Tests:**
  - happy: ES000C → "who could turn" lists at least one installed camera with azimuth, elevation and the word "estimate". Covers AE14.
  - happy: Spain's country report → each number equals the matching query on the store. Covers AE15.
  - edge: a country with a single station → the report says it has no island of its own to split
  - happy: Spain's report → its groups add up to Spain's station count and its orbit total equals the distinct trajectories with a Spanish station, not the sum per camera
  - edge: a station first seen this month → listed as new, not as lost or lonely
  - error: the chain between two unknown codes → "station not found", not an empty chain

### U7. Talk to and the introduction message
- **Goal:** for a station, "Talk to" lists the stations its owner should contact with each reason, and builds an English message with station codes, numbers from the store and the station's link, ready to paste on GMN's mailing list
- **Covers:** R17 · F8
- **Files:** `site/views/talk.js`, `tests/talk.test.mjs`
- **Depends on:** U6
- **Status:** todo
- **Tests:**
  - happy: ES000C → at least one "could turn" camera with "estimate", the list copies as station codes with their reasons, and the optional message names ES000C and that camera with no value outside the store. Covers AE17.
  - edge: a message citing a pair carries that pair's meteor map link
  - happy: NZ002C with September and October → every stopped station that shared meteors with it in September, with "lost shared meteors" and the count. Covers AE18.
  - edge: a station with nobody to talk to → the message is not offered
  - error: the clipboard is not available → the message stays selectable in a text box

### U8. Twelve months of history
- **Goal:** the 12 real months (November 2025 → October 2026) are loaded; a station's history shows one row per month with nights, detections, orbits and partners and marks the month it lost a partner; a country's history shows its two-station share, lonely cameras and island changes per month
- **Covers:** R20, R21 · F10
- **Files:** `load/build.py`, `site/views/history.js`, `tests/test_history.py`
- **Depends on:** U5
- **Status:** todo
- **Tests:**
  - happy: ES000C's history → its October 2026 row shows 31 nights, 1,797 detections and 0 orbits. Covers AE21.
  - happy: Spain's history → 12 months listed, October's two-station share equals AE9's. Covers AE22.
  - edge: a station that started in June → no rows before June, not zeros
  - error: one month's file missing at GMN → the rebuild stops naming the month; the published store stays as it was

### U9. MCP server with named tools
- **Goal:** a stdio MCP server opens a local `.rl` read-only with `relate-db` (`--store`, default the October fixture `store/gmn-202610.rl`; the README shows `curl -L -o store/gmn.rl` of the release asset for 12 months) and exposes `lonely_cameras`, `take_down`, `country_report`, `who_could_turn`, `talk_to`, `witness_chain` and `station_history`, each running its query file and returning the query name, parameters and rows
- **Covers:** R7 · F4
- **Files:** `mcp/server.py`, `tests/test_mcp.py`, `docs/agent-run.md`
- **Notes:** a stdlib JSON-RPC loop with our named tools, handling: negotiate `protocolVersion` (2025-06-18, 2025-03-26, 2024-11-05), `-32700` on bad JSON, `-32602` for an unknown tool, `title`, `annotations` (`readOnlyHint` true), `outputSchema` and `structuredContent {query, parameters, rows}` plus a text copy, open the store once with `relate.connect(path, read_only=True)` and pass parameters as a dict, logs to stderr; the README also gives `relate serve --database store/gmn.rl --mcp stdio --read-only` as a zero-code fallback with Relate's own `read_cypher`
- **Depends on:** U3
- **Status:** todo
- **Tests:**
  - happy: a recorded agent run asks about HU000B → the tool's rows equal the page's take-down for HU000B. Covers AE6.
  - happy: every tool → equal rows to the CLI for the same query and parameters
  - edge: a tool called without `month` → the latest month
  - error: a tool called with an unknown station → an empty result with the station named, the expected format ("6-character GMN code like HU000B") and up to 3 similar codes, `isError` false
  - edge: a tool called without `month` → `parameters` carries the month it resolved, not an empty value
  - edge: months and nights are ordered by date, never by code or file name

### U10. README
- **Goal:** the README shows the architecture diagram (mermaid, rendered by GitHub: GMN → loader → release `gmn.rl` → queries → page / MCP / CLI), says the store uses single-file `.rl` mode and why, what the graph models and cannot know, the judge's one command (`relate --load` of the October fixture's blob URL, and of Pages' `gmn.rl` for 12 months) and first take-down, `curl -L` of the release asset for offline use, and the CC BY 4.0 citation
- **Covers:** R9 · F3
- **Files:** `README.md`, `tests/test_readme.py`
- **Depends on:** U3
- **Status:** todo
- **Tests:**
  - happy: the README's command on a fresh clone with no keys → a take-down answer. Covers AE5.
  - happy: the README's queries → HU000B 899, ES000C running with no partner, 46 stopped, US004L 86. Covers AE16.
  - edge: the README has a mermaid block naming the components of `docs/ARCHITECTURE.md`
  - edge: the README has a "Works with the meteor map" section crediting GMN's meteor map
  - error: a number in the README that differs from the test's result → the test fails naming it

### U11. Deploy to GitHub Pages
- **Goal:** `site/` is published on GitHub Pages at a public URL that opens without a login, and the URL is in `PENDING.md`; the same workflow runs daily on a schedule, loads the current month with `--partial` and publishes the page data and `gmn-latest.rl` without committing them, starting from the latest release's `gmn.rl`, which it also publishes unchanged as Pages' `gmn.rl` for `relate --load` (S8); a monthly workflow (day 15) runs `build.py <previous month>` with `permissions: contents: write`, creates the release and commits `data/months.json`
- **Covers:** R5 · F3
- **Files:** `.github/workflows/pages.yml`, `.github/workflows/monthly.yml`, `PENDING.md`
- **Depends on:** U5
- **Status:** todo
- **Tests:**
  - happy: push to main → the public URL serves the page whose title is "Second Witness"
  - happy: the scheduled run → the page shows the current month as partial with today's date, and `gmn-latest.rl` answers a take-down with `relate --load`
  - happy: a manual run of the monthly workflow for 202611 → a release `store-202611` exists and `data/months.json` names it
  - edge: the monthly workflow before day 15 of the next month → it does not release the month
  - edge: a closed month in the window whose `Last-Modified` changed since the last release → the store is rebuilt and the latest release is replaced
  - edge: the daily job with an unchanged `ETag` → no download, the page keeps the same data
  - edge: the page opened on a phone width → no horizontal scroll
  - error: the data files missing from the deploy → the page shows "data not found" and the workflow fails its content check

### U12. CI and uptime
- **Goal:** every push runs the gates of `## Commands`; a scheduled job checks the public page, Pages' `gmn.rl` and the release URL `releases/latest/download/gmn.rl` every 6 h and goes red if either stops answering with its own content
- **Covers:** —
- **Files:** `.github/workflows/ci.yml`, `.github/workflows/uptime.yml`, `load/gmn.py`, `load/build.py` (`Month.generated` from the file's `# Summary generated on` line)
- **Depends on:** — (CI); U11 (uptime)
- **Status:** todo
- **Tests:**
  - happy: push to main → CI green; manual run of uptime → green
  - error: the page serves a 404 page or the store URL answers without the `.rl` bundle → uptime red
  - error: the page's `as_of` is more than 2 days old → uptime red
  - error: `as_of` is today but `Month.generated` is more than 2 days old (GMN stopped updating) → uptime red

### U13. Why a camera is lonely, partner lines and last night
- **Goal:** the loader reads GMN's nightly camera summaries, the weblog status per country and yesterday's daily trajectory file, and stores a probable `cause` per station and last night's pairs; the page shows the cause on a station, draws lines to its partners on the map and lists last night's pairs with the new ones marked; the MCP's `lonely_cameras` and `take_down` return `cause`
- **Covers:** R22, R23, R24
- **Files:** `load/gmn.py`, `load/build.py`, `queries/last_night.cypher`, `queries/lonely_cameras.cypher`, `queries/take_down.cypher`, `site/views/station.js`, `site/views/map.js`, `site/views/last_night.js`, `tests/test_cause.py`, `tests/last_night.test.mjs`
- **Notes:** summary path from fields 1 and 2 of the per-night upload index (`<CC>/<CAM>/<CAM>_<stamp>_detected/`), about 1,400 files of 1.8 KB a day; country list from `status/Rmsindexes/country_dataset.json`; summary values are strings (`"False"`); the cause rule is one pure function with the order decommissioned > upload failure > clock > partial night > cloudy > old calibration > unknown, mapping all ten weblog statuses (D24; "Cloudy weather" is green on GMN's page, "Check calibration" is old calibration, an upload failure across a whole country is GMN's server, D27), and "recalibrated" is not "converged"; the night folder comes from `latest/index.html`, whose links carry a double slash (`weblog//`); one stack image (`<P>_captured_stack.jpg`) is shown as evidence only on the station view, loaded on open, never in lists, since GMN's images answered 429 while JSON answered 200; `SHARED_NIGHT` lives only in `gmn-latest.rl`; the daily file is cut by 1° of solar longitude, not by UTC day (D25), so the view's label is the min and max "Beginning UTC Time" of its rows, never "yesterday"; each cause links `weblog/<CC>/<CODE>/latest/`, a 404 there is `no_data` (not dark), about 1,000 dropped frames a night are normal (D27) and never a cause, and `cloudy` is ruled out on a night a partner within 100 km triangulated; the partner panel adds distance and bearing and the map draws `fov100` of the station and its partners, one point per `site` and lines split at ±180°; a camera with detections but no trajectory in the 12-month window is `not_in_pipeline`; a weblog "cloudy" contradicted by the camera's own detections that night is not taken as the cause
- **Depends on:** U2, U3, U5, U11
- **Status:** todo
- **Tests:**
  - happy: a summary with `clock_synchronized: "False"` for a station running with no partner → cause `clock` with the night and URL. Covers AE24.
  - edge: no summary for the night (404) → cause `unknown`, the load goes on
  - edge: weblog says "Decommissioned" and the summary has a bad clock → `decommissioned` (order of the rule)
  - happy: ES001G picked on October 2026 → one line to ES0013 labelled 144, partner count equal to the take-down's. Covers AE25.
  - happy: `--partial` with a sample `traj_summary_yesterday.txt` → last night's pairs equal the file's, pairs absent from October marked new. Covers AE26.
  - edge: a sample daily file whose trajectories cross UTC midnight → the label names both dates
  - error: the weblog times out → causes keep the previous day's value and the job does not fail
  - edge: weblog says "Cloudy weather" but a partner within 100 km has trajectories that night → cause is not `cloudy`
  - edge: `latest/index.html` answers 404 → `no_data`, not `dark`
  - edge: each of the ten weblog statuses → one cause or `unknown`, never a crash
  - edge: a camera whose only detections fall in the last incomplete nights of the partial month → `pending`, not lonely
  - edge: a camera with detections every month and no trajectory in 12 months → `not_in_pipeline`, listed apart from running with no partner
  - edge: weblog says "Cloudy weather" and the camera recorded detections that night → cause is not `cloudy`
  - edge: a daily file with `\n\r` line endings → same pairs as with `\n`

### U14. Column check by header name
- **Goal:** the loader reads the two `#` header lines of each trajectory file and checks that the columns it uses (the trajectory ID and `Participating stations`) sit where it reads them, so a reordered layout with 86 columns stops the load instead of writing a wrong graph
- **Covers:** R1, R6
- **Files:** `load/gmn.py`, `tests/test_load.py`
- **Notes:** names repeat (`Beginning`, `IAU`) and are split over two lines, so match the joined name of the used columns only; keep the 86-column check; see D26
- **Depends on:** U1
- **Status:** todo
- **Tests:**
  - happy: October 2026 → the check passes and the store equals the current build
  - error: a file with 86 columns whose `Participating stations` moved → non-zero exit naming the column, store untouched
  - edge: the four `#` lines (names, units, a dashed rule), `Summary generated on` with or without `+00:00`, and `nan`, `None` or `...` in unused fields → loads; a renamed unused column → a warning, not a stop

## Cut line
| Tier | Units | Why |
|---|---|---|
| must | U1, U2, U3, U4, U5, U6, U7, U8, U9, U10, U11, U12 | user-directed: all twelve ship by the deadline; with 435 h left, the margin for video, submission and deck is kept by building in dependency order and stopping at U12 before polishing |
| must | U14 | the column check by name closes a silent wrong-graph risk found by two reviews (D25, D26); about 1 h |
| should | U13 | added after the web review of 2026-11-25 (D23, D24); built only after U12, and R24 is the first to drop if time runs short |
| cut | — | every R1–R24 is covered |

## Risks
- Downloading 12 real months (59–118 MB of trajectories each; November 2025 is 87 MB) and an older month with a different layout — likelihood: baja (checked on 2026-11-23: November 2025 and May 2026 both have 86 columns) — mitigation: load month by month with the column check of U1 and cache downloads under `research/raw/` — fallback: a shorter window, stated in the README and BRIEF
- The MCP server needs Python and `relate-db` on the judge's machine — likelihood: media — mitigation: the README gives the install line and a recorded agent run in `docs/agent-run.md` — fallback: the CLI command and the page answer the same questions
- A slow phone loading 2.5 MB of WASM plus the data — likelihood: media — mitigation: load the latest month first and the rest on demand — fallback: the README's screenshots and the CLI command
- The mailing list answers after the deadline or not at all — likelihood: alta — mitigation: the BRIEF keeps the assumptions marked as unconfirmed — fallback: the submission cites the list threads (D9–D16) instead of replies
- GMN's `kml_fov` is slow (listing 11 s on 2026-11-25, over 120 s for another client) — likelihood: media — mitigation: fetch each `<CODE>-100km.kml` by name (0.8 s) and use the listing only for dates — fallback: keep the previous polygons with their date
- Relate WASM traps on a query in front of the camera — likelihood: baja — mitigation: the parity test runs every query on WASM in CI — fallback: the page shows the reload message and the CLI command

## Out of scope
- Where to put a new camera; more than 12 months; other networks (EDMOND, FRIPON) — deferred by the BRIEF
- Orbit quality, meteor showers and any science on the meteors; changing anything in GMN or in a station; telling a cloudy night from a broken lens; storing operators' names or contacts or sending messages — outside this product (BRIEF)
