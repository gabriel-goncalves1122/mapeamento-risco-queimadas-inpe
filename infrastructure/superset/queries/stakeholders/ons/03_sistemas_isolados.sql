SELECT
  f.__time as momento_evento,
  f.fire_event_id,
  LOOKUP(f.fk_sistema_isolado, 'sistema_isolado_nome') as nome_sistema_isolado,
  f.total_focos,
  f.indice_ameaca_sistema_isolado,
  LOOKUP(f.fk_sistema_isolado, 'sistema_isolado_uf') as uf_sigla
FROM fato_eventos_incendio f
WHERE f.__time >= CURRENT_TIMESTAMP - INTERVAL '7' DAY
  AND f.indice_ameaca_sistema_isolado > 0
GROUP BY 1, 2, 3, 4, 5, 6
ORDER BY f.indice_ameaca_sistema_isolado DESC
LIMIT 50
