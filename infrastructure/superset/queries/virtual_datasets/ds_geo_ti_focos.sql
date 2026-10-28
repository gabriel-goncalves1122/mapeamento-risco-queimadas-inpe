-- ============================================================
-- VIRTUAL DATASET: Focos em Terras Indígenas (Layer 2)
-- ALIMENTA: Mapa Múltiplo Deck.GL (Camada de Dispersão Scatter)
-- ============================================================
SELECT
  __time,
  latitude_centroide AS latitude,
  longitude_centroide AS longitude,
  max_frp,
  CASE
    WHEN fk_terra_indigena IS NOT NULL AND fk_terra_indigena != 'NAO INFORMADO' THEN 'DENTRO'
    ELSE 'ENTORNO'
  END AS tipo_ameaca
FROM fato_eventos_incendio
WHERE 
  ((fk_terra_indigena IS NOT NULL AND fk_terra_indigena != 'NAO INFORMADO') OR indice_pressao_terra_indigena > 0)
  AND sample_bucket < 25 -- Amostragem otimizada
  {% if from_dttm is defined and from_dttm is not none %}
  AND __time >= '{{ from_dttm }}' AND __time < '{{ to_dttm }}'
  {% endif %}
-- Agrupamento por coordenadas para evitar renderizar milhares de geometrias inúteis
GROUP BY 1, 2, 3, 4, 5
ORDER BY max_frp DESC
LIMIT 50000
