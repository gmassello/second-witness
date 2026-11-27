MATCH (c:Country {code: $country})-[t:STATS]->(m:Month)
RETURN m.id AS month, m.partial AS partial, t.orbits AS orbits, t.two_station_share AS two_station_share,
       t.running_no_partner AS running_no_partner, t.islands AS islands
ORDER BY month
