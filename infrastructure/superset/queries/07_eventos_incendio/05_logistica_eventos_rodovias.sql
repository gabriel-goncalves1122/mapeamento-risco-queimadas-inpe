-- setor: eventos_incendio
-- objetivo: priorizar rodovias federais proximas de eventos de incendio
-- datasource: fato_eventos_incendio, dim_rodovias_federais
-- granularidade: trecho_rodoviario
-- visualizacao: tabela_ranking
SELECT
  f.fk_trecho_rodoviario,
  r.codigo_rodovia,
  r.status_operacional,
  r.criticidade_rodovia,
  COUNT(*) AS total_eventos,
  SUM(f.total_focos) AS focos_representados,
  MIN(f.distancia_rodovia_km) AS menor_distancia_km,
  AVG(f.distancia_rodovia_km) AS distancia_media_km,
  MAX(f.indice_ameaca_rodovia) AS maior_ameaca_rodovia
FROM fato_eventos_incendio f
LEFT JOIN dim_rodovias_federais r
  ON f.fk_trecho_rodoviario = r.id_trecho_rodoviario
WHERE f.fk_trecho_rodoviario <> 'NAO INFORMADO'
GROUP BY 1, 2, 3, 4
ORDER BY total_eventos DESC;
