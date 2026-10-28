-- categoria: fatos_streaming
-- objetivo: simular o padrao exato dos Virtual Datasets (GROUP BY + ORDER BY + LIMIT)
-- datasource: fato_eventos_incendio
-- padrao_carga: groupby_ordered_limit
-- visualizacao: mapa_scatter
SELECT
  fire_event_id, __time, latitude_centroide, longitude_centroide,
  fk_bioma, total_focos, soma_frp, max_frp, area_evento_km2
FROM fato_eventos_incendio
WHERE __time >= TIMESTAMP '2025-08-01' AND __time < TIMESTAMP '2025-11-01'
GROUP BY 1, 2, 3, 4, 5, 6, 7, 8, 9
ORDER BY max_frp DESC
LIMIT 50000;
