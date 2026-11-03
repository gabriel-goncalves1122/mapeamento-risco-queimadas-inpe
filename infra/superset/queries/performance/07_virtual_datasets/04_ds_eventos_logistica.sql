-- categoria: virtual_datasets
-- objetivo: simular query real do dashboard de eventos logistica (Virtual Dataset)
-- datasource: fato_eventos_incendio
-- padrao_carga: virtual_dataset
-- visualizacao: dashboard_completo
SELECT
  fire_event_id,
  __time,
  total_focos,
  
  -- Rodovias Metrics
  indice_ameaca_rodovia,
  distancia_rodovia_km,
  
  -- Rodovias Lookups
  fk_trecho_rodoviario,
  LOOKUP(fk_trecho_rodoviario, 'rodovia_codigo') AS rodovia_codigo,
  LOOKUP(fk_trecho_rodoviario, 'rodovia_criticidade') AS rodovia_criticidade,
  
  -- Município Relacionado
  fk_municipio_principal,
  LOOKUP(fk_municipio_principal, 'municipios_nome') AS municipio_nome,
  LOOKUP(fk_municipio_principal, 'municipios_uf') AS municipio_uf,
  max_frp

FROM fato_eventos_incendio
WHERE
  indice_ameaca_rodovia > 0
  AND fk_trecho_rodoviario IS NOT NULL
  AND fk_trecho_rodoviario != 'NAO_INFORMADO'
  AND __time >= TIMESTAMP '2025-08-01' AND __time < TIMESTAMP '2025-11-01'
GROUP BY 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12
ORDER BY max_frp DESC
LIMIT 50000;
