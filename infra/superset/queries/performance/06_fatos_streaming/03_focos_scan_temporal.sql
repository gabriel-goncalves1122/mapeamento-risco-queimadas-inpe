-- categoria: fatos_streaming
-- objetivo: medir motor Scan em tabela de 3.3M linhas com filtro temporal
-- datasource: fato_focos_incendio
-- padrao_carga: scan_temporal
-- visualizacao: tabela
SELECT
  __time, latitude, longitude, potencia_radiativa_fogo, risco_fogo_inpe,
  fk_bioma, fk_municipio
FROM fato_focos_incendio
WHERE __time >= TIMESTAMP '2025-09-01' AND __time < TIMESTAMP '2025-09-08'
LIMIT 10000;
