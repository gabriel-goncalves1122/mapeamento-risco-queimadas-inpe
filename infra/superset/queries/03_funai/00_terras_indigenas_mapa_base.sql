-- setor: funai
-- objetivo: expor terras indigenas para mapa de poligonos e filtros territoriais
-- datasource: dim_terras_indigenas
-- granularidade: terra_indigena
-- visualizacao: deck_gl_polygon
SELECT
  codigo_ti,
  nome_terra_indigena,
  etnia,
  municipios,
  estado_sigla,
  area_hectares,
  classe_area_ti,
  estagio_regularizacao,
  modalidade,
  coordenacao_regional,
  em_faixa_fronteira,
  prioridade_funai,
  codigos_ibge_interceptados,
  codigo_ibge_principal,
  qtd_municipios_interceptados,
  percentual_area_interceptada,
  match_status_municipios,
  latitude,
  longitude,
  path_json
FROM dim_terras_indigenas;
