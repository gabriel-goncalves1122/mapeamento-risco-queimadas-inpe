-- categoria: latency_simple
-- objetivo: medir latencia de inventario com UNION ALL entre dimensoes
-- datasource: todas_dimensoes
-- padrao_carga: union_counts
-- visualizacao: tabela
SELECT 'municipios' AS datasource, COUNT(*) AS total FROM dim_municipios_coordenadas
UNION ALL
SELECT 'hospitais' AS datasource, COUNT(*) AS total FROM dim_hospitais_cnes
UNION ALL
SELECT 'terras_indigenas' AS datasource, COUNT(*) AS total FROM dim_terras_indigenas
UNION ALL
SELECT 'rodovias' AS datasource, COUNT(*) AS total FROM dim_rodovias_federais
UNION ALL
SELECT 'ons_linhas' AS datasource, COUNT(*) AS total FROM dim_ons_linhas_transmissao
UNION ALL
SELECT 'ons_subestacoes' AS datasource, COUNT(*) AS total FROM dim_ons_subestacoes
UNION ALL
SELECT 'ons_sistemas_isolados' AS datasource, COUNT(*) AS total FROM dim_ons_sistemas_isolados;
