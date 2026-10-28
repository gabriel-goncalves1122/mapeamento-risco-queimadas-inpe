-- setor: qualidade
-- objetivo: auditar relacionamentos nativos resolvidos no ETL sem tabelas ponte publicas
-- datasource: dim_hospitais_cnes, dim_terras_indigenas
-- granularidade: status_relacionamento
-- visualizacao: tabela_barra
SELECT
  'hospital_municipio' AS relacionamento,
  match_status_municipio AS status,
  COUNT(*) AS registros
FROM dim_hospitais_cnes
GROUP BY match_status_municipio
UNION ALL
SELECT
  'terra_indigena_municipios' AS relacionamento,
  match_status_municipios AS status,
  COUNT(*) AS registros
FROM dim_terras_indigenas
GROUP BY match_status_municipios;
