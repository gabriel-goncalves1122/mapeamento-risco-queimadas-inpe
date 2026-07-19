SELECT 'CRITICAL' AS severity, 'hospitais_fora_bbox_brasil' AS check_name, COUNT(*) AS failures
FROM dim_hospitais_cnes
WHERE latitude < -35 OR latitude > 6 OR longitude < -75 OR longitude > -30;

SELECT 'CRITICAL' AS severity, 'municipios_centroide_fora_bbox_brasil' AS check_name, COUNT(*) AS failures
FROM dim_municipios_coordenadas
WHERE latitude < -35 OR latitude > 6 OR longitude < -75 OR longitude > -30;

SELECT 'WARNING' AS severity, 'terras_centroide_fora_bbox_brasil' AS check_name, COUNT(*) AS failures
FROM dim_terras_indigenas
WHERE latitude < -35 OR latitude > 6 OR longitude < -75 OR longitude > -30;

SELECT 'CRITICAL' AS severity, 'municipios_codigo_ibge_duplicado' AS check_name, COUNT(*) AS failures
FROM (
  SELECT codigo_ibge
  FROM dim_municipios_coordenadas
  GROUP BY codigo_ibge
  HAVING COUNT(*) > 1
);

SELECT 'CRITICAL' AS severity, 'hospitais_codigo_cnes_duplicado' AS check_name, COUNT(*) AS failures
FROM (
  SELECT codigo_cnes
  FROM dim_hospitais_cnes
  GROUP BY codigo_cnes
  HAVING COUNT(*) > 1
);

SELECT 'CRITICAL' AS severity, 'terras_codigo_ti_duplicado' AS check_name, COUNT(*) AS failures
FROM (
  SELECT codigo_ti
  FROM dim_terras_indigenas
  GROUP BY codigo_ti
  HAVING COUNT(*) > 1
);
