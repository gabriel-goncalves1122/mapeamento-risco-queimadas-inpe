-- categoria: olap_pesado
-- objetivo: medir agrupamento em dimensao linear com varias classificacoes
-- datasource: dim_rodovias_federais
-- padrao_carga: categorical_groupby
-- visualizacao: barras_empilhadas
SELECT
  codigo_rodovia,
  jurisdicao,
  classe_status_operacional,
  classe_situacao_fisica,
  classe_revestimento,
  COUNT(*) AS trechos_total
FROM dim_rodovias_federais
GROUP BY
  codigo_rodovia,
  jurisdicao,
  classe_status_operacional,
  classe_situacao_fisica,
  classe_revestimento
ORDER BY trechos_total DESC;
