-- setor: catalogo
-- objetivo: resumir escala das dimensoes para pagina inicial do painel
-- datasource: todas_dimensoes
-- granularidade: indicador
-- visualizacao: indicadores
SELECT 'municipios' AS indicador, COUNT(*) AS total, COUNT(DISTINCT estado_sigla) AS grupos
FROM dim_municipios_coordenadas
UNION ALL
SELECT 'hospitais_cnes' AS indicador, COUNT(*) AS total, COUNT(DISTINCT codigo_ibge_municipio) AS grupos
FROM dim_hospitais_cnes
UNION ALL
SELECT 'terras_indigenas' AS indicador, COUNT(*) AS total, COUNT(DISTINCT codigo_ibge_principal) AS grupos
FROM dim_terras_indigenas
UNION ALL
SELECT 'rodovias_federais' AS indicador, COUNT(*) AS total, COUNT(DISTINCT codigo_rodovia) AS grupos
FROM dim_rodovias_federais
UNION ALL
SELECT 'linhas_transmissao' AS indicador, COUNT(*) AS total, COUNT(DISTINCT estado_sigla_estimado) AS grupos
FROM dim_ons_linhas_transmissao
UNION ALL
SELECT 'subestacoes_ons' AS indicador, COUNT(*) AS total, COUNT(DISTINCT agente_responsavel) AS grupos
FROM dim_ons_subestacoes
UNION ALL
SELECT 'sistemas_isolados' AS indicador, COUNT(*) AS total, COUNT(DISTINCT estado_sigla) AS grupos
FROM dim_ons_sistemas_isolados;
