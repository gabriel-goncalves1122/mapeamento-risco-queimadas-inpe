-- categoria: virtual_datasets
-- objetivo: simular query real do dashboard de focos individuais (Virtual Dataset)
-- datasource: fato_focos_incendio
-- padrao_carga: virtual_dataset
-- visualizacao: dashboard_completo
SELECT
  __time,
  latitude,
  longitude,
  
  -- Metrics
  potencia_radiativa_fogo AS frp,
  risco_fogo_inpe,
  dias_sem_chuva,
  
  -- Dimensions & Lookups
  fk_bioma,
  fk_satelite_sensor,
  fk_municipio,
  LOOKUP(fk_municipio, 'municipios_nome') AS municipio_nome,
  LOOKUP(fk_municipio, 'municipios_uf') AS municipio_uf

FROM fato_focos_incendio
WHERE
  latitude IS NOT NULL
  AND longitude IS NOT NULL
  AND coordenada_valida = 1
  AND __time >= TIMESTAMP '2025-09-01' AND __time < TIMESTAMP '2025-09-08'
GROUP BY 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11
ORDER BY frp DESC
LIMIT 50000;
