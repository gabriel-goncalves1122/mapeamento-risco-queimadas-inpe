-- setor: defesa_civil
-- objetivo: cruzar municipios com a capacidade hospitalar CNES ja resolvida no ETL
-- datasource: dim_municipios_coordenadas, dim_hospitais_cnes
-- granularidade: municipio
-- visualizacao: mapa_coropletico_tabela
SELECT
  m.regiao_brasil,
  m.estado_sigla,
  m.codigo_ibge,
  m.municipios_nome,
  COUNT(DISTINCT h.codigo_cnes) AS hospitais_total,
  SUM(CASE WHEN h.funciona_24h = 'SIM' THEN 1 ELSE 0 END) AS hospitais_24h,
  SUM(CASE WHEN h.dentro_terra_indigena = 1 THEN 1 ELSE 0 END) AS hospitais_dentro_ti,
  SUM(CASE WHEN h.ate_15km = 1 THEN 1 ELSE 0 END) AS hospitais_ate_15km_ti,
  m.latitude,
  m.longitude,
  m.path_json
FROM dim_municipios_coordenadas m
LEFT JOIN dim_hospitais_cnes h
  ON h.codigo_ibge_municipio = m.codigo_ibge
GROUP BY
  m.regiao_brasil,
  m.estado_sigla,
  m.codigo_ibge,
  m.municipios_nome,
  m.latitude,
  m.longitude,
  m.path_json
ORDER BY hospitais_total DESC;
