UNWIND $partners.shared AS r MATCH (a:Station {code: r.a}), (b:Station {code: r.b}) MERGE (a)-[e:SHARED {month: r.p.month}]->(b) SET e += r.p;
