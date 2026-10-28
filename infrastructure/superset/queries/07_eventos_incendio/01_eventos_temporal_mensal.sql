-- setor: eventos_incendio
-- objetivo: acompanhar volume mensal de eventos, focos representados e FRP acumulado
-- datasource: fato_eventos_incendio
-- granularidade: mes
-- visualizacao: serie_temporal
SELECT
  TIME_FLOOR(__time, 'P1M') AS mes,
  COUNT(*) AS total_eventos,
  SUM(total_focos) AS focos_representados,
  SUM(soma_frp) AS frp_total,
  AVG(media_risco_fogo) AS risco_medio_eventos,
  MAX(max_frp) AS maior_frp_evento,
  MAX(duracao_dias) AS maior_duracao_dias
FROM fato_eventos_incendio
GROUP BY 1
ORDER BY 1;
