MATCH (s:Station)-[t:STATS {month: $month}]->()
WHERE t.island IS NOT NULL
WITH t.island AS island, count(s) AS stations, collect(DISTINCT s.country) AS countries
ORDER BY stations DESC, island
WITH collect({island: island, stations: stations, countries: countries}) AS islands
MATCH (s:Station)-[t:STATS {month: $month}]->()
WHERE t.cut_off > 0
WITH islands, s, t
ORDER BY t.cut_off DESC, s.code
WITH islands, collect({station: s.code, cut_off: t.cut_off, island: t.island}) AS cuts
MATCH (s:Station)-[t:STATS {month: $month}]->()
WHERE t.two_station_orbits > 0
WITH islands, cuts, s, t
ORDER BY t.two_station_orbits DESC, s.code
WITH islands, cuts, collect({station: s.code, orbits_lost: t.two_station_orbits}) AS losses
MATCH (s:Station)-[t:STATS {month: $month, partners: 1}]->()
WITH islands, cuts, losses, count(s) AS single_partner
MATCH (c:Country)-[cs:STATS {month: $month}]->()
WHERE cs.orbits > 0
WITH islands, cuts, losses, single_partner, c, cs
ORDER BY cs.two_station_share DESC, c.code
RETURN islands, size(cuts) AS cut_point_count, cuts[0..20] AS cut_points, losses[0..20] AS top_losses,
       single_partner, collect({country: c.code, orbits: cs.orbits, two_station_share: cs.two_station_share}) AS countries
