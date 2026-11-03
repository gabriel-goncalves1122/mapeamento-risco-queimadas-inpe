-- setor: eventos_incendio
-- objetivo: enriquecer apenas os hospitais mais afetados, evitando join realtime amplo com CNES
-- datasource: dim_hospitais_cnes, fato_eventos_incendio
-- granularidade: hospital_top
-- visualizacao: tabela_detalhe
WITH top_hospitais AS (
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
  ORDER BY total_eventos DESC
  LIMIT 100
)
SELECT
  h.codigo_cnes,
  h.nome_hospital,
  h.codigo_ibge_municipio,
  h.categoria_unidade,
  h.tipo_unidade_critica,
  h.funciona_24h,
  h.latitude,
  h.longitude,
  t.total_eventos,
  t.focos_representados,
  t.menor_distancia_km,
  t.distancia_media_km,
  t.maior_pressao_saude
FROM dim_hospitais_cnes h
INNER JOIN top_hospitais t
  ON h.codigo_cnes = t.codigo_cnes;
