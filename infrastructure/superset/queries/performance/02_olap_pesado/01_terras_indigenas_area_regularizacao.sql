-- categoria: olap_pesado
-- objetivo: medir agregacoes numericas em dimensao espacial com path_json pesado
-- datasource: dim_terras_indigenas
-- padrao_carga: numeric_aggregations
-- visualizacao: barras
SELECT
  estado_sigla,
  estagio_regularizacao,
  prioridade_funai,
  COUNT(*) AS terras_indigenas_total,
  SUM(area_hectares) AS area_hectares_total,
  AVG(qtd_municipios_interceptados) AS media_municipios_interceptados,
  AVG(percentual_area_interceptada) AS media_percentual_interceptado
FROM dim_terras_indigenas
GROUP BY
  estado_sigla,
  estagio_regularizacao,
  prioridade_funai
ORDER BY area_hectares_total DESC;
