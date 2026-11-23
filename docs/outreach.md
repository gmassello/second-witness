# Outreach — validating Second Witness with GMN

- **Channel**: https://globalmeteornetwork.groups.io/g/main (new topic, posted by the author)
- **Posted**: 2026-11-23, new topic "Would a "who confirms whom" view of the network help?", signed German; held for moderator approval (first post of a new member)
- **Figures**: `research/metrics-202610.json` (`liveness.running_no_partner`, `liveness.running_no_partner_top`, `multiplicity.2`, `two_station_share`)
- **List threads it builds on**: #16152 (unmatched detections not tracked), #16294 and #16295 (a lone camera asking for partners), #12017 and #14763 (coverage tools, which camera to fix first)

## Message

Subject: Would a "who confirms whom" view of the network help?

Hi all,

I'm building a small open tool on GMN's public data (CC BY 4.0) that looks at the network as pairs of stations that actually confirmed the same meteor, instead of overlapping fields of view.

A few things it found for October 2026:

- 115 stations uploaded detections but shared no meteor with any other station, so none of them became an orbit. One camera uploaded on all 31 nights, with 1,797 detections and zero orbits.
- 62,267 of the 126,593 orbits (49%) rest on exactly two stations, so losing either one loses the orbit.
- The network splits into islands that never confirm each other, and some single stations are the only link between a group and the rest.

Five questions before I go further:

1. In July (#16152) Mark mentioned that GMN doesn't track how many of a station's detections never become an orbit. Would coordinators and operators use that number per station and per country, together with the list of cameras that run with no partner?
2. Would it help to see, for one station, who loses their only partner if it goes dark, and which nearby camera could turn to pair with a lonely one?
3. Would operators use a suggestion of whom to talk to (by station code), with a short message to post here, to set up new pairs?
4. In the daily Rmsindexes JSON files, is the fourth field of each row the number of detections that night?
5. Should cameras at the same site count as a single witness when deciding whether a camera "has a partner"? As I understand it, RMS only keeps two co-located cameras in a solution when a third camera elsewhere saw the meteor too.

It only reads GMN's public files and sends nothing anywhere. Any feedback, including "we already do this", is very welcome.

Thanks,
German

## Replies

None yet.
