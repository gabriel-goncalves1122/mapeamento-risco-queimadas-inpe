SELECT
  f.__time as momento_evento,
  f.fire_event_id,
  LOOKUP(f.fk_terra_indigena, 'ti_nome') as nome_terra_indigena,
  LOOKUP(f.fk_terra_indigena, 'ti_etnia') as etnia,
  LOOKUP(f.fk_terra_indigena, 'ti_uf') as uf_sigla,
  f.total_focos,
  f.area_evento_km2,
  f.soma_frp
FROM fato_eventos_incendio f
WHERE f.__time >= CURRENT_TIMESTAMP - INTERVAL '7' DAY
  AND f.fk_terra_indigena IS NOT NULL
  AND f.fk_terra_indigena != 'NAO_INFORMADO'
GROUP BY 1, 2, 3, 4, 5, 6, 7, 8
ORDER BY f.total_focos DESC
LIMIT 50
