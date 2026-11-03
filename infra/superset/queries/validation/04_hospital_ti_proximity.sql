SELECT 'CRITICAL' AS severity, 'hospital_sem_ti_proxima' AS check_name, COUNT(*) AS failures
FROM dim_hospitais_cnes
WHERE codigo_ti_proxima IS NULL OR codigo_ti_proxima = '' OR codigo_ti_proxima = 'NAO INFORMADO';

SELECT dentro_terra_indigena, ate_1km, ate_3km, ate_7km, ate_15km, ate_50km, COUNT(*) AS hospitais
FROM dim_hospitais_cnes
GROUP BY dentro_terra_indigena, ate_1km, ate_3km, ate_7km, ate_15km, ate_50km
ORDER BY hospitais DESC;

SELECT codigo_cnes, codigo_ti_proxima, distancia_ti_km, dentro_terra_indigena, ate_15km
FROM dim_hospitais_cnes
WHERE dentro_terra_indigena = 1 OR ate_15km = 1
LIMIT 50;
