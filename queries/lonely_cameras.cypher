MATCH (s:Station)-[t:STATS {month: $month}]->()
WHERE t.status = 'running_no_partner' AND ($country IS NULL OR s.country = $country)
RETURN s.code AS station, s.country AS country, t.status AS status, t.nights AS nights, t.detections AS detections,
       t.az AS az, t.alt AS alt, t.upload AS upload, t.last_upload AS last_upload
ORDER BY detections DESC, station
