-- categoria: fatos_streaming
-- objetivo: agregacao bioma x mes - teste do motor GroupBy em fato com 158K linhas
-- datasource: fato_eventos_incendio
-- padrao_carga: groupby_temporal
-- visualizacao: heatmap
SELECT
  fk_bioma,
  TIME_FLOOR(__time, 'P1M') AS mes,
  COUNT(*) AS eventos,
  SUM(total_focos) AS focos_total,
  MAX(max_frp) AS pico_frp
FROM fato_eventos_incendio
GROUP BY 1, 2
ORDER BY pico_frp DESC;
