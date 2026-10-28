-- setor: catalogo
-- objetivo: inventariar dimensoes ativas ja ingeridas no Druid
-- datasource: todas_dimensoes
-- granularidade: datasource
-- visualizacao: tabela
SELECT 'dim_municipios_coordenadas' AS datasource, COUNT(*) AS total_linhas
FROM dim_municipios_coordenadas
UNION ALL
SELECT 'dim_hospitais_cnes' AS datasource, COUNT(*) AS total_linhas
FROM dim_hospitais_cnes
UNION ALL
SELECT 'dim_terras_indigenas' AS datasource, COUNT(*) AS total_linhas
FROM dim_terras_indigenas
UNION ALL
SELECT 'dim_rodovias_federais' AS datasource, COUNT(*) AS total_linhas
FROM dim_rodovias_federais
UNION ALL
SELECT 'dim_ons_linhas_transmissao' AS datasource, COUNT(*) AS total_linhas
FROM dim_ons_linhas_transmissao
UNION ALL
SELECT 'dim_ons_subestacoes' AS datasource, COUNT(*) AS total_linhas
FROM dim_ons_subestacoes
UNION ALL
SELECT 'dim_ons_sistemas_isolados' AS datasource, COUNT(*) AS total_linhas
FROM dim_ons_sistemas_isolados;
