MATCH (s:Station)-[t:STATS {month: $month}]->()
WHERE t.change IS NOT NULL OR t.lost > 0 OR t.upload IN ['late', 'dark', 'silent']
RETURN s.code AS station, s.country AS country, t.change AS change, t.lost AS lost, t.status AS status,
       t.upload AS upload, t.last_upload AS last_upload
ORDER BY lost DESC, station
