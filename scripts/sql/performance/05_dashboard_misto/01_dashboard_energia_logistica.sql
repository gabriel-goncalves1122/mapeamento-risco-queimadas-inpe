-- categoria: dashboard_misto
-- objetivo: simular comparativo operacional entre energia e logistica
-- datasource: dim_ons_linhas_transmissao, dim_ons_subestacoes, dim_rodovias_federais
-- padrao_carga: union_aggregate
-- visualizacao: tabela_barras
SELECT
  'linhas_transmissao' AS camada,
  estado_sigla_estimado AS territorio,
  classe_criticidade_linha AS classe_risco,
  COUNT(*) AS ativos_total,
  SUM(extensao_km) AS medida_total
FROM dim_ons_linhas_transmissao
GROUP BY
  estado_sigla_estimado,
  classe_criticidade_linha
UNION ALL
SELECT
  'subestacoes' AS camada,
  'NAO INFORMADO' AS territorio,
  criticidade_subestacao AS classe_risco,
  COUNT(*) AS ativos_total,
  SUM(capacidade_mw) AS medida_total
FROM dim_ons_subestacoes
GROUP BY criticidade_subestacao
UNION ALL
SELECT
  'rodovias' AS camada,
  'NAO INFORMADO' AS territorio,
  criticidade_rodovia AS classe_risco,
  COUNT(*) AS ativos_total,
  COUNT(*) AS medida_total
FROM dim_rodovias_federais
GROUP BY criticidade_rodovia;
