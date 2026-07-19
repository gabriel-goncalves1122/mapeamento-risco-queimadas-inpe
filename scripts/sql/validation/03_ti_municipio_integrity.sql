SELECT 'CRITICAL' AS severity, 'ti_sem_municipio_nativo' AS check_name, COUNT(*) AS failures
FROM dim_terras_indigenas
WHERE codigo_ibge_principal IS NULL OR codigo_ibge_principal = '' OR codigo_ibge_principal = 'NAO INFORMADO';

SELECT 'CRITICAL' AS severity, 'ti_sem_lista_multivalue' AS check_name, COUNT(*) AS failures
FROM dim_terras_indigenas
WHERE codigos_ibge_interceptados IS NULL OR codigos_ibge_interceptados = '' OR codigos_ibge_interceptados = 'NAO INFORMADO';

SELECT 'WARNING' AS severity, 'ti_com_fallback_municipio_proximo' AS check_name, COUNT(*) AS failures
FROM dim_terras_indigenas
WHERE match_status_municipios = 'FALLBACK_MUNICIPIO_PROXIMO';

SELECT codigo_ti, codigo_ibge_principal, codigos_ibge_interceptados, qtd_municipios_interceptados, percentual_area_interceptada, match_status_municipios
FROM dim_terras_indigenas
LIMIT 50;
