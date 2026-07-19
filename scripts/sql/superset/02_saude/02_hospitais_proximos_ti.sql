-- setor: saude
-- objetivo: cruzar hospitais com a terra indigena mais proxima para priorizacao territorial
-- datasource: dim_hospitais_cnes, dim_terras_indigenas, dim_municipios_coordenadas
-- granularidade: hospital_ti_proxima
-- visualizacao: tabela_mapa_pontos
SELECT
  h.codigo_cnes,
  h.nome_hospital,
  h.estado_sigla,
  h.codigo_ibge_municipio,
  m.municipios_nome,
  h.codigo_ti_proxima,
  t.nome_terra_indigena,
  t.etnia,
  t.prioridade_funai,
  t.estagio_regularizacao,
  h.distancia_ti_km,
  h.dentro_terra_indigena,
  h.ate_1km,
  h.ate_3km,
  h.ate_7km,
  h.ate_15km,
  h.ate_50km,
  h.latitude,
  h.longitude,
  h.path_json
FROM dim_hospitais_cnes h
LEFT JOIN dim_terras_indigenas t
  ON h.codigo_ti_proxima = t.codigo_ti
LEFT JOIN dim_municipios_coordenadas m
  ON h.codigo_ibge_municipio = m.codigo_ibge
WHERE h.dentro_terra_indigena = 1
   OR h.ate_15km = 1
ORDER BY h.distancia_ti_km ASC;
