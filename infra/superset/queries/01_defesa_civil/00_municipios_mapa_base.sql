-- setor: defesa_civil
-- objetivo: expor mapa base municipal para filtros territoriais
-- datasource: dim_municipios_coordenadas
-- granularidade: municipio
-- visualizacao: deck_gl_polygon
SELECT
  codigo_ibge,
  codigo_ibge_7digitos,
  municipios_nome,
  estado_sigla,
  estado_nome,
  regiao_brasil,
  latitude,
  longitude,
  path_json
FROM dim_municipios_coordenadas;
