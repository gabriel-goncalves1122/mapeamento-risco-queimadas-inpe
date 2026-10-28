-- ============================================================
-- VIRTUAL DATASET: Eventos Geral & Defesa Civil
-- ALIMENTA: Painel Geral e Dashboard Defesa Civil
-- TABELA BASE: fato_eventos_incendio
-- ============================================================
SELECT
  fire_event_id,
  __time,
  -- Geolocation & Basic info
  latitude_centroide,
  longitude_centroide,
  fk_bioma,
  
  -- Metrics
  total_focos,
  soma_frp,
  max_frp,
  area_evento_km2,
  duracao_dias,
  media_risco_fogo,
  
  -- Município Lookups
  fk_municipio_principal,
  LOOKUP(fk_municipio_principal, 'municipios_nome') AS municipio_nome,
  LOOKUP(fk_municipio_principal, 'municipios_uf') AS municipio_uf,
  LOOKUP(fk_municipio_principal, 'municipios_regiao') AS municipio_regiao,
  
  -- Saúde Metrics & Lookups
  indice_pressao_maxima,
  indice_pressao_saude,
  distancia_hospital_km,
  fk_hospital,
  LOOKUP(fk_hospital, 'hospitais_nome') AS hospital_nome,
  LOOKUP(fk_hospital, 'hospitais_tipo') AS hospital_tipo,
  LOOKUP(fk_hospital, 'hospitais_critico') AS hospital_critico,
  LOOKUP(fk_hospital, 'hospitais_24h') AS hospital_24h
FROM fato_eventos_incendio
WHERE 1=1
  {% if from_dttm is not none %}
  AND __time >= '{{ from_dttm }}' AND __time < '{{ to_dttm }}'
  {% endif %}
GROUP BY 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23
ORDER BY max_frp DESC
LIMIT 50000
