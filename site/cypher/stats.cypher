UNWIND $stats.months AS r CREATE (m:Month) SET m += r;
UNWIND $stats.countries AS r CREATE (c:Country) SET c += r;
UNWIND $stats.stations AS r CREATE (s:Station) SET s += r;
UNWIND $stats.station_stats AS r MATCH (s:Station {code: r.code}), (m:Month {id: r.month}) CREATE (s)-[t:STATS]->(m) SET t += r.p;
UNWIND $stats.country_stats AS r MATCH (c:Country {code: r.code}), (m:Month {id: r.month}) CREATE (c)-[t:STATS]->(m) SET t += r.p;
