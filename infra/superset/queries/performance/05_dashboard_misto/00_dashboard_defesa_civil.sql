-- categoria: dashboard_misto
-- objetivo: simular painel territorial combinando municipios, hospitais e TIs
-- datasource: dim_municipios_coordenadas, dim_hospitais_cnes, dim_terras_indigenas
-- padrao_carga: dashboard_composite
-- visualizacao: tabela_mapa
WITH hospitais AS (
  SELECT
    codigo_ibge,
    COUNT(*) AS hospitais_total,
    SUM(CASE WHEN funciona_24h = 'SIM' THEN 1 ELSE 0 END) AS hospitais_24h,
    SUM(CASE WHEN dentro_terra_indigena = 1 THEN 1 ELSE 0 END) AS hospitais_ate_50km_ti
  FROM dim_hospitais_cnes
  GROUP BY codigo_ibge
),
terras AS (
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
  COUNT(*) AS municipios_total,
  SUM(COALESCE(h.hospitais_total, 0)) AS hospitais_total,
  SUM(COALESCE(h.hospitais_24h, 0)) AS hospitais_24h,
  SUM(COALESCE(h.hospitais_ate_50km_ti, 0)) AS hospitais_ate_50km_ti,
  SUM(COALESCE(t.terras_indigenas_total, 0)) AS terras_indigenas_total,
  SUM(COALESCE(t.area_ti_hectares, 0)) AS area_ti_hectares
FROM dim_municipios_coordenadas m
LEFT JOIN hospitais h
  ON h.codigo_ibge = m.codigo_ibge
LEFT JOIN terras t
  ON t.codigo_ibge_principal = m.codigo_ibge
GROUP BY
  m.regiao_brasil,
  m.estado_sigla
ORDER BY hospitais_total DESC;
