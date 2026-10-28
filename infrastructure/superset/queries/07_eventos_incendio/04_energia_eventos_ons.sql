-- setor: eventos_incendio
-- objetivo: cruzar eventos com linhas e subestacoes ONS por proximidade operacional
-- datasource: fato_eventos_incendio, dim_ons_linhas_transmissao, dim_ons_subestacoes
-- granularidade: ativo_ons
-- visualizacao: tabela_ranking
SELECT
  f.fk_linha_transmissao,
  l.classe_tensao,
  l.classe_criticidade_linha,
  f.fk_subestacao,
  s.criticidade_subestacao,
  COUNT(*) AS total_eventos,
  SUM(f.total_focos) AS focos_representados,
  MIN(f.distancia_linha_km) AS menor_distancia_linha_km,
  MIN(f.distancia_subestacao_km) AS menor_distancia_subestacao_km,
  MAX(f.indice_ameaca_linha) AS maior_ameaca_linha,
  MAX(f.indice_ameaca_subestacao) AS maior_ameaca_subestacao
FROM fato_eventos_incendio f
LEFT JOIN dim_ons_linhas_transmissao l
  ON f.fk_linha_transmissao = l.id_linha_transmissao
LEFT JOIN dim_ons_subestacoes s
  ON f.fk_subestacao = s.id_subestacao
GROUP BY 1, 2, 3, 4, 5
ORDER BY maior_ameaca_subestacao DESC;
