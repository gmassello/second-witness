MATCH (x:Station {code: $station})
OPTIONAL MATCH (x)-[tx:STATS {month: $month}]->(m:Month)
OPTIONAL MATCH (x)-[s:SHARED {month: $month}]-(p:Station)-[tp:STATS {month: $month}]->()
OPTIONAL MATCH (mo:Month {id: $month})
RETURN x.code AS station, x.country AS country, coalesce(tx.status, 'no_upload') AS status,
       coalesce(tx.nights, 0) AS nights, coalesce(tx.detections, 0) AS detections, coalesce(tx.orbits, 0) AS orbits,
       coalesce(tx.two_station_orbits, 0) AS orbits_lost, coalesce(tx.three_station_orbits, 0) AS third_witness_orbits,
       mo.sigma2_median AS sigma2_median, mo.sigma3_median AS sigma3_median,
       tx.island AS island, coalesce(tx.cut_off, 0) AS cut_off, tx.change AS change,
       p.code AS partner, s.meteors AS meteors, s.two_station AS two_station, s.sample_ids AS sample_ids,
       CASE WHEN tp.partners = 1 THEN 'loses_only_partner' WHEN tp.partners = 2 THEN 'left_with_one' END AS effect,
       CASE WHEN p IS NULL THEN NULL ELSE 'https://tammojan.github.io/meteormap/?data=' + substring($month, 0, 4) + '-' + substring($month, 4) + '&stations=' + x.code + ';' + p.code
            + CASE WHEN x.lat IS NULL OR p.lat IS NULL THEN '' ELSE '&lat=' + toString(round((x.lat + p.lat) / 2, 2)) + '&lng=' + toString(round((x.lon + p.lon) / 2, 2)) + '&zoom=7' END END AS link,
       'Data: Global Meteor Network, CC BY 4.0' AS credit
ORDER BY two_station DESC, meteors DESC, partner
