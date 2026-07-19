-- categoria: joins_dimensionais
-- objetivo: simular painel de defesa civil cruzando hospitais e municipios
-- datasource: dim_hospitais_cnes, dim_municipios_coordenadas
-- padrao_carga: left_join_groupby
-- visualizacao: mapa_coropletico
SELECT
  m.regiao_brasil,
  m.estado_sigla,
  m.codigo_ibge,
  m.municipios_nome,
  COUNT(DISTINCT h.codigo_cnes) AS hospitais_total,
  SUM(CASE WHEN h.funciona_24h = 'SIM' THEN 1 ELSE 0 END) AS hospitais_24h,
  SUM(CASE WHEN h.match_status_municipio <> 'OK_ESPACIAL' THEN 1 ELSE 0 END) AS hospitais_fallback
FROM dim_municipios_coordenadas m
LEFT JOIN dim_hospitais_cnes h
  ON h.codigo_ibge_municipio = m.codigo_ibge
GROUP BY
  m.regiao_brasil,
  m.estado_sigla,
  m.codigo_ibge,
  m.municipios_nome
ORDER BY hospitais_total DESC;
