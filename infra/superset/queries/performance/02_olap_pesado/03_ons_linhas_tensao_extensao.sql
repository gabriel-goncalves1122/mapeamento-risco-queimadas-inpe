-- categoria: olap_pesado
-- objetivo: medir agregacoes ONS por tensao, extensao e criticidade
-- datasource: dim_ons_linhas_transmissao
-- padrao_carga: numeric_groupby
-- visualizacao: barras
SELECT
  estado_sigla_estimado,
  classe_tensao,
  classe_criticidade_linha,
  COUNT(*) AS linhas_total,
  SUM(extensao_km) AS extensao_km_total,
  AVG(tensao_kv) AS tensao_kv_media,
  MAX(tensao_kv) AS tensao_kv_maxima
FROM dim_ons_linhas_transmissao
GROUP BY
  estado_sigla_estimado,
  classe_tensao,
  classe_criticidade_linha
ORDER BY extensao_km_total DESC;
