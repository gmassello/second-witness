# Second Witness — Brief

## Summary
Second Witness shows the volunteers who run the Global Meteor Network which of their cameras are working alone and which ones the network depends on. It opens on the cameras that detect meteors every night but that no other camera confirms, so none of their meteors becomes an orbit. From there a coordinator can take any camera down and see who loses their only partner and how many orbits a month disappear, or see which installed neighbour could turn its camera to pair with a lonely one. Every answer is a Cypher query on an embedded Relate graph that runs in a browser tab, and a coding agent can ask the same over MCP.

## Problem frame
A meteor only gets an orbit when two or more stations see it, so a GMN camera is worth what its partners are worth. More witnesses also make a better orbit: in October 2026 the median velocity uncertainty was 0.311 km/s with two stations, 32% lower with three and 69% lower with five or more. Coordinators write every year that cameras are still waiting for partners and that cameras stop reporting, but nothing shows the network as a network. GMN's own Status page answers a geometric question per point of the map (how many fields of view cover this spot) and flags inactive cameras. It does not show which stations actually confirm each other, which ones run every night with nobody to confirm them, which one is the only partner of another, or what a region loses when one goes dark. Today operators plan overlap by comparing KML files by hand, and a decommissioned camera's cost to its neighbours is invisible until their orbit counts drop.

## Discovery
- D1. Coordinators state the pain in GMN's annual reports, year after year: "Many sites and participants are still waiting to find partners to improve the coverage on their cameras", and "some lonely cameras in Queensland and New South Wales wait for multi-station partners" — https://www.emeteornews.net/2026/02/06/global-meteor-network-report-2025/ · https://www.emeteornews.net/2023/02/11/global-meteor-network-report-2022/
- D2. Cameras drop out without anyone seeing who it hurts: in 2025, 96 cameras that reported in 2024 stopped, and in Russia "14 of the formerly active cameras were decommissioned" — https://www.emeteornews.net/2026/02/06/global-meteor-network-report-2025/
- D3. Overlap is planned by hand today: operators are told to "point new cameras in function of optimal coverage with other cameras" and to "compare kml files at the same elevation (e.g. 100km)" — https://www.emeteornews.net/2024/02/06/global-meteor-network-report-2023/
- D4. The existing tool is geometric and per point: Status v2's experimental FOV Analysis finds "points that fall within the selected Fov of at least the minimum number of actve cameras" and flags cameras with no detections for 14 or 30 days. It does not list co-observing pairs, stations without a partner, single points of failure, or what is lost when a station goes down — https://globalmeteornetwork.org/status/help2.html
- D5. The population is counted: 1,365 cameras contributed orbits in 2025 (236 new), 1,621 cameras ever, about 40 countries, 966,063 orbits that year — https://www.emeteornews.net/2026/02/06/global-meteor-network-report-2025/
- D6. The data is open and refreshed every 6 hours: "The data are released under the CC BY 4.0 license", with a request to cite the site and two papers (Vida et al. 2020, 2021). Each trajectory row lists its "Participating stations" — https://globalmeteornetwork.org/data/
- D7. Nobody else in the contest works on meteors or astronomy: 57 gallery entries and 143 Relate repos read on 2026-11-21 — https://relate.devpost.com/project-gallery (competitor survey kept outside the repo until judging ends)
- D8. GMN has no live API, CLI or MCP for network data: its Datasette platform answered 503 on 2026-11-21 and the `gmn-python-api` package depends on it. What it does publish are static files with open CORS: the location and aim of 1,904 stations, and a per-country, per-night index of which stations uploaded and how many detections each had — https://globalmeteornetwork.org/data/kml_fov/GMN_station_coordinates_public.json · https://globalmeteornetwork.org/status/Rmsindexes/country_dataset.json

## Impact
- **Persona**: a GMN national coordinator, or an operator deciding where the next camera in their country goes, like the coordinators who list "lonely cameras" by region in each annual report (D1); `sin contactar`
- **Pierde hoy**: "a camera in my region went quiet and I only noticed when my neighbour's orbits dropped": cameras that film meteors every night for nothing, orbits that nobody can confirm, and new cameras pointed by guesswork
- **La cifra**: in October 2026, 1,431 stations uploaded data and 115 of them detected meteors but shared none with another station, so none of their detections became an orbit; ES000C uploaded all 31 nights with 1,797 detections and zero orbits. Between September and October 67 stations stopped appearing; in September they had been one of the two witnesses of 1,228 orbits, and 629 neighbours lost meteors they used to share with them (NZ002C lost 408). Of the 126,593 orbits of October, 62,267 (49.2%) rest on exactly two stations; HU000B is the second witness of 899. The network is 18 islands that never confirm each other, and one station, US004L, is the only link between 86 stations and the rest of North America. Measured with `research/measure.py`; the figures are in `research/metrics-202610.json`
- **Despues del evento**: offer the monthly country report to the GMN coordinators on their mailing list, as a page they can open without installing anything

## Safety
- **Accion irreversible**: `sin accion irreversible: Second Witness only reads GMN's public data and its own committed store; it writes nothing to GMN and contacts no operator`

## Demo surface
- **Que ejecuta el jurado**: on the public page, sees the cameras that work alone, picks one or types a station code or a country, and presses "Take it down" or "Who could turn"
- **Que resultado nuevo sale**: the stations that lose their only partner, the stations left with a single one, the orbits per month that lose their second witness, or the stations it alone was tying to the rest of the network, each with the path of shared meteors that proves it; for a lonely camera, the nearby installed cameras that could pair with it by turning, marked as an estimate
- **Que apuesta demuestra**: the network's real shape is in the orbits, not in the fields of view. Two cameras whose fields overlap on a map may never confirm a meteor (weather, aim, clocks), and two that look apart may confirm hundreds. Building the graph from who actually saw the same meteor turns a coverage map into a dependency graph that can say what breaks, and crossing it with what each camera uploaded separates a camera that is off from one that works and nobody confirms
- **Donde**: `sin superficie: not built yet; the PLAN decides the public URL`

## Actors
- A1. GMN coordinator or operator — looks up a station or a country and asks what depends on it
- A2. Judge — opens the page or clones the repo and runs a take-down without asking anything
- A3. Coding agent — asks the same question over MCP on behalf of a coordinator

## Requirements
- R1. Given a month of GMN trajectories, I get the graph of stations that saw the same meteor, weighted by how many meteors each pair shared [criterion: Effective use of connected context]
- R2. When I take a station down, I see which stations lose their only partner, which are left with one, how many orbits that month lose their second witness, and for how many it was the third witness that made the orbit more precise [criterion: Usefulness]
- R3. Every answer shows its proof: the shared-meteor count on each edge and a sample of the trajectory IDs behind it, so a coordinator can check it in GMN's own data [criterion: Clarity]
- R4. I find a station or a country by typing any part of its code or name [criterion: Effective use of connected context]
- R5. A judge opens the public page, or clones the repo and runs one command, and gets a take-down answer without an account, a key or a server [criterion: Completeness]
- R6. The graph is a persistent Relate store committed to the repo, rebuilt from GMN's public files by one documented command [criterion: Completeness]
- R7. A coding agent asks over MCP with named tools (take down, lonely cameras, country report) and gets the same answer as the page [criterion: Effective use of connected context]
- R8. The fragility of the whole network fits on one screen: its islands, the stations whose loss costs the most orbits or splits an island, the stations with a single partner, and the share of each country's orbits seen by only two stations [criterion: Creativity]
- R9. The README says which Relate mode the store uses and why, what the graph cannot know (a camera that uploads zero detections may face clouds or a broken lens), and how to run the first take-down [criterion: Clarity]
- R10. When I open a country, I see whether its stations confirm meteors with any neighbour country and which single station, if any, holds two of its regions together [criterion: Usefulness]
- R11. I see which stations stopped appearing since last month and what each one's neighbours lost [criterion: Usefulness]
- R12. I see which islands come closest to each other, measured between the cameras of each one [criterion: Creativity]
- R13. The first screen lists the cameras that upload detections but have no partner, apart from those that stopped uploading and those that upload zero detections [criterion: Usefulness]
- R14. For a running camera with no partner, I see which nearby installed camera could pair with it by turning, with both cameras' current aim, marked as an estimate [criterion: Creativity]
- R15. A coordinator gets one page per country for the month: islands, cut points, running cameras with no partner, cameras lost since last month and the third-witness count [criterion: Clarity]
- R16. Every number on the page and from the MCP tools comes from a Cypher query on the committed store [criterion: Effective use of connected context]

## Key flows
- F1. **Take it down** — A1 types a station code → picks it → presses "Take it down" → the stations that lose their only partner or drop to one, the orbits per month lost and the ones that lose their third witness, each with its shared-meteor path. (A1; R1, R2, R3, R4)
- F2. **Where is the network fragile** — A1 opens a country → which island it belongs to, which neighbours it confirms with and how far the nearest other island is, its share of two-station orbits, the stations whose loss costs the most orbits or splits the island, the ones with a single partner and the ones running with none. (A1; R8, R10, R12, R13)
- F3. **Judge check** — A2 opens the page or runs the one command against the committed store → a take-down answer appears → A2 opens the store and runs the README's Cypher query. (A2; R5, R6, R9, R16)
- F4. **Agent asks** — A3 calls the MCP tool with a station code → the same take-down answer as the page. (A3; R7)
- F5. **What changed since last month** — A1 opens the change view → the stations that stopped appearing, with the meteors each neighbour lost. (A1; R11)
- F6. **Who could turn** — A1 picks a running camera with no partner → the installed cameras nearby, with their current aim and the turn that would cross both fields at 100 km, marked as an estimate. (A1; R14)
- F7. **Country report** — A1 opens a country's monthly page → islands, cut points, lonely running cameras, cameras lost and third witnesses, in one page to share. (A1; R15)

## Acceptance examples
- AE1. **Covers R1.** Given the committed October 2026 store, when the judge queries the edge between two stations, then its weight equals the number of trajectories in `traj_summary_monthly_202610.txt` whose participating stations include both.
- AE2. **Covers R2.** Given a station that is the only partner of another station in the month, when the user takes it down, then that other station is listed as losing its only partner.
- AE3. **Covers R2, R3.** Given HU000B in the October 2026 store, when the user takes it down, then the orbits lost equal the count of two-station trajectories that include HU000B, and at least one trajectory ID is shown for each affected partner.
- AE4. **Covers R4.** Given the committed store, when the user types "BR", then the Brazilian stations are listed.
- AE5. **Covers R5, R6.** Given a fresh clone with no network and no keys, when the judge runs the documented command, then a take-down answer is printed from the committed store.
- AE6. **Covers R7.** Given the MCP server running on the committed store, when an agent asks about HU000B, then the answer equals the page's answer for HU000B, verified with a recorded agent run and not only a direct tool call.
- AE7. **Covers R9, R13.** Given a station in GMN's station list, when the user looks it up, then Second Witness says "no data uploaded" if it is absent from the month's index, "running, no partner" if it uploaded detections but shares no meteor, and "uploaded, zero detections" otherwise, without claiming why.
- AE8. **Covers R8, R10.** Given the October 2026 store, when the user takes US004L down, then 86 stations are shown as cut off from the rest of their island, and the answer says they still confirm meteors among themselves.
- AE9. **Covers R8.** Given the October 2026 store, when the user opens Spain, then its share of orbits seen by only two stations equals the count over `traj_summary_monthly_202610.txt` of Spanish trajectories with exactly two participating stations.
- AE10. **Covers R11.** Given the September and October 2026 stores, when the user opens the change view, then 67 stations are listed as stopped, and NZ002C is shown as having lost 408 shared meteors.
- AE11. **Covers R12.** Given the October 2026 store, when the user opens Spain, then Spain and Portugal show as an island separate from the European one, with its nearest camera pair about 470 km apart.
- AE12. **Covers R2.** Given the October 2026 store, when the user takes down a station that is a third witness, then the uncertainty shown for three-station orbits equals the median over the month's three-station trajectories.
- AE13. **Covers R13.** Given the October 2026 store, when the user opens the first screen, then ES000C is listed as running with no partner, with 31 nights and 1,797 detections.
- AE14. **Covers R14.** Given ES000C, when the user asks who could turn, then at least one installed camera nearby is listed with its current azimuth and elevation and the word "estimate".
- AE15. **Covers R15.** Given the October 2026 store, when the user opens Spain's country report, then each of its numbers equals the answer of the matching query on the store.
- AE16. **Covers R16.** Given the October 2026 store, when the judge runs the README's queries, then HU000B's 899 orbits, ES000C as running with no partner, the 67 stopped stations and US004L's 86 cut-off stations come out of Cypher on the store.

## Key decisions
- Global Meteor Network station pairs — chosen over the Backfocus adapter-chain solver, a DarkSky ordinance-precedent finder and an Astronomical League program planner, because GMN's helped group is counted in its own reports, its coordinators state the pain in writing (D1, D2), and the graph comes straight out of its open data. settled: user-approved
- Pairs measured from orbits, not inferred from fields of view — chosen over geometric overlap from the KML files, because that is what GMN's Status already does (D4) and because a measured pair is the only one that produced an orbit. settled: user-approved
- The take-down question is the product — chosen over "where should I point my new camera", because that answer is a geometric prediction and this one is measured; it reuses the blast-radius pattern already built in hindsight (`knowledge/hackathons/datahub-agent-hackathon/README.md`). settled: user-approved
- Running cameras with no partner as the first screen — chosen over opening on the take-down, because it is the finding a judge understands without knowing meteors, and the one a coordinator can act on today. settled: user-approved
- "Who could turn" — chosen over "where to put a new camera", because turning an installed camera costs nothing and uses the aim GMN already publishes; it stays marked as an estimate because it is geometry, not a measured pair. settled: user-approved
- Two calendar months as the graph window, the current and the previous — chosen over a single day or a year, because a day leaves stations unpaired by weather (71 single-partner stations in the one-day file downloaded on 2026-11-21, against 28 in all of October 2026), a year hides cameras that already went dark, and comparing two months is what shows who stopped. settled: user-approved
- Sources are the monthly trajectories, the station coordinates and the per-night upload index, loaded into the committed store — chosen over GMN's Datasette platform, which was down (D8), and over reading GMN live from the browser, because the demo must not depend on GMN being up. settled: user-approved
- The questions are Cypher queries on the store — chosen over computing them in code and keeping Relate as storage, because the criterion measures how the product uses the graph; the scripts in `research/` only produced the evidence for this brief and are not part of the system. settled: user-approved
- No LLM inside the product; the agent is the user's, over MCP — chosen over a built-in assistant, because the answers are deterministic and a model adds nothing a number does not already say. settled: user-approved
- Runs in the browser on Relate's WebAssembly build, with the same store usable from the CLI and MCP — chosen over a hosted server, because judges must run it "without asking you anything" and the DataHub entry did best when it could be checked without installing anything (`knowledge/hackathons/datahub-agent-hackathon/README.md`). settled: user-approved
- Name: Second Witness — a meteor needs a second witness to get an orbit. settled: user-approved

## Scope boundaries
### Deferred
- Where to put a new camera — needs an estimate of the pairs a camera that does not exist yet would make; "Who could turn" is the base it would build on
- A history longer than two months — two months answer who stopped; trends need a store per month
### Outside this product
- Orbit quality, meteor showers and any science on the meteors themselves — those are properties of the trajectory, not of who saw it; the orbit uncertainty is used only to weigh a third witness
- Changing anything in GMN or in a station's software — Second Witness reads public data; acting on its answer is the coordinator's call
- Telling a cloudy night from a broken lens — both upload zero detections, so the index cannot hold that difference

## Assumptions
- GMN's monthly trajectory file keeps its column layout, with "Participating stations" as the last column. If it changes, the build command fails loudly instead of building a wrong graph.
- The fourth field of each row in the per-night upload index is the number of detections that night (ES0001 shows 0 and ES0005 shows 118 on 2026-10-20). GMN does not document it. When a station uploads more than one folder in a night, the folder with the most detections counts.
- A station's position and aim are its latest entry in the coordinates file dated on or before the last day of the month.
- "Who could turn" crosses the two fields of view at 100 km, the height GMN recommends for comparing coverage (D3). It is an estimate, not a pair that produced an orbit.
- Two-station trajectories are a fair proxy for "orbits that depend on a station": a third station might have seen the meteor without making the solution, and that is not counted.
- A cut point measures connection, not lost orbits: the 86 stations behind US004L keep confirming each other. A country's share of two-station orbits also reflects how many cameras it has and how they are aimed, not only fragility.
- Coordinators would use a per-station take-down answer. Nobody at GMN has been asked; the mailing list (https://globalmeteornetwork.groups.io/g/main) is where to ask, and its pages returned 402 to automated reads.

## Outstanding questions
- Does GMN already compute the station co-observation network internally? — blocks: R8 | resolve before planning: no
- Which answers run as live Cypher and which are precomputed into the store at load time (most likely the cut points of the whole network)? — blocks: R16 | resolve before planning: yes
