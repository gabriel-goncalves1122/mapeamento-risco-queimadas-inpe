-- ============================================================
-- VIRTUAL DATASET: Focos Ameaçando Infraestrutura (Layer 2)
-- ALIMENTA: Mapa Múltiplo Deck.GL (Camada de Dispersão Scatter)
-- ============================================================
SELECT
  __time,
  latitude_centroide AS latitude,
  longitude_centroide AS longitude,
  max_frp,
  CASE 
    WHEN indice_ameaca_linha > 0 THEN 'Ameaça a Linha'
    WHEN indice_ameaca_subestacao > 0 THEN 'Ameaça a Subestação'
    ELSE 'Outros'
  END AS tipo_ameaca
FROM fato_eventos_incendio
WHERE 
  (indice_ameaca_linha > 0 OR indice_ameaca_subestacao > 0 OR indice_ameaca_sistema_isolado > 0)
  AND sample_bucket < 25 -- Amostragem para densidade customizável
  {% if from_dttm is defined and from_dttm is not none %}
  AND __time >= '{{ from_dttm }}' AND __time < '{{ to_dttm }}'
  {% endif %}
-- Agrupamento limpo focando apenas nos dados de Heatmap/Scatter
GROUP BY 1, 2, 3, 4, 5
ORDER BY max_frp DESC
LIMIT 50000
