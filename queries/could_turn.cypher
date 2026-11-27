MATCH (a:Station {code: $station})-[c:COULD_PAIR {month: $month}]->(b:Station)
MATCH (a)-[ta:STATS {month: $month}]->(), (b)-[tb:STATS {month: $month}]->()
RETURN a.code AS station, ta.az AS az, ta.alt AS alt, b.code AS other, tb.az AS other_az, tb.alt AS other_alt,
       c.turn_deg AS turn_deg, c.to_az AS to_az, c.km AS km, c.km2 AS km2, c.estimate AS estimate,
       c.aim_changed AS aim_changed, c.fov_date AS fov_date
ORDER BY km2 DESC, other
