-- categoria: joins_dimensionais
-- objetivo: simular painel de saude cruzando hospitais com TI mais proxima
-- datasource: dim_hospitais_cnes, dim_terras_indigenas
-- padrao_carga: nearest_fk_join
-- visualizacao: tabela_mapa
SELECT
  t.estado_sigla,
  t.nome_terra_indigena,
  t.prioridade_funai,
  t.estagio_regularizacao,
  COUNT(DISTINCT h.codigo_cnes) AS hospitais_relacionados,
  SUM(CASE WHEN h.dentro_terra_indigena = 1 THEN 1 ELSE 0 END) AS hospitais_dentro_ti,
  SUM(CASE WHEN h.dentro_terra_indigena = 1 THEN 1 ELSE 0 END) AS hospitais_ate_15km,
  AVG(h.distancia_ti_km) AS distancia_media_km
FROM dim_terras_indigenas t
LEFT JOIN dim_hospitais_cnes h
  ON h.codigo_ti_proxima = t.codigo_ti
GROUP BY
  t.estado_sigla,
  t.nome_terra_indigena,
  t.prioridade_funai,
  t.estagio_regularizacao
ORDER BY hospitais_relacionados DESC;
