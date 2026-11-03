-- categoria: joins_dimensionais
-- objetivo: simular filtro territorial de TIs por municipio principal
-- datasource: dim_terras_indigenas, dim_municipios_coordenadas
-- padrao_carga: dimension_lookup_join
-- visualizacao: tabela
SELECT
  m.regiao_brasil,
  m.estado_sigla,
  m.municipios_nome,
  t.prioridade_funai,
  t.estagio_regularizacao,
  COUNT(*) AS terras_indigenas_total,
  SUM(t.area_hectares) AS area_hectares_total,
  AVG(t.qtd_municipios_interceptados) AS media_municipios_interceptados
FROM dim_terras_indigenas t
LEFT JOIN dim_municipios_coordenadas m
  ON t.codigo_ibge_principal = m.codigo_ibge
GROUP BY
  m.regiao_brasil,
  m.estado_sigla,
  m.municipios_nome,
  t.prioridade_funai,
  t.estagio_regularizacao
ORDER BY area_hectares_total DESC;
