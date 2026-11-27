MATCH (s:Station)-[t:STATS {month: $month}]->()
WHERE t.change IS NOT NULL OR t.lost > 0
RETURN s.code AS station, s.country AS country, t.change AS change, t.lost AS lost, t.status AS status
ORDER BY lost DESC, station
