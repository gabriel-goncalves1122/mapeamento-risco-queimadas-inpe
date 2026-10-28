-- setor: eventos_incendio
-- objetivo: agregar eventos por codigo CNES sem join amplo com a dimensao de hospitais
-- datasource: fato_eventos_incendio
-- granularidade: hospital_fk
-- visualizacao: tabela_ranking
SELECT
  fk_hospital AS codigo_cnes,
  COUNT(*) AS total_eventos,
  SUM(total_focos) AS focos_representados,
  MIN(distancia_hospital_km) AS menor_distancia_km,
  AVG(distancia_hospital_km) AS distancia_media_km,
  MAX(indice_pressao_saude) AS maior_pressao_saude
FROM fato_eventos_incendio
WHERE fk_hospital <> 'NAO INFORMADO'
GROUP BY 1
ORDER BY total_eventos DESC;
