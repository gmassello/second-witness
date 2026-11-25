# Outreach — validating Second Witness with GMN

- **Channel**: https://globalmeteornetwork.groups.io/g/main (new topic, posted by the author)
- **Posted**: 2026-11-23, new topic "Would a "who confirms whom" view of the network help?", signed German; approved by the moderators as #16511; six replies and our answer by 2026-11-25
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

- **#16512, Ferran Casarramona, 2026-11-24**: is thinking of turning his camera from south to north, because the Moon interferes and to overlap more with other stations; asks whether it is worth the effort and whether he needs new IDs. An operator asking the R14 question ("which camera could turn to pair") in reply to the post.
- **#16513, Peter McKellar, 2026-11-24**: no new ID; only a new calibration of the new patch of sky after a night with a full frame of stars, and the list helps if needed.
- **#16514, Mark McIntyre, 2026-11-24**: IDs are country- and camera-specific and do not change when the camera moves within the same country (a new country means a new prefix); a new pointing needs a new platepar (SkyFit2); pointing north would overlap more, though mountains may block the view.

- **Our reply to #16512, 2026-11-24**: asked Ferran for his station codes to show, from October's data, his partners with shared meteors and sample trajectory IDs, and how many of his orbits rest on two stations; said the tool cannot predict a new pointing but can compare the first full month after the turn; disclosed the hackathon (ends December 11) and the MIT repo.
- **#16516, Peter Murray, 2026-11-24**: tells Ferran his station is to Ferran's west (ES001J and ES001L) and that he is setting up a new camera, ES001N, pointing toward Ferran, waiting for good data to make its platepar: "Nice to put a name to local stations."
- **#16517, Mark McIntyre, 2026-11-24**, answering questions 1, 2, 3 and 5:
  - Q1: cameras without a partner "would be interesting", but the number of unmatched detections "would not necessarily tell us much": a camera can fail to match because of miscalibration, a bad mask or weather, and part of the unmatched events are not meteors. RMS also measures meteor flux, which needs no matching and matters to users in the space sector.
  - Q2 and Q3: "might be useful", but not all operators are on the list and only Denis has the full list of camera owners; UKMON has contacts for about 90% of UK cameras, none for the European cameras that could pair with eastern UK.
  - Q5: no. Co-located cameras point in different directions and rarely see the same meteor (his four in Oxfordshire rarely overlap). The solver considers all pairs more than 50 km apart, so two co-located cameras may both be kept when a third camera is more than 50 km away.
- **#16524, Ferran Casarramona, 2026-11-25**: his cameras are ES001G and ES001H; the meteormap in GMN's Meteor Trajectory Viewer already shows which stations confirm meteors with his cameras (mostly ES0019 and ES0013) in past periods; Peter's ES001N will add many trajectories, so he may wait for it; asks how much the Moon (or the Sun, for contrail detection) affects detection.
- **Analysis of #16517, 2026-11-25**: checked against October 2026's file. Same-site cameras rarely make an orbit alone (16 two-station orbits under 1 km), as Mark said; but 7,423 of 62,267 two-station orbits have stations under 50 km apart, so 50 km is not a hard limit in the data and no pair is dropped by distance. His doubt on talk-to is about reaching owners, so R17 now gives codes a coordinator can pass on.
- **Our reply to #16524, 2026-11-25**: October 2026 for Ferran's cameras: ES001G 144 orbits, all with ES0013 and 137 with ES0013 alone; ES001H 52 orbits with ES0013 (30), ES0019 (10), Peter's ES001L (9) and ES000U (5); meteor map link for ES001G + ES0013 (checked: 144 meteors).
- **Our reply to #16517, 2026-11-25**: unmatched detections dropped as a figure; same-site cameras kept separate (16 two-station orbits under 1 km in October); asked whether 50 km is a preference, given 7,423 two-station orbits (12%) under 50 km; talk-to gives codes a coordinator can pass on (219 of 235 UK cameras with a partner already share meteors with a continental camera); asked question 4 again.

Not answered yet: question 4 (the fourth Rmsindexes field).
