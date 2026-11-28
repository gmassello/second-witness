MATCH (c:Country {code: $country})-[cs:STATS {month: $month}]->()
OPTIONAL MATCH (s:Station {country: $country})-[t:STATS {month: $month}]->()
WITH c, cs, s, t
ORDER BY t.cut_off DESC, s.code
WITH c, cs, count(t) AS stations,
     sum(CASE WHEN t.status = 'paired' THEN 1 ELSE 0 END) AS paired,
     sum(CASE WHEN t.status = 'running_no_partner' THEN 1 ELSE 0 END) AS running_no_partner,
     sum(CASE WHEN t.status = 'uploaded_zero' THEN 1 ELSE 0 END) AS uploaded_zero,
     sum(CASE WHEN t.status = 'no_upload' THEN 1 ELSE 0 END) AS no_upload,
     collect(DISTINCT t.island) AS islands,
     collect(CASE WHEN t.cut_off > 0 THEN {station: s.code, cut_off: t.cut_off} END) AS cut_points,
     collect(CASE WHEN t.partners = 1 THEN s.code END) AS single_partner,
     collect(CASE WHEN t.change IN ['stopped', 'possibly_moved'] THEN {station: s.code, change: t.change} END) AS lost,
     collect(CASE WHEN t.change = 'new' THEN s.code END) AS new
OPTIONAL MATCH (a:Station {country: $country})-[e:SHARED {month: $month}]-(b:Station)
WHERE b.country <> $country
WITH c, cs, stations, paired, running_no_partner, uploaded_zero, no_upload, islands, cut_points, single_partner, lost, new, e, b
ORDER BY b.country
WITH c, cs, stations, paired, running_no_partner, uploaded_zero, no_upload, islands, cut_points, single_partner, lost, new,
     collect(DISTINCT b.country) AS neighbours, coalesce(sum(e.meteors), 0) AS cross_border_meteors
OPTIONAL MATCH (x:Station)-[n:NEAREST_ISLAND {month: $month}]-(y:Station), (x)-[tx:STATS {month: $month}]->(), (y)-[ty:STATS {month: $month}]->()
WHERE tx.island IN islands AND NOT ty.island IN islands
WITH c, cs, stations, paired, running_no_partner, uploaded_zero, no_upload, islands, cut_points, single_partner, lost, new,
     neighbours, cross_border_meteors, x, y, n, tx, ty
ORDER BY n.km, x.code
RETURN c.code AS country, c.name AS name, stations, cs.orbits AS orbits, cs.two_station_orbits AS two_station_orbits,
       cs.three_station_orbits AS three_station_orbits, cs.two_station_share AS two_station_share,
       cs.running_no_partner AS running_no_partner,
       {paired: paired, running_no_partner: running_no_partner, uploaded_zero: uploaded_zero, no_upload: no_upload} AS groups,
       islands, cut_points, single_partner, lost, new, neighbours, cross_border_meteors,
       collect(CASE WHEN n IS NULL THEN NULL ELSE {station: x.code, other: y.code, km: n.km, island: tx.island, other_island: ty.island} END) AS nearest
