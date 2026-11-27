MATCH ()-[l:LINK]->()
WITH l.month AS month LIMIT 1
MATCH (a:Station {code: $station}), (b:Station {code: $other})
OPTIONAL MATCH (a)-[ta:STATS]->(:Month {id: month})
OPTIONAL MATCH (b)-[tb:STATS]->(:Month {id: month})
OPTIONAL MATCH p = allShortestPaths((a)-[:LINK*]-(b))
WITH month, a, b, ta, tb, p, [n IN nodes(p) | n.code] AS path, [r IN relationships(p) | r.meteors] AS meteors
WITH month, a, b, ta, tb, path, meteors, reduce(t = 0, m IN coalesce(meteors, []) | t + m) AS weight
ORDER BY weight DESC, path
LIMIT 1
RETURN month, a.code AS station, b.code AS other, ta.island AS island, tb.island AS other_island,
       CASE WHEN ta.island IS NULL OR tb.island IS NULL THEN 'no_partner'
            WHEN ta.island <> tb.island THEN 'different_islands' END AS reason,
       path, meteors
