-- setor: eventos_incendio
-- objetivo: monitorar qualidade operacional da fato de eventos
-- datasource: fato_eventos_incendio
-- granularidade: regra
-- visualizacao: tabela_status
SELECT
  'eventos_abaixo_min_samples' AS regra,
  SUM(CASE WHEN total_focos < param_min_samples THEN 1 ELSE 0 END) AS pendencias
FROM fato_eventos_incendio
UNION ALL
SELECT
  'eventos_acima_duracao_parametro' AS regra,
  SUM(CASE WHEN duracao_dias > param_max_duration_days THEN 1 ELSE 0 END) AS pendencias
FROM fato_eventos_incendio
UNION ALL
SELECT
  'eventos_sem_path_json' AS regra,
  SUM(CASE WHEN path_json IS NULL OR path_json = '' OR path_json = '[]' THEN 1 ELSE 0 END) AS pendencias
FROM fato_eventos_incendio
UNION ALL
SELECT
  'eventos_sem_municipio_principal' AS regra,
  SUM(CASE WHEN fk_municipio_principal = 'NAO INFORMADO' THEN 1 ELSE 0 END) AS pendencias
FROM fato_eventos_incendio;
