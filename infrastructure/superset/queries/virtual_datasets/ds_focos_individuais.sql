-- ============================================================
-- VIRTUAL DATASET: Focos Individuais (Granularidade Fina)
-- ALIMENTA: Dashboard Focos
-- TABELA BASE: fato_focos_incendio
-- ============================================================
SELECT
  __time,
  latitude,
  longitude,
  
  -- Metrics
  potencia_radiativa_fogo AS frp,
  risco_fogo_inpe,
  dias_sem_chuva,
  
  -- Dimensions & Lookups
  fk_bioma,
  fk_satelite_sensor,
  fk_municipio,
  LOOKUP(fk_municipio, 'municipios_nome') AS municipio_nome,
  LOOKUP(fk_municipio, 'municipios_uf') AS municipio_uf

FROM fato_focos_incendio
WHERE
  latitude IS NOT NULL
  AND longitude IS NOT NULL
  AND coordenada_valida = 1
  {% if from_dttm is not none %}
  AND __time >= '{{ from_dttm }}' AND __time < '{{ to_dttm }}'
  {% endif %}
GROUP BY 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11
ORDER BY frp DESC
LIMIT 50000
