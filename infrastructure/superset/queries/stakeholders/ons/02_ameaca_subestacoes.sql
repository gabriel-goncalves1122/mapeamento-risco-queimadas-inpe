SELECT
  f.__time as momento_evento,
  f.fire_event_id,
  LOOKUP(f.fk_subestacao, 'subestacao_nome') as nome_subestacao,
  CAST(LOOKUP(f.fk_subestacao, 'subestacao_capacidade') AS FLOAT) as capacidade_mw,
  LOOKUP(f.fk_subestacao, 'subestacao_risco_cascata') as risco_cascata,
  CAST(LOOKUP(f.fk_subestacao, 'subestacao_betweenness') AS FLOAT) as betweenness_score,
  f.total_focos,
  f.indice_ameaca_subestacao
FROM fato_eventos_incendio f
WHERE f.__time >= CURRENT_TIMESTAMP - INTERVAL '7' DAY
  AND f.indice_ameaca_subestacao > 0
GROUP BY 1, 2, 3, 4, 5, 6, 7, 8
ORDER BY f.indice_ameaca_subestacao DESC
LIMIT 50
