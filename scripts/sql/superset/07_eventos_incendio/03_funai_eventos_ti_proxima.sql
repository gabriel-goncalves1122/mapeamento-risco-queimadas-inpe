-- setor: eventos_incendio
-- objetivo: analisar pressao de eventos sobre terras indigenas proximas
-- datasource: fato_eventos_incendio, dim_terras_indigenas
-- granularidade: terra_indigena
-- visualizacao: tabela_ranking
SELECT
  f.fk_terra_indigena_proxima AS codigo_ti,
  t.nome_terra_indigena,
  t.estado_sigla,
  t.prioridade_funai,
  COUNT(*) AS total_eventos,
  SUM(f.total_focos) AS focos_representados,
  MIN(f.distancia_terra_indigena_km) AS menor_distancia_km,
  AVG(f.distancia_terra_indigena_km) AS distancia_media_km,
  MAX(f.indice_pressao_terra_indigena) AS maior_pressao_ti
FROM fato_eventos_incendio f
LEFT JOIN dim_terras_indigenas t
  ON f.fk_terra_indigena_proxima = t.codigo_ti
WHERE f.fk_terra_indigena_proxima <> 'NAO INFORMADO'
GROUP BY 1, 2, 3, 4
ORDER BY total_eventos DESC;
