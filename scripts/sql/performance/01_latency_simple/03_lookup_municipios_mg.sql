-- categoria: latency_simple
-- objetivo: medir consulta de lookup territorial usada como filtro de painel
-- datasource: dim_municipios_coordenadas
-- padrao_carga: lookup_filter
-- visualizacao: tabela
SELECT
  codigo_ibge,
  municipios_nome,
  estado_sigla,
  regiao_brasil
FROM dim_municipios_coordenadas
WHERE estado_sigla = 'MG';
