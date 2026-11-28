MATCH (x:Station {code: $station})-[c:COULD_PAIR {month: $month}]->(p:Station)
RETURN p.code AS other, 'could_pair' AS reason, c.km2 AS n, c.km AS km, c.turn_deg AS turn_deg, true AS estimate,
       false AS was_only, $month AS month, NULL AS link
UNION ALL
MATCH (x:Station {code: $station})-[tx:STATS {month: $month}]->(), (x)-[s:SHARED {month: $month}]-(p:Station)
WHERE tx.partners = 1
RETURN p.code AS other, 'only_partner' AS reason, s.meteors AS n, NULL AS km, NULL AS turn_deg, false AS estimate,
       true AS was_only, $month AS month,
       'https://tammojan.github.io/meteormap/?data=' + substring($month, 0, 4) + '-' + substring($month, 4) + '&stations=' + x.code + ';' + p.code
       + CASE WHEN x.lat IS NULL OR p.lat IS NULL THEN '' ELSE '&lat=' + toString(round((x.lat + p.lat) / 2, 2)) + '&lng=' + toString(round((x.lon + p.lon) / 2, 2)) + '&zoom=7' END AS link
UNION ALL
MATCH (pm:Month)
WHERE pm.id < $month
WITH max(pm.id) AS prev
MATCH (x:Station {code: $station})-[s:SHARED]-(p:Station)-[tp:STATS {month: $month}]->()
WHERE s.month = prev AND tp.change IN ['stopped', 'possibly_moved']
OPTIONAL MATCH (x)-[tx:STATS]->(:Month {id: prev})
RETURN p.code AS other, 'partner_stopped' AS reason, s.meteors AS n, NULL AS km, NULL AS turn_deg, false AS estimate,
       coalesce(tx.partners = 1, false) AS was_only, prev AS month,
       'https://tammojan.github.io/meteormap/?data=' + substring(prev, 0, 4) + '-' + substring(prev, 4) + '&stations=' + x.code + ';' + p.code
       + CASE WHEN x.lat IS NULL OR p.lat IS NULL THEN '' ELSE '&lat=' + toString(round((x.lat + p.lat) / 2, 2)) + '&lng=' + toString(round((x.lon + p.lon) / 2, 2)) + '&zoom=7' END AS link
