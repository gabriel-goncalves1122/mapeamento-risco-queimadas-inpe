-- setor: funai
-- objetivo: resumir terras indigenas por regularizacao, prioridade e faixa de fronteira
-- datasource: dim_terras_indigenas
-- granularidade: status_prioridade
-- visualizacao: barras_empilhadas
SELECT
  estagio_regularizacao,
  modalidade,
  prioridade_funai,
  em_faixa_fronteira,
  COUNT(*) AS terras_indigenas_total,
  SUM(area_hectares) AS area_hectares_total
FROM dim_terras_indigenas
GROUP BY
  estagio_regularizacao,
  modalidade,
  prioridade_funai,
  em_faixa_fronteira
ORDER BY terras_indigenas_total DESC;
