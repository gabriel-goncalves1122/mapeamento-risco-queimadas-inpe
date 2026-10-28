SELECT 'CRITICAL' AS severity, 'eventos_com_menos_que_min_samples' AS check_name, COUNT(*) AS failures
FROM fato_eventos_incendio
WHERE total_focos < param_min_samples;

SELECT 'CRITICAL' AS severity, 'eventos_com_duracao_maior_que_parametro' AS check_name, COUNT(*) AS failures
FROM fato_eventos_incendio
WHERE duracao_dias > param_max_duration_days;

SELECT 'CRITICAL' AS severity, 'eventos_sem_path_json' AS check_name, COUNT(*) AS failures
FROM fato_eventos_incendio
WHERE path_json IS NULL OR path_json = '' OR path_json = '[]';

SELECT 'CRITICAL' AS severity, 'eventos_municipio_principal_orfao' AS check_name, COUNT(*) AS failures
FROM fato_eventos_incendio f
LEFT JOIN dim_municipios_coordenadas m ON f.fk_municipio_principal = m.codigo_ibge
WHERE f.fk_municipio_principal <> 'NAO INFORMADO'
  AND m.codigo_ibge IS NULL;

SELECT 'WARNING' AS severity, 'eventos_sem_ti_proxima' AS check_name, COUNT(*) AS failures
FROM fato_eventos_incendio
WHERE fk_terra_indigena_proxima IS NULL
   OR fk_terra_indigena_proxima = ''
   OR fk_terra_indigena_proxima = 'NAO INFORMADO';

SELECT 'WARNING' AS severity, 'eventos_sem_hospital_proximo' AS check_name, COUNT(*) AS failures
FROM fato_eventos_incendio
WHERE fk_hospital IS NULL OR fk_hospital = '' OR fk_hospital = 'NAO INFORMADO';

SELECT 'INFO' AS severity, 'hospitais_distintos_na_fato' AS check_name, COUNT(DISTINCT fk_hospital) AS failures
FROM fato_eventos_incendio
WHERE fk_hospital <> 'NAO INFORMADO';
