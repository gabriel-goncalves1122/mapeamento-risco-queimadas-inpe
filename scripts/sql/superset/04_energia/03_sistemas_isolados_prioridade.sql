-- setor: energia
-- objetivo: mapear sistemas isolados por UF, regiao eletrica e prioridade
-- datasource: dim_ons_sistemas_isolados
-- granularidade: sistema_isolado
-- visualizacao: mapa_pontos_tabela
SELECT
  estado_sigla,
  regiao_eletrica,
  prioridade_sistema_isolado,
  COUNT(*) AS sistemas_total,
  MIN(latitude) AS latitude_referencia,
  MIN(longitude) AS longitude_referencia
FROM dim_ons_sistemas_isolados
GROUP BY
  estado_sigla,
  regiao_eletrica,
  prioridade_sistema_isolado
ORDER BY sistemas_total DESC;
