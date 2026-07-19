SELECT 'CRITICAL' AS severity, 'fk_hospital_sem_codigo_municipio_nativo' AS check_name, COUNT(*) AS failures
FROM dim_hospitais_cnes
WHERE codigo_ibge_municipio IS NULL OR codigo_ibge_municipio = '' OR codigo_ibge_municipio = 'NAO INFORMADO';

SELECT 'CRITICAL' AS severity, 'fk_ti_sem_codigo_municipio_nativo' AS check_name, COUNT(*) AS failures
FROM dim_terras_indigenas
WHERE codigo_ibge_principal IS NULL OR codigo_ibge_principal = '' OR codigo_ibge_principal = 'NAO INFORMADO';

SELECT 'CRITICAL' AS severity, 'fk_hospital_ti_sem_codigo_nativo' AS check_name, COUNT(*) AS failures
FROM dim_hospitais_cnes
WHERE codigo_ti_proxima IS NULL OR codigo_ti_proxima = '' OR codigo_ti_proxima = 'NAO INFORMADO';

SELECT 'CRITICAL' AS severity, 'fk_hospital_municipio_inexistente' AS check_name, COUNT(*) AS failures
FROM dim_hospitais_cnes h
LEFT JOIN dim_municipios_coordenadas m ON h.codigo_ibge_municipio = m.codigo_ibge
WHERE m.codigo_ibge IS NULL;

SELECT 'WARNING' AS severity, 'hospital_municipio_por_fallback_proximo' AS check_name, COUNT(*) AS failures
FROM dim_hospitais_cnes
WHERE match_status_municipio = 'FALLBACK_MUNICIPIO_PROXIMO';
