-- setor: saude
-- objetivo: ranquear municipios por oferta hospitalar e qualidade do match espacial
-- datasource: dim_hospitais_cnes, dim_municipios_coordenadas
-- granularidade: municipio
-- visualizacao: tabela_barra
SELECT
  m.regiao_brasil,
  m.estado_sigla,
  h.codigo_ibge_municipio,
  m.municipios_nome,
  COUNT(DISTINCT h.codigo_cnes) AS hospitais_total,
  SUM(CASE WHEN h.funciona_24h = 'SIM' THEN 1 ELSE 0 END) AS hospitais_24h,
  SUM(CASE WHEN h.match_status_municipio = 'OK_ESPACIAL' THEN 1 ELSE 0 END) AS matches_espaciais,
  SUM(CASE WHEN h.match_status_municipio <> 'OK_ESPACIAL' THEN 1 ELSE 0 END) AS matches_fallback,
  SUM(CASE WHEN h.tipo_unidade_critica <> 'NAO INFORMADO' THEN 1 ELSE 0 END) AS unidades_criticas
FROM dim_hospitais_cnes h
LEFT JOIN dim_municipios_coordenadas m
  ON h.codigo_ibge_municipio = m.codigo_ibge
GROUP BY
  m.regiao_brasil,
  m.estado_sigla,
  h.codigo_ibge_municipio,
  m.municipios_nome
ORDER BY hospitais_total DESC;
