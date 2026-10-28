-- setor: energia
-- objetivo: destacar subestacoes por capacidade e responsavel operacional
-- datasource: dim_ons_subestacoes
-- granularidade: agente_capacidade
-- visualizacao: tabela_barra
SELECT
  agente_responsavel,
  classe_capacidade,
  criticidade_subestacao,
  COUNT(*) AS subestacoes_total,
  SUM(capacidade_mw) AS capacidade_mw_total,
  AVG(capacidade_mw) AS capacidade_mw_media
FROM dim_ons_subestacoes
GROUP BY
  agente_responsavel,
  classe_capacidade,
  criticidade_subestacao
ORDER BY capacidade_mw_total DESC;
