-- ============================================================
-- VIRTUAL DATASET: Focos Individuais — Dispersão Geográfica
-- ALIMENTA: Scatter Plot / Mapa de Pontos no Dashboard Focos
-- TABELA BASE: fato_focos_incendio
-- ============================================================
-- Utiliza a coluna sample_bucket (hash de lat+lon+time, 0-99)
-- para garantir amostragem uniforme por todo o território,
-- evitando concentração regional causada pelo Early Termination.
-- ============================================================
SELECT
  __time,
  latitude,
  longitude,
  potencia_radiativa_fogo AS frp,
  risco_fogo_inpe,
  dias_sem_chuva,
  fk_bioma,
  fk_municipio,
  LOOKUP(fk_municipio, 'municipios_nome') AS municipio_nome,
  LOOKUP(fk_municipio, 'municipios_uf') AS municipio_uf
FROM fato_focos_incendio
WHERE coordenada_valida = 1
  AND sample_bucket < 5
  {% if from_dttm is defined and from_dttm is not none %}
  AND __time >= '{{ from_dttm }}' AND __time < '{{ to_dttm }}'
  {% endif %}
GROUP BY 1, 2, 3, 4, 5, 6, 7, 8, 9, 10
ORDER BY frp DESC
LIMIT 50000