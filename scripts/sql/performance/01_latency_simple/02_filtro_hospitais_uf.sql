-- categoria: latency_simple
-- objetivo: medir filtro seletivo em coluna de baixa cardinalidade
-- datasource: dim_hospitais_cnes
-- padrao_carga: filtered_groupby
-- visualizacao: barras
SELECT
  estado_sigla,
  COUNT(*) AS hospitais_total,
  SUM(CASE WHEN funciona_24h = 'SIM' THEN 1 ELSE 0 END) AS hospitais_24h
FROM dim_hospitais_cnes
WHERE estado_sigla IN ('MG', 'SP', 'RJ', 'PA', 'AM')
GROUP BY estado_sigla;
