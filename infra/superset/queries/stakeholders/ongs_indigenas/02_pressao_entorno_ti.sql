SELECT
  f.__time as momento_evento,
  f.fire_event_id,
  LOOKUP(f.fk_terra_indigena_proxima, 'ti_nome') as nome_terra_indigena,
  LOOKUP(f.fk_terra_indigena_proxima, 'ti_etnia') as etnia,
  LOOKUP(f.fk_terra_indigena_proxima, 'ti_uf') as uf_sigla,
  f.total_focos,
  f.indice_pressao_terra_indigena
FROM fato_eventos_incendio f
WHERE f.__time >= CURRENT_TIMESTAMP - INTERVAL '7' DAY
  AND f.indice_pressao_terra_indigena > 0
  AND (f.fk_terra_indigena IS NULL OR f.fk_terra_indigena = 'NAO_INFORMADO')
GROUP BY 1, 2, 3, 4, 5, 6, 7
ORDER BY f.indice_pressao_terra_indigena DESC
LIMIT 50
