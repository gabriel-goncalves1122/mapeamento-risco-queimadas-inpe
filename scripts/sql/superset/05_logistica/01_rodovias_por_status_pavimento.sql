-- setor: logistica
-- objetivo: comparar malha rodoviaria por status operacional e pavimento
-- datasource: dim_rodovias_federais
-- granularidade: status_pavimento
-- visualizacao: barras_empilhadas
SELECT
  codigo_rodovia,
  jurisdicao,
  classe_status_operacional,
  classe_situacao_fisica,
  classe_revestimento,
  tipo_pavimento,
  COUNT(*) AS trechos_total
FROM dim_rodovias_federais
GROUP BY
  codigo_rodovia,
  jurisdicao,
  classe_status_operacional,
  classe_situacao_fisica,
  classe_revestimento,
  tipo_pavimento
ORDER BY trechos_total DESC;
