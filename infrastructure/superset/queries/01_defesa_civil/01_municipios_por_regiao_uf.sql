-- setor: defesa_civil
-- objetivo: comparar cobertura territorial por regiao e UF
-- datasource: dim_municipios_coordenadas
-- granularidade: regiao_uf
-- visualizacao: tabela_barra
SELECT
  regiao_brasil,
  estado_sigla,
  COUNT(*) AS municipios_total
FROM dim_municipios_coordenadas
GROUP BY regiao_brasil, estado_sigla
ORDER BY regiao_brasil, estado_sigla;
