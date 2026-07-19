-- setor: saude
-- objetivo: expor hospitais CNES para mapa de pontos e filtros operacionais
-- datasource: dim_hospitais_cnes
-- granularidade: hospital
-- visualizacao: deck_gl_scatterplot
SELECT
  codigo_cnes,
  nome_hospital,
  tipo_unidade,
  categoria_unidade,
  tipo_unidade_critica,
  categoria_atendimento,
  classe_capacidade_saude,
  funciona_24h,
  codigo_ibge_municipio,
  municipios_nome,
  estado_sigla,
  match_status_municipio,
  codigo_ti_proxima,
  distancia_ti_km,
  dentro_terra_indigena,
  ate_1km,
  ate_3km,
  ate_7km,
  ate_15km,
  ate_50km,
  latitude,
  longitude,
  path_json
FROM dim_hospitais_cnes
WHERE latitude BETWEEN -35 AND 6
  AND longitude BETWEEN -75 AND -30;
