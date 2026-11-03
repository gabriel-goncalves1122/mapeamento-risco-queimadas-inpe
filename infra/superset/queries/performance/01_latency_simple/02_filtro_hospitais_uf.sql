-- categoria: latency_simple
-- objetivo: medir filtro seletivo em coluna de baixa cardinalidade
-- datasource: dim_hospitais_cnes
-- padrao_carga: filtered_groupby
-- visualizacao: barras
SELECT
  LOOKUP(codigo_ibge, 'municipios_uf') AS estado_sigla,
  COUNT(*) AS hospitais_total,
  SUM(CASE WHEN funciona_24h = 'SIM' THEN 1 ELSE 0 END) AS hospitais_24h
FROM dim_hospitais_cnes
WHERE LOOKUP(codigo_ibge, 'municipios_uf') IN ('MG', 'SP', 'RJ', 'PA', 'AM')
GROUP BY 1;
