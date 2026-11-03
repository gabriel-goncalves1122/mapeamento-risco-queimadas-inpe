-- setor: funai
-- objetivo: cruzar cada terra indigena com seu municipio principal calculado no ETL
-- datasource: dim_terras_indigenas, dim_municipios_coordenadas
-- granularidade: terra_indigena_municipio_principal
-- visualizacao: tabela_mapa
SELECT
  t.codigo_ti,
  t.nome_terra_indigena,
  t.etnia,
  t.estado_sigla,
  t.area_hectares,
  t.prioridade_funai,
  t.estagio_regularizacao,
  t.codigo_ibge_principal,
  m.municipios_nome AS municipio_principal,
  m.regiao_brasil,
  t.qtd_municipios_interceptados,
  t.percentual_area_interceptada,
  t.match_status_municipios,
  t.latitude,
  t.longitude,
  t.path_json
FROM dim_terras_indigenas t
LEFT JOIN dim_municipios_coordenadas m
  ON t.codigo_ibge_principal = m.codigo_ibge
ORDER BY t.area_hectares DESC;
