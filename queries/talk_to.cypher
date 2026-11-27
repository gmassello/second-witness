MATCH (x:Station {code: $station})-[c:COULD_PAIR {month: $month}]->(p:Station)
RETURN p.code AS other, 'could_pair' AS reason, c.km2 AS n, true AS estimate, NULL AS month
UNION ALL
MATCH (x:Station {code: $station})-[tx:STATS {month: $month}]->(), (x)-[s:SHARED {month: $month}]-(p:Station)
WHERE tx.partners = 1
RETURN p.code AS other, 'only_partner' AS reason, s.meteors AS n, false AS estimate, $month AS month
UNION ALL
MATCH (x:Station {code: $station})-[s:SHARED]-(p:Station)-[tp:STATS {month: $month}]->(), (x)-[tx:STATS]->()
WHERE s.month < $month AND tx.month = s.month AND tx.partners = 1 AND tp.change IN ['stopped', 'possibly_moved']
RETURN p.code AS other, 'only_partner_stopped' AS reason, s.meteors AS n, false AS estimate, s.month AS month
