-- categoria: virtual_datasets
-- objetivo: simular query real do dashboard de eventos indigenas (Virtual Dataset)
-- datasource: fato_eventos_incendio
-- padrao_carga: virtual_dataset
-- visualizacao: dashboard_completo
SELECT
  fire_event_id,
  __time,
  latitude_centroide,
  longitude_centroide,
  total_focos,
  soma_frp,
  area_evento_km2,
  duracao_dias,
  
  -- TI Metrics
  indice_pressao_terra_indigena,
  distancia_terra_indigena_km,
  
  -- TI Classification
  CASE
    WHEN fk_terra_indigena IS NOT NULL AND fk_terra_indigena != 'NAO INFORMADO'
    THEN 'DENTRO'
    ELSE 'ENTORNO'
  END AS tipo_ameaca,
  
  -- TI Lookups (Dentro)
  fk_terra_indigena,
  LOOKUP(fk_terra_indigena, 'ti_nome') AS ti_nome_dentro,
  LOOKUP(fk_terra_indigena, 'ti_etnia') AS ti_etnia_dentro,
  LOOKUP(fk_terra_indigena, 'ti_uf') AS ti_uf_dentro,
  
  -- TI Lookups (Proxima/Entorno)
  fk_terra_indigena_proxima,
  LOOKUP(fk_terra_indigena_proxima, 'ti_nome') AS ti_nome_proxima,
  LOOKUP(fk_terra_indigena_proxima, 'ti_etnia') AS ti_etnia_proxima,
  LOOKUP(fk_terra_indigena_proxima, 'ti_uf') AS ti_uf_proxima,

  -- Unified TI Lookups for easy filtering
  COALESCE(
    LOOKUP(fk_terra_indigena, 'ti_nome'),
    LOOKUP(fk_terra_indigena_proxima, 'ti_nome')
  ) AS ti_nome_unificado,
  COALESCE(
    LOOKUP(fk_terra_indigena, 'ti_etnia'),
    LOOKUP(fk_terra_indigena_proxima, 'ti_etnia')
  ) AS ti_etnia_unificada,
  max_frp
  
FROM fato_eventos_incendio
WHERE 
  ((fk_terra_indigena IS NOT NULL AND fk_terra_indigena != 'NAO INFORMADO')
  OR indice_pressao_terra_indigena > 0)
  AND __time >= TIMESTAMP '2025-08-01' AND __time < TIMESTAMP '2025-11-01'
GROUP BY 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22
ORDER BY max_frp DESC
LIMIT 50000;
