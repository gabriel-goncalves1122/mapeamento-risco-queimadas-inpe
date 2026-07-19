-- categoria: payload_espacial
-- objetivo: simular mapa de pontos retornando payload de geometria ao cliente
-- datasource: dim_hospitais_cnes
-- padrao_carga: result_payload
-- visualizacao: deck_gl_scatterplot
SELECT
  codigo_cnes,
  nome_hospital,
  estado_sigla,
  codigo_ibge_municipio,
  latitude,
  longitude,
  path_json
FROM dim_hospitais_cnes
WHERE latitude BETWEEN -35 AND 6
  AND longitude BETWEEN -75 AND -30
LIMIT 1000;
