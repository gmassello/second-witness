---
status: accepted
date: 2026-11-25
decision-makers: [German]
consulted: [the operator of ES001G and ES001H (GMN list #16524)]
informed: []
---

# 0005. "Could pair" from GMN's 100 km field-of-view polygons, and every pair's proof links to the meteor map

## Context and Problem Statement

An operator on the GMN list found his camera's partners in GMN's meteor map (BRIEF D21). Volunteer tools already draw GMN's data, among them the meteor map (GPL-3.0, a single static page). None counts pairs or models the network. R14 needs field-of-view geometry, R3 needs a proof a coordinator trusts, and the README must say how Second Witness relates to them. What do we take from them?

## Decision Drivers

* R3: proof checkable in GMN's own data and tools
* R14: "could pair" geometry, marked as an estimate
* C8, C9: GMN data is CC BY; no new dependencies; the repo is MIT
* BRIEF Safety: no exact camera position

## Considered Options

* A — draw our own map and compute fields of view from azimuth, elevation and field size
* B — link every pair to the meteor map, and cross GMN's own 100 km polygons (`kml_fov/<CODE>-100km.kml`) for "could pair"; the dated pointing history (`GMN_station_coordinates_public.json`) gives aim numbers and past months
* C — copy the meteor map's code or its `rms-sites.json`

## Decision Outcome

Chosen option "B", because the meteor map already shows a pair's meteors on a map that coordinators know, and GMN's polygons are the same ones both tools and Status draw, so "could pair" agrees with what operators see.

### Consequences

* Good: no map code; the proof opens in one click; the README credits both tools and positions Second Witness as the network view they lack.
* Bad: the polygons are a current snapshot with no history, so "could pair" for a past month uses today's pointing; the answer shows the polygon date.
* Bad: the proof link depends on a third-party page that takes about 40–50 s to open a month; the sample trajectory IDs stay as the proof that does not, and the demo does not wait on the link.
* To watch: the meteor map filters stations by substring and counts a repeated station twice; our counts match exact codes and deduplicate per row, so a number can differ from a count taken by hand on the map.

### Confirmation

- GET on 2026-11-25: the `kml_fov/` listing answered 200 in 11.3 s (593 KB, about 1,820 stations × 25/70/100 km); `ES001G-100km.kml` answered 200 in 0.8 s with one lon/lat polygon at 100 km and no azimuth. `GMN_station_coordinates_public.json` holds dated entries with `azim_center`, `alt_center`, `fov_w` and `fov_h` (ES001G: 2025-06-22, 127.6°, 36.0°).
- The meteor map reads `stations` (`;` = all listed) and `data` (7 characters = a monthly file) from the URL. Checked in Chrome on 2026-11-25: `?data=2026-10&stations=ES001G;ES0013` shows 144 meteors, equal to the count of October rows of `traj_summary_monthly_202610.txt` listing both stations; `ES001G;ES0019` shows 0, also equal. The page took about 40–50 s to load the month and fired about 1,800 field-of-view requests, many failing with `ERR_INSUFFICIENT_RESOURCES`, without affecting the count.
- Tests: U2 (`COULD_PAIR` from the polygons, timeout keeps the previous ones), U4 (positions moved up to 2 km), U5 (every pair carries its link), U7 (the message carries it), U10 (the README credits both tools).

## Pros and Cons of the Options

### A — own map and geometry

* Good, because no third party.
* Bad, because a map library is a new dependency and our footprints could disagree with GMN's.

### B — link and GMN's polygons

* Good, because no new code for maps, and the same geometry GMN publishes.
* Bad, because the polygons are current only.

### C — copy their code or station file

* Good, because ready-made.
* Bad, because GPL-3.0 code and a station file built from a private source cannot go into an MIT repo.

## More Information

Station positions follow the meteor map's practice: an offset inside 2 km. GMN's public file already rounds them to 2 decimals.
