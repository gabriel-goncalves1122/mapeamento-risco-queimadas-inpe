-- setor: funai
-- objetivo: medir abrangencia municipal das terras indigenas usando a dimensao multi-value
-- datasource: dim_terras_indigenas
-- granularidade: faixa_cobertura
-- visualizacao: tabela_barra
SELECT
  match_status_municipios,
  classe_area_ti,
  prioridade_funai,
  COUNT(*) AS terras_indigenas_total,
  SUM(qtd_municipios_interceptados) AS municipios_interceptados_total,
  AVG(qtd_municipios_interceptados) AS media_municipios_por_ti,
  AVG(percentual_area_interceptada) AS media_percentual_area_interceptada
FROM dim_terras_indigenas
GROUP BY
  match_status_municipios,
  classe_area_ti,
  prioridade_funai
ORDER BY terras_indigenas_total DESC;
