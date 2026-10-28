SELECT
  LOOKUP(f.fk_terra_indigena_proxima, 'ti_nome') as nome_terra_indigena,
  LOOKUP(f.fk_terra_indigena_proxima, 'ti_etnia') as etnia,
  LOOKUP(f.fk_terra_indigena_proxima, 'ti_uf') as uf_sigla,
  COUNT(f.fire_event_id) as total_eventos,
  SUM(f.total_focos) as total_focos_entorno,
  SUM(f.indice_pressao_terra_indigena) as pressao_acumulada
FROM fato_eventos_incendio f
WHERE f.__time >= CURRENT_TIMESTAMP - INTERVAL '7' DAY
  AND f.fk_terra_indigena_proxima IS NOT NULL
  AND f.fk_terra_indigena_proxima != 'NAO_INFORMADO'
GROUP BY 1, 2, 3
ORDER BY pressao_acumulada DESC
LIMIT 50
