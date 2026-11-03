-- categoria: dashboard_misto
-- objetivo: simular painel de governanca com qualidade geografica e relacionamentos
-- datasource: dim_hospitais_cnes, dim_terras_indigenas, dim_municipios_coordenadas
-- padrao_carga: quality_dashboard
-- visualizacao: indicadores
SELECT
  'hospitais_sem_municipio' AS regra,
  COUNT(*) AS avaliados,
  SUM(CASE WHEN codigo_ibge IS NULL OR codigo_ibge = 'NAO INFORMADO' THEN 1 ELSE 0 END) AS pendencias
FROM dim_hospitais_cnes
UNION ALL
SELECT
  'hospitais_fora_bbox' AS regra,
  COUNT(*) AS avaliados,
  SUM(CASE WHEN latitude < -35 OR latitude > 6 OR longitude < -75 OR longitude > -30 THEN 1 ELSE 0 END) AS pendencias
FROM dim_hospitais_cnes
UNION ALL
SELECT
  'terras_indigenas_sem_municipio_principal' AS regra,
  COUNT(*) AS avaliados,
  SUM(CASE WHEN codigo_ibge_principal IS NULL OR codigo_ibge_principal = 'NAO INFORMADO' THEN 1 ELSE 0 END) AS pendencias
FROM dim_terras_indigenas
UNION ALL
SELECT
  'municipios_sem_path_json' AS regra,
  COUNT(*) AS avaliados,
  SUM(CASE WHEN path_json IS NULL OR path_json = '' THEN 1 ELSE 0 END) AS pendencias
FROM dim_municipios_coordenadas;
