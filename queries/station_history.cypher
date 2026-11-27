MATCH (s:Station {code: $station})-[t:STATS]->(m:Month)
OPTIONAL MATCH (s)-[e:SHARED]-(p:Station)
WHERE e.month = m.id
WITH s, t, m, collect(CASE WHEN p IS NULL THEN NULL ELSE {partner: p.code, meteors: e.meteors} END) AS partners
RETURN m.id AS month, m.partial AS partial, t.status AS status, t.nights AS nights, t.detections AS detections,
       t.orbits AS orbits, t.partners AS partner_count, partners, t.lost AS lost, t.change AS change,
       CASE WHEN t.lost > 0 THEN 'lost_partner' WHEN t.partners = 0 AND t.nights > 0 THEN 'no_partner' END AS mark
ORDER BY month
