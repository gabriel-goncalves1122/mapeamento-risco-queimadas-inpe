-- categoria: olap_pesado
-- objetivo: forcar agregacao multidimensional e count distinct na maior dimensao
-- datasource: dim_hospitais_cnes
-- padrao_carga: groupby_distinct
-- visualizacao: tabela_barras
SELECT
  estado_sigla,
  categoria_unidade,
  classe_capacidade_saude,
  funciona_24h,
  COUNT(*) AS registros_total,
  COUNT(DISTINCT codigo_cnes) AS hospitais_distintos,
  SUM(CASE WHEN dentro_terra_indigena = 1 THEN 1 ELSE 0 END) AS dentro_ti,
  SUM(CASE WHEN ate_15km = 1 THEN 1 ELSE 0 END) AS ate_15km_ti
FROM dim_hospitais_cnes
GROUP BY
  estado_sigla,
  categoria_unidade,
  classe_capacidade_saude,
  funciona_24h
ORDER BY registros_total DESC;
