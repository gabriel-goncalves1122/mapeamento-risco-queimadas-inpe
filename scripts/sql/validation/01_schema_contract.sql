SELECT 'CRITICAL' AS severity, 'municipios_path_json_vazio' AS check_name, COUNT(*) AS failures
FROM dim_municipios_coordenadas
WHERE path_json IS NULL OR path_json = '' OR path_json = '[]';

SELECT 'CRITICAL' AS severity, 'hospitais_path_json_vazio' AS check_name, COUNT(*) AS failures
FROM dim_hospitais_cnes
WHERE path_json IS NULL OR path_json = '' OR path_json = '[]';

SELECT 'CRITICAL' AS severity, 'terras_path_json_vazio' AS check_name, COUNT(*) AS failures
FROM dim_terras_indigenas
WHERE path_json IS NULL OR path_json = '' OR path_json = '[]';

SELECT 'CRITICAL' AS severity, 'hospitais_sem_codigo_ibge_municipio' AS check_name, COUNT(*) AS failures
FROM dim_hospitais_cnes
WHERE codigo_ibge_municipio IS NULL OR codigo_ibge_municipio = '' OR codigo_ibge_municipio = 'NAO INFORMADO';

SELECT 'CRITICAL' AS severity, 'terras_sem_codigos_ibge_interceptados' AS check_name, COUNT(*) AS failures
FROM dim_terras_indigenas
WHERE codigos_ibge_interceptados IS NULL OR codigos_ibge_interceptados = '' OR codigos_ibge_interceptados = 'NAO INFORMADO';
