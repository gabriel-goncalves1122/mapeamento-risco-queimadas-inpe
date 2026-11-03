-- setor: saude
-- objetivo: destacar unidades criticas ou 24h para resposta operacional
-- datasource: dim_hospitais_cnes, dim_municipios_coordenadas
-- granularidade: municipio_tipo_unidade
-- visualizacao: tabela_barra
SELECT
  m.regiao_brasil,
  h.estado_sigla,
  h.codigo_ibge_municipio,
  m.municipios_nome,
  h.tipo_unidade_critica,
  h.categoria_atendimento,
  h.classe_capacidade_saude,
  COUNT(DISTINCT h.codigo_cnes) AS hospitais_total,
  SUM(CASE WHEN h.funciona_24h = 'SIM' THEN 1 ELSE 0 END) AS hospitais_24h,
  SUM(CASE WHEN h.ate_50km = 1 THEN 1 ELSE 0 END) AS hospitais_ate_50km_ti
FROM dim_hospitais_cnes h
LEFT JOIN dim_municipios_coordenadas m
  ON h.codigo_ibge_municipio = m.codigo_ibge
WHERE h.funciona_24h = 'SIM'
   OR h.tipo_unidade_critica <> 'NAO INFORMADO'
GROUP BY
  m.regiao_brasil,
  h.estado_sigla,
  h.codigo_ibge_municipio,
  m.municipios_nome,
  h.tipo_unidade_critica,
  h.categoria_atendimento,
  h.classe_capacidade_saude
ORDER BY hospitais_total DESC;
