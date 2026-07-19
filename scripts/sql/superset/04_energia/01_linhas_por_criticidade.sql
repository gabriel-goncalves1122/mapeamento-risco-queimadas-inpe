-- setor: energia
-- objetivo: resumir linhas ONS por criticidade, tensao e UF estimada
-- datasource: dim_ons_linhas_transmissao
-- granularidade: criticidade_tensao_uf
-- visualizacao: barras_empilhadas
SELECT
  estado_sigla_estimado,
  classe_criticidade_linha,
  classe_tensao,
  COUNT(*) AS linhas_total,
  SUM(extensao_km) AS extensao_km_total,
  AVG(tensao_kv) AS tensao_kv_media
FROM dim_ons_linhas_transmissao
GROUP BY
  estado_sigla_estimado,
  classe_criticidade_linha,
  classe_tensao
ORDER BY extensao_km_total DESC;
