MATCH (s:Station)
WHERE s.code CONTAINS toUpper($text)
RETURN 'station' AS kind, s.code AS code, s.country AS country
UNION ALL
MATCH (c:Country)
WHERE c.code CONTAINS toUpper($text) OR toLower(c.name) CONTAINS toLower($text)
RETURN 'country' AS kind, c.code AS code, c.code AS country
