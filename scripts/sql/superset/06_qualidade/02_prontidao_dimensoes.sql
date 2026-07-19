-- setor: qualidade
-- objetivo: medir prontidao das FKs dimensionais para receber a fato futuramente
-- datasource: dim_hospitais_cnes, dim_terras_indigenas, dim_municipios_coordenadas
-- granularidade: regra_prontidao
-- visualizacao: tabela_indicadores
SELECT
  'hospitais_com_municipio_existente' AS regra,
  COUNT(*) AS avaliados,
  SUM(CASE WHEN m.codigo_ibge IS NULL THEN 1 ELSE 0 END) AS pendencias
FROM dim_hospitais_cnes h
LEFT JOIN dim_municipios_coordenadas m
  ON h.codigo_ibge_municipio = m.codigo_ibge
UNION ALL
SELECT
  'hospitais_com_ti_proxima_existente' AS regra,
  COUNT(*) AS avaliados,
  SUM(CASE WHEN t.codigo_ti IS NULL THEN 1 ELSE 0 END) AS pendencias
FROM dim_hospitais_cnes h
LEFT JOIN dim_terras_indigenas t
  ON h.codigo_ti_proxima = t.codigo_ti
UNION ALL
SELECT
  'terras_indigenas_com_municipio_principal_existente' AS regra,
  COUNT(*) AS avaliados,
  SUM(CASE WHEN m.codigo_ibge IS NULL THEN 1 ELSE 0 END) AS pendencias
FROM dim_terras_indigenas t
LEFT JOIN dim_municipios_coordenadas m
  ON t.codigo_ibge_principal = m.codigo_ibge;
