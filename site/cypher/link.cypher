MATCH (:Station)-[l:LINK]->(:Station) DELETE l;
MATCH (a:Station)-[s:SHARED {month: $latest}]->(b:Station) CREATE (a)-[:LINK {month: $latest, meteors: s.meteors}]->(b);
