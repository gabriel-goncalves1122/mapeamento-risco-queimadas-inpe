-- categoria: joins_dimensionais
-- objetivo: simular dashboard combinando municipios, hospitais e TIs
-- datasource: dim_municipios_coordenadas, dim_hospitais_cnes, dim_terras_indigenas
-- padrao_carga: multi_join_aggregate
-- visualizacao: tabela_mapa
WITH hospitais_por_municipio AS (
  SELECT
    codigo_ibge_municipio,
    COUNT(DISTINCT codigo_cnes) AS hospitais_total,
    SUM(CASE WHEN ate_15km = 1 THEN 1 ELSE 0 END) AS hospitais_ate_15km_ti
  FROM dim_hospitais_cnes
  GROUP BY codigo_ibge_municipio
),
tis_por_municipio AS (
  SELECT
    codigo_ibge_principal,
    COUNT(*) AS terras_indigenas_total,
    SUM(area_hectares) AS area_ti_hectares
  FROM dim_terras_indigenas
  GROUP BY codigo_ibge_principal
)
SELECT
  m.regiao_brasil,
  m.estado_sigla,
  m.codigo_ibge,
  m.municipios_nome,
  COALESCE(h.hospitais_total, 0) AS hospitais_total,
  COALESCE(h.hospitais_ate_15km_ti, 0) AS hospitais_ate_15km_ti,
  COALESCE(t.terras_indigenas_total, 0) AS terras_indigenas_total,
  COALESCE(t.area_ti_hectares, 0) AS area_ti_hectares
FROM dim_municipios_coordenadas m
LEFT JOIN hospitais_por_municipio h
  ON h.codigo_ibge_municipio = m.codigo_ibge
LEFT JOIN tis_por_municipio t
  ON t.codigo_ibge_principal = m.codigo_ibge;
