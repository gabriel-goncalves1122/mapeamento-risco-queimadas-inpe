SELECT
  f.__time as momento_evento,
  f.fire_event_id,
  LOOKUP(f.fk_linha_transmissao, 'linha_nome') as nome_linha,
  CAST(LOOKUP(f.fk_linha_transmissao, 'linha_tensao') AS FLOAT) as tensao_kv,
  LOOKUP(f.fk_linha_transmissao, 'linha_uf') as uf_linha,
  f.total_focos,
  f.indice_ameaca_linha
FROM fato_eventos_incendio f
WHERE f.__time >= CURRENT_TIMESTAMP - INTERVAL '7' DAY
  AND f.indice_ameaca_linha > 0
GROUP BY 1, 2, 3, 4, 5, 6, 7
ORDER BY f.indice_ameaca_linha DESC
LIMIT 50
