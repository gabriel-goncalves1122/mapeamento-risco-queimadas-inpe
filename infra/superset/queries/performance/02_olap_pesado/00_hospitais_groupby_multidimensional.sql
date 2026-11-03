-- categoria: olap_pesado
-- objetivo: forcar agregacao multidimensional e count distinct na maior dimensao
-- datasource: dim_hospitais_cnes
-- padrao_carga: groupby_distinct
-- visualizacao: tabela_barras
SELECT
  tipo_unidade_critica,
  categoria_unidade,
  classe_capacidade_saude,
  funciona_24h,
  COUNT(*) AS registros_total,
  COUNT(DISTINCT codigo_cnes) AS hospitais_distintos,
  SUM(CASE WHEN dentro_terra_indigena = 1 THEN 1 ELSE 0 END) AS dentro_ti
FROM dim_hospitais_cnes
GROUP BY
  tipo_unidade_critica,
  categoria_unidade,
  classe_capacidade_saude,
  funciona_24h
ORDER BY registros_total DESC;
