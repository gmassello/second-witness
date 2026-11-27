UNWIND $pairs.shared AS r MATCH (a:Station {code: r.a}), (b:Station {code: r.b}) CREATE (a)-[e:SHARED]->(b) SET e += r.p;
UNWIND $pairs.could AS r MATCH (a:Station {code: r.a}), (b:Station {code: r.b}) CREATE (a)-[e:COULD_PAIR]->(b) SET e += r.p;
UNWIND $pairs.nearest AS r MATCH (a:Station {code: r.a}), (b:Station {code: r.b}) CREATE (a)-[e:NEAREST_ISLAND]->(b) SET e += r.p;
