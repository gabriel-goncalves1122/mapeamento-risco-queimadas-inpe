-- setor: qualidade
-- objetivo: conferir coordenadas e path_json das dimensoes espaciais
-- datasource: todas_dimensoes_espaciais
-- granularidade: datasource
-- visualizacao: tabela_indicadores
SELECT
  'dim_municipios_coordenadas' AS datasource,
  COUNT(*) AS total,
  SUM(CASE WHEN latitude < -35 OR latitude > 6 OR longitude < -75 OR longitude > -30 THEN 1 ELSE 0 END) AS fora_bbox_brasil,
  SUM(CASE WHEN path_json IS NULL OR path_json = '' THEN 1 ELSE 0 END) AS sem_path_json
FROM dim_municipios_coordenadas
UNION ALL
SELECT
  'dim_hospitais_cnes' AS datasource,
  COUNT(*) AS total,
  SUM(CASE WHEN latitude < -35 OR latitude > 6 OR longitude < -75 OR longitude > -30 THEN 1 ELSE 0 END) AS fora_bbox_brasil,
  SUM(CASE WHEN path_json IS NULL OR path_json = '' THEN 1 ELSE 0 END) AS sem_path_json
FROM dim_hospitais_cnes
UNION ALL
SELECT
  'dim_terras_indigenas' AS datasource,
  COUNT(*) AS total,
  SUM(CASE WHEN latitude < -35 OR latitude > 6 OR longitude < -75 OR longitude > -30 THEN 1 ELSE 0 END) AS fora_bbox_brasil,
  SUM(CASE WHEN path_json IS NULL OR path_json = '' THEN 1 ELSE 0 END) AS sem_path_json
FROM dim_terras_indigenas
UNION ALL
SELECT
  'dim_rodovias_federais' AS datasource,
  COUNT(*) AS total,
  SUM(CASE WHEN latitude < -35 OR latitude > 6 OR longitude < -75 OR longitude > -30 THEN 1 ELSE 0 END) AS fora_bbox_brasil,
  SUM(CASE WHEN path_json IS NULL OR path_json = '' THEN 1 ELSE 0 END) AS sem_path_json
FROM dim_rodovias_federais
UNION ALL
SELECT
  'dim_ons_linhas_transmissao' AS datasource,
  COUNT(*) AS total,
  SUM(CASE WHEN latitude < -35 OR latitude > 6 OR longitude < -75 OR longitude > -30 THEN 1 ELSE 0 END) AS fora_bbox_brasil,
  SUM(CASE WHEN path_json IS NULL OR path_json = '' THEN 1 ELSE 0 END) AS sem_path_json
FROM dim_ons_linhas_transmissao
UNION ALL
SELECT
  'dim_ons_subestacoes' AS datasource,
  COUNT(*) AS total,
  SUM(CASE WHEN latitude < -35 OR latitude > 6 OR longitude < -75 OR longitude > -30 THEN 1 ELSE 0 END) AS fora_bbox_brasil,
  SUM(CASE WHEN path_json IS NULL OR path_json = '' THEN 1 ELSE 0 END) AS sem_path_json
FROM dim_ons_subestacoes
UNION ALL
SELECT
  'dim_ons_sistemas_isolados' AS datasource,
  COUNT(*) AS total,
  SUM(CASE WHEN latitude < -35 OR latitude > 6 OR longitude < -75 OR longitude > -30 THEN 1 ELSE 0 END) AS fora_bbox_brasil,
  SUM(CASE WHEN path_json IS NULL OR path_json = '' THEN 1 ELSE 0 END) AS sem_path_json
FROM dim_ons_sistemas_isolados;
