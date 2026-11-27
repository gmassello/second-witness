MATCH (c:Country {code: $country})-[cs:STATS {month: $month}]->()
OPTIONAL MATCH (s:Station {country: $country})-[t:STATS {month: $month}]->()
WITH c, cs, s, t
ORDER BY t.cut_off DESC, s.code
WITH c, cs, collect(DISTINCT t.island) AS islands, collect(CASE WHEN t.cut_off > 0 THEN s.code END) AS cut_points
OPTIONAL MATCH (a:Station {country: $country})-[e:SHARED {month: $month}]-(b:Station)
WHERE b.country <> $country
WITH c, cs, islands, cut_points, e, b
ORDER BY b.country
RETURN c.code AS country, c.name AS name, cs.orbits AS orbits, cs.two_station_orbits AS two_station_orbits,
       cs.two_station_share AS two_station_share, cs.running_no_partner AS running_no_partner,
       islands, cut_points, collect(DISTINCT b.country) AS neighbours, coalesce(sum(e.meteors), 0) AS cross_border_meteors
