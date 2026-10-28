SELECT 'CRITICAL' AS severity, 'hospital_sem_municipio_nativo' AS check_name, COUNT(*) AS failures
FROM dim_hospitais_cnes
WHERE codigo_ibge_municipio IS NULL OR codigo_ibge_municipio = '' OR codigo_ibge_municipio = 'NAO INFORMADO';

SELECT 'WARNING' AS severity, 'hospital_municipio_por_fallback_proximo' AS check_name, COUNT(*) AS failures
FROM dim_hospitais_cnes
WHERE match_status_municipio = 'FALLBACK_MUNICIPIO_PROXIMO';

SELECT codigo_ibge_municipio, COUNT(*) AS hospitais
FROM dim_hospitais_cnes
GROUP BY codigo_ibge_municipio
ORDER BY hospitais DESC
LIMIT 20;

SELECT codigo_cnes, nome_hospital, codigo_ibge_municipio, codigo_ibge_cnes, municipios_nome, match_status_municipio
FROM dim_hospitais_cnes
WHERE match_status_municipio <> 'OK_ESPACIAL'
LIMIT 50;
